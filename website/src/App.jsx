import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { Home } from './pages/Home';
import { Commands } from './pages/Commands';
import { Dashboard } from './pages/Dashboard';
import { ServerConfig } from './pages/ServerConfig';
import { WelcomeConfig } from './pages/WelcomeConfig';
import { ModerationConfig } from './pages/ModerationConfig';

function App() {
  return (
    <Router>
      <div className="app-wrapper">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/commands" element={<Commands />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/:id" element={<ServerConfig />} />
            <Route path="/dashboard/:id/welcome" element={<WelcomeConfig />} />
            <Route path="/dashboard/:id/moderation" element={<ModerationConfig />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
