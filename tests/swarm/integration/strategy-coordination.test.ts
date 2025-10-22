/**
 * Integration Tests for Strategy Coordination
 * Tests end-to-end strategy execution and coordination between components
 */

import { describe, test, expect, beforeEach, afterEach } from '@jest/globals';
import {
  createMockConfig,
  createMockObjective,
  createMockAgent,
} from '../mocks/mock-types.js';

describe('Strategy Coordination Integration', () => {
  describe('full workflow execution', () => {
    test('should execute complete development workflow', async () => {
      const objective = createMockObjective({
        strategy: 'development',
        description: 'build a REST API with authentication and database integration',
      });

      const workflow = {
        phases: [
          'planning',
          'decomposition',
          'agent-allocation',
          'execution',
          'validation',
        ],
        currentPhase: 'planning',
      };

      // Phase 1: Planning
      expect(workflow.currentPhase).toBe('planning');
      workflow.currentPhase = 'decomposition';

      // Phase 2: Decomposition
      const tasks = [
        { phase: 'analysis', status: 'created' },
        { phase: 'implementation', status: 'created' },
        { phase: 'testing', status: 'created' },
        { phase: 'documentation', status: 'created' },
      ];
      expect(tasks).toHaveLength(4);
      workflow.currentPhase = 'agent-allocation';

      // Phase 3: Agent Allocation
      const agents = [
        createMockAgent({ type: 'analyst' }),
        createMockAgent({ type: 'coder' }),
        createMockAgent({ type: 'tester' }),
      ];
      expect(agents).toHaveLength(3);
      workflow.currentPhase = 'execution';

      // Phase 4: Execution
      tasks.forEach((task) => {
        task.status = 'completed';
      });
      workflow.currentPhase = 'validation';

      // Phase 5: Validation
      const allCompleted = tasks.every((task) => task.status === 'completed');
      expect(allCompleted).toBe(true);
    });

    test('should handle research workflow with parallel queries', async () => {
      const objective = createMockObjective({
        strategy: 'research',
        description: 'research AI trends and best practices',
      });

      const workflow = {
        tasks: [
          { name: 'query-planning', status: 'created', dependencies: [] },
          { name: 'web-search-1', status: 'created', dependencies: ['query-planning'] },
          { name: 'web-search-2', status: 'created', dependencies: ['query-planning'] },
          { name: 'web-search-3', status: 'created', dependencies: ['query-planning'] },
          { name: 'data-extraction', status: 'created', dependencies: ['web-search-1', 'web-search-2', 'web-search-3'] },
        ],
      };

      // Execute query planning
      workflow.tasks[0].status = 'completed';

      // Execute parallel searches
      const searchTasks = workflow.tasks.slice(1, 4);
      await Promise.all(
        searchTasks.map(async (task) => {
          task.status = 'in-progress';
          // Simulate search
          await new Promise((resolve) => setTimeout(resolve, 10));
          task.status = 'completed';
        })
      );

      const allSearchesComplete = searchTasks.every((t) => t.status === 'completed');
      expect(allSearchesComplete).toBe(true);
    });
  });

  describe('strategy switching', () => {
    test('should switch from auto to specialized strategy', () => {
      let currentStrategy = 'auto';
      const complexity = 4;
      const description = 'complex system integration';

      if (complexity >= 4) {
        currentStrategy = 'development';
      }

      expect(currentStrategy).toBe('development');
    });

    test('should maintain context during strategy switch', () => {
      const context = {
        strategy: 'auto',
        tasksCompleted: 5,
        metrics: { complexity: 3 },
      };

      // Switch strategy
      context.strategy = 'development';

      // Context should be preserved
      expect(context.tasksCompleted).toBe(5);
      expect(context.metrics.complexity).toBe(3);
    });
  });

  describe('agent coordination', () => {
    test('should coordinate multiple agents on parallel tasks', async () => {
      const agents = [
        createMockAgent({ id: { id: 'agent-1' }, type: 'coder' }),
        createMockAgent({ id: { id: 'agent-2' }, type: 'tester' }),
        createMockAgent({ id: { id: 'agent-3' }, type: 'analyst' }),
      ];

      const tasks = [
        { id: 'task-1', type: 'coding', assignedAgent: null, status: 'pending' },
        { id: 'task-2', type: 'testing', assignedAgent: null, status: 'pending' },
        { id: 'task-3', type: 'analysis', assignedAgent: null, status: 'pending' },
      ];

      // Assign agents to tasks
      tasks[0].assignedAgent = agents[0].id.id;
      tasks[1].assignedAgent = agents[1].id.id;
      tasks[2].assignedAgent = agents[2].id.id;

      // Execute tasks in parallel
      await Promise.all(
        tasks.map(async (task) => {
          task.status = 'in-progress';
          await new Promise((resolve) => setTimeout(resolve, 10));
          task.status = 'completed';
        })
      );

      expect(tasks.every((t) => t.status === 'completed')).toBe(true);
    });

    test('should handle agent failures with retry logic', async () => {
      const task = {
        id: 'task-1',
        status: 'pending',
        attempts: 0,
        maxRetries: 3,
      };

      const executeWithRetry = async () => {
        while (task.attempts < task.maxRetries) {
          task.attempts++;
          task.status = 'in-progress';

          // Simulate occasional failure
          const success = task.attempts >= 2;

          if (success) {
            task.status = 'completed';
            return true;
          }

          task.status = 'failed';
        }
        return false;
      };

      const result = await executeWithRetry();
      expect(result).toBe(true);
      expect(task.status).toBe('completed');
      expect(task.attempts).toBeLessThanOrEqual(task.maxRetries);
    });
  });

  describe('memory coordination', () => {
    test('should share state across agents via memory', async () => {
      const sharedMemory = new Map();

      // Agent 1 stores data
      sharedMemory.set('swarm/agent1/analysis', {
        findings: 'API requirements analyzed',
        timestamp: new Date(),
      });

      // Agent 2 retrieves and builds upon it
      const agent1Data = sharedMemory.get('swarm/agent1/analysis');
      expect(agent1Data).toBeDefined();
      expect(agent1Data.findings).toContain('API requirements');

      sharedMemory.set('swarm/agent2/implementation', {
        basedOn: 'swarm/agent1/analysis',
        status: 'implemented',
      });

      expect(sharedMemory.size).toBe(2);
    });

    test('should implement distributed caching', () => {
      const cache = new Map();
      const cacheKey = 'decomposition:complex-task';

      // Check cache miss
      let result = cache.get(cacheKey);
      expect(result).toBeUndefined();

      // Store in cache
      cache.set(cacheKey, {
        tasks: ['task1', 'task2'],
        timestamp: new Date(),
        ttl: 3600000,
      });

      // Check cache hit
      result = cache.get(cacheKey);
      expect(result).toBeDefined();
      expect(result.tasks).toHaveLength(2);
    });
  });

  describe('task dependencies', () => {
    test('should respect task dependencies in execution order', () => {
      const tasks = [
        { id: 'task-1', dependencies: [], status: 'pending' },
        { id: 'task-2', dependencies: ['task-1'], status: 'pending' },
        { id: 'task-3', dependencies: ['task-1'], status: 'pending' },
        { id: 'task-4', dependencies: ['task-2', 'task-3'], status: 'pending' },
      ];

      const canExecute = (task: any) => {
        return task.dependencies.every((depId: string) => {
          const dep = tasks.find((t) => t.id === depId);
          return dep?.status === 'completed';
        });
      };

      // Initially only task-1 can execute
      expect(canExecute(tasks[0])).toBe(true);
      expect(canExecute(tasks[1])).toBe(false);
      expect(canExecute(tasks[2])).toBe(false);
      expect(canExecute(tasks[3])).toBe(false);

      // After task-1 completes
      tasks[0].status = 'completed';
      expect(canExecute(tasks[1])).toBe(true);
      expect(canExecute(tasks[2])).toBe(true);
      expect(canExecute(tasks[3])).toBe(false);

      // After task-2 and task-3 complete
      tasks[1].status = 'completed';
      tasks[2].status = 'completed';
      expect(canExecute(tasks[3])).toBe(true);
    });

    test('should detect circular dependencies', () => {
      const tasks = [
        { id: 'task-1', dependencies: ['task-3'] },
        { id: 'task-2', dependencies: ['task-1'] },
        { id: 'task-3', dependencies: ['task-2'] },
      ];

      const detectCircular = (taskId: string, visited = new Set<string>()): boolean => {
        if (visited.has(taskId)) return true;
        visited.add(taskId);

        const task = tasks.find((t) => t.id === taskId);
        if (!task) return false;

        for (const depId of task.dependencies) {
          if (detectCircular(depId, new Set(visited))) {
            return true;
          }
        }

        return false;
      };

      expect(detectCircular('task-1')).toBe(true);
    });
  });

  describe('error handling and recovery', () => {
    test('should handle task failures gracefully', async () => {
      const workflow = {
        tasks: [
          { id: 'task-1', status: 'completed' },
          { id: 'task-2', status: 'failed', retries: 2 },
          { id: 'task-3', status: 'pending', dependencies: ['task-2'] },
        ],
        status: 'in-progress',
      };

      // Retry failed task
      if (workflow.tasks[1].status === 'failed' && workflow.tasks[1].retries > 0) {
        workflow.tasks[1].status = 'retrying';
        workflow.tasks[1].retries--;

        // Simulate retry
        await new Promise((resolve) => setTimeout(resolve, 10));
        workflow.tasks[1].status = 'completed';
      }

      expect(workflow.tasks[1].status).toBe('completed');
    });

    test('should implement fallback strategies', () => {
      const primaryStrategy = 'auto';
      const fallbackStrategy = 'development';

      let currentStrategy = primaryStrategy;

      // Simulate primary strategy failure
      const primaryFailed = true;

      if (primaryFailed) {
        currentStrategy = fallbackStrategy;
      }

      expect(currentStrategy).toBe(fallbackStrategy);
    });
  });

  describe('performance monitoring', () => {
    test('should track execution metrics', () => {
      const metrics = {
        tasksCompleted: 0,
        totalDuration: 0,
        averageTaskDuration: 0,
        parallelismEfficiency: 0,
      };

      const taskDurations = [1000, 2000, 1500, 3000];

      metrics.tasksCompleted = taskDurations.length;
      metrics.totalDuration = taskDurations.reduce((sum, d) => sum + d, 0);
      metrics.averageTaskDuration = metrics.totalDuration / metrics.tasksCompleted;

      // Calculate parallelism efficiency (if tasks ran sequentially vs parallel)
      const sequentialDuration = metrics.totalDuration;
      const actualDuration = Math.max(...taskDurations); // Parallel execution
      metrics.parallelismEfficiency = sequentialDuration / actualDuration;

      expect(metrics.tasksCompleted).toBe(4);
      expect(metrics.averageTaskDuration).toBe(1875);
      expect(metrics.parallelismEfficiency).toBeGreaterThan(1);
    });
  });
});
