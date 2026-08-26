import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Settings, ExternalLink } from 'lucide-react';

export function Dashboard() {
  const [user, setUser] = useState(null);
  const [guilds, setGuilds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [clientId, setClientId] = useState('');

  useEffect(() => {
    fetch('/api/client_id')
      .then(res => res.json())
      .then(data => setClientId(data.client_id))
      .catch(console.error);

    fetch('/api/users/@me')
      .then(res => {
        if (!res.ok) throw new Error('Not logged in');
        return res.json();
      })
      .then(data => {
        setUser(data);
        return fetch('/api/users/@me/guilds');
      })
      .then(res => res.json())
      .then(data => {
        setGuilds(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        window.location.href = '/api/auth/login';
      });
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="dashboard-header"
      >
        <div className="user-profile">
          <img 
            src={`https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`} 
            alt="User Avatar" 
            className="avatar"
          />
          <div>
            <h1>Welcome, {user.global_name || user.username}</h1>
            <p>Select a server to configure SpaceX Bot.</p>
          </div>
        </div>
        <a href="/api/auth/logout" className="btn-secondary">Logout</a>
      </motion.div>

      <div className="guilds-grid">
        {guilds.map((guild, index) => (
          <motion.div 
            key={guild.id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.03 }}
            className={`guild-card ${!guild.bot_in_guild ? 'disabled' : ''}`}
          >
            <div className="guild-icon">
              {guild.icon ? (
                <img src={`https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`} alt={guild.name} />
              ) : (
                <div className="guild-icon-placeholder">{guild.name.charAt(0)}</div>
              )}
            </div>
            <h3>{guild.name}</h3>
            <div className="guild-actions">
              {guild.bot_in_guild ? (
                <Link to={`/dashboard/${guild.id}`} className="btn-primary">
                  <Settings size={18} /> Configure
                </Link>
              ) : (
                <a 
                  href={`https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=8&scope=bot%20applications.commands&guild_id=${guild.id}`} 
                  target="_blank" rel="noreferrer"
                  className="btn-secondary"
                >
                  <ExternalLink size={18} /> Invite Bot
                </a>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
