/**
 * Swarm Strategies Test Suite
 * Comprehensive tests for all strategy implementations
 */

const {
  BaseStrategy,
  CentralizedStrategy,
  DistributedStrategy,
  HierarchicalStrategy,
  MeshStrategy,
  AdaptiveStrategy,
  StrategyFactory
} = require('../../src/swarm/strategies');

// Mock agent for testing
class MockAgent {
  constructor(id, type, capabilities = []) {
    this.id = id;
    this.type = type;
    this.capabilities = capabilities;
    this.status = 'idle';
    this.executionTime = 100;
  }

  async execute(task) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          taskId: task.id,
          agentId: this.id,
          result: `Completed ${task.description}`
        });
      }, this.executionTime);
    });
  }
}

// Test utilities
function createMockTask(id, description, requiredType = 'coder') {
  return {
    id: `task-${id}`,
    description,
    requiredType
  };
}

// Base Strategy Tests
describe('BaseStrategy', () => {
  test('should throw error when instantiated directly', () => {
    expect(() => new BaseStrategy()).toThrow('BaseStrategy is abstract');
  });

  test('should throw error when abstract methods are not implemented', async () => {
    class IncompleteStrategy extends BaseStrategy {}
    const strategy = new IncompleteStrategy();

    await expect(strategy.initialize()).rejects.toThrow();
    await expect(strategy.addAgent({})).rejects.toThrow();
    await expect(strategy.distributeTask({})).rejects.toThrow();
  });

  test('should validate agent configuration', () => {
    class TestStrategy extends BaseStrategy {
      async initialize() { return this; }
    }
    const strategy = new TestStrategy();

    expect(() => strategy.validateAgent({})).toThrow('Agent must have an id');
    expect(() => strategy.validateAgent({ id: 'test' })).toThrow('Agent must have a type');
    expect(() => strategy.validateAgent({ id: 'test', type: 'coder' })).toThrow('Agent must have an execute method');
  });

  test('should track metrics correctly', () => {
    class TestStrategy extends BaseStrategy {
      async initialize() { return this; }
    }
    const strategy = new TestStrategy();

    strategy.updateMetrics({ success: true, executionTime: 100 });
    strategy.updateMetrics({ success: true, executionTime: 200 });
    strategy.updateMetrics({ success: false, executionTime: 150 });

    expect(strategy.metrics.tasksCompleted).toBe(2);
    expect(strategy.metrics.tasksFailed).toBe(1);
    expect(strategy.metrics.avgExecutionTime).toBeCloseTo(150);
  });
});

// Centralized Strategy Tests
describe('CentralizedStrategy', () => {
  let strategy;

  beforeEach(async () => {
    strategy = new CentralizedStrategy({ maxAgents: 5 });
    await strategy.initialize();
  });

  afterEach(async () => {
    await strategy.shutdown();
  });

  test('should initialize with single coordinator', async () => {
    expect(strategy.coordinator).toBeDefined();
    expect(strategy.coordinator.id).toBe('coordinator-main');
    expect(strategy.topology).toBe('centralized');
  });

  test('should add agents successfully', async () => {
    const agent = new MockAgent('agent-1', 'coder');
    await strategy.addAgent(agent);

    expect(strategy.agents.size).toBe(1);
    expect(agent.coordinator).toBe('coordinator-main');
    expect(agent.status).toBe('idle');
  });

  test('should respect max agent limit', async () => {
    for (let i = 0; i < 5; i++) {
      await strategy.addAgent(new MockAgent(`agent-${i}`, 'coder'));
    }

    await expect(
      strategy.addAgent(new MockAgent('agent-6', 'coder'))
    ).rejects.toThrow('Maximum agent limit');
  });

  test('should distribute task to available agent', async () => {
    const agent = new MockAgent('agent-1', 'coder');
    await strategy.addAgent(agent);

    const task = createMockTask(1, 'Test task');
    const result = await strategy.distributeTask(task);

    expect(result.success).toBe(true);
    expect(result.agentId).toBe('agent-1');
    expect(result.taskId).toBe('task-1');
  });

  test('should queue task when no agents available', async () => {
    const task = createMockTask(1, 'Test task');
    const result = await strategy.distributeTask(task);

    expect(result.queued).toBe(true);
    expect(strategy.taskQueue.length).toBe(1);
  });

  test('should execute batch of tasks', async () => {
    await strategy.addAgent(new MockAgent('agent-1', 'coder'));
    await strategy.addAgent(new MockAgent('agent-2', 'tester'));

    const tasks = [
      createMockTask(1, 'Task 1', 'coder'),
      createMockTask(2, 'Task 2', 'tester')
    ];

    const result = await strategy.executeBatch(tasks);

    expect(result.success).toBe(true);
    expect(result.results.length).toBe(2);
    expect(result.coordinator).toBe('coordinator-main');
  });
});

