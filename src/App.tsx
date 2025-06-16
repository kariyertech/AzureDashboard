import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AppLayout from './components/Layout/AppLayout';
import PipelinesPage from './pages/PipelinesPage';
import ReleasesPage from './pages/ReleasesPage';
import ProjectsPage from './pages/TeamsPage'; // Artık projeleri listeliyor
import ReposPage from './pages/ReposPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route 
          path="/"
          element={ 
            <AppLayout>
              <Dashboard />
            </AppLayout>
          }
        />
        <Route 
          path="/pipelines"
          element={
            <AppLayout>
              <PipelinesPage />
            </AppLayout>
          }
        />
        <Route 
          path="/releases"
          element={
            <AppLayout>
              <ReleasesPage />
            </AppLayout>
          }
        />
        <Route 
          path="/projects"
          element={
            <AppLayout>
              <ProjectsPage />
            </AppLayout>
          }
        />
        <Route 
          path="/repos"
          element={
            <AppLayout>
              <ReposPage />
            </AppLayout>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;