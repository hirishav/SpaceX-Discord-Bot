import { Link } from 'react-router-dom';
import { config } from '../config';

export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <h3>{config.BOT_NAME}</h3>
            <p>Discord Server sambhalna ab easy hai. Top-tier moderation, global economy, and utility features packed into one bot.</p>
          </div>
          
          <div className="footer-links">
            <h4>Quick Links</h4>
            <Link to="/">Home</Link>
            <Link to="/commands">Commands</Link>
            <a href={config.SUPPORT_URL} target="_blank" rel="noopener noreferrer">Support Server</a>
          </div>

          <div className="footer-links">
            <h4>Support</h4>
            <a href={config.INVITE_URL} target="_blank" rel="noopener noreferrer">Invite Bot</a>
            <a href={config.TOPGG_URL} target="_blank" rel="noopener noreferrer">Vote on Top.gg</a>
          </div>
        </div>
        
        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} {config.BOT_NAME}. Not affiliated with Discord Inc.</p>
        </div>
      </div>
    </footer>
  );
}