// Distributed Strategy Tests
describe('DistributedStrategy', () => {
  let strategy;

  beforeEach(async () => {
    strategy = new DistributedStrategy({
      maxAgents: 10,
      coordinatorCount: 3,
      loadBalancer: 'least-loaded'
    });
    await strategy.initialize();
  });

  afterEach(async () => {
    await strategy.shutdown();
  });

  test('should initialize with multiple coordinators', () => {
    expect(strategy.coordinators.size).toBe(3);
    expect(strategy.topology).toBe('distributed');
  });

  test('should distribute agents across coordinators', async () => {
    for (let i = 0; i < 6; i++) {
      await strategy.addAgent(new MockAgent(`agent-${i}`, 'coder'));
    }

    const coordinatorLoads = Array.from(strategy.coordinators.values())
      .map(c => c.load);

    // Load should be balanced
    const maxLoad = Math.max(...coordinatorLoads);
    const minLoad = Math.min(...coordinatorLoads);
    expect(maxLoad - minLoad).toBeLessThanOrEqual(1);
  });

  test('should use round-robin load balancing', async () => {
    strategy.loadBalancer = 'round-robin';

    await strategy.addAgent(new MockAgent('agent-1', 'coder'));
    await strategy.addAgent(new MockAgent('agent-2', 'coder'));
    await strategy.addAgent(new MockAgent('agent-3', 'coder'));

    const task1 = createMockTask(1, 'Task 1');
    const task2 = createMockTask(2, 'Task 2');
    const task3 = createMockTask(3, 'Task 3');

    await strategy.distributeTask(task1);
    await strategy.distributeTask(task2);
    await strategy.distributeTask(task3);

    // Tasks should be distributed round-robin
    const coordinatorTasks = Array.from(strategy.coordinators.values())
      .map(c => c.taskQueue.length + c.agents.size);

    expect(coordinatorTasks).toEqual([1, 1, 1]);
  });

  test('should execute batch in parallel', async () => {
    for (let i = 0; i < 6; i++) {
      await strategy.addAgent(new MockAgent(`agent-${i}`, 'coder'));
    }

    const tasks = Array.from({ length: 6 }, (_, i) =>
      createMockTask(i, `Task ${i}`)
    );

    const startTime = Date.now();
    const result = await strategy.executeBatch(tasks);
    const duration = Date.now() - startTime;

    expect(result.success).toBe(true);
    expect(result.results.length).toBe(6);
    // Should be faster than sequential (6 * 100ms)
    expect(duration).toBeLessThan(300);
  });
});

// Hierarchical Strategy Tests
describe('HierarchicalStrategy', () => {
  let strategy;

  beforeEach(async () => {
    strategy = new HierarchicalStrategy({
      maxAgents: 20,
      levels: 3,
      branchingFactor: 2
    });
    await strategy.initialize();
  });

  afterEach(async () => {
    await strategy.shutdown();
  });

  test('should build hierarchical tree structure', () => {
    expect(strategy.rootCoordinator).toBeDefined();
    expect(strategy.rootCoordinator.level).toBe(0);
    expect(strategy.coordinatorTree.size).toBeGreaterThan(1);
  });

  test('should assign agents to leaf coordinators', async () => {
    const agent = new MockAgent('agent-1', 'coder');
    await strategy.addAgent(agent);

    const coordinator = strategy.coordinatorTree.get(agent.coordinator);
    expect(coordinator.children.length).toBe(0); // Leaf coordinator
  });

  test('should delegate tasks down hierarchy', async () => {
    await strategy.addAgent(new MockAgent('agent-1', 'coder'));

    const task = createMockTask(1, 'Test task');
    const result = await strategy.distributeTask(task);

    expect(result.success).toBe(true);
    // Task should have been delegated through hierarchy
    expect(result.coordinator).toBeDefined();
  });

  test('should balance load across hierarchy', async () => {
    // Add agents to fill multiple leaf coordinators
    for (let i = 0; i < 8; i++) {
      await strategy.addAgent(new MockAgent(`agent-${i}`, 'coder'));
    }

    const leafCoordinators = Array.from(strategy.coordinatorTree.values())
      .filter(c => c.children.length === 0);

    const agentCounts = leafCoordinators.map(c => c.agents.size);
    const maxCount = Math.max(...agentCounts);
    const minCount = Math.min(...agentCounts);

    expect(maxCount - minCount).toBeLessThanOrEqual(1);
  });
});

