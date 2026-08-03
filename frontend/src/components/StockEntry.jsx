import React, { useState, useEffect } from 'react';
import api from '../services/api';
import CameraScanner from './CameraScanner';
import InventoryList from './InventoryList';
import { Html5Qrcode } from 'html5-qrcode';

const StockEntry = () => {
  const [activeSubTab, setActiveSubTab] = useState('inventory'); // 'inventory' | 'intake'
  const [categories, setCategories] = useState([]);
  const [cameraActive, setCameraActive] = useState(false);
  const [searchBarcode, setSearchBarcode] = useState('');
  const [message, setMessage] = useState({ type: '', text: '' });
  const [submitting, setSubmitting] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);

  const fileInputRef = React.useRef(null);

  const [formData, setFormData] = useState({
    name: '',
    generic_name: '',
    batch_number: '',
    manufacture_date: '',
    expiry_date: '',
    quantity: 10,
    unit_cost: 1000.0,
    criticality: 'essential',
    category: '',
    barcode: '',
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await api.get('/inventory/categories/');
      setCategories(res.data);
      if (res.data.length > 0) {
        setFormData((prev) => ({ ...prev, category: res.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleBarcodeScanned = async (scannedCode) => {
    setFormData((prev) => ({ ...prev, barcode: scannedCode }));
    setActiveSubTab('intake');
    setMessage({ type: 'info', text: `Scanned Barcode: ${scannedCode}. Searching inventory...` });

    try {
      const res = await api.get(`/inventory/drugs/barcode/${scannedCode}/`);
      const existing = res.data;
      setFormData({
        name: existing.name,
        generic_name: existing.generic_name,
        batch_number: existing.batch_number,
        manufacture_date: existing.manufacture_date || '',
        expiry_date: existing.expiry_date,
        quantity: existing.quantity,
        unit_cost: existing.unit_cost,
        criticality: existing.criticality,
        category: existing.category,
        barcode: existing.barcode,
      });
      setMessage({ type: 'success', text: `Found existing drug record for batch ${existing.batch_number}. Form populated.` });
    } catch (err) {
      setMessage({ type: 'info', text: `Barcode ${scannedCode} ready for new product entry.` });
    }
  };

  const handleImageFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingImage(true);
    setMessage({ type: 'info', text: 'Processing barcode photo...' });

    try {
      const html5QrCode = new Html5Qrcode('file-scanner-temp');
      const scannedCode = await html5QrCode.scanFile(file, true);
      html5QrCode.clear();

      if (navigator.vibrate) navigator.vibrate(100);
      handleBarcodeScanned(scannedCode);
    } catch (err) {
      console.error('Image scan error:', err);
      setMessage({
        type: 'error',
        text: 'Unable to decode a barcode from this image. Please ensure the photo is clear and well-lit.',
      });
    } finally {
      setUploadingImage(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleLookup = () => {
    if (searchBarcode.trim()) {
      handleBarcodeScanned(searchBarcode.trim());
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });
    setSubmitting(true);

    try {
      await api.post('/inventory/drugs/', formData);
      setMessage({ type: 'success', text: `Successfully saved ${formData.name} to inventory!` });
      setFormData({
        name: '', generic_name: '', batch_number: '', manufacture_date: '',
        expiry_date: '', quantity: 10, unit_cost: 1000.0, criticality: 'essential',
        category: categories[0]?.id || '', barcode: '',
      });
      setActiveSubTab('inventory');
    } catch (err) {
      const errData = err.response?.data;
      const errorMsg = errData ? JSON.stringify(errData) : 'Failed to save drug entry.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setSubmitting(false);
    }
  };

  const alertClass = message.type === 'success' ? 'ph-alert-success'
    : message.type === 'error' ? 'ph-alert-danger'
    : 'ph-alert-info';

  return (
    <div className="w-100">
      <div id="file-scanner-temp" className="d-none" />
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*"
        onChange={handleImageFileUpload}
        className="d-none"
      />

      {/* Page Header */}
      <div className="page-header">
        <div>
          <h3>
            <i className="bi bi-box-seam-fill" style={{ color: 'var(--ph-primary)' }}></i>
            Pharmacy Inventory &amp; Stock Intake
          </h3>
          <p>View full drug inventory, scan barcode labels, or add new stock records</p>
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="ph-filter-tabs" style={{ marginBottom: 0 }}>
            <button
              onClick={() => setActiveSubTab('inventory')}
              className={`ph-filter-tab ${activeSubTab === 'inventory' ? 'active' : ''}`}
            >
              <i className="bi bi-boxes me-1.5"></i>
              Stock Inventory List
            </button>
            <button
              onClick={() => setActiveSubTab('intake')}
              className={`ph-filter-tab ${activeSubTab === 'intake' ? 'active' : ''}`}
            >
              <i className="bi bi-plus-circle me-1.5"></i>
              New Stock Intake
            </button>
          </div>

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingImage}
            className="btn-ph-outline"
          >
            <i className="bi bi-image"></i>
            {uploadingImage ? 'Decoding...' : 'Upload Photo'}
          </button>
          <button
            onClick={() => setCameraActive(!cameraActive)}
            className={cameraActive ? 'btn-ph-danger' : 'btn-ph-primary'}
          >
            <i className="bi bi-camera-fill"></i>
            {cameraActive ? 'Close Scanner' : 'Launch Scanner'}
          </button>
        </div>
      </div>

      {/* Camera Modal / Stream */}
      {cameraActive && (
        <CameraScanner
          onScanSuccess={(code) => {
            setCameraActive(false);
            handleBarcodeScanned(code);
          }}
          onClose={() => setCameraActive(false)}
        />
      )}

      {/* Render selected view */}
      {activeSubTab === 'inventory' ? (
        <InventoryList />
      ) : (
        <>
          {/* Barcode Search Bar */}
          <div className="ph-card" style={{ marginBottom: 24 }}>
            <div className="ph-card-body">
              <div className="ph-input-group">
                <div className="ph-input-group-icon">
                  <i className="bi bi-search"></i>
                </div>
                <input
                  type="text"
                  value={searchBarcode}
                  onChange={(e) => setSearchBarcode(e.target.value)}
                  placeholder="Manual lookup by Barcode / QR Code..."
                  className="ph-input"
                />
                <button onClick={handleLookup} className="ph-input-group-btn">
                  Lookup Barcode
                </button>
              </div>
            </div>
          </div>

          {/* Messages */}
          {message.text && (
            <div className={`ph-alert ${alertClass}`} style={{ marginBottom: 24 }}>
              <i className="bi bi-info-circle-fill"></i>
              <span>{message.text}</span>
            </div>
          )}

          {/* Form Card */}
          <div className="ph-card">
            <div className="ph-card-header" style={{ paddingBottom: 0 }}>
              <h5 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                <i className="bi bi-card-checklist" style={{ color: 'var(--ph-primary)' }}></i>
                Product Details &amp; Intake Information
              </h5>
            </div>

            <div className="ph-card-body" style={{ padding: '28px 32px' }}>
              <form onSubmit={handleSubmit}>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                  gap: 24,
                }}>
                  <div>
                    <label className="ph-label">Product Trade Name *</label>
                    <input
                      type="text" name="name" required
                      value={formData.name} onChange={handleChange}
                      placeholder="e.g. Amoxicillin 500mg"
                      className="ph-input"
                    />
                  </div>
                  <div>
                    <label className="ph-label">Generic Name</label>
                    <input
                      type="text" name="generic_name"
                      value={formData.generic_name} onChange={handleChange}
                      placeholder="e.g. Amoxicillin Trihydrate"
                      className="ph-input"
                    />
                  </div>
                  <div>
                    <label className="ph-label">Batch / Lot Number *</label>
                    <input
                      type="text" name="batch_number" required
                      value={formData.batch_number} onChange={handleChange}
                      placeholder="e.g. BATCH-2026-X99"
                      className="ph-input" style={{ fontFamily: 'monospace' }}
                    />
                  </div>
                  <div>
                    <label className="ph-label">Barcode / QR Code Number *</label>
                    <input
                      type="text" name="barcode" required
                      value={formData.barcode} onChange={handleChange}
                      placeholder="e.g. 8901234567890"
                      className="ph-input" style={{ fontFamily: 'monospace' }}
                    />
                  </div>
                  <div>
                    <label className="ph-label">Manufacture Date</label>
                    <input
                      type="date" name="manufacture_date"
                      value={formData.manufacture_date} onChange={handleChange}
                      className="ph-input"
                    />
                  </div>
                  <div>
                    <label className="ph-label">Expiry Date *</label>
                    <input
                      type="date" name="expiry_date" required
                      value={formData.expiry_date} onChange={handleChange}
                      className="ph-input"
                    />
                  </div>
                  <div>
                    <label className="ph-label">Quantity Units *</label>
                    <input
                      type="number" name="quantity" required min="0"
                      value={formData.quantity} onChange={handleChange}
                      className="ph-input"
                    />
                  </div>
                  <div>
                    <label className="ph-label">Unit Cost (₦) *</label>
                    <input
                      type="number" step="0.01" name="unit_cost" required min="0"
                      value={formData.unit_cost} onChange={handleChange}
                      className="ph-input"
                    />
                  </div>
                  <div>
                    <label className="ph-label">Criticality Tag *</label>
                    <select
                      name="criticality" value={formData.criticality} onChange={handleChange}
                      className="ph-select"
                    >
                      <option value="vital">Vital (Life Saving / Zero Stockout Tolerance)</option>
                      <option value="essential">Essential (Standard Medical Need)</option>
                      <option value="desirable">Desirable (Over-The-Counter / Substitute Available)</option>
                    </select>
                  </div>
                  <div>
                    <label className="ph-label">Assigned Category &amp; Alert Window *</label>
                    <select
                      name="category" value={formData.category} onChange={handleChange}
                      className="ph-select"
                    >
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name} ({cat.alert_lead_time_days} Days Lead Time)
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div style={{
                  marginTop: 32, paddingTop: 20,
                  borderTop: '1px solid var(--ph-border)',
                  display: 'flex', justifyContent: 'flex-end',
                }}>
                  <button type="submit" disabled={submitting} className="btn-ph-primary stock-submit-btn" style={{ padding: '12px 36px', fontSize: '0.95rem' }}>
                    {submitting ? (
                      <><span className="ph-spinner"></span> Saving...</>
                    ) : (
                      <><i className="bi bi-check-lg"></i> Save Stock Record</>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StockEntry;
