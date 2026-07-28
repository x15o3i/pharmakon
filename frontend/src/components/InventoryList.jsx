import React, { useState, useEffect } from 'react';
import api from '../services/api';

const InventoryList = ({ onSelectEdit }) => {
  const [drugs, setDrugs] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedTier, setSelectedTier] = useState('');
  const [selectedCriticality, setSelectedCriticality] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const [drugRes, catRes] = await Promise.all([
        api.get('/inventory/drugs/'),
        api.get('/inventory/categories/'),
      ]);
      setDrugs(drugRes.data);
      setCategories(catRes.data);
    } catch (err) {
      console.error('Failed to fetch inventory directory:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDrug = async (id, name) => {
    if (!window.confirm(`Are you sure you want to remove "${name}" from inventory?`)) return;
    setDeletingId(id);
    try {
      await api.delete(`/inventory/drugs/${id}/`);
      setDrugs((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error('Failed to delete drug:', err);
      alert('Failed to delete stock item.');
    } finally {
      setDeletingId(null);
    }
  };

  const filteredDrugs = drugs.filter((drug) => {
    const search = searchTerm.toLowerCase().trim();
    const matchesSearch =
      !search ||
      drug.name.toLowerCase().includes(search) ||
      drug.generic_name.toLowerCase().includes(search) ||
      drug.batch_number.toLowerCase().includes(search) ||
      drug.barcode.toLowerCase().includes(search);

    const matchesCategory = !selectedCategory || String(drug.category) === String(selectedCategory);
    const matchesTier = !selectedTier || drug.abc_tier === selectedTier;
    const matchesCriticality = !selectedCriticality || drug.criticality === selectedCriticality;

    return matchesSearch && matchesCategory && matchesTier && matchesCriticality;
  });

  const totalValue = filteredDrugs.reduce((acc, curr) => acc + parseFloat(curr.total_value || 0), 0);
  const totalQuantity = filteredDrugs.reduce((acc, curr) => acc + parseInt(curr.quantity || 0, 10), 0);

  const getExpiryBadge = (expiryDateStr) => {
    const expiry = new Date(expiryDateStr);
    const today = new Date();
    const diffDays = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));

    if (diffDays <= 7) {
      return (
        <span className="ph-badge ph-badge-danger">
          <i className="bi bi-exclamation-triangle-fill"></i>
          {diffDays < 0 ? 'Expired' : `< ${diffDays} Days`}
        </span>
      );
    }
    if (diffDays <= 60) {
      return (
        <span className="ph-badge ph-badge-warning">
          <i className="bi bi-clock-fill"></i>
          Expiring Soon
        </span>
      );
    }
    return (
      <span className="ph-badge ph-badge-success">
        <i className="bi bi-check-circle-fill"></i>
        Safe Stock
      </span>
    );
  };

  return (
    <div className="w-100">
      {/* Overview Stat Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 16,
        marginBottom: 24,
      }}>
        <div className="ph-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span className="stat-card-title">Total Listed Stock Items</span>
              <div className="stat-card-value" style={{ marginTop: 4 }}>{filteredDrugs.length}</div>
            </div>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'var(--ph-primary-light)', color: 'var(--ph-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem'
            }}>
              <i className="bi bi-boxes"></i>
            </div>
          </div>
        </div>

        <div className="ph-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span className="stat-card-title">Total Units in Stock</span>
              <div className="stat-card-value" style={{ marginTop: 4 }}>{totalQuantity.toLocaleString()}</div>
            </div>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'rgba(14, 165, 233, 0.1)', color: 'var(--ph-info)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem'
            }}>
              <i className="bi bi-capsule"></i>
            </div>
          </div>
        </div>

        <div className="ph-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span className="stat-card-title">Total Financial Valuation</span>
              <div className="stat-card-value" style={{ marginTop: 4, color: 'var(--ph-primary)' }}>
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'rgba(16, 185, 129, 0.1)', color: 'var(--ph-success)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem'
            }}>
              <i className="bi bi-currency-dollar"></i>
            </div>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar Card */}
      <div className="ph-card" style={{ marginBottom: 24 }}>
        <div className="ph-card-body">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 12,
            alignItems: 'center',
          }}>
            <div className="ph-input-group" style={{ gridColumn: 'span 2' }}>
              <div className="ph-input-group-icon">
                <i className="bi bi-search"></i>
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search inventory by Drug Name, Generic, Batch #, or Barcode..."
                className="ph-input"
              />
            </div>

            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="ph-select"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>

            <select
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              className="ph-select"
            >
              <option value="">All Pareto ABC Tiers</option>
              <option value="A">Tier A (High Value 80%)</option>
              <option value="B">Tier B (Medium Value 15%)</option>
              <option value="C">Tier C (Low Value 5%)</option>
            </select>

            <select
              value={selectedCriticality}
              onChange={(e) => setSelectedCriticality(e.target.value)}
              className="ph-select"
            >
              <option value="">All Criticality Tags</option>
              <option value="vital">Vital (Life Saving)</option>
              <option value="essential">Essential (Standard)</option>
              <option value="desirable">Desirable (Substitute)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Inventory Table */}
      <div className="ph-card">
        <div className="ph-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h5 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
            <i className="bi bi-list-ul" style={{ color: 'var(--ph-primary)' }}></i>
            Pharmacy Inventory Directory ({filteredDrugs.length} Items)
          </h5>

          <button onClick={fetchInventory} className="btn-ph-outline" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
            <i className="bi bi-arrow-clockwise"></i> Refresh
          </button>
        </div>

        {loading ? (
          <div className="ph-loading" style={{ padding: 40 }}>
            <div className="ph-spinner ph-spinner-dark" style={{ width: 28, height: 28, margin: '0 auto 12px' }}></div>
            Loading pharmacy inventory list...
          </div>
        ) : filteredDrugs.length === 0 ? (
          <div className="ph-empty" style={{ padding: 48 }}>
            <div className="ph-empty-icon" style={{ background: 'var(--ph-bg)', color: 'var(--ph-text-muted)' }}>
              <i className="bi bi-inbox"></i>
            </div>
            <h5>No matching stock records found.</h5>
            <p>Try adjusting your search query or filters above.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="ph-table">
              <thead>
                <tr>
                  <th>Product Trade &amp; Generic Name</th>
                  <th>Batch &amp; Barcode</th>
                  <th>Expiry Status</th>
                  <th>Stock Units</th>
                  <th>Unit Cost ($)</th>
                  <th>Total Valuation ($)</th>
                  <th>ABC Tier</th>
                  <th>Criticality</th>
                  <th>Category</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDrugs.map((drug) => (
                  <tr key={drug.id}>
                    <td>
                      <div style={{ fontWeight: 700, color: 'var(--ph-text)' }}>{drug.name}</div>
                      {drug.generic_name && (
                        <div style={{ fontSize: '0.78rem', color: 'var(--ph-text-muted)' }}>{drug.generic_name}</div>
                      )}
                    </td>

                    <td>
                      <div style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.85rem' }}>{drug.batch_number}</div>
                      <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--ph-text-muted)' }}>
                        BC: {drug.barcode}
                      </div>
                    </td>

                    <td>
                      <div>{getExpiryBadge(drug.expiry_date)}</div>
                      <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--ph-text-muted)', marginTop: 2 }}>
                        {drug.expiry_date}
                      </div>
                    </td>

                    <td>
                      <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{drug.quantity}</span> units
                    </td>

                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                      ${parseFloat(drug.unit_cost).toFixed(2)}
                    </td>

                    <td style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--ph-primary)' }}>
                      ${parseFloat(drug.total_value).toFixed(2)}
                    </td>

                    <td>
                      <span className={`ph-badge ${
                        drug.abc_tier === 'A' ? 'ph-badge-danger' :
                        drug.abc_tier === 'B' ? 'ph-badge-warning' : 'ph-badge-neutral'
                      }`}>
                        Tier {drug.abc_tier}
                      </span>
                    </td>

                    <td>
                      <span className="ph-badge ph-badge-neutral" style={{ textTransform: 'capitalize' }}>
                        {drug.criticality}
                      </span>
                    </td>

                    <td>
                      <span style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--ph-text-secondary)' }}>
                        {drug.category_details?.name || 'Standard'}
                      </span>
                    </td>

                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={() => handleDeleteDrug(drug.id, drug.name)}
                        disabled={deletingId === drug.id}
                        className="btn-ph-danger"
                        style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                        title="Remove stock record"
                      >
                        <i className="bi bi-trash"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default InventoryList;
