import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';

const CameraScanner = ({ onScanSuccess, onClose }) => {
  const [status, setStatus] = useState('initializing');
  const [errorMsg, setErrorMsg] = useState('');
  const [cameras, setCameras] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState('');

  const html5QrCodeRef = useRef(null);
  const isStoppingRef = useRef(false);

  useEffect(() => {
    let isMounted = true;

    const startScanner = async () => {
      try {
        setStatus('initializing');
        setErrorMsg('');

        const qrInstance = new Html5Qrcode('reader');
        html5QrCodeRef.current = qrInstance;

        const config = {
          fps: 10,
          qrbox: { width: 280, height: 150 },
          formatsToSupport: [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.DATA_MATRIX,
          ],
        };

        await qrInstance.start(
          { facingMode: 'environment' },
          config,
          (decodedText) => {
            if (isMounted && !isStoppingRef.current) {
              if (navigator.vibrate) navigator.vibrate(100);
              handleCloseAndSuccess(decodedText);
            }
          },
          () => {}
        );

        if (isMounted) setStatus('scanning');

        try {
          const devices = await Html5Qrcode.getCameras();
          if (isMounted && devices && devices.length > 1) setCameras(devices);
        } catch (e) {
          // Ignore camera enumeration failure
        }
      } catch (err) {
        if (!isMounted) return;
        console.error('Camera startup error:', err);
        setStatus('error');
        const errStr = err?.toString() || '';
        if (errStr.includes('NotAllowedError') || errStr.includes('Permission') || errStr.includes('denied')) {
          setErrorMsg('Camera permission was denied. Please allow camera access in your browser settings.');
        } else if (errStr.includes('NotFoundError') || errStr.includes('DevicesNotFoundError')) {
          setErrorMsg('No camera detected on your device.');
        } else {
          setErrorMsg('Unable to access camera. Please ensure no other tab or app is using the camera.');
        }
      }
    };

    const timer = setTimeout(() => startScanner(), 100);

    return () => {
      isMounted = false;
      clearTimeout(timer);
      stopScannerInstance();
    };
  }, []);

  const stopScannerInstance = async () => {
    if (html5QrCodeRef.current && !isStoppingRef.current) {
      isStoppingRef.current = true;
      try {
        if (html5QrCodeRef.current.isScanning) {
          await html5QrCodeRef.current.stop();
        }
        html5QrCodeRef.current.clear();
      } catch (err) {
        console.error('Error stopping scanner:', err);
      }
    }
  };

  const handleCloseAndSuccess = async (scannedCode) => {
    await stopScannerInstance();
    onScanSuccess(scannedCode);
  };

  const handleManualClose = async () => {
    await stopScannerInstance();
    onClose();
  };

  const handleCameraChange = async (e) => {
    const newCameraId = e.target.value;
    setSelectedCameraId(newCameraId);

    if (html5QrCodeRef.current) {
      try {
        if (html5QrCodeRef.current.isScanning) {
          await html5QrCodeRef.current.stop();
        }

        const config = {
          fps: 10,
          qrbox: { width: 280, height: 150 },
          formatsToSupport: [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.QR_CODE,
          ],
        };

        await html5QrCodeRef.current.start(
          newCameraId,
          config,
          (decodedText) => {
            if (!isStoppingRef.current) {
              if (navigator.vibrate) navigator.vibrate(100);
              handleCloseAndSuccess(decodedText);
            }
          },
          () => {}
        );
      } catch (err) {
        console.error('Camera switch error:', err);
      }
    }
  };

  return (
    <div style={{
      background: 'var(--ph-surface)',
      border: '1px solid var(--ph-border)',
      borderRadius: 'var(--ph-radius-lg)',
      overflow: 'hidden',
      marginBottom: 20,
      boxShadow: 'var(--ph-shadow-md)',
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 20px',
        background: 'var(--ph-navy)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <i className="bi bi-camera-video-fill" style={{ color: 'var(--ph-gold)' }}></i>
          <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#fff' }}>Live Barcode &amp; QR Scanner</span>
        </div>
        <button
          onClick={handleManualClose}
          style={{
            background: 'none', border: 'none',
            color: 'rgba(255,255,255,0.6)', fontSize: '1rem',
            cursor: 'pointer', width: 36, height: 36,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            borderRadius: 8,
          }}
          aria-label="Close scanner"
        >
          <i className="bi bi-x-lg"></i>
        </button>
      </div>

      {/* Body */}
      <div style={{
        padding: 16,
        background: '#000',
        textAlign: 'center',
        position: 'relative',
        minHeight: 280,
      }}>
        {status === 'initializing' && (
          <div style={{
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            padding: '60px 20px', gap: 12,
          }}>
            <div className="ph-spinner" style={{ width: 32, height: 32 }}></div>
            <small style={{ color: 'rgba(255,255,255,0.5)' }}>Accessing device camera...</small>
          </div>
        )}

        {status === 'error' && (
          <div style={{ padding: 20 }}>
            <div className="ph-alert ph-alert-danger">
              <i className="bi bi-exclamation-triangle-fill"></i>
              <span>{errorMsg}</span>
            </div>
          </div>
        )}

        <div
          id="reader"
          style={{
            width: '100%',
            maxWidth: 480,
            margin: '0 auto',
            borderRadius: 'var(--ph-radius)',
            overflow: 'hidden',
            display: status === 'error' ? 'none' : 'block',
          }}
        />

        {status === 'scanning' && (
          <p style={{
            color: 'rgba(255,255,255,0.4)',
            fontSize: '0.72rem',
            marginTop: 12,
            marginBottom: 0,
          }}>
            <i className="bi bi-info-circle" style={{ marginRight: 4 }}></i>
            Center the barcode or QR code inside the box.
          </p>
        )}

        {cameras.length > 1 && status === 'scanning' && (
          <div style={{ marginTop: 12, maxWidth: 300, margin: '12px auto 0' }}>
            <select
              value={selectedCameraId}
              onChange={handleCameraChange}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 8,
                background: '#1a1f36', color: '#fff', border: '1px solid #252b42',
                fontSize: '0.85rem', minHeight: 44,
              }}
            >
              {cameras.map((cam, idx) => (
                <option key={cam.id} value={cam.id}>
                  Camera {idx + 1}: {cam.label || 'Unknown'}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraScanner;
