import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { config } from '../config';
import logoUrl from '../assets/logo.jpg';

export function Navbar() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch('/api/users/@me')
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Not logged in');
      })
      .then(data => setUser(data))
      .catch(() => setUser(null));
  }, []);

  return (
    <nav className="navbar">
      <div className="container nav-content">
        <Link to="/" className="logo" style={{ display: 'flex', alignItems: 'center' }}>
          <img src={logoUrl} alt="SpaceX Logo" style={{ width: '48px', height: '48px', borderRadius: '12px', marginRight: '12px', objectFit: 'cover' }} />
          {config.BOT_NAME}
        </Link>
        
        <div className={`navbar-links ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`} onClick={() => setMobileMenuOpen(false)}>Home</Link>
          <Link to="/commands" className={`nav-link ${location.pathname === '/commands' ? 'active' : ''}`} onClick={() => setMobileMenuOpen(false)}>Commands</Link>
          <a href={config.SUPPORT_URL} target="_blank" rel="noopener noreferrer" className="nav-link">Support</a>
          <a href="/#feedback" className="nav-link" onClick={(e) => {
            if (location.pathname === '/') {
              e.preventDefault();
              const section = document.querySelector('.reviews-section');
              if (section) section.scrollIntoView({ behavior: 'smooth' });
              setMobileMenuOpen(true);
            }
          }}>Feedback</a>
          <a href="/#contact" className="nav-link" onClick={(e) => {
            if (location.pathname === '/') {
              e.preventDefault();
              const section = document.querySelector('.contact-section');
              if (section) section.scrollIntoView({ behavior: 'smooth' });
              setMobileMenuOpen(false);
            }
          }}>Contact</a>
          
          <div className="nav-actions" style={{ display: 'flex', gap: '12px' }}>
            <a href={config.TOPGG_URL} target="_blank" rel="noopener noreferrer" className="btn btn-vote nav-invite" style={{ fontWeight: 'bold' }}>
              Vote
            </a>
            {user ? (
              <Link to="/dashboard" className="btn btn-primary nav-invite">
                Dashboard
              </Link>
            ) : (
              <a href="/api/auth/login" className="btn btn-primary nav-invite">
                Login
              </a>
            )}
          </div>
        </div>

        <button className="mobile-menu-btn" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Basic inline style for mobile menu just to keep it clean */}
      <style>{`
        @media (max-width: 768px) {
          .navbar-links.mobile-open {
            display: flex;
            flex-direction: column;
            position: absolute;
            top: 70px;
            left: 0;
            width: 100%;
            background: var(--bg-card);
            padding: 24px;
            border-bottom: 1px solid var(--border-light);
            gap: 20px;
          }
          .nav-actions {
            width: 100%;
            flex-direction: column;
          }
          .nav-invite {
            width: 100%;
          }
        }
      `}</style>
    </nav>
  );
}
