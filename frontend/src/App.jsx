import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import StockEntry from './components/StockEntry';
import AuditLog from './components/AuditLog';
import AdminCategories from './components/AdminCategories';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error('Component error caught by boundary:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="ph-alert ph-alert-danger" style={{ margin: 24 }}>
          <i className="bi bi-exclamation-triangle-fill" style={{ fontSize: '1.2rem' }}></i>
          <div>
            <div style={{ fontWeight: 700, marginBottom: 2 }}>Something went wrong</div>
            <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
              {this.state.error?.message || 'An unexpected error occurred.'}
            </div>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              style={{
                marginTop: 8, padding: '4px 12px', borderRadius: 6,
                border: '1px solid currentColor', background: 'transparent',
                color: 'inherit', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
              }}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const Sidebar = ({ activeTab, setActiveTab, sidebarOpen, setSidebarOpen }) => {
  const { user, logout } = useAuth();

  if (!user) return null;

  const isAdmin = user.role === 'admin';
  const isSupervisor = user.role === 'supervisor' || isAdmin;

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'bi-speedometer2' },
    { id: 'stock', label: 'Stock & Scanner', icon: 'bi-box-seam' },
  ];

  if (isSupervisor) {
    navItems.push({ id: 'audit', label: 'Audit Log', icon: 'bi-journal-text' });
  }
  if (isAdmin) {
    navItems.push({ id: 'admin', label: 'Admin Rules', icon: 'bi-sliders' });
  }

  const initials = user.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : '??';

  const handleNav = (tab) => {
    setActiveTab(tab);
    setSidebarOpen(false);
  };

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="sidebar-mobile-toggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle navigation"
      >
        <i className={`bi ${sidebarOpen ? 'bi-x-lg' : 'bi-list'}`}></i>
      </button>

      {/* Overlay */}
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <i className="bi bi-shield-plus"></i>
          </div>
          <div className="sidebar-brand-text">
            <h5>Pharmakon</h5>
            <small>Pharmaceutical Intelligence</small>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Main Menu</div>
          {navItems.map((item) => (
            <div key={item.id} className="sidebar-nav-item">
              <button
                onClick={() => handleNav(item.id)}
                className={`sidebar-nav-link ${activeTab === item.id ? 'active' : ''}`}
              >
                <i className={`bi ${item.icon}`}></i>
                <span>{item.label}</span>
              </button>
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user.full_name}</div>
              <div className="sidebar-user-role">{user.role}</div>
            </div>
          </div>
          <button onClick={logout} className="sidebar-signout">
            <i className="bi bi-box-arrow-left"></i>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};

const MainContent = () => {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--ph-bg)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'linear-gradient(135deg, var(--ph-gold) 0%, var(--ph-gold-dark) 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 4px 12px rgba(201, 168, 76, 0.3)',
          }}>
            <i className="bi bi-shield-plus" style={{ fontSize: '1.5rem', color: '#fff' }}></i>
          </div>
          <div className="ph-spinner ph-spinner-dark" style={{ width: 28, height: 28, marginBottom: 12 }}></div>
          <p style={{ fontSize: '0.8rem', color: 'var(--ph-text-muted)', fontWeight: 500, margin: 0 }}>
            Initializing Pharmakon...
          </p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
      />
      <main className="main-content fade-in">
        <ErrorBoundary key={activeTab}>
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'stock' && <StockEntry />}
          {activeTab === 'audit' && <AuditLog />}
          {activeTab === 'admin' && <AdminCategories />}
        </ErrorBoundary>
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  );
}

export default App;
