import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Save, AlertCircle } from 'lucide-react';
import { DashboardSidebar } from '../components/DashboardSidebar';

export function ModerationConfig() {
  const { id } = useParams();
  const [serverName, setServerName] = useState('...');
  const [serverIcon, setServerIcon] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Default true, will set to false if found in disabled_modules_server
  const [modules, setModules] = useState({
    fun: true,
    economy: true,
    moderation: true,
    utility: true,
    ticket: true
  });

  // Disabled commands state
  const [allCommands, setAllCommands] = useState([]);
  const [disabledCommands, setDisabledCommands] = useState([]);
  const [commandSearch, setCommandSearch] = useState('');

  useEffect(() => {
    Promise.all([
      fetch(`/api/guilds/${id}/moderation`).then(res => res.json()),
      fetch(`/api/guilds/${id}/config`).then(res => res.json()),
      fetch(`/api/commands`).then(res => res.json())
    ])
    .then(([modData, configData, cmdData]) => {
      if (modData.error) throw new Error(modData.error);
      
      const disabled = modData.disabled_modules || [];
      setModules({
        fun: !disabled.includes('fun'),
        economy: !disabled.includes('economy'),
        moderation: !disabled.includes('moderation'),
        utility: !disabled.includes('utility'),
        ticket: !disabled.includes('ticket')
      });
      
      setDisabledCommands(modData.disabled_commands || []);
      if (cmdData && cmdData.commands) {
        setAllCommands(cmdData.commands);
      }

      setServerName(configData.name);
      setServerIcon(configData.icon);
      
      setLoading(false);
    })
    .catch(err => {
      setError(err.message || 'Failed to load configuration.');
      setLoading(false);
    });
  }, [id]);

  const handleToggle = (moduleName) => {
    setModules(prev => ({
      ...prev,
      [moduleName]: !prev[moduleName]
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    setError(null);

    const disabledList = Object.keys(modules).filter(key => !modules[key]);

    try {
      const res = await fetch(`/api/guilds/${id}/moderation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          disabled_modules: disabledList,
          disabled_commands: disabledCommands
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
          <h2>Moderation & Modules</h2>
        </div>

        {error && <div className="alert-error">{error}</div>}
        {success && <div className="alert-success">Settings saved successfully!</div>}

        <form onSubmit={handleSave} className="config-form">
          <p className="help-text" style={{ marginBottom: '20px' }}>Enable or disable core bot modules across your entire server.</p>

          <div className="form-group toggle-group">
            <div>
              <label>Moderation Module</label>
              <p className="help-text">Commands like ban, kick, mute, warn, purge.</p>
            </div>
            <label className="switch">
              <input type="checkbox" checked={modules.moderation} onChange={() => handleToggle('moderation')} />
              <span className="slider round"></span>
            </label>
          </div>

          <div className="form-group toggle-group">
            <div>
              <label>Economy & Stocks</label>
              <p className="help-text">Global economy commands, gambling, and virtual stock market.</p>
            </div>
            <label className="switch">
              <input type="checkbox" checked={modules.economy} onChange={() => handleToggle('economy')} />
              <span className="slider round"></span>
            </label>
          </div>

          <div className="form-group toggle-group">
            <div>
              <label>Fun Commands</label>
              <p className="help-text">Roasts, confessions, love match, and other fun games.</p>
            </div>
            <label className="switch">
              <input type="checkbox" checked={modules.fun} onChange={() => handleToggle('fun')} />
              <span className="slider round"></span>
            </label>
          </div>

          <div className="form-group toggle-group">
            <div>
              <label>Ticket System</label>
              <p className="help-text">Support ticket management and transcripts.</p>
            </div>
            <label className="switch">
              <input type="checkbox" checked={modules.ticket} onChange={() => handleToggle('ticket')} />
              <span className="slider round"></span>
            </label>
          </div>

          <div className="form-group toggle-group">
            <div>
              <label>Utility Commands</label>
              <p className="help-text">AFK, RemindMe, UserInfo, ServerInfo, etc.</p>
            </div>
            <label className="switch">
              <input type="checkbox" checked={modules.utility} onChange={() => handleToggle('utility')} />
              <span className="slider round"></span>
            </label>
          </div>

          <div className="form-group" style={{ marginTop: '30px' }}>
            <label>Disable Specific Commands</label>
            <p className="help-text">Select individual commands to disable them across your server.</p>
            <input 
              type="text" 
              placeholder="Search commands..." 
              value={commandSearch}
              onChange={(e) => setCommandSearch(e.target.value)}
              style={{ marginBottom: '10px' }}
            />
            <div style={{ maxHeight: '250px', overflowY: 'auto', background: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              {allCommands.filter(cmd => cmd.toLowerCase().includes(commandSearch.toLowerCase())).map(cmd => (
                <label key={cmd} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={disabledCommands.includes(cmd)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setDisabledCommands([...disabledCommands, cmd]);
                      } else {
                        setDisabledCommands(disabledCommands.filter(c => c !== cmd));
                      }
                    }}
                    style={{ width: '18px', height: '18px', accentColor: '#8b5cf6' }}
                  />
                  <span style={{ fontSize: '15px', color: disabledCommands.includes(cmd) ? '#f87171' : '#fff' }}>/{cmd}</span>
                </label>
              ))}
              {allCommands.filter(cmd => cmd.toLowerCase().includes(commandSearch.toLowerCase())).length === 0 && (
                <p style={{ color: '#aaa', fontStyle: 'italic' }}>No commands found.</p>
              )}
            </div>
          </div>

          <div className="form-actions" style={{ marginTop: '30px' }}>
            <button type="submit" className="btn-primary save-btn" disabled={saving}>
              <Save size={18} /> {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
