import React from 'react';
import { useAuth } from '../../context/AuthContext';

const Header: React.FC = () => {
  const { authSettings } = useAuth();

  // Always ensure dark mode class is removed
  React.useEffect(() => {
    document.documentElement.classList.remove('dark');
  }, []);

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 py-4 px-6 flex items-center justify-between">
      <h1 className="text-2xl font-bold text-gray-900">Azure DevOps Dashboard</h1>
      <div className="flex items-center space-x-4">
        {authSettings && (
          <div className="hidden md:flex items-center text-sm text-gray-600">
            {/* Organization info */}
            <span>{authSettings.organization}</span>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;