import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Ticket, Wallet, Smile, Plus, UserPlus, Star, Send, Image, Users, Code, Ghost, Briefcase, MessageSquare } from 'lucide-react';
import { config } from '../config';
import heroImg from '../assets/hero.png';
import './Home.css';

export function Home() {
  const [reviews, setReviews] = useState([]);
  const [newReview, setNewReview] = useState({ username: '', text: '', rating: 5 });

  useEffect(() => {
    const saved = localStorage.getItem('spacex_reviews');
    if (saved) {
      setReviews(JSON.parse(saved));
    }
  }, []);

  const handleReviewSubmit = (e) => {
    e.preventDefault();
    if (!newReview.username.trim() || !newReview.text.trim()) return;
    
    const updatedReviews = [newReview, ...reviews];
    setReviews(updatedReviews);
    localStorage.setItem('spacex_reviews', JSON.stringify(updatedReviews));
    setNewReview({ username: '', text: '', rating: 5 });
  };

  return (
    <div className="home-page">
      {/* HERO SECTION */}
      <section className="hero container">
        <div className="hero-content">
          <h1>Discord Server Sambhalna Ab Easy Hai</h1>
          <p>
            Tickets handle karna ho ya server clean rakhna ho — {config.BOT_NAME} kaam sambhal lega.
            Packed with global economy, stocks, moderation, and fun commands.
          </p>
          <div className="hero-actions">
            <a href={config.INVITE_URL} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
              <Plus size={18} /> Add to Discord
            </a>
            <Link to="/commands" className="btn btn-secondary">
              View Commands
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          {/* Hero visual */}
          <img src={heroImg} alt="SpaceX Interface" style={{ width: '100%', borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }} onError={(e) => {
            e.target.style.display = 'none';
            e.target.parentElement.classList.add('visual-placeholder');
          }} />
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section className="features-section section">
        <div className="container">
          <div className="section-header">
            <h2>Core Capabilities</h2>
            <p>Everything you need for a healthy, active community.</p>
          </div>
          
          <div className="features-grid">
            <div className="feature-card">
              <Shield className="feature-icon" size={32} />
              <h3>Moderation</h3>
              <p>Moderation ka kaam baar-baar manually karne ki zarurat nahi. Ban, kick, mute, warn, and automated role audits built right in.</p>
            </div>
            
            <div className="feature-card">
              <Ticket className="feature-icon" size={32} />
              <h3>Tickets</h3>
              <p>Support ka kaam ab messy nahi. Fully featured ticket panels, claims, closures, and auto-generated transcripts.</p>
            </div>
            
            <div className="feature-card">
              <Wallet className="feature-icon" size={32} />
              <h3>Economy & Stocks</h3>
              <p>Keep your chat active with a global economy. Work, rob, play blackjack, or invest in dynamic virtual stocks.</p>
            </div>

            <div className="feature-card">
              <UserPlus className="feature-icon" size={32} />
              <h3>Welcome System</h3>
              <p>Give new members a warm welcome. Setup custom welcome channels, messages, and ping them easily.</p>
            </div>

            <div className="feature-card">
              <Smile className="feature-icon" size={32} />
              <h3>Fun & Comedy</h3>
              <p>Fun commands bhi hain. Server ko boring nahi hone denge. Confessions, roasting, and love matches.</p>
            </div>
          </div>
        </div>
      </section>

      {/* REVIEWS SECTION */}
      <section className="reviews-section section">
        <div className="container">
          <div className="section-header">
            <h2>Community Feedback</h2>
            <p>Tell us what you think about SpaceX.</p>
          </div>
          
          <div className="review-form-container">
            <form onSubmit={handleReviewSubmit} className="review-form">
              <div className="form-group">
                <input 
                  type="text" 
                  placeholder="Discord Username" 
                  value={newReview.username}
                  onChange={(e) => setNewReview({...newReview, username: e.target.value})}
                  required
                />
                <select 
                  value={newReview.rating} 
                  onChange={(e) => setNewReview({...newReview, rating: parseInt(e.target.value)})}
                >
                  <option value="5">5 Stars</option>
                  <option value="4">4 Stars</option>
                  <option value="3">3 Stars</option>
                  <option value="2">2 Stars</option>
                  <option value="1">1 Star</option>
                </select>
              </div>
              <textarea 
                placeholder="Write your review here..." 
                value={newReview.text}
                onChange={(e) => setNewReview({...newReview, text: e.target.value})}
                required
                rows="3"
              ></textarea>
              <button type="submit" className="btn btn-primary" style={{ width: 'fit-content' }}>
                <Send size={16} /> Submit Review
              </button>
            </form>
          </div>

          <div className="reviews-grid" style={{ marginTop: '60px' }}>
            {reviews.length > 0 ? reviews.map((review, idx) => (
              <div className="review-card" key={idx}>
                <div className="review-header">
                  <img src={`https://ui-avatars.com/api/?name=${encodeURIComponent(review.username)}&background=18181b&color=fff&rounded=true`} alt={review.username} className="reviewer-avatar" />
                  <div className="reviewer-info">
                    <h4>{review.username}</h4>
                    <div className="stars">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} size={14} className={`star-icon ${i < review.rating ? 'filled' : ''}`} />
                      ))}
                    </div>
                  </div>
                </div>
                <p className="review-text">"{review.text}"</p>
              </div>
            )) : (
              <div className="no-reviews" style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'var(--text-muted)', padding: '40px', background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-light)' }}>
                <p>No reviews yet. Be the first to rate SpaceX!</p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* VOTE / SUPPORT SECTION */}
      <section className="cta-section section">
        <div className="container cta-container">
          <div className="cta-content">
            <h2>{config.BOT_NAME} pasand aa raha hai?</h2>
            <p>Top.gg pe ek vote = bot ko thoda aur grow karne mein help ❤️</p>
            <a href={config.TOPGG_URL} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
              Vote on Top.gg
            </a>
          </div>
          <div className="cta-content">
            <h2>Support Chahiye?</h2>
            <p>Kuch toot gaya? Koi command samajh nahi aa rahi? Ya bas {config.BOT_NAME} ke saath chill karna hai?</p>
            <a href={config.SUPPORT_URL} target="_blank" rel="noopener noreferrer" className="btn btn-secondary">
              Join Support Server
            </a>
          </div>
        </div>
      </section>

      {/* CONTACT SECTION */}
      <section className="contact-section section" id="contact">
        <div className="container">
          <div className="section-header">
            <h2>Get In Touch</h2>
            <p>Connect with the developer on these platforms</p>
          </div>
          
          <div className="social-links-grid">
            <a href="https://discord.com" target="_blank" rel="noopener noreferrer" className="social-card" onClick={(e) => { e.preventDefault(); alert('Discord ID: phrenic_rishav'); }}>
              <img src="https://cdn.simpleicons.org/discord/5865F2" alt="Discord" style={{ width: '28px', height: '28px' }} />
              <span>Discord</span>
            </a>
            <a href="https://www.instagram.com/phrenic_rishav/" target="_blank" rel="noopener noreferrer" className="social-card">
              <img src="https://cdn.simpleicons.org/instagram/E4405F" alt="Instagram" style={{ width: '28px', height: '28px' }} />
              <span>Instagram</span>
            </a>
            <a href="https://www.facebook.com/people/Rishav-Das/61578312563981/" target="_blank" rel="noopener noreferrer" className="social-card">
              <img src="https://cdn.simpleicons.org/facebook/1877F2" alt="Facebook" style={{ width: '28px', height: '28px' }} />
              <span>Facebook</span>
            </a>
            <a href="https://t.me/phrenic_rishav" target="_blank" rel="noopener noreferrer" className="social-card">
              <img src="https://cdn.simpleicons.org/telegram/26A5E4" alt="Telegram" style={{ width: '28px', height: '28px' }} />
              <span>Telegram</span>
            </a>
            <a href="https://www.snapchat.com/@phrenic_rishav?share_id=Pd322-KLTv0&locale=en-US" target="_blank" rel="noopener noreferrer" className="social-card">
              <img src="https://cdn.simpleicons.org/snapchat/FFFC00" alt="Snapchat" style={{ width: '28px', height: '28px' }} />
              <span>Snapchat</span>
            </a>
            <a href="https://www.linkedin.com/in/rishav-rd/" target="_blank" rel="noopener noreferrer" className="social-card">
              <img src="https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png" alt="LinkedIn" style={{ width: '28px', height: '28px' }} />
              <span>LinkedIn</span>
            </a>
            <a href="https://github.com/hirishav/" target="_blank" rel="noopener noreferrer" className="social-card">
              <img src="https://cdn.simpleicons.org/github/white" alt="GitHub" style={{ width: '28px', height: '28px' }} />
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
