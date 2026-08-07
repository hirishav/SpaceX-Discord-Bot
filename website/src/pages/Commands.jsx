import { useState } from 'react';
import { Search, Star } from 'lucide-react';
import { commandData, getCategories } from '../data/commands';
import './Commands.css';

export function Commands() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  
  const categories = getCategories();

  const filteredCommands = commandData.filter(cmd => {
    const matchesSearch = cmd.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          cmd.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = activeCategory === 'All' || cmd.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="commands-page section container">
      <div className="commands-header">
        <h1>Command Directory</h1>
        <p>Explore all the features SpaceX has to offer.</p>
        <p style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontSize: '0.95rem', color: 'var(--accent)', marginTop: '-20px', marginBottom: '32px' }}>
          <Star size={16} fill="#eab308" color="#eab308" />
          <span>Star commands are highly used in most servers</span>
        </p>
        
        <div className="search-bar">
          <Search className="search-icon" size={20} />
          <input 
            type="text" 
            placeholder="Search for a command (e.g. ban, ticket, bal...)" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="commands-layout">
        <aside className="categories-sidebar">
          <h3>Categories</h3>
          <ul className="category-list">
            {categories.map(category => (
              <li key={category}>
                <button 
                  className={`category-btn ${activeCategory === category ? 'active' : ''}`}
                  onClick={() => setActiveCategory(category)}
                >
                  {category}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <div className="commands-grid">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((cmd, idx) => (
              <div key={idx} className="command-card">
                <div className="command-card-header">
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {cmd.usage}
                    {cmd.popular && (
                      <span style={{ display: 'flex' }} title={`${cmd.popular}x Popular Command`}>
                        {[...Array(cmd.popular)].map((_, i) => (
                          <Star key={i} size={16} fill="#eab308" color="#eab308" style={{ filter: 'drop-shadow(0 0 4px rgba(234, 179, 8, 0.4))', marginLeft: i > 0 ? '-6px' : '0' }} />
                        ))}
                      </span>
                    )}
                  </h4>
                  <span className="badge">{cmd.category}</span>
                </div>
                <p>{cmd.description}</p>
                {cmd.aliases.length > 0 && (
                  <div className="aliases">
                    <strong>Aliases:</strong> 
                    {cmd.aliases.map(alias => (
                      <span key={alias} className="alias-tag">{alias}</span>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="no-results">
              <p>No commands found for "{searchQuery}".</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
