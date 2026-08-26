import React from 'react';
import { NavLink } from 'react-router-dom';
import { Settings, Shield, UserPlus, FileText, Bell } from 'lucide-react';

export function DashboardSidebar({ serverName, serverIcon, serverId }) {
  return (
    <aside className="dashboard-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-server-info">
          {serverIcon ? (
            <img src={`https://cdn.discordapp.com/icons/${serverId}/${serverIcon}.png`} alt={serverName} />
          ) : (
            <div className="sidebar-icon-placeholder">{serverName?.charAt(0) || '?'}</div>
          )}
          <h3>{serverName}</h3>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <NavLink to={`/dashboard/${serverId}`} end className={({ isActive }) => isActive ? 'active' : ''}>
          <Settings size={18} /> General
        </NavLink>
        <NavLink to={`/dashboard/${serverId}/moderation`} className={({ isActive }) => isActive ? 'active' : ''}>
          <Shield size={18} /> Moderation
        </NavLink>
        <NavLink to={`/dashboard/${serverId}/welcome`} className={({ isActive }) => isActive ? 'active' : ''}>
          <UserPlus size={18} /> Welcome
        </NavLink>
      </nav>
    </aside>
  );
}
