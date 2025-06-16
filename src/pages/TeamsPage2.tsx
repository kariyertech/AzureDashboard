import React, { useEffect, useState } from 'react';
import { useProject } from '../context/ProjectContext';
import axios from 'axios';

const TeamsPage: React.FC = () => {
  const { selectedProjectId } = useProject();
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedProjectId) return;
    setLoading(true);
    setError(null);
    axios.get(`/api/projects/${selectedProjectId}/teams`)
      .then(res => setTeams(res.data))
      .catch(() => setError('Takım verileri alınamadı'))
      .finally(() => setLoading(false));
  }, [selectedProjectId]);

  if (!selectedProjectId) {
    return <div className="p-6 text-gray-500">Lütfen önce bir proje seçin.</div>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Teams</h2>
      {loading && <div>Yükleniyor...</div>}
      {error && <div className="text-red-500">{error}</div>}
      <ul className="space-y-2">
        {teams.map((team: any) => (
          <li key={team.id || team.name} className="bg-info-50 px-4 py-2 rounded shadow-sm">
            {team.name}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TeamsPage;
