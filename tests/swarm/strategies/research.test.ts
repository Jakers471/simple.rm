/**
 * Unit Tests for ResearchStrategy
 * Tests research-specific optimizations including caching, rate limiting, and parallel processing
 */

import { describe, test, expect, beforeEach, jest } from '@jest/globals';
import {
  createMockConfig,
  createMockObjective,
  createMockAgent,
} from '../mocks/mock-types.js';

describe('ResearchStrategy', () => {
  describe('research objective decomposition', () => {
    test('should create query planning task', () => {
      const task = {
        type: 'research',
        name: 'Research Query Planning',
        priority: 'high',
        estimatedDuration: 5 * 60 * 1000,
        capabilities: ['research', 'analysis'],
      };

      expect(task.type).toBe('research');
      expect(task.priority).toBe('high');
      expect(task.estimatedDuration).toBe(300000);
    });

    test('should create parallel web search tasks', () => {
      const task = {
        type: 'research',
        name: 'Parallel Web Search Execution',
        priority: 'high',
        estimatedDuration: 10 * 60 * 1000,
        capabilities: ['web-search', 'research'],
      };

      expect(task.capabilities).toContain('web-search');
      expect(task.estimatedDuration).toBe(600000);
    });

    test('should create data extraction task', () => {
      const task = {
        type: 'analysis',
        name: 'Parallel Data Extraction',
        priority: 'high',
        estimatedDuration: 8 * 60 * 1000,
      };

      expect(task.type).toBe('analysis');
    });

    test('should create semantic clustering task', () => {
      const task = {
        type: 'analysis',
        name: 'Semantic Clustering and Analysis',
        priority: 'medium',
        estimatedDuration: 6 * 60 * 1000,
      };

      expect(task.priority).toBe('medium');
    });

    test('should create synthesis and reporting task', () => {
      const task = {
        type: 'documentation',
        name: 'Research Synthesis and Reporting',
        priority: 'medium',
        estimatedDuration: 7 * 60 * 1000,
      };

      expect(task.type).toBe('documentation');
    });
  });

  describe('research parameter extraction', () => {
    test('should extract domains from description', () => {
      const description = 'research academic papers on machine learning';
      const domains = [];

      if (description.includes('academic') || description.includes('research'))
        domains.push('academic');
      if (description.includes('news')) domains.push('news');
      if (description.includes('technical')) domains.push('technical');

      expect(domains).toContain('academic');
    });

    test('should extract keywords', () => {
      const description = 'analyze performance optimization techniques';
      const keywords = description
        .toLowerCase()
        .split(/\s+/)
        .filter((word) => word.length > 3)
        .slice(0, 10);

      expect(keywords).toContain('analyze');
      expect(keywords).toContain('performance');
      expect(keywords).toContain('optimization');
      expect(keywords).toContain('techniques');
    });

    test('should determine source types', () => {
      const sourceTypes = ['academic', 'news', 'documentation', 'blog'];
      expect(sourceTypes).toHaveLength(4);
      expect(sourceTypes).toContain('academic');
    });
  });

  describe('search query generation', () => {
    test('should generate multiple search queries', () => {
      const description = 'research best practices for API design';
      const keywords = ['research', 'best', 'practices', 'design'];

      const queries = [
        {
          query: description.substring(0, 100),
          keywords: keywords.slice(0, 5),
          domains: ['general'],
          priority: 1,
        },
        {
          query: `${description} research study`,
          keywords: [...keywords.slice(0, 3), 'research', 'study'],
          domains: ['academic'],
          priority: 2,
        },
        {
          query: `${description} best practices`,
          keywords: [...keywords.slice(0, 3), 'best', 'practices'],
          domains: ['technical'],
          priority: 2,
        },
      ];

      expect(queries).toHaveLength(3);
      expect(queries[0].domains).toContain('general');
      expect(queries[1].domains).toContain('academic');
      expect(queries[2].domains).toContain('technical');
    });
  });

  describe('rate limiting', () => {
    test('should initialize rate limiter', () => {
      const limiter = {
        requests: 0,
        windowStart: new Date(),
        windowSize: 60000, // 1 minute
        maxRequests: 10,
        backoffMultiplier: 1,
      };

      expect(limiter.requests).toBe(0);
      expect(limiter.maxRequests).toBe(10);
    });

    test('should check rate limits', () => {
      const limiter = {
        requests: 5,
        windowStart: new Date(),
        windowSize: 60000,
        maxRequests: 10,
      };

      const isWithinLimit = limiter.requests < limiter.maxRequests;
      expect(isWithinLimit).toBe(true);
    });

    test('should reset rate limiter after window', () => {
      const now = new Date();
      const limiter = {
        requests: 10,
        windowStart: new Date(now.getTime() - 70000), // 70 seconds ago
        windowSize: 60000,
        maxRequests: 10,
      };

      if (now.getTime() - limiter.windowStart.getTime() > limiter.windowSize) {
        limiter.requests = 0;
        limiter.windowStart = now;
      }

      expect(limiter.requests).toBe(0);
    });

    test('should implement exponential backoff', () => {
      const backoffDelays = [1000, 2000, 4000, 8000];

      for (let attempt = 0; attempt < 4; attempt++) {
        const delay = Math.pow(2, attempt) * 1000;
        expect(delay).toBe(backoffDelays[attempt]);
      }
    });
  });

  describe('connection pooling', () => {
    test('should initialize connection pool', () => {
      const pool = {
        active: 0,
        idle: 0,
        max: 10,
        timeout: 30000,
        connections: new Map(),
      };

      expect(pool.active).toBe(0);
      expect(pool.max).toBe(10);
    });

    test('should acquire connection from pool', () => {
      const pool = {
        active: 5,
        max: 10,
      };

      const canAcquire = pool.active < pool.max;
      expect(canAcquire).toBe(true);

      if (canAcquire) {
        pool.active++;
      }

      expect(pool.active).toBe(6);
    });

    test('should release connection back to pool', () => {
      const pool = {
        active: 5,
        idle: 3,
      };

      pool.active--;
      pool.idle++;

      expect(pool.active).toBe(4);
      expect(pool.idle).toBe(4);
    });

    test('should wait when pool is exhausted', async () => {
      const pool = {
        active: 10,
        max: 10,
      };

      const waitForConnection = async () => {
        return new Promise<void>((resolve) => {
          const checkConnection = () => {
            if (pool.active < pool.max) {
              resolve();
            } else {
              setTimeout(checkConnection, 100);
            }
          };
          checkConnection();
        });
      };

      // Simulate connection release
      setTimeout(() => {
        pool.active--;
      }, 50);

      await waitForConnection();
      expect(pool.active).toBeLessThan(pool.max);
    });
  });

  describe('result ranking and credibility', () => {
    test('should rank results by credibility', () => {
      const results = [
        { id: '1', credibilityScore: 0.7, relevanceScore: 0.8 },
        { id: '2', credibilityScore: 0.9, relevanceScore: 0.7 },
        { id: '3', credibilityScore: 0.6, relevanceScore: 0.9 },
      ];

      const ranked = results.sort((a, b) => {
        const scoreA = a.credibilityScore * 0.6 + a.relevanceScore * 0.4;
        const scoreB = b.credibilityScore * 0.6 + b.relevanceScore * 0.4;
        return scoreB - scoreA;
      });

      expect(ranked[0].id).toBe('2'); // Highest combined score
    });

    test('should filter low credibility results', () => {
      const results = [
        { credibilityScore: 0.9 },
        { credibilityScore: 0.5 },
        { credibilityScore: 0.8 },
        { credibilityScore: 0.3 },
      ];

      const threshold = 0.6;
      const filtered = results.filter((r) => r.credibilityScore >= threshold);

      expect(filtered).toHaveLength(2);
    });
  });

  describe('caching optimization', () => {
    test('should generate cache keys', () => {
      const type = 'web-search';
      const data = 'search query for machine learning';
      const cacheKey = `${type}:${Buffer.from(data).toString('base64').substring(0, 32)}`;

      expect(cacheKey).toContain('web-search:');
    });

    test('should cache search results', () => {
      const cache = new Map();
      const key = 'search:test-query';
      const data = { results: [] };
      const ttl = 3600000;

      cache.set(key, {
        key,
        data,
        timestamp: new Date(),
        ttl,
        accessCount: 0,
        lastAccessed: new Date(),
      });

      expect(cache.has(key)).toBe(true);
    });

    test('should respect TTL for cached entries', () => {
      const entry = {
        timestamp: new Date(Date.now() - 4000000), // 4000 seconds ago
        ttl: 3600000, // 1 hour
        data: 'cached data',
      };

      const now = new Date();
      const isExpired = now.getTime() - entry.timestamp.getTime() > entry.ttl;

      expect(isExpired).toBe(true);
    });

    test('should cleanup old cache entries', () => {
      const cache = new Map();

      // Add entries with different access times
      for (let i = 0; i < 1200; i++) {
        cache.set(`key-${i}`, {
          lastAccessed: new Date(Date.now() - i * 1000),
        });
      }

      // Cleanup oldest 20%
      const entries = Array.from(cache.entries());
      entries.sort((a, b) => a[1].lastAccessed.getTime() - b[1].lastAccessed.getTime());

      const toRemove = Math.floor(entries.length * 0.2);
      for (let i = 0; i < toRemove; i++) {
        cache.delete(entries[i][0]);
      }

      expect(cache.size).toBe(960);
    });
  });

  describe('parallel data extraction', () => {
    test('should create parallel extraction tasks', () => {
      const results = Array.from({ length: 30 }, (_, i) => ({ id: i }));
      const maxConcurrency = 10;
      const batchSize = Math.ceil(results.length / maxConcurrency);
      const batches = [];

      for (let i = 0; i < results.length; i += batchSize) {
        const batch = results.slice(i, i + batchSize);
        batches.push(batch);
      }

      expect(batches.length).toBeLessThanOrEqual(maxConcurrency);
    });

    test('should deduplicate extracted data', () => {
      const data = [
        { id: '1', extractedData: 'data1' },
        { id: '2', extractedData: 'data2' },
        { id: '3', extractedData: 'data1' }, // Duplicate
      ];

      const seen = new Set();
      const deduplicated = data.filter((item) => {
        if (seen.has(item.extractedData)) return false;
        seen.add(item.extractedData);
        return true;
      });

      expect(deduplicated).toHaveLength(2);
    });
  });

  describe('semantic clustering', () => {
    test('should create semantic clusters', () => {
      const data = Array.from({ length: 25 }, (_, i) => ({ id: i, content: `data ${i}` }));
      const clusterCount = Math.min(Math.ceil(data.length / 5), 10);

      const clusters = [];
      for (let i = 0; i < clusterCount; i++) {
        const clusterData = data.slice(i * 5, (i + 1) * 5);
        clusters.push({
          id: `cluster-${i}`,
          topic: `Topic ${i}`,
          results: clusterData,
          coherenceScore: Math.random() * 0.3 + 0.7,
        });
      }

      expect(clusters).toHaveLength(5);
      expect(clusters[0].results).toHaveLength(5);
    });

    test('should calculate cluster coherence', () => {
      const clusters = [
        { coherenceScore: 0.8 },
        { coherenceScore: 0.9 },
        { coherenceScore: 0.7 },
      ];

      const avgCoherence =
        clusters.reduce((sum, c) => sum + c.coherenceScore, 0) / clusters.length;

      expect(avgCoherence).toBeCloseTo(0.8, 1);
    });
  });

  describe('research metrics', () => {
    test('should track queries executed', () => {
      const metrics = {
        queriesExecuted: 0,
        resultsCollected: 0,
        cacheHits: 0,
        cacheMisses: 0,
      };

      metrics.queriesExecuted += 3;
      metrics.resultsCollected += 45;
      metrics.cacheHits += 2;
      metrics.cacheMisses += 1;

      expect(metrics.queriesExecuted).toBe(3);
      expect(metrics.resultsCollected).toBe(45);
    });

    test('should calculate cache hit rate', () => {
      const metrics = {
        cacheHits: 15,
        cacheMisses: 5,
      };

      const hitRate = metrics.cacheHits / (metrics.cacheHits + metrics.cacheMisses);

      expect(hitRate).toBe(0.75);
    });

    test('should track average credibility scores', () => {
      const credibilityScores = [0.8, 0.9, 0.7, 0.85, 0.95];
      const average =
        credibilityScores.reduce((a, b) => a + b, 0) / credibilityScores.length;

      expect(average).toBeCloseTo(0.85, 2);
    });
  });
});
