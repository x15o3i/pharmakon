import React, { useState, useEffect } from 'react';
import api from '../services/api';

const AuditLog = () => {
  const [actions, setActions] = useState([]);
  const [notificationLogs, setNotificationLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('actions');

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const [actRes, notifRes] = await Promise.all([
        api.get('/alerts/actions/'),
        api.get('/alerts/logs/'),
      ]);
      setActions(actRes.data);
      setNotificationLogs(notifRes.data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-100">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h3>
            <i className="bi bi-file-earmark-medical-fill" style={{ color: 'var(--ph-gold-dark)' }}></i>
            Compliance Audit &amp; Activity Log
          </h3>
          <p>Complete audit trail of resolved alerts, actions, and dispatched notifications</p>
        </div>
        <div className="ph-filter-tabs">
          <button
            onClick={() => setActiveSubTab('actions')}
            className={`ph-filter-tab ${activeSubTab === 'actions' ? 'active' : ''}`}
          >
            Closed-Loop Actions
          </button>
          <button
            onClick={() => setActiveSubTab('notifications')}
            className={`ph-filter-tab ${activeSubTab === 'notifications' ? 'active' : ''}`}
          >
            Notification Logs
          </button>
        </div>
      </div>

      {loading ? (
        <div className="ph-card">
          <div className="ph-loading">
            <div className="ph-spinner ph-spinner-dark" style={{ width: 28, height: 28, margin: '0 auto 12px' }}></div>
            Loading audit history...
          </div>
        </div>
      ) : activeSubTab === 'actions' ? (
        <div className="ph-card">
          {actions.length === 0 ? (
            <div className="ph-empty">
              <div className="ph-empty-icon" style={{ background: 'var(--ph-bg)', color: 'var(--ph-text-muted)' }}>
                <i className="bi bi-clipboard2-check"></i>
              </div>
              <h5>No closed-loop actions recorded yet.</h5>
              <p>Actions will appear here when staff resolve expiry alerts.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="ph-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Action Type</th>
                    <th>Performed By</th>
                    <th>Reason / Explanation</th>
                  </tr>
                </thead>
                <tbody>
                  {actions.map((act) => (
                    <tr key={act.id}>
                      <td>
                        <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--ph-text-muted)' }}>
                          {new Date(act.performed_at).toLocaleString()}
                        </span>
                      </td>
                      <td>
                        <span className="ph-badge ph-badge-info">
                          <i className="bi bi-shield-check"></i>
                          {act.action_type.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {act.performed_by_details?.full_name || 'Staff Member'}
                      </td>
                      <td style={{ fontSize: '0.82rem', color: 'var(--ph-text-secondary)' }}>
                        {act.reason ? (
                          <em>{act.reason}</em>
                        ) : (
                          <span style={{ color: 'var(--ph-text-muted)' }}>&mdash; Standard action &mdash;</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="ph-card">
          {notificationLogs.length === 0 ? (
            <div className="ph-empty">
              <div className="ph-empty-icon" style={{ background: 'var(--ph-bg)', color: 'var(--ph-text-muted)' }}>
                <i className="bi bi-bell"></i>
              </div>
              <h5>No notification logs recorded yet.</h5>
              <p>Notification delivery records will appear here.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="ph-table">
                <thead>
                  <tr>
                    <th>Sent Timestamp</th>
                    <th>Channel</th>
                    <th>Recipient</th>
                    <th>Delivery Status</th>
                  </tr>
                </thead>
                <tbody>
                  {notificationLogs.map((log) => (
                    <tr key={log.id}>
                      <td>
                        <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--ph-text-muted)' }}>
                          {new Date(log.sent_at).toLocaleString()}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <i className={`bi ${
                            log.channel === 'email' ? 'bi-envelope' :
                            log.channel === 'whatsapp' ? 'bi-whatsapp' : 'bi-chat-dots'
                          }`} style={{
                            color: log.channel === 'email' ? 'var(--ph-gold-dark)' :
                                   log.channel === 'whatsapp' ? 'var(--ph-success)' : 'var(--ph-accent)',
                          }}></i>
                          {log.channel.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>
                        {log.recipient}
                      </td>
                      <td>
                        <span className="ph-badge ph-badge-success">
                          {log.status.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AuditLog;