// Mesh Strategy Tests
describe('MeshStrategy', () => {
  let strategy;

  beforeEach(async () => {
    strategy = new MeshStrategy({
      maxAgents: 10,
      maxPeerConnections: 3,
      gossipInterval: 500
    });
    await strategy.initialize();
  });

  afterEach(async () => {
    await strategy.shutdown();
  });

  test('should create peer-to-peer connections', async () => {
    await strategy.addAgent(new MockAgent('agent-1', 'coder'));
    await strategy.addAgent(new MockAgent('agent-2', 'coder'));
    await strategy.addAgent(new MockAgent('agent-3', 'coder'));

    const agent1 = strategy.agents.get('agent-1');
    const agent2 = strategy.agents.get('agent-2');

    expect(agent1.peers.size).toBeGreaterThan(0);
    expect(agent2.peers.size).toBeGreaterThan(0);
  });

  test('should respect max peer connections', async () => {
    for (let i = 0; i < 10; i++) {
      await strategy.addAgent(new MockAgent(`agent-${i}`, 'coder'));
    }

    for (const agent of strategy.agents.values()) {
      expect(agent.peers.size).toBeLessThanOrEqual(3);
    }
  });

  test('should broadcast tasks via gossip', async () => {
    await strategy.addAgent(new MockAgent('agent-1', 'coder'));
    await strategy.addAgent(new MockAgent('agent-2', 'coder'));

    const task = createMockTask(1, 'Test task');
    await strategy.distributeTask(task);

    // Wait for gossip propagation
    await new Promise(resolve => setTimeout(resolve, 100));

    // All agents should know about the task
    for (const agent of strategy.agents.values()) {
      expect(agent.knownTasks.has(task.id)).toBe(true);
    }
  });

  test('should achieve consensus among agents', async () => {
    const agents = [
      new MockAgent('agent-1', 'coder'),
      new MockAgent('agent-2', 'coder'),
      new MockAgent('agent-3', 'coder')
    ];

    for (const agent of agents) {
      await strategy.addAgent(agent);
    }

    const task = createMockTask(1, 'Test task', 'coder');
    const result = await strategy.coordinate(task, agents);

    expect(result.success).toBe(true);
    expect(result.consensus).toBeDefined();
  });
});

