import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  PlayCircle,
  UserCheck,
  ShieldAlert,
  BarChart3,
  Shield,
  Activity
} from 'lucide-react';
import { SyntheticBanner } from './SyntheticBanner';
import './Layout.css';

export const Layout: React.FC = () => {
  return (
    <div className="app-container">
      <SyntheticBanner />
      <div className="app-body">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="sidebar-logo">
              <Shield className="sidebar-logo-icon" />
              <div>
                <span className="sidebar-title">Risk Intel</span>
                <span className="sidebar-badge">v1.0</span>
              </div>
            </div>
            <p className="sidebar-subtitle">Adaptive Trader Behaviour Engine</p>
          </div>

          <nav className="sidebar-nav">
            <NavLink
              to="/"
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
            >
              <LayoutDashboard size={18} />
              <span>Overview</span>
            </NavLink>

            <NavLink
              to="/replay"
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
            >
              <PlayCircle size={18} />
              <span>Session Replay</span>
            </NavLink>

            <NavLink
              to="/baseline"
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
            >
              <UserCheck size={18} />
              <span>Trader Baseline</span>
            </NavLink>

            <NavLink
              to="/interventions"
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
            >
              <ShieldAlert size={18} />
              <span>Interventions</span>
            </NavLink>

            <NavLink
              to="/evaluation"
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
            >
              <BarChart3 size={18} />
              <span>Evaluation & Impact</span>
            </NavLink>
          </nav>

          <div className="sidebar-footer">
            <div className="system-status">
              <Activity size={14} className="status-dot" />
              <span>Shadow Mode Active</span>
            </div>
            <p className="system-note">Simulated orders only</p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
