import React, { useState } from 'react';
import api from '../services/api';

const ACTION_OPTIONS = [
  { value: 'removed_from_shelf', label: 'Removed from Shelf', icon: 'bi-x-square', desc: 'Item pulled from display shelves.' },
  { value: 'discounted', label: 'Discounted', icon: 'bi-tag', desc: 'Marked down for clearance sales.' },
  { value: 'returned_to_supplier', label: 'Returned to Supplier', icon: 'bi-arrow-return-left', desc: 'Shipped back under manufacturer return terms.' },
  { value: 'disposed', label: 'Disposed', icon: 'bi-trash3', desc: 'Safely destroyed per bio-hazard protocols.' },
  { value: 'no_action_needed', label: 'No Action Needed', icon: 'bi-check-lg', desc: 'Stock retained (requires written reason below).' },
];

const ActionModal = ({ alert, onClose, onActionSuccess }) => {
  const [actionType, setActionType] = useState('removed_from_shelf');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const drug = alert.drug_details;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (actionType === 'no_action_needed' && !reason.trim()) {
      setError('A mandatory explanation is required when selecting "No Action Needed".');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/alerts/actions/', {
        alert: alert.id,
        action_type: actionType,
        reason: reason.trim(),
      });
      onActionSuccess();
    } catch (err) {
      const errData = err.response?.data;
      if (errData?.reason) {
        setError(Array.isArray(errData.reason) ? errData.reason[0] : errData.reason);
      } else {
        setError(errData?.detail || 'Failed to submit action.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="ph-modal-backdrop" onClick={onClose}>
      <div className="ph-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ph-modal-header">
          <h5>
            <i className="bi bi-shield-check" style={{ color: 'var(--ph-gold-dark)' }}></i>
            Record Expiry Action
          </h5>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', color: 'var(--ph-text-muted)',
              fontSize: '1.1rem', cursor: 'pointer', width: 36, height: 36,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              borderRadius: 8,
            }}
          >
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        <div className="ph-modal-body">
          {/* Drug Context */}
          <div style={{
            padding: '14px 16px', borderRadius: 'var(--ph-radius)',
            background: 'var(--ph-bg)', border: '1px solid var(--ph-border)',
            marginBottom: 20,
          }}>
            <div style={{
              fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em',
              fontWeight: 600, color: 'var(--ph-text-muted)', marginBottom: 4,
            }}>
              Target Product
            </div>
            <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--ph-text)', marginBottom: 6 }}>
              {drug?.name}
            </div>
            <div style={{ display: 'flex', gap: 16, fontSize: '0.8rem', flexWrap: 'wrap' }}>
              <span>Batch: <strong style={{ fontFamily: 'monospace' }}>{drug?.batch_number}</strong></span>
              <span>Expires: <strong style={{ color: 'var(--ph-danger)', fontFamily: 'monospace' }}>{drug?.expiry_date}</strong></span>
              <span>Qty: <strong>{drug?.quantity}</strong></span>
            </div>
          </div>

          {error && (
            <div className="ph-alert ph-alert-danger" style={{ marginBottom: 16 }}>
              <i className="bi bi-exclamation-triangle-fill"></i>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 18 }}>
              <label className="ph-label" style={{ marginBottom: 10 }}>Select Action Taken</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {ACTION_OPTIONS.map((opt) => (
                  <label
                    key={opt.value}
                    className={`ph-radio-card ${actionType === opt.value ? 'selected' : ''}`}
                  >
                    <input
                      type="radio"
                      name="actionType"
                      value={opt.value}
                      checked={actionType === opt.value}
                      onChange={(e) => setActionType(e.target.value)}
                    />
                    <div>
                      <div className="ph-radio-card-title">
                        <i className={`bi ${opt.icon}`} style={{ marginRight: 6, opacity: 0.6 }}></i>
                        {opt.label}
                      </div>
                      <div className="ph-radio-card-desc">{opt.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <label className="ph-label" style={{ margin: 0 }}>Reason / Audit Notes</label>
                {actionType === 'no_action_needed' && (
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--ph-danger)' }}>* Mandatory</span>
                )}
              </div>
              <textarea
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder={
                  actionType === 'no_action_needed'
                    ? 'Required: Explain why no action is taken...'
                    : 'Optional notes for compliance audit trail...'
                }
                className="ph-textarea"
              />
            </div>

            <div style={{
              display: 'flex', justifyContent: 'flex-end', gap: 10,
              paddingTop: 16, borderTop: '1px solid var(--ph-border)',
            }}>
              <button type="button" onClick={onClose} className="btn-ph-outline">
                Cancel
              </button>
              <button type="submit" disabled={submitting} className="btn-ph-primary">
                {submitting ? (
                  <><span className="ph-spinner"></span> Submitting...</>
                ) : (
                  <>Confirm Action</>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ActionModal;
