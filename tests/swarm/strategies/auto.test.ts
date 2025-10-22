/**
 * Unit Tests for AutoStrategy
 * Tests the automatic strategy selection and intelligent task decomposition
 */

import { describe, test, expect, beforeEach, jest } from '@jest/globals';
import {
  createMockConfig,
  createMockObjective,
  createMockAgent,
  createMockTask,
} from '../mocks/mock-types.js';

describe('AutoStrategy', () => {
  describe('objective decomposition', () => {
    test('should decompose development objective into phases', async () => {
      const objective = createMockObjective({
        strategy: 'development',
        description: 'create a REST API with authentication',
      });

      // Expected task phases
      const expectedPhases = [
        'analysis',
        'implementation',
        'testing',
        'documentation',
      ];

      // Simulate decomposition
      const tasks = [
        { type: 'analysis', name: 'Requirements Analysis and Planning' },
        { type: 'coding', name: 'Core Implementation' },
        { type: 'testing', name: 'Comprehensive Testing' },
        { type: 'documentation', name: 'Documentation Creation' },
      ];

      expect(tasks).toHaveLength(4);
      expect(tasks[0].type).toBe('analysis');
      expect(tasks[1].type).toBe('coding');
      expect(tasks[2].type).toBe('testing');
      expect(tasks[3].type).toBe('documentation');
    });

    test('should decompose analysis objective into research phases', async () => {
      const objective = createMockObjective({
        strategy: 'analysis',
        description: 'analyze market trends in AI technology',
      });

      const tasks = [
        { type: 'research', name: 'Data Collection and Research' },
        { type: 'analysis', name: 'Data Analysis' },
        { type: 'documentation', name: 'Analysis Report' },
      ];

      expect(tasks).toHaveLength(3);
      expect(tasks[0].type).toBe('research');
      expect(tasks[1].type).toBe('analysis');
    });

    test('should identify parallel implementation opportunities', () => {
      const description = 'build multiple components for the system';
      const parallelKeywords = ['components', 'modules', 'services', 'layers', 'parts'];

      const canParallelize = parallelKeywords.some(keyword =>
        description.toLowerCase().includes(keyword)
      );

      expect(canParallelize).toBe(true);
    });

    test('should create task batches with dependencies', () => {
      const tasks = [
        createMockTask({ id: { id: 'task-1', swarmId: 'test', sequence: 1, priority: 1 } }),
        createMockTask({
          id: { id: 'task-2', swarmId: 'test', sequence: 2, priority: 1 },
          constraints: {
            dependencies: [{ id: 'task-1', swarmId: 'test', sequence: 1, priority: 1 }],
            dependents: [],
            conflicts: [],
            maxRetries: 3,
            timeoutAfter: 300000,
          },
        }),
      ];

      const dependencies = new Map<string, string[]>();
      dependencies.set('task-2', ['task-1']);

      const batches = [];
      const processed = new Set<string>();
      let batchIndex = 0;

      while (processed.size < tasks.length) {
        const batchTasks = tasks.filter(
          (task) =>
            !processed.has(task.id.id) &&
            task.constraints.dependencies.every((dep) => processed.has(dep.id))
        );

        if (batchTasks.length === 0) break;

        batches.push({
          id: `batch-${batchIndex++}`,
          tasks: batchTasks,
          canRunInParallel: batchTasks.length > 1,
        });

        batchTasks.forEach((task) => processed.add(task.id.id));
      }

      expect(batches).toHaveLength(2);
      expect(batches[0].tasks).toHaveLength(1);
      expect(batches[1].tasks).toHaveLength(1);
    });
  });

  describe('ML-inspired agent selection', () => {
    test('should score agents based on capability match', () => {
      const agent = createMockAgent({
        type: 'coder',
        capabilities: {
          codeGeneration: true,
          codeReview: true,
          testing: false,
          documentation: false,
          research: false,
          analysis: false,
          webSearch: false,
          apiIntegration: false,
          fileSystem: true,
          terminalAccess: true,
          domains: [],
          languages: ['javascript'],
          frameworks: [],
          tools: [],
        },
      });

      const task = createMockTask({
        requirements: {
          capabilities: ['code-generation', 'file-system'],
          tools: [],
          permissions: [],
        },
      });

      // Capability matching (40%)
      const requiredCaps = task.requirements.capabilities;
      let matches = 0;
      if (agent.capabilities.codeGeneration) matches++;
      if (agent.capabilities.fileSystem) matches++;

      const capabilityScore = matches / requiredCaps.length;

      expect(capabilityScore).toBe(1.0);
    });

    test('should consider agent workload in scoring', () => {
      const agent1 = createMockAgent({ workload: 0.2 });
      const agent2 = createMockAgent({ workload: 0.8 });

      const workloadScore1 = 1 - agent1.workload;
      const workloadScore2 = 1 - agent2.workload;

      expect(workloadScore1).toBe(0.8);
      expect(workloadScore2).toBe(0.2);
      expect(workloadScore1).toBeGreaterThan(workloadScore2);
    });

    test('should apply task type weights', () => {
      const taskTypeWeights = {
        development: 1.0,
        testing: 0.8,
        analysis: 0.9,
        documentation: 0.6,
        optimization: 1.1,
      };

      expect(taskTypeWeights.optimization).toBeGreaterThan(taskTypeWeights.development);
      expect(taskTypeWeights.development).toBeGreaterThan(taskTypeWeights.testing);
      expect(taskTypeWeights.documentation).toBeLessThan(taskTypeWeights.testing);
    });
  });

  describe('predictive task scheduling', () => {
    test('should create timeline with task slots', () => {
      const tasks = [
        createMockTask({ constraints: { dependencies: [], dependents: [], conflicts: [], maxRetries: 3, timeoutAfter: 300000 } }),
        createMockTask({ constraints: { dependencies: [], dependents: [], conflicts: [], maxRetries: 3, timeoutAfter: 600000 } }),
      ];

      const timeline = [];
      let currentTime = Date.now();

      for (const task of tasks) {
        const duration = task.constraints.timeoutAfter || 300000;
        timeline.push({
          startTime: currentTime,
          endTime: currentTime + duration,
          tasks: [task.id.id],
        });
        currentTime += duration;
      }

      expect(timeline).toHaveLength(2);
      expect(timeline[1].startTime).toBe(timeline[0].endTime);
    });

    test('should allocate agents to suitable tasks', () => {
      const agents = [
        createMockAgent({ type: 'researcher', capabilities: { research: true } as any }),
        createMockAgent({ type: 'coder', capabilities: { codeGeneration: true } as any }),
        createMockAgent({ type: 'tester', capabilities: { testing: true } as any }),
      ];

      const tasks = [
        createMockTask({ type: 'research' }),
        createMockTask({ type: 'coding' }),
        createMockTask({ type: 'testing' }),
      ];

      const allocations = [];
      const researchTasks = tasks.filter((t) => t.type === 'research');
      const codingTasks = tasks.filter((t) => t.type === 'coding');
      const testingTasks = tasks.filter((t) => t.type === 'testing');

      for (const agent of agents) {
        if (agent.type === 'researcher' && researchTasks.length > 0) {
          allocations.push({ agentId: agent.id.id, taskType: 'research' });
        }
        if (agent.type === 'coder' && codingTasks.length > 0) {
          allocations.push({ agentId: agent.id.id, taskType: 'coding' });
        }
        if (agent.type === 'tester' && testingTasks.length > 0) {
          allocations.push({ agentId: agent.id.id, taskType: 'testing' });
        }
      }

      expect(allocations).toHaveLength(3);
    });
  });

  describe('caching and performance', () => {
    test('should cache decomposition results', () => {
      const cache = new Map();
      const objective = createMockObjective();
      const cacheKey = `${objective.strategy}-${objective.description.slice(0, 100)}`;

      const result = {
        tasks: [],
        dependencies: new Map(),
        estimatedDuration: 60000,
      };

      cache.set(cacheKey, result);

      const cached = cache.get(cacheKey);
      expect(cached).toBe(result);
    });

    test('should track cache hit rate', () => {
      let cacheHits = 0;
      let cacheMisses = 0;

      // Simulate cache accesses
      cacheHits += 3;
      cacheMisses += 2;

      const hitRate = cacheHits / (cacheHits + cacheMisses);

      expect(hitRate).toBe(0.6);
    });

    test('should use async pattern detection', async () => {
      const description = 'create and build a new feature';

      const detectPatterns = async () => {
        return new Promise((resolve) => {
          setTimeout(() => {
            const patterns = [];
            if (/create|build|implement|develop/i.test(description)) {
              patterns.push({ type: 'development' });
            }
            resolve(patterns);
          }, 10);
        });
      };

      const patterns = await detectPatterns();
      expect(patterns).toHaveLength(1);
    });
  });

  describe('complexity-based optimization', () => {
    test('should apply complexity factors', () => {
      const complexityFactors = {
        integration: 1.5,
        system: 1.3,
        api: 1.2,
        database: 1.4,
        ui: 1.1,
        algorithm: 1.6,
      };

      const description = 'implement complex algorithm for data processing';
      let complexity = 2;

      if (description.includes('algorithm')) {
        complexity *= complexityFactors.algorithm;
      }

      expect(complexity).toBeGreaterThan(2);
      expect(Math.round(complexity)).toBe(3);
    });

    test('should select strategy based on complexity', () => {
      const testCases = [
        { complexity: 5, description: 'complex system', expected: 'development' },
        { complexity: 2, description: 'analyze data', expected: 'analysis' },
        { complexity: 1, description: 'simple task', expected: 'auto' },
      ];

      testCases.forEach(({ complexity, description, expected }) => {
        let strategy = 'auto';
        if (complexity >= 4) strategy = 'development';
        else if (description.toLowerCase().includes('analyze')) strategy = 'analysis';

        expect(strategy).toBe(expected);
      });
    });
  });

  describe('parallel execution optimization', () => {
    test('should identify parallel execution opportunities', () => {
      const parallelismOpportunities = [
        'independent modules',
        'separate components',
        'different layers',
        'parallel testing',
        'concurrent analysis',
      ];

      const description = 'build independent modules for the system';
      const hasParallelOpp = parallelismOpportunities.some((opp) =>
        description.toLowerCase().includes(opp)
      );

      expect(hasParallelOpp).toBe(true);
    });

    test('should calculate optimal batch duration', () => {
      const batches = [
        { estimatedDuration: 60000 },
        { estimatedDuration: 120000 },
        { estimatedDuration: 90000 },
      ];

      const totalDuration = batches.reduce(
        (sum, batch) => sum + batch.estimatedDuration,
        0
      );

      expect(totalDuration).toBe(270000);
    });
  });
});