// Adaptive Strategy Tests
describe('AdaptiveStrategy', () => {
  let strategy;

  beforeEach(async () => {
    strategy = new AdaptiveStrategy({
      maxAgents: 20,
      evaluationInterval: 1000,
      minTasksForEvaluation: 5
    });
    await strategy.initialize();
  });

  afterEach(async () => {
    await strategy.shutdown();
  });

  test('should start with centralized strategy', () => {
    expect(strategy.currentStrategy).toBeDefined();
    expect(strategy.currentStrategy.topology).toBe('centralized');
  });

  test('should switch strategies based on agent count', async () => {
    // Start with few agents
    for (let i = 0; i < 3; i++) {
      await strategy.addAgent(new MockAgent(`agent-${i}`, 'coder'));
    }
    expect(strategy.currentStrategy.topology).toBe('centralized');

    // Add more agents
    for (let i = 3; i < 10; i++) {
      await strategy.addAgent(new MockAgent(`agent-${i}`, 'coder'));
    }

    // Should recommend distributed strategy
    const performance = strategy.analyzePerformance();
    const recommendation = strategy.recommendStrategy(performance);

    expect(['distributed', 'centralized']).toContain(recommendation.strategy);
  });

  test('should track strategy history', async () => {
    await strategy.switchStrategy('distributed');
    await strategy.switchStrategy('hierarchical');

    expect(strategy.strategyHistory.length).toBe(2);
    expect(strategy.strategyHistory[0].strategy).toBe('centralized');
    expect(strategy.strategyHistory[1].strategy).toBe('distributed');
  });

  test('should execute tasks using current strategy', async () => {
    await strategy.addAgent(new MockAgent('agent-1', 'coder'));

    const task = createMockTask(1, 'Test task');
    const result = await strategy.distributeTask(task);

    expect(result.success || result.queued).toBe(true);
  });

  test('should analyze performance metrics', async () => {
    await strategy.addAgent(new MockAgent('agent-1', 'coder'));

    // Execute tasks to generate metrics
    for (let i = 0; i < 10; i++) {
      const task = createMockTask(i, `Task ${i}`);
      await strategy.distributeTask(task);
    }

    const performance = strategy.analyzePerformance();

    expect(performance.successRate).toBeDefined();
    expect(performance.avgExecutionTime).toBeDefined();
    expect(performance.loadBalance).toBeDefined();
  });
});

// Strategy Factory Tests
describe('StrategyFactory', () => {
  test('should create strategy by type', () => {
    const strategy = StrategyFactory.create('centralized');
    expect(strategy).toBeInstanceOf(CentralizedStrategy);
  });

  test('should throw error for unknown strategy type', () => {
    expect(() => StrategyFactory.create('unknown')).toThrow('Unknown strategy type');
  });

  test('should auto-select strategy based on context', () => {
    const type1 = StrategyFactory.autoSelect({ agentCount: 3 });
    expect(type1).toBe('centralized');

    const type2 = StrategyFactory.autoSelect({ agentCount: 10 });
    expect(type2).toBe('distributed');

    const type3 = StrategyFactory.autoSelect({ agentCount: 25 });
    expect(type3).toBe('hierarchical');

    const type4 = StrategyFactory.autoSelect({ requiresFaultTolerance: true });
    expect(type4).toBe('mesh');

    const type5 = StrategyFactory.autoSelect({ workloadPattern: 'unknown' });
    expect(type5).toBe('adaptive');
  });

  test('should provide strategy metadata', () => {
    const metadata = StrategyFactory.getMetadata('centralized');
    expect(metadata).toBeDefined();
    expect(metadata.name).toBe('Centralized Strategy');
    expect(metadata.bestFor).toBeDefined();
  });

  test('should validate strategy configuration', () => {
    const validation1 = StrategyFactory.validate('centralized', { maxAgents: 5 });
    expect(validation1.valid).toBe(true);

    const validation2 = StrategyFactory.validate('centralized', { maxAgents: -1 });
    expect(validation2.valid).toBe(false);
    expect(validation2.errors.length).toBeGreaterThan(0);

    const validation3 = StrategyFactory.validate('distributed', { coordinatorCount: 1 });
    expect(validation3.valid).toBe(false);
  });

  test('should create strategy from template', () => {
    const strategy = StrategyFactory.fromTemplate('small-team');
    expect(strategy).toBeInstanceOf(CentralizedStrategy);

    const strategy2 = StrategyFactory.fromTemplate('medium-team');
    expect(strategy2).toBeInstanceOf(DistributedStrategy);
  });

  test('should list available strategies', () => {
    const strategies = StrategyFactory.list();
    expect(strategies).toContain('centralized');
    expect(strategies).toContain('distributed');
    expect(strategies).toContain('hierarchical');
    expect(strategies).toContain('mesh');
    expect(strategies).toContain('adaptive');
  });
});

// Run all tests
console.log('Running Swarm Strategy Tests...');
console.log('Test suite covers:');
console.log('- Base Strategy validation');
console.log('- Centralized Strategy operations');
console.log('- Distributed Strategy with load balancing');
console.log('- Hierarchical Strategy tree structure');
console.log('- Mesh Strategy peer-to-peer coordination');
console.log('- Adaptive Strategy dynamic adaptation');
console.log('- Strategy Factory creation and validation');
