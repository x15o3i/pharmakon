import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const quickLogin = async (demoEmail) => {
    setEmail(demoEmail);
    setPassword('Password123!');
    setSubmitting(true);
    setError('');
    try {
      await login(demoEmail, 'Password123!');
    } catch (err) {
      setError('Demo login failed. Make sure seed_db has been executed.');
    } finally {
      setSubmitting(false);
    }
  };

  const features = [
    { icon: 'bi-camera-fill', text: 'Barcode & QR scanning with camera support' },
    { icon: 'bi-bell-fill', text: 'Automated expiry alerts via SMS, email & WhatsApp' },
    { icon: 'bi-graph-up-arrow', text: 'ABC/VED Pareto classification engine' },
    { icon: 'bi-clipboard2-check-fill', text: 'Closed-loop audit trail & compliance logs' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Left Branded Panel */}
      <div
        className="login-left-panel"
        style={{
          width: '45%',
          background: 'linear-gradient(160deg, #0b0e1a 0%, #111627 50%, #1a1f36 100%)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '60px 56px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Decorative circles */}
        <div style={{
          position: 'absolute', top: -80, right: -80,
          width: 300, height: 300, borderRadius: '50%',
          background: 'rgba(255,255,255,0.03)',
        }} />
        <div style={{
          position: 'absolute', bottom: -60, left: -60,
          width: 200, height: 200, borderRadius: '50%',
          background: 'rgba(255,255,255,0.04)',
        }} />

        {/* Brand */}
        <div style={{ marginBottom: 48, position: 'relative', zIndex: 1 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14,
            background: 'rgba(255,255,255,0.15)',
            backdropFilter: 'blur(8px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 20,
          }}>
            <i className="bi bi-shield-plus" style={{ fontSize: '1.5rem', color: '#fff' }}></i>
          </div>
          <h1 style={{
            fontSize: '1.75rem', fontWeight: 800, color: '#fff',
            margin: '0 0 8px', lineHeight: 1.2,
          }}>
            Pharmakon
          </h1>
          <p style={{
            fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)',
            margin: 0, maxWidth: 320, lineHeight: 1.6,
          }}>
            Pharmaceutical Intelligence Platform
          </p>
        </div>

        {/* Features */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, position: 'relative', zIndex: 1 }}>
          {features.map((f, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '14px 18px', borderRadius: 10,
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: 'rgba(201, 168, 76, 0.25)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <i className={`bi ${f.icon}`} style={{ color: '#e8d9a0', fontSize: '1rem' }}></i>
              </div>
              <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: '0.85rem', fontWeight: 500 }}>
                {f.text}
              </span>
            </div>
          ))}
        </div>

        {/* Footer */}
        <p style={{
          position: 'absolute', bottom: 28, left: 56, right: 56,
          fontSize: '0.72rem', color: 'rgba(255,255,255,0.3)',
          zIndex: 1,
        }}>
          &copy; {new Date().getFullYear()} Pharmakon. All rights reserved.
        </p>
      </div>

      {/* Right Login Panel */}
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '40px', background: '#f8fafc',
      }}>
        <div style={{ width: '100%', maxWidth: 400 }}>
          {/* Mobile brand (hidden on desktop) */}
          <div style={{ textAlign: 'center', marginBottom: 32 }} className="d-lg-none">
            <div style={{
              width: 56, height: 56, borderRadius: 14,
              background: 'linear-gradient(135deg, var(--ph-gold) 0%, var(--ph-gold-dark) 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 12px',
              boxShadow: '0 4px 12px rgba(201, 168, 76, 0.3)',
            }}>
            <i className="bi bi-shield-plus" style={{ fontSize: '1.5rem', color: '#fff' }}></i>
          </div>
          <h3 style={{ fontWeight: 800, color: 'var(--ph-text)', margin: 0, fontSize: '1.25rem' }}>
            Pharmakon
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--ph-text-muted)', margin: '4px 0 0' }}>
            Pharmaceutical Intelligence Platform
          </p>
          </div>

          <h2 style={{
            fontSize: '1.5rem', fontWeight: 700, color: 'var(--ph-text)',
            margin: '0 0 6px',
          }}>
            Welcome back
          </h2>
          <p style={{
            fontSize: '0.85rem', color: 'var(--ph-text-muted)',
            margin: '0 0 28px',
          }}>
            Sign in to your pharmacy account
          </p>

          {error && (
            <div className="ph-alert ph-alert-danger" style={{ marginBottom: 20 }}>
              <i className="bi bi-exclamation-triangle-fill"></i>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 18 }}>
              <label className="ph-label">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@pharmacy.com"
                className="ph-input"
                style={{ height: 44 }}
              />
            </div>

            <div style={{ marginBottom: 28 }}>
              <label className="ph-label">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="ph-input"
                style={{ height: 44 }}
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="btn-ph-primary"
              style={{ width: '100%', justifyContent: 'center', height: 44 }}
            >
              {submitting ? (
                <>
                  <span className="ph-spinner"></span>
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <i className="bi bi-arrow-right"></i>
                </>
              )}
            </button>
          </form>

          {import.meta.env.DEV && (
            <div style={{
              marginTop: 32, paddingTop: 24,
              borderTop: '1px solid var(--ph-border)',
            }}>
              <p style={{
                fontSize: '0.72rem', textTransform: 'uppercase',
                letterSpacing: '0.06em', fontWeight: 600,
                color: 'var(--ph-text-muted)', textAlign: 'center',
                margin: '0 0 12px',
              }}>
                Quick Demo Access
              </p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => quickLogin('pharmacist@pharmacy.com')}
                  style={{
                    flex: 1, padding: '8px 0', borderRadius: 8,
                    border: '1px solid var(--ph-border)', background: '#fff',
                    fontSize: '0.8rem', fontWeight: 600, color: 'var(--ph-text-secondary)',
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  Pharmacist
                </button>
                <button
                  type="button"
                  onClick={() => quickLogin('supervisor@pharmacy.com')}
                  style={{
                    flex: 1, padding: '8px 0', borderRadius: 8,
                    border: '1px solid var(--ph-border)', background: '#fff',
                    fontSize: '0.8rem', fontWeight: 600, color: 'var(--ph-text-secondary)',
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  Supervisor
                </button>
                <button
                  type="button"
                  onClick={() => quickLogin('admin@pharmacy.com')}
                  style={{
                    flex: 1, padding: '8px 0', borderRadius: 8,
                    border: '1px solid var(--ph-gold)', background: 'var(--ph-gold-bg)',
                    fontSize: '0.8rem', fontWeight: 600, color: 'var(--ph-gold-dark)',
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  Admin
                </button>
              </div>
            </div>
          )}

          <p style={{
            textAlign: 'center', marginTop: 32,
            fontSize: '0.75rem', color: 'var(--ph-text-muted)',
          }}>
            Pharmaceutical Intelligence Platform
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
