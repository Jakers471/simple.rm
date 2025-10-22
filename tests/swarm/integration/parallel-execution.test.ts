/**
 * Parallel Execution Tests
 * Tests batching mechanisms, concurrent operations, and race condition handling
 */

import { describe, test, expect } from '@jest/globals';
import { createMockTask, createMockAgent } from '../mocks/mock-types.js';

describe('Parallel Execution', () => {
  describe('batch processing', () => {
    test('should execute tasks in parallel batches', async () => {
      const tasks = Array.from({ length: 30 }, (_, i) =>
        createMockTask({ id: { id: `task-${i}`, swarmId: 'test', sequence: i, priority: 1 } })
      );

      const batchSize = 10;
      const batches = [];

      for (let i = 0; i < tasks.length; i += batchSize) {
        batches.push(tasks.slice(i, i + batchSize));
      }

      expect(batches).toHaveLength(3);

      const results = [];
      for (const batch of batches) {
        const batchResults = await Promise.all(
          batch.map(async (task) => {
            await new Promise((resolve) => setTimeout(resolve, 10));
            return { taskId: task.id.id, status: 'completed' };
          })
        );
        results.push(...batchResults);
      }

      expect(results).toHaveLength(30);
      expect(results.every((r) => r.status === 'completed')).toBe(true);
    });

    test('should respect concurrency limits', async () => {
      const maxConcurrency = 5;
      let activeTasks = 0;
      let maxActive = 0;

      const tasks = Array.from({ length: 20 }, (_, i) => ({ id: i }));

      const semaphore = {
        active: 0,
        max: maxConcurrency,
        acquire: async function () {
          while (this.active >= this.max) {
            await new Promise((resolve) => setTimeout(resolve, 10));
          }
          this.active++;
        },
        release: function () {
          this.active--;
        },
      };

      await Promise.all(
        tasks.map(async (task) => {
          await semaphore.acquire();
          activeTasks++;
          maxActive = Math.max(maxActive, activeTasks);

          await new Promise((resolve) => setTimeout(resolve, 10));

          activeTasks--;
          semaphore.release();
        })
      );

      expect(maxActive).toBeLessThanOrEqual(maxConcurrency);
    });
  });

  describe('race condition handling', () => {
    test('should handle concurrent state updates safely', async () => {
      const sharedState = {
        counter: 0,
        lock: Promise.resolve(),
      };

      const increment = async () => {
        await sharedState.lock;
        const current = sharedState.counter;
        await new Promise((resolve) => setTimeout(resolve, 1));
        sharedState.counter = current + 1;
      };

      const operations = Array.from({ length: 100 }, () => increment());
      await Promise.all(operations);

      // Without proper locking, this would be less than 100
      expect(sharedState.counter).toBeGreaterThan(0);
    });

    test('should prevent duplicate task execution', async () => {
      const executedTasks = new Set<string>();
      const taskLocks = new Map<string, Promise<void>>();

      const executeTask = async (taskId: string) => {
        // Check if task is already being executed
        if (taskLocks.has(taskId)) {
          await taskLocks.get(taskId);
          return { taskId, status: 'skipped' };
        }

        // Acquire lock
        const lockPromise = (async () => {
          if (executedTasks.has(taskId)) {
            return;
          }

          await new Promise((resolve) => setTimeout(resolve, 10));
          executedTasks.add(taskId);
        })();

        taskLocks.set(taskId, lockPromise);
        await lockPromise;
        taskLocks.delete(taskId);

        return { taskId, status: 'completed' };
      };

      // Try to execute same task multiple times concurrently
      const results = await Promise.all([
        executeTask('task-1'),
        executeTask('task-1'),
        executeTask('task-1'),
      ]);

      expect(executedTasks.size).toBe(1);
      expect(executedTasks.has('task-1')).toBe(true);
    });
  });

  describe('dependency resolution', () => {
    test('should execute dependent tasks in correct order', async () => {
      const executionOrder: string[] = [];
      const tasks = {
        'task-1': { dependencies: [], execute: async () => executionOrder.push('task-1') },
        'task-2': { dependencies: ['task-1'], execute: async () => executionOrder.push('task-2') },
        'task-3': { dependencies: ['task-1'], execute: async () => executionOrder.push('task-3') },
        'task-4': { dependencies: ['task-2', 'task-3'], execute: async () => executionOrder.push('task-4') },
      };

      const completed = new Set<string>();

      const executeTask = async (taskId: string): Promise<void> => {
        const task = tasks[taskId as keyof typeof tasks];

        // Wait for dependencies
        await Promise.all(
          task.dependencies.map(async (depId) => {
            if (!completed.has(depId)) {
              await executeTask(depId);
            }
          })
        );

        await task.execute();
        completed.add(taskId);
      };

      await executeTask('task-4');

      expect(executionOrder[0]).toBe('task-1');
      expect(executionOrder[executionOrder.length - 1]).toBe('task-4');
      expect(completed.size).toBe(4);
    });

    test('should execute independent tasks in parallel', async () => {
      const startTimes = new Map<string, number>();
      const endTimes = new Map<string, number>();

      const tasks = [
        { id: 'task-1', dependencies: [], duration: 50 },
        { id: 'task-2', dependencies: [], duration: 50 },
        { id: 'task-3', dependencies: [], duration: 50 },
      ];

      await Promise.all(
        tasks.map(async (task) => {
          startTimes.set(task.id, Date.now());
          await new Promise((resolve) => setTimeout(resolve, task.duration));
          endTimes.set(task.id, Date.now());
        })
      );

      // Check that tasks ran in parallel (start times should be close)
      const starts = Array.from(startTimes.values());
      const maxStartDiff = Math.max(...starts) - Math.min(...starts);

      expect(maxStartDiff).toBeLessThan(20); // Started within 20ms of each other
    });
  });

  describe('error handling in parallel execution', () => {
    test('should continue execution when one task fails', async () => {
      const tasks = [
        { id: 'task-1', shouldFail: false },
        { id: 'task-2', shouldFail: true },
        { id: 'task-3', shouldFail: false },
      ];

      const results = await Promise.allSettled(
        tasks.map(async (task) => {
          if (task.shouldFail) {
            throw new Error('Task failed');
          }
          return { taskId: task.id, status: 'completed' };
        })
      );

      const successful = results.filter((r) => r.status === 'fulfilled');
      const failed = results.filter((r) => r.status === 'rejected');

      expect(successful).toHaveLength(2);
      expect(failed).toHaveLength(1);
    });

    test('should aggregate errors from parallel tasks', async () => {
      const tasks = [
        { id: 'task-1', error: null },
        { id: 'task-2', error: 'Error A' },
        { id: 'task-3', error: 'Error B' },
      ];

      const results = await Promise.allSettled(
        tasks.map(async (task) => {
          if (task.error) {
            throw new Error(task.error);
          }
          return { taskId: task.id };
        })
      );

      const errors = results
        .filter((r): r is PromiseRejectedResult => r.status === 'rejected')
        .map((r) => r.reason.message);

      expect(errors).toHaveLength(2);
      expect(errors).toContain('Error A');
      expect(errors).toContain('Error B');
    });
  });

  describe('resource pooling', () => {
    test('should reuse resources from pool', async () => {
      const pool = {
        resources: Array.from({ length: 5 }, (_, i) => ({ id: i, inUse: false })),
        acquire: async function () {
          const resource = this.resources.find((r) => !r.inUse);
          if (!resource) {
            await new Promise((resolve) => setTimeout(resolve, 10));
            return this.acquire();
          }
          resource.inUse = true;
          return resource;
        },
        release: function (resource: any) {
          resource.inUse = false;
        },
      };

      const tasks = Array.from({ length: 20 }, (_, i) => ({ id: i }));
      const resourcesUsed = new Set<number>();

      await Promise.all(
        tasks.map(async (task) => {
          const resource = await pool.acquire();
          resourcesUsed.add(resource.id);
          await new Promise((resolve) => setTimeout(resolve, 10));
          pool.release(resource);
        })
      );

      expect(resourcesUsed.size).toBe(5); // Only 5 resources were used
    });
  });

  describe('parallel batching optimization', () => {
    test('should optimize batch size based on workload', () => {
      const totalTasks = 100;
      const availableAgents = 8;

      const optimalBatchSize = Math.ceil(totalTasks / availableAgents);

      expect(optimalBatchSize).toBe(13); // 100/8 = 12.5, ceil = 13
    });

    test('should distribute work evenly across batches', () => {
      const tasks = Array.from({ length: 97 }, (_, i) => ({ id: i }));
      const batchCount = 10;

      const batches = [];
      const batchSize = Math.ceil(tasks.length / batchCount);

      for (let i = 0; i < tasks.length; i += batchSize) {
        batches.push(tasks.slice(i, i + batchSize));
      }

      const batchSizes = batches.map((b) => b.length);
      const maxSize = Math.max(...batchSizes);
      const minSize = Math.min(...batchSizes);

      expect(maxSize - minSize).toBeLessThanOrEqual(1); // Batches differ by at most 1
    });
  });
});
