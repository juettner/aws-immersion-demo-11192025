import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

export interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="layout">
      <header className="layout__header">
        <div className="layout__header-content">
          <Link to="/" className="layout__logo">
            🎵 Concert Platform
          </Link>
          <nav className="layout__nav">
            <Link
              to="/"
              className={`layout__nav-link ${isActive('/') ? 'layout__nav-link--active' : ''}`}
            >
              Home
            </Link>
            <Link
              to="/dashboard"
              className={`layout__nav-link ${isActive('/dashboard') ? 'layout__nav-link--active' : ''}`}
            >
              Dashboard
            </Link>
            <Link
              to="/chatbot"
              className={`layout__nav-link ${isActive('/chatbot') ? 'layout__nav-link--active' : ''}`}
            >
              AI Chatbot
            </Link>
          </nav>
        </div>
      </header>
      <main className="layout__main">{children}</main>
      <footer className="layout__footer">
        <div className="layout__footer-content">
          <p>© 2025 Concert Data Platform. Powered by AWS.</p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
