import React, { createContext, useContext, useState, ReactNode } from 'react';

// Define the shape of the context data
interface AuthContextType {
  isAuthenticated: boolean;
  authSettings: { organization: string } | null;
  login: (data: any) => void;
  logout: () => void;
}

// Create the context with a default undefined value
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Define the props for the AuthProvider component
interface AuthProviderProps {
  children: ReactNode;
}

// Create the AuthProvider component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(true); // Changed initial state to true
  const [authSettings, setAuthSettings] = useState<{ organization: string } | null>(null);

  const login = (data: any) => {
    // Implement your login logic here
    console.log('Login attempt with data:', data);
    // For now, let's simulate a successful login
    setIsAuthenticated(true);
    setAuthSettings({ organization: 'DefaultOrg' }); // Example data
  };

  const logout = () => {
    // Implement your logout logic here
    setIsAuthenticated(false);
    setAuthSettings(null);
    console.log('User logged out');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, authSettings, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Create a custom hook to use the AuthContext
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
