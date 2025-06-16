import React, { useEffect, useState } from 'react';
import { getProjects } from '../services/api';
import { Project as DevOpsProject } from '../types';

const TeamsPage: React.FC = () => {
  const [projects, setProjects] = useState<DevOpsProject[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getProjects()
      .then((data) => {
        // Sort projects alphabetically by project_name
        const sorted = [...data].sort((a, b) => a.project_name.localeCompare(b.project_name));
        setProjects(sorted);
      })
      .catch(() => setError('Failed to fetch projects'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h2 className="text-3xl font-bold mb-8 flex items-center gap-3">
        <span className="inline-block bg-primary-100 text-primary-700 rounded-full p-2">
          <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>
        </span>
        <span>Projects</span>
      </h2>
      {loading && (
        <div className="flex items-center gap-2 text-gray-500 animate-pulse mb-6">
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
          </svg>
          Loading projects...
        </div>
      )}
      {error && <div className="text-red-500 font-medium mb-6">{error}</div>}
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {projects.map((project) => (
          <li key={project.project_id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-6 py-5 rounded-xl shadow hover:shadow-lg transition-shadow flex items-center gap-3">
            <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-primary-100 text-primary-600 font-bold text-lg">
              {project.project_name.charAt(0).toUpperCase()}
            </span>
            <span className="font-semibold text-lg text-gray-900 dark:text-gray-100 truncate">{project.project_name}</span>
          </li>
        ))}
      </ul>
      {!loading && projects.length === 0 && !error && (
        <div className="text-gray-400 text-center mt-10">No projects found.</div>
      )}
    </div>
  );
};

export default TeamsPage;
