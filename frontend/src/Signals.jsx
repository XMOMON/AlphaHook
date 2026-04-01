import React, { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CRYPTO_PAIRS = [
  "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "MATIC/USDT", "LINK/USDT",
  "DOT/USDT", "SHIB/USDT", "LTC/USDT", "UNI/USDT", "ATOM/USDT", "XLM/USDT", "VET/USDT", "FIL/USDT", "THETA/USDT", "XMR/USDT",
  "EOS/USDT", "AAVE/USDT", "XTZ/USDT", "MKR/USDT", "BSV/USDT", "BCH/USDT", "TRX/USDT", "NEO/USDT", "CAKE/USDT", "ALGO/USDT",
  "FTM/USDT", "KSM/USDT", "DASH/USDT", "RUNE/USDT", "FEA/USDT", "HNT/USDT", "ENJ/USDT", "MANA/USDT", "SAND/USDT", "APE/USDT",
  "GMT/USDT", "GALA/USDT", "ONE/USDT", "CHZ/USDT", "ANKR/USDT", "IOTA/USDT", "KAVA/USDT", "CRV/USDT", "SNX/USDT"
];

const FOREX_MAJORS = [
  "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "USD/CAD", "NZD/USD"
];

export default function Signals() {
  const [signals, setSignals] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [expandedNote, setExpandedNote] = useState(null);
  const [formData, setFormData] = useState({
    pair: 'BTC/USDT',
    direction: 'LONG',
    entry: '',
    tp1: '',
    tp2: '',
    sl: '',
    reason: '',
    confidence: 'BUY',
    source: 'Manual',
    notes: '',
    expires_at: ''
  });

  const fetchSignals = () => {
    fetch(`${API_URL}/api/v1/signals/`)
      .then(res => res.json())
      .then(data => setSignals(data))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCancel = async (id) => {
    try {
      await fetch(`${API_URL}/api/v1/signals/${id}`, { method: 'DELETE' });
      fetchSignals();
    } catch (err) {
      console.error('Error cancelling signal:', err);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['entry', 'tp1', 'tp2', 'sl'].includes(name) ? parseFloat(value) || value : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if (!payload.expires_at) delete payload.expires_at;
      const response = await fetch(`${API_URL}/api/v1/signals/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        setShowModal(false);
        fetchSignals();
      } else {
        console.error('Failed to create signal:', await response.text());
      }
    } catch (err) {
      console.error('Error submitting signal:', err);
    }
  };

  return (
    <>
      <div className="animate-fade-in relative h-full">
        <div className="page-header">
          <h1 className="page-title">Signals</h1>
          <button 
            className="btn btn-primary" 
            onClick={() => setShowModal(true)}
          >
            + New Signal
          </button>
        </div>

      {/* Modal moved outside of animate-fade-in context to fix positioning */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="glass-panel w-full max-w-md p-6" style={{ width: '400px' }}>
            <h2 style={{ marginBottom: '20px', color: '#fff', fontSize: '1.2rem', fontWeight: 600 }}>Create New Signal</h2>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <label>Pair</label>
                  <input type="text" name="pair" value={formData.pair} onChange={handleInputChange} required className="input-field" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px' }} />
                </div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <label>Direction</label>
                  <select name="direction" value={formData.direction} onChange={handleInputChange} className="input-field" style={{ background: 'var(--bg-lighter)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', padding: '8px', borderRadius: '4px' }}>
                    <option value="LONG">LONG</option>
                    <option value="SHORT">SHORT</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Entry Price</label>
                <input type="number" step="any" name="entry" value={formData.entry} onChange={handleInputChange} required className="input-field" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px' }} />
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <label>TP1</label>
                  <input type="number" step="any" name="tp1" value={formData.tp1} onChange={handleInputChange} required className="input-field" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px' }} />
                </div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <label>TP2</label>
                  <input type="number" step="any" name="tp2" value={formData.tp2} onChange={handleInputChange} required className="input-field" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px' }} />
                </div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <label>SL</label>
                  <input type="number" step="any" name="sl" value={formData.sl} onChange={handleInputChange} required className="input-field" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px' }} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <label>Confidence</label>
                  <select name="confidence" value={formData.confidence} onChange={handleInputChange} className="input-field" style={{ background: 'var(--bg-lighter)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', padding: '8px', borderRadius: '4px' }}>
                    <option value="STRONG_BUY">STRONG BUY</option>
                    <option value="BUY">BUY</option>
                    <option value="NEUTRAL">NEUTRAL</option>
                    <option value="SELL">SELL</option>
                    <option value="STRONG_SELL">STRONG SELL</option>
                  </select>
                </div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <label>Source</label>
                  <input type="text" name="source" value={formData.source} onChange={handleInputChange} className="input-field" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px' }} />
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Reason</label>
                <textarea name="reason" value={formData.reason} onChange={handleInputChange} className="input-field" placeholder="Short reason for the trade..." style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px', minHeight: '50px' }}></textarea>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Notes / Analysis <span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>(optional)</span></label>
                <textarea name="notes" value={formData.notes} onChange={handleInputChange} className="input-field" placeholder="Multi-timeframe analysis, chart patterns, key levels..." style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px', minHeight: '70px' }}></textarea>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Expires At <span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>(optional — auto-cancel if not triggered)</span></label>
                <input type="datetime-local" name="expires_at" value={formData.expires_at} onChange={handleInputChange} className="input-field" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '4px' }} />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn" style={{ flex: 1, background: 'rgba(255,255,255,0.1)', color: '#fff' }}>Cancel</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Submit</button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Pair</th>
              <th>Direction</th>
              <th>Entry</th>
              <th>TP1</th>
              <th>TP2</th>
              <th>SL</th>
              <th>R:R</th>
              <th>Confidence</th>
              <th>Status</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {signals.length === 0 ? (
              <tr><td colSpan="10" style={{textAlign: 'center', padding: '40px', color: 'var(--text-muted)'}}>No signals yet — click + New Signal to get started</td></tr>
            ) : (
              signals.map(s => {
                const statusStyle = s.status === 'PENDING' 
                  ? { background: 'rgba(240,185,11,0.1)', color: '#f0b90b', border: '1px solid rgba(240,185,11,0.3)' }
                  : s.status === 'EXECUTED'
                  ? { background: 'rgba(14,203,129,0.1)', color: '#0ecb81', border: '1px solid rgba(14,203,129,0.3)' }
                  : { background: 'rgba(132,142,156,0.1)', color: '#848e9c', border: '1px solid rgba(132,142,156,0.3)' };
                return (
                  <React.Fragment key={s.id}>
                    <tr style={{ opacity: s.status === 'CANCELLED' ? 0.5 : 1 }}>
                      <td style={{fontWeight: 600}}>
                        {s.pair}
                        {s.notes && (
                          <span 
                            onClick={() => setExpandedNote(expandedNote === s.id ? null : s.id)} 
                            style={{marginLeft: '8px', cursor: 'pointer', fontSize: '0.85rem', opacity: 0.7}}
                            title="View notes"
                          >
                            📝
                          </span>
                        )}
                      </td>
                      <td><span className={`badge ${s.direction === 'LONG' ? 'badge-long' : 'badge-short'}`}>{s.direction}</span></td>
                      <td>${s.entry?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})}</td>
                      <td style={{color: 'var(--success)', fontSize: '0.9rem'}}>{s.tp1?.toLocaleString(undefined, {maximumFractionDigits: 4})}</td>
                      <td style={{color: 'var(--success)', fontSize: '0.9rem'}}>{s.tp2?.toLocaleString(undefined, {maximumFractionDigits: 4})}</td>
                      <td style={{color: 'var(--danger)', fontSize: '0.9rem'}}>{s.sl?.toLocaleString(undefined, {maximumFractionDigits: 4})}</td>
                      <td style={{fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-primary)'}}>
                        {s.entry && s.sl && s.tp2 && (s.entry - s.sl) !== 0
                          ? (() => {
                              const rr = s.direction === 'LONG'
                                ? ((s.tp2 - s.entry) / (s.entry - s.sl))
                                : ((s.entry - s.tp2) / (s.sl - s.entry));
                              return `${rr.toFixed(1)}R`;
                            })()
                          : '—'
                        }
                      </td>
                      <td><span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{s.confidence?.replace('_', ' ')}</span></td>
                      <td>
                        <span className="badge" style={{...statusStyle, padding: '4px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600}}>
                          {s.status === 'PENDING' && <span style={{display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#f0b90b', marginRight: '6px', animation: 'pulse 1.5s infinite'}}></span>}
                          {s.status === 'EXECUTED' && '✓ '}
                          {s.status}
                        </span>
                      </td>
                      <td style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>{new Date(s.created_at).toLocaleString()}</td>
                      <td>
                        {s.status === 'PENDING' && (
                          <button onClick={() => handleCancel(s.id)} className="btn btn-danger" style={{padding: '4px 12px', fontSize: '0.8rem'}}>Cancel</button>
                        )}
                      </td>
                    </tr>
                    {expandedNote === s.id && s.notes && (
                      <tr>
                        <td colSpan="10" style={{padding: '12px 20px', background: 'rgba(240,185,11,0.03)', borderLeft: '3px solid var(--accent-primary)'}}>
                          <div style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 600}}>📝 ANALYSIS NOTES</div>
                          <div style={{fontSize: '0.9rem', color: 'var(--text-main)', whiteSpace: 'pre-wrap', lineHeight: '1.5'}}>{s.notes}</div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
    </>
  );
}
