import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Save, AlertCircle } from 'lucide-react';
import { DashboardSidebar } from '../components/DashboardSidebar';

export function ServerConfig() {
  const { id } = useParams();
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Form State
  const [prefix, setPrefix] = useState('!!');

  useEffect(() => {
    fetch(`/api/guilds/${id}/config`)
      .then(res => {
        if (res.status === 403) throw new Error('Forbidden: You do not have permissions for this server.');
        if (res.status === 404) throw new Error('Bot is not in this server.');
        if (!res.ok) throw new Error('Failed to load configuration.');
        return res.json();
      })
      .then(data => {
        setConfig(data);
        setPrefix(data.prefix || '!!');
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    setError(null);

    try {
      const res = await fetch(`/api/guilds/${id}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prefix })
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
  
  if (error && !config) {
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
      <DashboardSidebar serverName={config.name} serverIcon={config.icon} serverId={id} />
      
      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="server-config-content"
      >
        <div className="config-header">
          <Link to="/dashboard" className="back-link"><ArrowLeft size={20} /> Back to Servers</Link>
          <h2>General Settings</h2>
        </div>

        {error && <div className="alert-error">{error}</div>}
        {success && <div className="alert-success">Settings saved successfully!</div>}

        <form onSubmit={handleSave} className="config-form">
          <div className="form-group">
            <label htmlFor="prefix">Command Prefix</label>
            <p className="help-text">The prefix required to run text commands in your server.</p>
            <input 
              type="text" 
              id="prefix" 
              value={prefix} 
              onChange={(e) => setPrefix(e.target.value)} 
              maxLength={5}
              placeholder="!!"
              required
            />
          </div>



          <div className="form-actions">
            <button type="submit" className="btn-primary save-btn" disabled={saving}>
              <Save size={18} /> {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
