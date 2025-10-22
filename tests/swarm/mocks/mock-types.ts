/**
 * Mock types and utilities for swarm strategy testing
 */

export interface MockSwarmConfig {
  name: string;
  description: string;
  version: string;
  mode: 'mesh' | 'hierarchical' | 'ring' | 'star';
  strategy: 'auto' | 'research' | 'development' | 'analysis';
  maxAgents: number;
  maxTasks: number;
  maxDuration: number;
  resourceLimits: Record<string, any>;
  qualityThreshold: number;
  reviewRequired: boolean;
  testingRequired: boolean;
  monitoring: {
    metricsEnabled: boolean;
    loggingEnabled: boolean;
    tracingEnabled: boolean;
  };
  performance: {
    maxConcurrency: number;
    defaultTimeout: number;
    cacheEnabled: boolean;
    cacheSize: number;
    cacheTtl: number;
  };
}

export interface MockAgentState {
  id: { id: string };
  type: string;
  status: string;
  capabilities: {
    codeGeneration: boolean;
    codeReview: boolean;
    testing: boolean;
    documentation: boolean;
    research: boolean;
    analysis: boolean;
    webSearch: boolean;
    apiIntegration: boolean;
    fileSystem: boolean;
    terminalAccess: boolean;
    domains: string[];
    languages: string[];
    frameworks: string[];
    tools: string[];
  };
  workload: number;
}

export interface MockSwarmObjective {
  id: string;
  description: string;
  strategy: string;
  requirements: {
    qualityThreshold: number;
  };
}

export interface MockTaskDefinition {
  id: { id: string; swarmId: string; sequence: number; priority: number };
  type: string;
  name: string;
  description: string;
  instructions: string;
  requirements: {
    capabilities: string[];
    tools: string[];
    permissions: string[];
  };
  constraints: {
    dependencies: any[];
    dependents: any[];
    conflicts: any[];
    maxRetries: number;
    timeoutAfter: number;
  };
  priority: string;
  input: any;
  context: any;
  examples: any[];
  status: string;
  createdAt: Date;
  updatedAt: Date;
  attempts: any[];
  statusHistory: any[];
}

export function createMockConfig(overrides: Partial<MockSwarmConfig> = {}): MockSwarmConfig {
  return {
    name: 'test-swarm',
    description: 'Test swarm configuration',
    version: '1.0.0',
    mode: 'mesh',
    strategy: 'auto',
    maxAgents: 8,
    maxTasks: 50,
    maxDuration: 3600000,
    resourceLimits: {},
    qualityThreshold: 0.8,
    reviewRequired: true,
    testingRequired: false,
    monitoring: {
      metricsEnabled: true,
      loggingEnabled: false,
      tracingEnabled: false,
    },
    performance: {
      maxConcurrency: 10,
      defaultTimeout: 300000,
      cacheEnabled: true,
      cacheSize: 100,
      cacheTtl: 3600000,
    },
    ...overrides,
  };
}

export function createMockAgent(overrides: Partial<MockAgentState> = {}): MockAgentState {
  return {
    id: { id: `agent-${Math.random().toString(36).substr(2, 9)}` },
    type: 'coder',
    status: 'idle',
    capabilities: {
      codeGeneration: true,
      codeReview: true,
      testing: true,
      documentation: true,
      research: false,
      analysis: false,
      webSearch: false,
      apiIntegration: false,
      fileSystem: true,
      terminalAccess: true,
      domains: ['general'],
      languages: ['javascript', 'typescript'],
      frameworks: ['node'],
      tools: ['terminal', 'editor'],
    },
    workload: 0,
    ...overrides,
  };
}

export function createMockObjective(overrides: Partial<MockSwarmObjective> = {}): MockSwarmObjective {
  return {
    id: `objective-${Math.random().toString(36).substr(2, 9)}`,
    description: 'Test objective for swarm',
    strategy: 'auto',
    requirements: {
      qualityThreshold: 0.8,
    },
    ...overrides,
  };
}

export function createMockTask(overrides: Partial<MockTaskDefinition> = {}): MockTaskDefinition {
  const taskId = `task-${Math.random().toString(36).substr(2, 9)}`;
  return {
    id: {
      id: taskId,
      swarmId: 'test-swarm',
      sequence: 1,
      priority: 1,
    },
    type: 'coding',
    name: 'Test Task',
    description: 'Test task description',
    instructions: 'Test task instructions',
    requirements: {
      capabilities: ['code-generation'],
      tools: ['terminal', 'editor'],
      permissions: ['read', 'write'],
    },
    constraints: {
      dependencies: [],
      dependents: [],
      conflicts: [],
      maxRetries: 3,
      timeoutAfter: 300000,
    },
    priority: 'medium',
    input: {},
    context: {},
    examples: [],
    status: 'created',
    createdAt: new Date(),
    updatedAt: new Date(),
    attempts: [],
    statusHistory: [],
    ...overrides,
  } as any;
}
