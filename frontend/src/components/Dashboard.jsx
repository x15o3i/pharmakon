import React, { useState, useEffect } from 'react';
import api from '../services/api';
import ActionModal from './ActionModal';

const Dashboard = () => {
  const [summary, setSummary] = useState({
    red_count: 0,
    amber_count: 0,
    green_count: 0,
    total_active_drugs: 0,
    urgent_alerts: [],
  });
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [triggeringCheck, setTriggeringCheck] = useState(false);
  const [sendingSummary, setSendingSummary] = useState(false);
  const [summaryToast, setSummaryToast] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const res = await api.get('/alerts/alerts/dashboard_summary/');
      setSummary(res.data);
    } catch (err) {
      console.error('Failed to load dashboard summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRunExpiryCheck = async () => {
    setTriggeringCheck(true);
    try {
      await api.post('/alerts/alerts/trigger_check/');
      await fetchDashboardData();
    } catch (err) {
      console.error('Trigger check failed:', err);
    } finally {
      setTriggeringCheck(false);
    }
  };

  const handleSendWhatsAppSummary = async () => {
    setSendingSummary(true);
    setSummaryToast(null);
    try {
      const res = await api.post('/alerts/alerts/send_whatsapp_summary/');
      setSummaryToast({ type: 'success', message: res.data.message || 'WhatsApp Expiry Summary Report sent successfully!' });
      await fetchDashboardData();
    } catch (err) {
      console.error('Send WhatsApp Summary failed:', err);
      setSummaryToast({ type: 'danger', message: 'Failed to send WhatsApp Expiry Summary Report.' });
    } finally {
      setSendingSummary(false);
    }
  };

  const filteredAlerts = summary.urgent_alerts.filter((alert) => {
    if (filterSeverity === 'RED') return alert.severity === 'red';
    if (filterSeverity === 'AMBER') return alert.severity === 'amber';
    return true;
  });

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h3>
            <i className="bi bi-shield-exclamation" style={{ color: 'var(--ph-danger)' }}></i>
            Stock Expiry Overview
          </h3>
          <p>Real-time monitoring &amp; closed-loop alert response</p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="btn-ph-outline"
          >
            <i className={`bi bi-arrow-clockwise ${loading ? 'spin' : ''}`}></i>
            Refresh
          </button>

          <button
            onClick={handleSendWhatsAppSummary}
            disabled={sendingSummary}
            className="btn-ph-outline"
            style={{ backgroundColor: '#25D366', color: '#ffffff', borderColor: '#25D366', fontWeight: 600 }}
          >
            {sendingSummary ? (
              <><span className="ph-spinner" style={{ borderColor: '#fff transparent #fff #fff' }}></span> Dispatching Report...</>
            ) : (
              <><i className="bi bi-whatsapp"></i> Send WhatsApp Summary</>
            )}
          </button>

          <button
            onClick={handleRunExpiryCheck}
            disabled={triggeringCheck}
            className="btn-ph-primary"
          >
            {triggeringCheck ? (
              <><span className="ph-spinner"></span> Scanning...</>
            ) : (
              <><i className="bi bi-arrow-repeat"></i> Run Expiry Scan</>
            )}
          </button>
        </div>
      </div>

      {/* Toast Notification Banner */}
      {summaryToast && (
        <div
          className={`ph-alert ${summaryToast.type === 'success' ? 'ph-alert-success' : 'ph-alert-danger'}`}
          style={{ marginBottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <span>
            <i className={`bi ${summaryToast.type === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'}`} style={{ marginRight: 8 }}></i>
            {summaryToast.message}
          </span>
          <button
            onClick={() => setSummaryToast(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 'bold' }}
          >
            &times;
          </button>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid-3" style={{ marginBottom: 24 }}>
        {/* Red */}
        <div
          onClick={() => setFilterSeverity('RED')}
          className={`stat-card stat-danger ${filterSeverity === 'RED' ? 'active' : ''}`}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-card-label" style={{ color: 'var(--ph-danger)' }}>
                Urgent Expiry (&lt; 7 Days)
              </div>
              <div className="stat-card-value" style={{ color: 'var(--ph-text)' }}>{summary.red_count}</div>
            </div>
            <div className="stat-card-icon" style={{ background: 'var(--ph-danger-bg)', color: 'var(--ph-danger)' }}>
              <i className="bi bi-exclamation-circle"></i>
            </div>
          </div>
          <div className="stat-card-desc">
            <i className="bi bi-info-circle" style={{ marginRight: 4 }}></i>
            Immediate action required (Disposal / Removal)
          </div>
        </div>

        {/* Amber */}
        <div
          onClick={() => setFilterSeverity('AMBER')}
          className={`stat-card stat-warning ${filterSeverity === 'AMBER' ? 'active' : ''}`}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-card-label" style={{ color: 'var(--ph-warning)' }}>
                Expiring Soon (Lead Time)
              </div>
              <div className="stat-card-value" style={{ color: 'var(--ph-text)' }}>{summary.amber_count}</div>
            </div>
            <div className="stat-card-icon" style={{ background: 'var(--ph-warning-bg)', color: 'var(--ph-warning)' }}>
              <i className="bi bi-clock-history"></i>
            </div>
          </div>
          <div className="stat-card-desc">
            <i className="bi bi-info-circle" style={{ marginRight: 4 }}></i>
            Warning window active (Discount / Return)
          </div>
        </div>

        {/* Green */}
        <div
          onClick={() => setFilterSeverity('ALL')}
          className={`stat-card stat-success ${filterSeverity === 'ALL' ? 'active' : ''}`}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-card-label" style={{ color: 'var(--ph-success)' }}>
                Safe Stock
              </div>
              <div className="stat-card-value" style={{ color: 'var(--ph-text)' }}>{summary.green_count}</div>
            </div>
            <div className="stat-card-icon" style={{ background: 'var(--ph-success-bg)', color: 'var(--ph-success)' }}>
              <i className="bi bi-check-circle"></i>
            </div>
          </div>
          <div className="stat-card-desc">
            <i className="bi bi-boxes" style={{ marginRight: 4 }}></i>
            Total active drugs in system: {summary.total_active_drugs}
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="ph-card">
        <div style={{
          padding: '16px 24px', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
          borderBottom: '1px solid var(--ph-border)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ph-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Filter:
            </span>
            <div className="ph-filter-tabs">
              <button
                className={`ph-filter-tab ${filterSeverity === 'ALL' ? 'active' : ''}`}
                onClick={() => setFilterSeverity('ALL')}
              >
                All Alerts
              </button>
              <button
                className={`ph-filter-tab ${filterSeverity === 'RED' ? 'active-danger' : ''}`}
                onClick={() => setFilterSeverity('RED')}
              >
                Red Only
              </button>
              <button
                className={`ph-filter-tab ${filterSeverity === 'AMBER' ? 'active-warning' : ''}`}
                onClick={() => setFilterSeverity('AMBER')}
              >
                Amber Only
              </button>
            </div>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--ph-text-muted)' }}>
            Showing {filteredAlerts.length} items
          </span>
        </div>

        {loading ? (
          <div className="ph-loading">
            <div className="ph-spinner ph-spinner-dark" style={{ width: 28, height: 28, margin: '0 auto 12px' }}></div>
            Loading live alert data...
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="ph-empty">
            <div className="ph-empty-icon">
              <i className="bi bi-check-circle"></i>
            </div>
            <h5>No active alerts found!</h5>
            <p>All pharmaceutical stock is within safe expiration parameters.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="ph-table">
              <thead>
                <tr>
                  <th>Urgency</th>
                  <th>Drug &amp; Batch</th>
                  <th>Expiry Date</th>
                  <th>Quantity</th>
                  <th>Escalation Status</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((alert) => {
                  const drug = alert.drug_details;
                  const isRed = alert.severity === 'red';

                  return (
                    <tr key={alert.id}>
                      <td>
                        <span className={`ph-badge ${isRed ? 'ph-badge-danger' : 'ph-badge-warning'}`}>
                          <i className={`bi ${isRed ? 'bi-exclamation-triangle-fill' : 'bi-clock-fill'}`}></i>
                          {isRed ? 'Urgent (<7 Days)' : 'Expiring Soon'}
                        </span>
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--ph-text)' }}>{drug?.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--ph-text-muted)' }}>
                          Batch: <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--ph-text)' }}>{drug?.batch_number}</span>
                          {' '}&middot;{' '}Barcode: {drug?.barcode}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{drug?.expiry_date}</span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 700 }}>{drug?.quantity}</span> units
                      </td>
                      <td>
                        {alert.escalated_to_details ? (
                          <span className="ph-badge ph-badge-info">
                            Escalated to {alert.escalated_to_details.full_name}
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: 'var(--ph-text-muted)' }}>
                            Standard Level {alert.escalation_level}
                          </span>
                        )}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          onClick={() => setSelectedAlert(alert)}
                          className="btn-ph-primary"
                          style={{ fontSize: '0.8rem', minHeight: 36, padding: '8px 16px' }}
                        >
                          Resolve Alert
                          <i className="bi bi-arrow-right"></i>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedAlert && (
        <ActionModal
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onActionSuccess={() => {
            setSelectedAlert(null);
            fetchDashboardData();
          }}
        />
      )}
    </div>
  );
};

export default Dashboard;
