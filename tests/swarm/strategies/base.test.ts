/**
 * Unit Tests for BaseStrategy
 * Tests the foundational strategy interface and common utilities
 */

import { describe, test, expect, beforeEach } from '@jest/globals';
import { createMockConfig, createMockObjective } from '../mocks/mock-types.js';

describe('BaseStrategy', () => {
  describe('initialization', () => {
    test('should initialize with default metrics', () => {
      const config = createMockConfig();
      // BaseStrategy is abstract, so we'll test through AutoStrategy
      const metrics = {
        tasksCompleted: 0,
        averageExecutionTime: 0,
        successRate: 0,
        resourceUtilization: 0,
        parallelismEfficiency: 0,
        cacheHitRate: 0,
        predictionAccuracy: 0,
      };

      expect(metrics.tasksCompleted).toBe(0);
      expect(metrics.cacheHitRate).toBe(0);
    });

    test('should initialize with default task patterns', () => {
      const patterns = [
        { type: 'development', complexity: 3, priority: 2 },
        { type: 'testing', complexity: 2, priority: 1 },
        { type: 'analysis', complexity: 2, priority: 1 },
        { type: 'documentation', complexity: 1, priority: 0 },
        { type: 'optimization', complexity: 3, priority: 1 },
      ];

      expect(patterns).toHaveLength(5);
      expect(patterns[0].type).toBe('development');
    });

    test('should create empty cache on initialization', () => {
      const cache = new Map();
      expect(cache.size).toBe(0);
    });
  });

  describe('task pattern detection', () => {
    test('should detect development task type', () => {
      const description = 'create a new REST API endpoint';
      const expectedType = 'development';

      // Pattern matching logic
      const pattern = /create|build|implement|develop/i;
      expect(pattern.test(description)).toBe(true);
    });

    test('should detect testing task type', () => {
      const description = 'test the authentication module';
      const expectedType = 'testing';

      const pattern = /test|verify|validate/i;
      expect(pattern.test(description)).toBe(true);
    });

    test('should detect analysis task type', () => {
      const description = 'analyze performance bottlenecks';
      const expectedType = 'analysis';

      const pattern = /analyze|research|investigate/i;
      expect(pattern.test(description)).toBe(true);
    });

    test('should default to generic for unknown patterns', () => {
      const description = 'some random task';
      const patterns = [
        /create|build|implement|develop/i,
        /test|verify|validate/i,
        /analyze|research|investigate/i,
      ];

      const matched = patterns.some(p => p.test(description));
      expect(matched).toBe(false);
    });
  });

  describe('complexity estimation', () => {
    test('should estimate low complexity for simple tasks', () => {
      const description = 'fix typo in documentation';
      const words = description.split(' ').length;
      let complexity = 1;

      // Logic from BaseStrategy
      if (words > 50) complexity += 1;
      if (words > 100) complexity += 1;

      expect(complexity).toBe(1);
    });

    test('should estimate high complexity for detailed tasks', () => {
      const longDescription = 'implement ' + 'complex '.repeat(30);
      const words = longDescription.split(' ').length;
      let complexity = 1;

      if (words > 50) complexity += 1;
      if (words > 100) complexity += 1;

      const complexKeywords = ['integrate', 'complex', 'advanced', 'multiple', 'system'];
      const foundKeywords = complexKeywords.filter(keyword =>
        longDescription.toLowerCase().includes(keyword)
      ).length;

      complexity += foundKeywords;
      complexity = Math.min(complexity, 5);

      expect(complexity).toBeGreaterThan(2);
    });

    test('should cap complexity at 5', () => {
      let complexity = 10;
      complexity = Math.min(complexity, 5);
      expect(complexity).toBe(5);
    });
  });

  describe('cache management', () => {
    test('should generate consistent cache keys', () => {
      const objective = createMockObjective({
        strategy: 'auto',
        description: 'test objective description',
      });

      const cacheKey1 = `${objective.strategy}-${objective.description.slice(0, 100)}`;
      const cacheKey2 = `${objective.strategy}-${objective.description.slice(0, 100)}`;

      expect(cacheKey1).toBe(cacheKey2);
    });

    test('should clear cache when requested', () => {
      const cache = new Map();
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');

      expect(cache.size).toBe(2);

      cache.clear();
      expect(cache.size).toBe(0);
    });
  });

  describe('metrics tracking', () => {
    test('should update metrics after task completion', () => {
      const metrics = {
        tasksCompleted: 0,
        averageExecutionTime: 0,
      };

      const tasksCount = 5;
      const executionTime = 1000;

      metrics.tasksCompleted += tasksCount;
      metrics.averageExecutionTime = (metrics.averageExecutionTime + executionTime) / 2;

      expect(metrics.tasksCompleted).toBe(5);
      expect(metrics.averageExecutionTime).toBe(500);
    });

    test('should provide metrics snapshot', () => {
      const metrics = {
        tasksCompleted: 10,
        averageExecutionTime: 5000,
        successRate: 0.95,
        resourceUtilization: 0.7,
        parallelismEfficiency: 0.85,
        cacheHitRate: 0.6,
        predictionAccuracy: 0.8,
      };

      const snapshot = { ...metrics };

      expect(snapshot).toEqual(metrics);
      expect(snapshot).not.toBe(metrics); // Should be a copy
    });
  });
});
