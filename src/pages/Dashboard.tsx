import React, { useEffect, useState } from 'react';
import { getProjects, getProjectMetrics, getRepositories, getPipelines, getReleaseDefinitions, getDeploymentsByEnvironment, getProjectDeploymentsByEnvironment } from '../services/api';
import { useProject } from '../context/ProjectContext';
import { Project } from '../types';
import { Download, Box, GitBranch, LineChart, GitCommit } from 'lucide-react';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';

function exportMetric(name: string, value: number | string) {
  const csv = `Metric,Value\n${name},${value}`;
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${name.replace(/\s/g, '_').toLowerCase()}_export.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

const Dashboard: React.FC = () => {
  const { selectedProjectId, setSelectedProjectId } = useProject();
  const [projects, setProjects] = useState<Project[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [metricsPrev, setMetricsPrev] = useState<any>(null);
  const [repoCount, setRepoCount] = useState<number | null>(null);
  const [pipelineCount, setPipelineCount] = useState<number | null>(null);
  const [releaseCount, setReleaseCount] = useState<number | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [fastLoading, setFastLoading] = useState(false);
  const [deploymentsEnvData, setDeploymentsEnvData] = useState<any>(null);
  const [deploymentsEnvLoading, setDeploymentsEnvLoading] = useState(false);
  const [deploymentsEnvError, setDeploymentsEnvError] = useState<string | null>(null);

  // Projeleri yükle
  useEffect(() => {
    getProjects()
      .then((data) => {
        // Projeleri A-Z'ye göre sırala
        const sorted = [...data].sort((a, b) => a.project_name.localeCompare(b.project_name));
        setProjects(sorted);
      })
      .catch(() => setProjects([]));
  }, []);

  // Projeler yüklendikten sonra, seçili proje yoksa ilk projeyi seç
  useEffect(() => {
    if (!selectedProjectId && projects.length > 0) {
      setSelectedProjectId(projects[0].project_id);
    }
  }, [projects, selectedProjectId, setSelectedProjectId]);

  // Seçili proje değiştiğinde, metrikleri yükle
  useEffect(() => {
    const selectedProjectObj = projects.find((p) => p.project_id === selectedProjectId);
    const projectName = selectedProjectObj?.project_name;
    if (selectedProjectId && projectName) {
      setMetricsLoading(true);
      setFastLoading(true);
      getProjectMetrics(projectName, '7d')
        .then((data) => setMetrics(data))
        .catch(() => {
          setMetrics(null);
        })
        .finally(() => setMetricsLoading(false));
      getProjectMetrics(projectName, '14d')
        .then((data) => setMetricsPrev(data))
        .catch(() => {
          setMetricsPrev(null);
        });
      Promise.all([
        getRepositories(projectName),
        getPipelines(projectName),
        getReleaseDefinitions(projectName)
      ]).then(([repos, pipelines, releases]) => {
        setRepoCount(repos.length);
        setPipelineCount(pipelines.length);
        setReleaseCount(releases.length);
      }).catch(() => {
        setRepoCount(null);
        setPipelineCount(null);
        setReleaseCount(null);
      }).finally(() => setFastLoading(false));
    } else {
      setRepoCount(null);
      setPipelineCount(null);
      setReleaseCount(null);
    }
  }, [selectedProjectId, projects]);

  // Seçili proje değiştiğinde, ortam bazlı deployment sayılarını yükle
  useEffect(() => {
    const selectedProjectObj = projects.find((p) => p.project_id === selectedProjectId);
    const projectName = selectedProjectObj?.project_name;
    if (selectedProjectId && projectName) {
      setDeploymentsEnvLoading(true);
      setDeploymentsEnvError(null);
      getProjectDeploymentsByEnvironment(projectName)
        .then((data) => setDeploymentsEnvData([data]))
        .catch(() => {
          setDeploymentsEnvError('Veri alınamadı');
          setDeploymentsEnvData(null);
        })
        .finally(() => setDeploymentsEnvLoading(false));
    } else {
      setDeploymentsEnvData(null);
    }
  }, [selectedProjectId, projects]);

  // Yüzde değişim hesaplama fonksiyonu
  function getDelta(current: number, prev: number) {
    if (prev === 0) return current === 0 ? 0 : 100;
    return ((current - prev) / prev) * 100;
  }

  // Önceki 7 günün değerlerini bul
  const prevWindow = metricsPrev && metrics ? {
    pipeline_count: metricsPrev.pipeline_count ?? metricsPrev.pipeline_runs ?? 0,
    release_count: metricsPrev.release_count ?? metricsPrev.releases ?? 0,
    repository_count: metricsPrev.repository_count ?? 0,
    commit_count: metricsPrev.commit_count ?? metricsPrev.commits ?? 0
  } : null;
  const currWindow = metrics ? {
    pipeline_count: metrics.pipeline_count ?? metrics.pipeline_runs ?? 0,
    release_count: metrics.release_count ?? metrics.releases ?? 0,
    repository_count: metrics.repository_count ?? 0,
    commit_count: metrics.commit_count ?? metrics.commits ?? 0
  } : null;

  // Farklar (sadece 7 günlük pencere için)
  const deltas = prevWindow && currWindow ? {
    pipeline: getDelta(currWindow.pipeline_count, prevWindow.pipeline_count),
    release: getDelta(currWindow.release_count, prevWindow.release_count),
    commit: getDelta(currWindow.commit_count, prevWindow.commit_count)
  } : { pipeline: 0, release: 0, commit: 0 };

  const selectedProject = projects.find((p) => p.project_id === selectedProjectId);

  return (
    <div className="p-6 space-y-8 bg-gray-50 min-h-screen">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {selectedProject ? `Details for: ${selectedProject.project_name}` : 'Select a Project'}
        </h1>
        <div className="relative min-w-[200px]">
          <select
            className="p-2 border rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 min-w-[200px] disabled:bg-gray-100 disabled:text-gray-400"
            value={selectedProjectId || ''}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            disabled={projects.length === 0}
          >
            <option value="" disabled>Select a project...</option>
            {projects.map((project) => (
              <option key={project.project_id} value={project.project_id}>
                {project.project_name}
              </option>
            ))}
          </select>
          {projects.length === 0 && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 animate-spin">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
            </span>
          )}
        </div>
      </div>
      {/* Üstteki ana metrik kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col justify-between min-h-[150px] relative border-l-4 border-blue-500">
          <div className="absolute top-4 right-4 bg-gray-100 rounded-full p-2"><Box className="w-6 h-6 text-blue-500" /></div>
          <div className="text-gray-500 font-semibold text-lg mb-2">Toplam Projeler</div>
          <div className="text-4xl font-bold text-gray-900">{projects.length}</div>
          <div className="mt-2 text-sm text-gray-500">Tüm projelerin toplam sayısı.</div>
        </div>
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col justify-between min-h-[150px] relative border-l-4 border-blue-400">
          <div className="absolute top-4 right-4 bg-gray-100 rounded-full p-2"><GitBranch className="w-6 h-6 text-blue-400" /></div>
          <div className="text-gray-500 font-semibold text-lg mb-2">Build Pipelines</div>
          <div className="text-4xl font-bold text-gray-900">{fastLoading ? <LoadingSpinner size="sm" /> : (currWindow?.pipeline_count ?? '-')}</div>
          {prevWindow && !fastLoading && (
            <div className={`mt-2 text-sm flex items-center gap-1 ${deltas.pipeline >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {deltas.pipeline >= 0 ? '↑' : '↓'} {Math.abs(deltas.pipeline).toFixed(1)}% <span className="text-gray-400">geçen dönemle karşılaştırmalı</span>
            </div>
          )}
          <div className="mt-2 text-sm text-gray-500">Son 7 günde oluşturulan toplam build pipeline sayısı.</div>
        </div>
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col justify-between min-h-[150px] relative border-l-4 border-orange-400">
          <div className="absolute top-4 right-4 bg-gray-100 rounded-full p-2"><LineChart className="w-6 h-6 text-orange-400" /></div>
          <div className="text-gray-500 font-semibold text-lg mb-2">Release Pipelines</div>
          <div className="text-4xl font-bold text-gray-900">{fastLoading ? <LoadingSpinner size="sm" /> : (currWindow?.release_count ?? '-')}</div>
          {prevWindow && !fastLoading && (
            <div className={`mt-2 text-sm flex items-center gap-1 ${deltas.release >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {deltas.release >= 0 ? '↑' : '↓'} {Math.abs(deltas.release).toFixed(1)}% <span className="text-gray-400">geçen dönemle karşılaştırmalı</span>
            </div>
          )}
          <div className="mt-2 text-sm text-gray-500">Son 7 günde oluşturulan toplam release pipeline sayısı.</div>
        </div>
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col justify-between min-h-[150px] relative border-l-4 border-green-500">
          <div className="absolute top-4 right-4 bg-gray-100 rounded-full p-2"><GitCommit className="w-6 h-6 text-green-500" /></div>
          <div className="text-gray-500 font-semibold text-lg mb-2">Toplam Commits</div>
          <div className="text-4xl font-bold text-gray-900">{metricsLoading ? <LoadingSpinner size="sm" /> : (currWindow?.commit_count ?? '-')}</div>
          {prevWindow && !metricsLoading && (
            <div className={`mt-2 text-sm flex items-center gap-1 ${deltas.commit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {deltas.commit >= 0 ? '↑' : '↓'} {Math.abs(deltas.commit).toFixed(1)}% <span className="text-gray-400">geçen dönemle karşılaştırmalı</span>
            </div>
          )}
          <div className="mt-2 text-sm text-gray-500">Son 7 günde yapılan toplam commit sayısı.</div>
        </div>
      </div>
      {/* Ortada: Deployment grafiği ve frequency */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 mb-2 justify-center items-center">
        {/* Compact Bar Chart */}
        <div className="rounded-2xl p-4 bg-white shadow flex flex-col min-h-[180px] border-l-4 border-blue-700 justify-between">
          <div className="text-gray-700 font-semibold text-base mb-2 text-center">Aylık Ortam Bazlı Deployment Sayıları</div>
          {deploymentsEnvLoading ? (
            <div className="flex justify-center items-center h-32"><LoadingSpinner size="md" /></div>
          ) : deploymentsEnvError ? (
            <div className="text-red-500 text-center">{deploymentsEnvError}</div>
          ) : deploymentsEnvData && deploymentsEnvData.length > 0 ? (
            <ResponsiveContainer width="100%" height={140}>
              <BarChart
                data={deploymentsEnvData}
                margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
                barCategoryGap={"40%"}
                barGap={4}
              >
                <CartesianGrid strokeDasharray="2 4" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="project" tick={{ fontSize: 12, fill: '#374151' }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#374151' }} axisLine={false} tickLine={false} />
                <Tooltip wrapperStyle={{ borderRadius: 8, boxShadow: '0 2px 8px #0001' }} contentStyle={{ fontSize: 13 }} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                <Bar dataKey="Test" fill="#6366f1" name="Test" radius={[8,8,0,0]} maxBarSize={18} />
                <Bar dataKey="Staging" fill="#f59e42" name="Staging" radius={[8,8,0,0]} maxBarSize={18} />
                <Bar dataKey="Production" fill="#22c55e" name="Production" radius={[8,8,0,0]} maxBarSize={18} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-400 text-center">Veri yok</div>
          )}
        </div>
        {/* Deployment Frequency Card */}
        <div className="rounded-2xl p-4 bg-white shadow flex flex-col min-h-[180px] border-l-4 border-blue-600 justify-center items-center">
          <div className="text-gray-700 font-semibold text-base mb-2 text-center">Deployment Frequency</div>
          <div className="text-3xl font-bold text-blue-700 mb-1">
            {deploymentsEnvLoading ? <LoadingSpinner size="sm" /> :
              (deploymentsEnvData && deploymentsEnvData[0]?.deployment_frequency !== undefined
                ? deploymentsEnvData[0].deployment_frequency
                : '-')}
            <span className="text-lg font-normal text-gray-500"> /gün</span>
          </div>
          <div className="text-gray-500 text-xs text-center">Son 30 günde günlük ortalama deployment sayısı.</div>
        </div>
      </div>
      {/* Diğer metrik kartları (3. satır) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-2">
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col min-h-[150px] border-l-4 border-indigo-500">
          <div className="text-gray-700 font-semibold text-lg mb-2">En Aktif Kullanıcılar</div>
          {metricsLoading ? <LoadingSpinner size="sm" /> : (
            metrics?.top_committers && metrics.top_committers.length > 0 ? (
              <ol className="list-decimal ml-4 text-gray-900">
                {metrics.top_committers.map((user: any, idx: number) => (
                  <li key={user.name + idx} className="mb-1 flex justify-between">
                    <span>{user.name}</span>
                    <span className="font-bold">{user.commit_count}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <div className="text-gray-400">No data</div>
            )
          )}
        </div>
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col min-h-[150px] border-l-4 border-green-600">
          <div className="text-gray-700 font-semibold text-lg mb-2">Release Başarı Oranı</div>
          <div className="text-3xl font-bold text-green-700">{metricsLoading ? <LoadingSpinner size="sm" /> : (metrics?.release_success_rate !== undefined && metrics?.release_success_rate !== null ? `${metrics.release_success_rate.toFixed(1)}%` : '-')}</div>
          <div className="text-gray-500 mt-2">Son 7 günde yapılan release işlemlerinin başarı oranı.</div>
        </div>
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col min-h-[150px] border-l-4 border-yellow-500">
          <div className="text-gray-700 font-semibold text-lg mb-2">Toplam Build Sayısı</div>
          <div className="text-3xl font-bold text-yellow-700">{metricsLoading ? <LoadingSpinner size="sm" /> : (metrics?.total_build_count_7d !== undefined && metrics?.total_build_count_7d !== null ? metrics.total_build_count_7d : '-')}</div>
          <div className="text-gray-500 mt-2">Son 7 günde oluşturulan toplam build sayısı.</div>
        </div>
        <div className="rounded-2xl p-6 bg-white shadow flex flex-col min-h-[150px] border-l-4 border-blue-600">
          <div className="text-gray-700 font-semibold text-lg mb-2">Başarılı Build Oranı</div>
          <div className="text-3xl font-bold text-blue-700">{metricsLoading ? <LoadingSpinner size="sm" /> : (metrics?.build_success_rate !== undefined && metrics?.build_success_rate !== null ? `${metrics.build_success_rate.toFixed(1)}%` : '-')}</div>
          <div className="text-gray-500 mt-2">Son 7 günde yapılan build işlemlerinin başarı oranı.</div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="rounded-2xl p-8 bg-gradient-to-br from-blue-200 to-blue-100 shadow relative">
          <button type="button" onClick={() => exportMetric('Repositories', repoCount ?? '-')} className="absolute top-4 right-4 bg-white/60 rounded-full p-2 hover:bg-white/80 transition">
            <Download className="w-6 h-6 text-blue-700" />
          </button>
          <div className="font-bold text-2xl text-blue-900 mb-2 text-center">Repositories</div>
          <div className="border-b-2 border-blue-300 w-10 mx-auto mb-2" />
          <div className="text-5xl font-extrabold text-blue-900 text-center">{repoCount ?? '-'}</div>
          <div className="mt-2 text-sm text-gray-500 text-center">Toplam repository sayısı.</div>
        </div>
        <div className="rounded-2xl p-8 bg-gradient-to-br from-orange-200 to-orange-100 shadow relative">
          <button type="button" onClick={() => exportMetric('Build Pipelines', pipelineCount ?? '-')} className="absolute top-4 right-4 bg-white/60 rounded-full p-2 hover:bg-white/80 transition">
            <Download className="w-6 h-6 text-orange-700" />
          </button>
          <div className="font-bold text-2xl text-orange-900 mb-2 text-center">Build Pipelines</div>
          <div className="border-b-2 border-orange-300 w-10 mx-auto mb-2" />
          <div className="text-5xl font-extrabold text-orange-900 text-center">{pipelineCount ?? '-'}</div>
          <div className="mt-2 text-sm text-gray-500 text-center">Toplam build pipeline sayısı.</div>
        </div>
        <div className="rounded-2xl p-8 bg-gradient-to-br from-green-200 to-green-100 shadow relative">
          <button type="button" onClick={() => exportMetric('Release Pipelines', releaseCount ?? '-')} className="absolute top-4 right-4 bg-white/60 rounded-full p-2 hover:bg-white/80 transition">
            <Download className="w-6 h-6 text-green-700" />
          </button>
          <div className="font-bold text-2xl text-green-900 mb-2 text-center">Release Pipelines</div>
          <div className="border-b-2 border-green-300 w-10 mx-auto mb-2" />
          <div className="text-5xl font-extrabold text-green-900 text-center">{releaseCount ?? '-'}</div>
          <div className="mt-2 text-sm text-gray-500 text-center">Toplam release pipeline sayısı.</div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;