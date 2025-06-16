// Azure DevOps related types
export interface DevOpsProject {
  project_id: string;
  project_name: string;
  repositories: string[];
  build_pipelines: string[];
  release_pipelines: string[];
}

export interface Project extends DevOpsProject {}

export interface Pipeline {
  id: string;
  name: string;
  folder: string;
  url: string;
  _links: { web: { href: string } };
}

export interface ReleaseDefinition {
  id: number;
  name: string;
  url: string;
  _links: { web: { href: string } };
}

export interface Release extends ReleaseDefinition { // Assuming Release might extend ReleaseDefinition or have similar fields
  // Add specific fields for a Release if different from ReleaseDefinition
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  project: { id: string; name: string };
}

export interface Commit {
  commitId: string;
  author: {
    name: string;
    email: string;
    date: string; // ISO Date string
  };
  committer: {
    name: string;
    email: string;
    date: string;
  };
  comment: string;
  url: string;
  repositoryName?: string; // Added to show which repo the commit belongs to
}

export interface Deployment {
  id: number;
  release: { id: number; name: string; };
  releaseEnvironment: { id: number; name: string; };
  deploymentStatus: string;
  completedOn: string; // ISO date string
  // Add other relevant fields
}

export interface Build {
  id: number;
  buildNumber: string;
  status: string;
  result: string;
  queueTime: string; // ISO date string
  startTime: string; // ISO date string
  finishTime: string; // ISO date string
  url: string;
  definition: { id: number; name: string; };
  project: { id: string; name: string; };
  repository: { id: string; type: string; name: string; };
  // Add other relevant fields
}

// UI related types
export interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

export type TimeFrame = 'weekly' | 'monthly' | 'yearly';
export type ChartType = 'bar' | 'line' | 'pie' | 'area';

export interface ProjectMetrics {
  project_name: string;
  pipeline_count: number;
  release_count: number;
  repository_count: number;
  commit_count?: number;
  pipeline_run_avg_7d?: number;
  release_avg_7d?: number;
  top_committers?: { name: string; commit_count: number }[];
  release_success_rate?: number | null;
  total_build_count_7d?: number;
  build_success_rate?: number | null;
}