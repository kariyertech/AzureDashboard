import axios from 'axios';
import { API_BASE_URL } from './config';
import { Project, Pipeline, Release, Repository, Commit, Deployment, Build } from '../types';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export interface ActivityMetrics {
  pipeline_runs: number;
  releases: number;
  commits: number;
}

export interface ActivitySummaryData {
  daily: ActivityMetrics;
  weekly: ActivityMetrics;
  monthly: ActivityMetrics;
}

export interface ProjectMetrics {
  project_name: string;
  pipeline_count: number;
  release_count: number;
  repository_count: number;
  commit_count?: number;
  pipeline_run_avg_7d?: number;
  release_avg_7d?: number;
  // New metrics:
  top_committers?: { name: string; commit_count: number }[];
  release_success_rate?: number | null;
  total_build_count_7d?: number;
  build_success_rate?: number | null;
}

export interface ProjectMetricsTimeseriesPoint {
  date: string;
  commits: number;
  builds: number;
  releases: number;
}

export const getEnvCheck = async () => {
  // ...existing code...
}

export const getProjects = async (): Promise<Project[]> => {
  // Fetch detailed project info from /devops-info instead of /projects
  const response = await apiClient.get<Project[]>('/devops-info');
  return response.data;
};

export const getPipelines = async (projectName: string): Promise<Pipeline[]> => {
  const response = await apiClient.get<Pipeline[]>(`/projects/${projectName}/pipelines`);
  return response.data;
};

// Assuming Release type is defined in ../types for release definitions
export const getReleaseDefinitions = async (projectName: string): Promise<Release[]> => {
  const response = await apiClient.get<Release[]>(`/projects/${projectName}/releases`);
  return response.data;
};

export const getRepositories = async (projectName: string): Promise<Repository[]> => {
  const response = await apiClient.get<Repository[]>(`/projects/${projectName}/repos`);
  return response.data;
};

export const getCommits = async (projectName: string, repositoryId: string, dateRange: { startDate: string, endDate: string }): Promise<Commit[]> => {
  const response = await apiClient.get<Commit[]>(`/projects/${projectName}/repos/${repositoryId}/commits`, {
    params: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate
    }
  });
  return response.data;
};

export const getDeployments = async (projectName: string, dateRange: { startDate: string, endDate: string }): Promise<Deployment[]> => {
  const response = await apiClient.get<Deployment[]>(`/projects/${projectName}/deployments`, {
    params: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate
    }
  });
  return response.data;
};

export const getBuilds = async (projectName: string, dateRange: { startDate: string, endDate: string }): Promise<Build[]> => {
  const response = await apiClient.get<Build[]>(`/projects/${projectName}/builds`, {
    params: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate
    }
  });
  return response.data;
};

export const getActivitySummary = async (): Promise<ActivitySummaryData> => {
  const response = await apiClient.get<ActivitySummaryData>('/activity_summary');
  return response.data;
};

export const getProjectMetrics = async (
  projectName: string,
  period: string = '30d'
): Promise<ProjectMetrics> => {
  const response = await apiClient.get<ProjectMetrics>(`/projects/${projectName}/metrics`, {
    params: { period },
  });
  return response.data;
};

export const getProjectMetricsTimeseries = async (
  projectName: string,
  period: string = '30d',
  interval: string = 'day'
): Promise<ProjectMetricsTimeseriesPoint[]> => {
  const response = await apiClient.get<ProjectMetricsTimeseriesPoint[]>(
    `/projects/${projectName}/metrics/timeseries`,
    { params: { period, interval } }
  );
  return response.data;
};

export const getRecentCommits = async (projectName: string): Promise<Commit[]> => {
  const response = await apiClient.get<Commit[]>(`/projects/${projectName}/recent-commits`);
  return response.data;
};

export interface DeploymentsByEnvironment {
  project: string;
  Test: number;
  Staging: number;
  Production: number;
  [key: string]: string | number;
}

export const getDeploymentsByEnvironment = async (): Promise<DeploymentsByEnvironment[]> => {
  const response = await apiClient.get<DeploymentsByEnvironment[]>('/deployments-by-environment');
  return response.data;
};

export const getProjectDeploymentsByEnvironment = async (projectName: string) => {
  const response = await apiClient.get(`/projects/${projectName}/deployments-by-environment`);
  return response.data;
};