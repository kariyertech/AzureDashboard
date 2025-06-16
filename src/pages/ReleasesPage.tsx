import React, { useEffect, useState } from 'react';
import { useProject } from '../context/ProjectContext';
import { getReleaseDefinitions } from '../services/api';
import { BookOpen } from 'lucide-react';

const ReleasesPage: React.FC = () => {
  const { selectedProjectId } = useProject();
  const [releases, setReleases] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedProjectId) return;
    setLoading(true);
    setError(null);
    getReleaseDefinitions(selectedProjectId)
      .then(setReleases)
      .catch(() => setError('Release verileri alınamadı'))
      .finally(() => setLoading(false));
  }, [selectedProjectId]);

  if (!selectedProjectId) {
    return <div className="p-6 text-gray-500">Please select a project first.</div>;
  }

  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6 flex items-center gap-2">
        <BookOpen className="w-7 h-7 text-primary-600" /> Releases
      </h2>
      {loading && (
        <div className="flex items-center gap-2 text-gray-500 animate-pulse">
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
          </svg>
          Loading releases...
        </div>
      )}
      {error && <div className="text-red-500 font-medium">{error}</div>}
      <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 mt-4">
        {releases.map((release: any) => (
          <li key={release.id || release.name} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-6 py-5 rounded-xl shadow hover:shadow-lg transition-shadow flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-primary-500" />
            <span className="font-semibold text-lg text-gray-900 dark:text-gray-100">{release.name}</span>
          </li>
        ))}
      </ul>
      {!loading && releases.length === 0 && !error && (
        <div className="text-gray-400 text-center mt-10">No releases found.</div>
      )}
    </div>
  );
};

export default ReleasesPage;
