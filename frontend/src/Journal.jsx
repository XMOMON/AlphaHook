import { useState, useEffect, useRef } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Journal() {
  const [trades, setTrades] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [draftNote, setDraftNote] = useState('');
  const [saving, setSaving] = useState(false);
  const textRef = useRef(null);

  const fetchTrades = () => {
    fetch(`${API_URL}/api/v1/trades/`)
      .then(res => res.json())
      .then(data => setTrades(data))
      .catch(console.error);
  };

  useEffect(() => {
    fetchTrades();
  }, []);

  useEffect(() => {
    if (editingId !== null && textRef.current) {
      textRef.current.focus();
    }
  }, [editingId]);

  const startEdit = (trade) => {
    setEditingId(trade.id);
    setDraftNote(trade.journal || '');
  };

  const saveNote = async (id) => {
    setSaving(true);
    try {
      await fetch(`${API_URL}/api/v1/trades/${id}/journal`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ journal: draftNote }),
      });
      setEditingId(null);
      fetchTrades();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const pnlColor = (v) => v >= 0 ? 'var(--success)' : 'var(--danger)';
  const sign = (v) => v >= 0 ? '+' : '';

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Trade Journal</h1>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{trades.length} trades</span>
      </div>

      {trades.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          No closed trades yet — your journal will populate as positions close.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {trades.map(t => (
            <div key={t.id} className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                {/* Pair + direction */}
                <div style={{ minWidth: '120px' }}>
                  <div style={{ fontWeight: 700, fontSize: '1rem' }}>{t.pair}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {t.exit_reason === 'TP1_PARTIAL' ? '½ close · TP1' : t.exit_reason}
                  </div>
                </div>

                {/* Entry / Exit */}
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', minWidth: '160px' }}>
                  <div>Entry: <b style={{ color: '#fff' }}>${t.entry?.toLocaleString(undefined, { maximumFractionDigits: 4 })}</b></div>
                  <div>Exit: <b style={{ color: '#fff' }}>${t.exit?.toLocaleString(undefined, { maximumFractionDigits: 4 })}</b></div>
                </div>

                {/* PnL */}
                <div style={{ minWidth: '110px' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: pnlColor(t.pnl_usd) }}>
                    {sign(t.pnl_usd)}${t.pnl_usd?.toFixed(2)}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: pnlColor(t.pnl_pct) }}>
                    {sign(t.pnl_pct)}{t.pnl_pct?.toFixed(2)}%
                  </div>
                </div>

                {/* Dates */}
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', flex: 1 }}>
                  <div>{t.opened_at ? new Date(t.opened_at).toLocaleString() : '—'}</div>
                  <div>→ {t.closed_at ? new Date(t.closed_at).toLocaleString() : '—'}</div>
                </div>

                {/* Edit button */}
                <button
                  onClick={() => editingId === t.id ? setEditingId(null) : startEdit(t)}
                  className="btn"
                  style={{
                    padding: '6px 14px',
                    fontSize: '0.8rem',
                    background: editingId === t.id ? 'rgba(240,185,11,0.15)' : 'rgba(255,255,255,0.07)',
                    color: editingId === t.id ? 'var(--accent-primary)' : 'var(--text-muted)',
                    border: `1px solid ${editingId === t.id ? 'rgba(240,185,11,0.4)' : 'rgba(255,255,255,0.08)'}`,
                  }}
                >
                  ✏️ {editingId === t.id ? 'Cancel' : (t.journal ? 'Edit Note' : 'Add Note')}
                </button>
              </div>

              {/* Inline journal editor */}
              {editingId === t.id && (
                <div style={{ marginTop: '16px', animation: 'fadeIn 0.2s ease' }}>
                  <textarea
                    ref={textRef}
                    value={draftNote}
                    onChange={e => setDraftNote(e.target.value)}
                    placeholder="What happened? Why did you take this trade? What would you do differently?"
                    style={{
                      width: '100%',
                      minHeight: '100px',
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid rgba(240,185,11,0.25)',
                      borderRadius: '8px',
                      color: '#fff',
                      padding: '12px',
                      fontSize: '0.9rem',
                      lineHeight: '1.6',
                      resize: 'vertical',
                      boxSizing: 'border-box',
                      fontFamily: 'inherit',
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                    <button
                      onClick={() => saveNote(t.id)}
                      disabled={saving}
                      className="btn btn-primary"
                      style={{ padding: '8px 20px' }}
                    >
                      {saving ? 'Saving...' : '💾 Save Note'}
                    </button>
                  </div>
                </div>
              )}

              {/* Display saved note */}
              {editingId !== t.id && t.journal && (
                <div style={{
                  marginTop: '14px',
                  padding: '12px 14px',
                  background: 'rgba(240,185,11,0.04)',
                  borderLeft: '3px solid var(--accent-primary)',
                  borderRadius: '0 6px 6px 0',
                  fontSize: '0.88rem',
                  color: 'var(--text-main)',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap',
                }}>
                  {t.journal}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
