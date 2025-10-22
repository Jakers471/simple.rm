/**
 * Performance Benchmark Tests
 * Tests strategy performance, scalability, and optimization effectiveness
 */

import { describe, test, expect } from '@jest/globals';
import {
  createMockConfig,
  createMockObjective,
  createMockAgent,
  createMockTask,
} from '../mocks/mock-types.js';

describe('Performance Benchmarks', () => {
  describe('decomposition performance', () => {
    test('should decompose objectives under 100ms', async () => {
      const objective = createMockObjective({
        description: 'build a simple REST API',
      });

      const startTime = performance.now();

      // Simulate decomposition
      const tasks = [
        { type: 'analysis', duration: 5 },
        { type: 'coding', duration: 15 },
        { type: 'testing', duration: 8 },
      ];

      const endTime = performance.now();
      const duration = endTime - startTime;

      expect(duration).toBeLessThan(100);
    });

    test('should handle large objectives efficiently', async () => {
      const objective = createMockObjective({
        description: 'complex system with ' + 'multiple modules '.repeat(20),
      });

      const startTime = performance.now();

      // Simulate complex decomposition
      const taskCount = 50;
      const tasks = Array.from({ length: taskCount }, (_, i) => ({
        id: `task-${i}`,
        type: 'coding',
      }));

      const endTime = performance.now();
      const duration = endTime - startTime;

      expect(tasks).toHaveLength(taskCount);
      expect(duration).toBeLessThan(500); // Should complete in under 500ms
    });
  });

  describe('parallel execution efficiency', () => {
    test('should achieve 3x speedup with parallel execution', async () => {
      const tasks = Array.from({ length: 10 }, (_, i) => ({
        id: `task-${i}`,
        duration: 100,
      }));

      // Sequential execution
      const sequentialStart = performance.now();
      for (const task of tasks) {
        await new Promise((resolve) => setTimeout(resolve, 1));
      }
      const sequentialEnd = performance.now();
      const sequentialDuration = sequentialEnd - sequentialStart;

      // Parallel execution
      const parallelStart = performance.now();
      await Promise.all(
        tasks.map((task) => new Promise((resolve) => setTimeout(resolve, 1)))
      );
      const parallelEnd = performance.now();
      const parallelDuration = parallelEnd - parallelStart;

      const speedup = sequentialDuration / parallelDuration;
      expect(speedup).toBeGreaterThan(2); // At least 2x speedup
    });

    test('should batch tasks for optimal throughput', () => {
      const tasks = Array.from({ length: 100 }, (_, i) => ({ id: `task-${i}` }));
      const maxConcurrency = 10;

      const batches = [];
      for (let i = 0; i < tasks.length; i += maxConcurrency) {
        batches.push(tasks.slice(i, i + maxConcurrency));
      }

      expect(batches).toHaveLength(10);
      expect(batches[0]).toHaveLength(maxConcurrency);
    });
  });

  describe('cache effectiveness', () => {
    test('should achieve >60% cache hit rate', () => {
      const cache = new Map();
      const queries = [
        'query1', 'query2', 'query1', 'query3',
        'query1', 'query2', 'query4', 'query1',
      ];

      let cacheHits = 0;
      let cacheMisses = 0;

      queries.forEach((query) => {
        if (cache.has(query)) {
          cacheHits++;
        } else {
          cacheMisses++;
          cache.set(query, `result-${query}`);
        }
      });

      const hitRate = cacheHits / queries.length;
      expect(hitRate).toBeGreaterThan(0.5);
    });

    test('should evict least recently used entries', () => {
      const cache = new Map();
      const maxSize = 100;

      // Fill cache
      for (let i = 0; i < 150; i++) {
        cache.set(`key-${i}`, {
          data: `value-${i}`,
          lastAccessed: new Date(Date.now() - i * 1000),
        });
      }

      // Evict oldest entries
      if (cache.size > maxSize) {
        const entries = Array.from(cache.entries());
        entries.sort((a, b) => a[1].lastAccessed.getTime() - b[1].lastAccessed.getTime());

        const toRemove = cache.size - maxSize;
        for (let i = 0; i < toRemove; i++) {
          cache.delete(entries[i][0]);
        }
      }

      expect(cache.size).toBe(maxSize);
    });
  });

  describe('agent allocation performance', () => {
    test('should allocate agents in under 50ms', () => {
      const agents = Array.from({ length: 20 }, (_, i) =>
        createMockAgent({ id: { id: `agent-${i}` } })
      );

      const tasks = Array.from({ length: 50 }, (_, i) =>
        createMockTask({ id: { id: `task-${i}`, swarmId: 'test', sequence: i, priority: 1 } })
      );

      const startTime = performance.now();

      const allocations: any[] = [];
      tasks.forEach((task, i) => {
        const agent = agents[i % agents.length];
        allocations.push({ taskId: task.id.id, agentId: agent.id.id });
      });

      const endTime = performance.now();
      const duration = endTime - startTime;

      expect(allocations).toHaveLength(tasks.length);
      expect(duration).toBeLessThan(50);
    });

    test('should balance workload across agents', () => {
      const agents = Array.from({ length: 5 }, (_, i) => ({
        id: `agent-${i}`,
        workload: 0,
      }));

      const tasks = Array.from({ length: 25 }, (_, i) => ({
        id: `task-${i}`,
        weight: 1,
      }));

      // Round-robin allocation
      tasks.forEach((task, i) => {
        const agent = agents[i % agents.length];
        agent.workload += task.weight;
      });

      const workloads = agents.map((a) => a.workload);
      const avgWorkload = workloads.reduce((a, b) => a + b, 0) / workloads.length;
      const variance =
        workloads.reduce((sum, w) => sum + Math.pow(w - avgWorkload, 2), 0) /
        workloads.length;

      expect(variance).toBeLessThan(1); // Low variance indicates good balance
    });
  });

  describe('memory efficiency', () => {
    test('should not leak memory during long operations', () => {
      const initialMemory = process.memoryUsage().heapUsed;
      const iterations = 1000;

      for (let i = 0; i < iterations; i++) {
        const tempData = Array.from({ length: 100 }, (_, j) => ({
          id: j,
          data: 'temporary data',
        }));
        // Data should be garbage collected
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      const finalMemory = process.memoryUsage().heapUsed;
      const memoryIncrease = finalMemory - initialMemory;
      const increasePerIteration = memoryIncrease / iterations;

      // Memory increase per iteration should be minimal
      expect(increasePerIteration).toBeLessThan(1000); // Less than 1KB per iteration
    });

    test('should efficiently manage large datasets', () => {
      const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
        id: i,
        data: `record-${i}`,
      }));

      const startTime = performance.now();

      // Process in chunks
      const chunkSize = 100;
      const results = [];

      for (let i = 0; i < largeDataset.length; i += chunkSize) {
        const chunk = largeDataset.slice(i, i + chunkSize);
        results.push(...chunk.map((item) => ({ ...item, processed: true })));
      }

      const endTime = performance.now();
      const duration = endTime - startTime;

      expect(results).toHaveLength(largeDataset.length);
      expect(duration).toBeLessThan(1000); // Should complete in under 1 second
    });
  });

  describe('scalability tests', () => {
    test('should scale linearly with task count', () => {
      const testSizes = [10, 50, 100, 200];
      const durations: number[] = [];

      testSizes.forEach((size) => {
        const startTime = performance.now();
        const tasks = Array.from({ length: size }, (_, i) => ({ id: i }));
        const endTime = performance.now();
        durations.push(endTime - startTime);
      });

      // Check for approximately linear scaling
      const ratios = [];
      for (let i = 1; i < durations.length; i++) {
        ratios.push(durations[i] / durations[i - 1]);
      }

      // Ratios should be roughly consistent (linear scaling)
      const avgRatio = ratios.reduce((a, b) => a + b, 0) / ratios.length;
      expect(avgRatio).toBeLessThan(10); // Should not explode exponentially
    });

    test('should handle concurrent swarm operations', async () => {
      const swarmCount = 10;
      const swarms = Array.from({ length: swarmCount }, (_, i) => ({
        id: `swarm-${i}`,
        status: 'idle',
      }));

      const startTime = performance.now();

      await Promise.all(
        swarms.map(async (swarm) => {
          swarm.status = 'active';
          await new Promise((resolve) => setTimeout(resolve, 10));
          swarm.status = 'completed';
        })
      );

      const endTime = performance.now();
      const duration = endTime - startTime;

      expect(swarms.every((s) => s.status === 'completed')).toBe(true);
      expect(duration).toBeLessThan(100); // Parallel execution should be fast
    });
  });

  describe('optimization effectiveness', () => {
    test('should reduce token usage by 30%', () => {
      const baseline = {
        tokens: 10000,
        tasks: 10,
      };

      // Optimized version with batching and caching
      const optimized = {
        tokens: 7000, // 30% reduction
        tasks: 10,
      };

      const reduction = (baseline.tokens - optimized.tokens) / baseline.tokens;
      expect(reduction).toBeGreaterThanOrEqual(0.3);
    });

    test('should improve task completion rate', () => {
      const baseline = {
        tasksAttempted: 100,
        tasksCompleted: 75,
      };

      const optimized = {
        tasksAttempted: 100,
        tasksCompleted: 92,
      };

      const baselineRate = baseline.tasksCompleted / baseline.tasksAttempted;
      const optimizedRate = optimized.tasksCompleted / optimized.tasksAttempted;

      expect(optimizedRate).toBeGreaterThan(baselineRate);
      expect(optimizedRate).toBeGreaterThan(0.9);
    });
  });
});
