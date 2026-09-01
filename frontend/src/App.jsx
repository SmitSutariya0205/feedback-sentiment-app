import React, { useState, useEffect } from 'react';
import { FeedbackForm } from './components/FeedbackForm';
import { HistoricalFeedback } from './components/HistoricalFeedback';
import { checkHealth } from './api/feedbackApi';
import './App.css';

export function App() {
  const [activeTab, setActiveTab] = useState('submit');
  const [apiHealth, setApiHealth] = useState({ status: 'checking', message: '' });

  useEffect(() => {
    async function verifyBackendConnection() {
      try {
        await checkHealth();
        setApiHealth({ status: 'online', message: 'FastAPI Backend Connected' });
      } catch (err) {
        setApiHealth({
          status: 'offline',
          message: 'FastAPI Server Unreachable',
        });
      }
    }

    verifyBackendConnection();
    // Poll health status every 30 seconds
    const interval = setInterval(verifyBackendConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-shell">
      {/* Background ambient lighting effects */}
      <div className="ambient-orb orb-primary"></div>
      <div className="ambient-orb orb-secondary"></div>

      <header className="app-header">
        <div className="header-container">
          <div className="brand-badge">
            <div className="brand-icon">⚡</div>
            <div className="brand-text">
              <h1 className="brand-title">SentimentIQ</h1>
              <span className="brand-tagline">FastAPI Product Sentiment Platform</span>
            </div>
          </div>

          <div className="header-actions">
            <div className={`health-indicator health-${apiHealth.status}`}>
              <span className="health-dot"></span>
              <span className="health-text">{apiHealth.message}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="main-container">
          {/* Navigation Tabs */}
          <nav className="tab-navigation" aria-label="Main Navigation">
            <button
              type="button"
              className={`tab-btn ${activeTab === 'submit' ? 'active' : ''}`}
              onClick={() => setActiveTab('submit')}
            >
              <span className="tab-icon">📝</span>
              <span className="tab-label">Submit Feedback</span>
            </button>
            <button
              type="button"
              className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              <span className="tab-icon">📊</span>
              <span className="tab-label">Historical Analytics</span>
            </button>
          </nav>

          {/* Active Tab View */}
          <div className="tab-content">
            {activeTab === 'submit' && <FeedbackForm />}
            {activeTab === 'history' && <HistoricalFeedback />}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <div className="footer-container">
          <p>© 2026 SentimentIQ Client — Connected to FastAPI VADER Backend</p>
          <div className="footer-links">
            <span className="footer-link">Bearer Authentication Active</span>
            <span className="footer-separator">•</span>
            <span className="footer-link">Request Tracing Enabled</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
