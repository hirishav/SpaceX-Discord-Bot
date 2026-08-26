import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Save, AlertCircle } from 'lucide-react';
import { DashboardSidebar } from '../components/DashboardSidebar';

export function WelcomeConfig() {
  const { id } = useParams();
  const [serverName, setServerName] = useState('...');
  const [serverIcon, setServerIcon] = useState(null);
  const [channels, setChannels] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Form State
  const [enabled, setEnabled] = useState(false);
  const [channelId, setChannelId] = useState('');
  const [message, setMessage] = useState('Welcome {user} to {server}! 🎉');
  const [mention, setMention] = useState(true);

  useEffect(() => {
    // Fetch channels and config
    Promise.all([
      fetch(`/api/guilds/${id}/channels`).then(res => res.json()),
      fetch(`/api/guilds/${id}/welcome`).then(res => res.json()),
      fetch(`/api/guilds/${id}/config`).then(res => res.json())
    ])
    .then(([channelsData, welcomeData, configData]) => {
      if (channelsData.error) throw new Error(channelsData.error);
      if (welcomeData.error) throw new Error(welcomeData.error);
      
      setChannels(channelsData.channels || []);
      
      setEnabled(welcomeData.enabled === 1);
      setChannelId(welcomeData.channel_id || '');
      setMessage(welcomeData.message || 'Welcome {user} to {server}! 🎉');
      setMention(welcomeData.mention === 1);

      setServerName(configData.name);
      setServerIcon(configData.icon);
      
      setLoading(false);
    })
    .catch(err => {
      setError(err.message || 'Failed to load configuration.');
      setLoading(false);
    });
  }, [id]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    setError(null);

    try {
      const res = await fetch(`/api/guilds/${id}/welcome`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: enabled ? 1 : 0,
          channel_id: channelId,
          message: message,
          mention: mention ? 1 : 0
        })
      });
      
      if (!res.ok) throw new Error('Failed to save configuration');
      
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="dashboard-loading"><div className="spinner"></div></div>;
  
  if (error && !serverName) {
    return (
      <div className="dashboard-error">
        <AlertCircle size={48} color="#f87171" />
        <h2>Access Denied</h2>
        <p>{error}</p>
        <Link to="/dashboard" className="btn-primary">Back to Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="server-config-layout">
      <DashboardSidebar serverName={serverName} serverIcon={serverIcon} serverId={id} />
      
      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="server-config-content"
      >
        <div className="config-header">
          <Link to="/dashboard" className="back-link"><ArrowLeft size={20} /> Back to Servers</Link>
          <h2>Welcome Settings</h2>
        </div>

        {error && <div className="alert-error">{error}</div>}
        {success && <div className="alert-success">Settings saved successfully!</div>}

        <form onSubmit={handleSave} className="config-form">
          <div className="form-group toggle-group">
            <div>
              <label>Enable Welcome Module</label>
              <p className="help-text">Announce when someone new joins the server.</p>
            </div>
            <label className="switch">
              <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
              <span className="slider round"></span>
            </label>
          </div>

          <div className={`form-group ${!enabled ? 'disabled' : ''}`}>
            <label htmlFor="channel">Welcome Channel</label>
            <p className="help-text">Where should SpaceX send the welcome message?</p>
            <select 
              id="channel" 
              value={channelId} 
              onChange={(e) => setChannelId(e.target.value)}
              disabled={!enabled}
            >
              <option value="">Select a channel...</option>
              {channels.map(ch => (
                <option key={ch.id} value={ch.id}>#{ch.name}</option>
              ))}
            </select>
          </div>

          <div className={`form-group ${!enabled ? 'disabled' : ''}`}>
            <label htmlFor="message">Welcome Message</label>
            <p className="help-text">Available placeholders: {'{user}'}, {'{server}'}, {'{membercount}'}</p>
            <textarea 
              id="message" 
              value={message} 
              onChange={(e) => setMessage(e.target.value)} 
              rows="4"
              disabled={!enabled}
            ></textarea>
          </div>
          
          <div className={`form-group toggle-group ${!enabled ? 'disabled' : ''}`}>
            <div>
              <label>Mention User</label>
              <p className="help-text">Mention the user when they join.</p>
            </div>
            <label className="switch">
              <input type="checkbox" checked={mention} onChange={(e) => setMention(e.target.checked)} disabled={!enabled} />
              <span className="slider round"></span>
            </label>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-primary save-btn" disabled={saving || (!enabled && false)}>
              <Save size={18} /> {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
