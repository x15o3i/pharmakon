import React, { useState, useEffect } from 'react';
import api from '../services/api';

const AdminCategories = () => {
  const [categories, setCategories] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingCategory, setEditingCategory] = useState(null);
  const [formData, setFormData] = useState({ name: '', alert_lead_time_days: 30, description: '' });
  const [reclassifying, setReclassifying] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [catRes, userRes] = await Promise.all([
        api.get('/inventory/categories/'),
        api.get('/accounts/users/'),
      ]);
      setCategories(catRes.data);
      setUsers(userRes.data);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCategory = async (e) => {
    e.preventDefault();
    try {
      if (editingCategory) {
        await api.put(`/inventory/categories/${editingCategory.id}/`, formData);
        setMessage('Category lead-time updated successfully!');
      } else {
        await api.post('/inventory/categories/', formData);
        setMessage('New category created successfully!');
      }
      setEditingCategory(null);
      setFormData({ name: '', alert_lead_time_days: 30, description: '' });
      fetchData();
    } catch (err) {
      console.error('Category save error:', err);
    }
  };

  const handleEdit = (cat) => {
    setEditingCategory(cat);
    setFormData({
      name: cat.name,
      alert_lead_time_days: cat.alert_lead_time_days,
      description: cat.description,
    });
  };

  const handleRunReclassification = async () => {
    setReclassifying(true);
    try {
      const res = await api.post('/inventory/drugs/reclassify/');
      setMessage(`ABC/VED Reclassification executed! Processed ${res.data.details.processed} drugs.`);
      fetchData();
    } catch (err) {
      console.error('Reclassification error:', err);
    } finally {
      setReclassifying(false);
    }
  };

  return (
    <div className="w-100">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h3>
              <i className="bi bi-sliders" style={{ color: 'var(--ph-gold-dark)' }}></i>
            Admin Category &amp; Threshold Rules
          </h3>
          <p>Configure alert lead times per category and trigger ABC/VED classification</p>
        </div>
        <button
          onClick={handleRunReclassification}
          disabled={reclassifying}
          className="btn-ph-primary"
          style={{ background: 'var(--ph-gold-dark)' }}
        >
          {reclassifying ? (
            <><span className="ph-spinner"></span> Running Classifier...</>
          ) : (
            <><i className="bi bi-cpu"></i> Run ABC/VED Classification</>
          )}
        </button>
      </div>

      {message && (
        <div className="ph-alert ph-alert-success" style={{ marginBottom: 20 }}>
          <i className="bi bi-check-circle-fill"></i>
          <span>{message}</span>
        </div>
      )}

      {loading ? (
        <div className="ph-card">
          <div className="ph-loading">
            <div className="ph-spinner ph-spinner-dark" style={{ width: 28, height: 28, margin: '0 auto 12px' }}></div>
            Loading admin data...
          </div>
        </div>
      ) : (
        <>
          {/* Category Cards */}
          <div className="ph-card" style={{ marginBottom: 24 }}>
            <div className="ph-card-header" style={{ paddingBottom: 0 }}>
              <h5 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                <i className="bi bi-shield-lock" style={{ color: 'var(--ph-gold-dark)' }}></i>
                Category Alert Lead Times
              </h5>
            </div>
            <div className="ph-card-body">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20, marginBottom: 24 }}>
                {categories.map((cat) => (
                  <div
                    key={cat.id}
                    style={{
                      padding: '22px', borderRadius: 'var(--ph-radius)',
                      border: '1px solid var(--ph-border)',
                      background: 'var(--ph-surface)',
                      transition: 'box-shadow 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                      <span style={{ fontWeight: 700, color: 'var(--ph-text)' }}>{cat.name}</span>
                      <button
                        onClick={() => handleEdit(cat)}
                        style={{
                          background: 'none', border: '1px solid var(--ph-border)',
                          borderRadius: 8, width: 36, height: 36,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          cursor: 'pointer', color: 'var(--ph-text-muted)', fontSize: '0.85rem',
                        }}
                        title="Edit threshold"
                      >
                        <i className="bi bi-pencil"></i>
                      </button>
                    </div>
                    <div style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--ph-gold-dark)', lineHeight: 1, marginBottom: 6 }}>
                      {cat.alert_lead_time_days}
                      <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--ph-text-muted)', marginLeft: 6 }}>
                        Days Lead Time
                      </span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--ph-text-muted)', margin: 0 }}>
                      {cat.description || 'No description provided.'}
                    </p>
                  </div>
                ))}
              </div>

              {/* Category Form */}
              <div style={{
                padding: '24px 28px', borderRadius: 'var(--ph-radius)',
                background: 'var(--ph-bg)', border: '1px solid var(--ph-border)',
              }}>
                <h6 style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: 16 }}>
                  {editingCategory ? `Edit Lead Time: ${editingCategory.name}` : 'Add New Category'}
                </h6>
                <form onSubmit={handleSaveCategory}>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                    gap: 16,
                  }}>
                    <div>
                      <label className="ph-label">Category Name</label>
                      <input
                        type="text" required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="e.g. Critical/High-Value"
                        className="ph-input"
                      />
                    </div>
                    <div>
                      <label className="ph-label">Alert Lead Time (Days)</label>
                      <input
                        type="number" required min="1"
                        value={formData.alert_lead_time_days}
                        onChange={(e) => setFormData({ ...formData, alert_lead_time_days: parseInt(e.target.value, 10) })}
                        className="ph-input"
                      />
                    </div>
                    <div>
                      <label className="ph-label">Description</label>
                      <input
                        type="text"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="Short description..."
                        className="ph-input"
                      />
                    </div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 18 }}>
                    {editingCategory && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingCategory(null);
                          setFormData({ name: '', alert_lead_time_days: 30, description: '' });
                        }}
                        className="btn-ph-outline"
                      >
                        Cancel
                      </button>
                    )}
                    <button type="submit" className="btn-ph-primary">
                      {editingCategory ? 'Update Threshold' : 'Save Category'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>

          {/* User Management Table */}
          <div className="ph-card">
            <div className="ph-card-header" style={{ paddingBottom: 0 }}>
              <h5 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                <i className="bi bi-people" style={{ color: 'var(--ph-accent)' }}></i>
                Registered Staff Accounts &amp; Roles
              </h5>
            </div>
            <div style={{ paddingTop: 12 }}>
              <div className="table-responsive">
                <table className="ph-table">
                  <thead>
                    <tr>
                      <th>Full Name</th>
                      <th>Email Address</th>
                      <th>Phone</th>
                      <th>System Role</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id}>
                        <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: 'var(--ph-text-secondary)' }}>
                          {u.email}
                        </td>
                        <td style={{ color: 'var(--ph-text-secondary)' }}>{u.phone || '\u2014'}</td>
                        <td>
                          <span className="ph-badge ph-badge-neutral" style={{ textTransform: 'capitalize' }}>
                            {u.role}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminCategories;
