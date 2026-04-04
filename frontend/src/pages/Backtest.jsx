import { useState } from 'react';
import axios from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

export default function Backtest() {
  const [form, setForm] = useState({
    pair: 'BTC/USDT',
    start_date: '',
    end_date: '',
    initial_balance: 10000,
    risk_per_trade: 0.02,
    slippage_pct: 0.001,
    commission_pct: 0.001,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...form,
        start_date: new Date(form.start_date).toISOString(),
        end_date: new Date(form.end_date).toISOString(),
      };
      const res = await axios.post('/backtest/', payload);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }));
  };

  return (
    <div>
      <h1 style={{ fontSize: '1.8rem', marginBottom: '20px' }}>Backtest</h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: '30px', background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>Pair</label>
            <select name="pair" value={form.pair} onChange={handleChange} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }}>
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="SOL/USDT">SOL/USDT</option>
              <option value="BNB/USDT">BNB/USDT</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>Start Date</label>
            <input type="datetime-local" name="start_date" value={form.start_date} onChange={handleChange} required style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }} />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>End Date</label>
            <input type="datetime-local" name="end_date" value={form.end_date} onChange={handleChange} required style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }} />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>Initial Balance ($)</label>
            <input type="number" name="initial_balance" value={form.initial_balance} onChange={handleChange} min={100} step={100} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }} />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>Risk per Trade (%)</label>
            <input type="number" name="risk_per_trade" value={form.risk_per_trade} onChange={handleChange} min={0.1} max={10} step={0.1} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }} />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>Slippage (%)</label>
            <input type="number" name="slippage_pct" value={form.slippage_pct} onChange={handleChange} min={0} max={5} step={0.01} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }} />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>Commission (%)</label>
            <input type="number" name="commission_pct" value={form.commission_pct} onChange={handleChange} min={0} max={1} step={0.01} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }} />
          </div>
        </div>

        <button type="submit" disabled={loading} style={{ marginTop: '20px', padding: '10px 20px', background: '#22ab94', color: '#fff', border: 'none', borderRadius: '8px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1 }}>
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
      </form>

      {error && <div style={{ color: '#f7525f', marginBottom: '20px' }}>Error: {error}</div>}

      {result && (
        <div>
          {/* Summary Stats */}
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ fontSize: '1.4rem', marginBottom: '15px' }}>Summary</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
              {Object.entries(result.stats).map(([key, val]) => (
                <div key={key} style={{ background: 'rgba(255,255,255,0.03)', padding: '15px', borderRadius: '10px' }}>
                  <div style={{ fontSize: '0.85rem', color: '#888', textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 600 }}>{typeof val === 'number' ? (key.includes('pct') ? `${val}%` : val.toLocaleString()) : String(val)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Equity Curve */}
          {result.equity_curve && result.equity_curve.length > 0 && (
            <div style={{ marginBottom: '30px' }}>
              <h2 style={{ fontSize: '1.4rem', marginBottom: '15px' }}>Equity Curve</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={result.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="timestamp" stroke="#888" tickFormatter={(t) => new Date(t).toLocaleDateString()} />
                  <YAxis stroke="#888" domain={['auto', 'auto']} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="balance" stroke="#22ab94" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Trades Table */}
          <div>
            <h2 style={{ fontSize: '1.4rem', marginBottom: '15px' }}>Trades</h2>
            <div style={{ overflowX: 'auto', borderRadius: '10px', border: '1px solid #333' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead style={{ background: 'rgba(255,255,255,0.05)' }}>
                  <tr>
                    <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #333' }}>#</th>
                    <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #333' }}>Pair</th>
                    <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #333' }}>Dir</th>
                    <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #333' }}>Entry</th>
                    <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #333' }}>Exit</th>
                    <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #333' }}>Reason</th>
                    <th style={{ padding: '10px', textAlign: 'right', borderBottom: '1px solid #333' }}>PnL %</th>
                    <th style={{ padding: '10px', textAlign: 'right', borderBottom: '1px solid #333' }}>PnL $</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trades.map((t, idx) => (
                    <tr key={t.signal_id || idx} style={{ borderBottom: '1px solid #222' }}>
                      <td style={{ padding: '10px' }}>{idx + 1}</td>
                      <td style={{ padding: '10px' }}>{t.pair}</td>
                      <td style={{ padding: '10px' }}>{t.direction}</td>
                      <td style={{ padding: '10px' }}>$ {t.entry_price.toFixed(2)}</td>
                      <td style={{ padding: '10px' }}>$ {t.exit_price.toFixed(2)}</td>
                      <td style={{ padding: '10px' }}>{t.exit_reason}</td>
                      <td style={{ padding: '10px', textAlign: 'right', color: t.pnl_pct >= 0 ? '#22ab94' : '#f7525f' }}>
                        {t.pnl_pct > 0 ? '+' : ''}{t.pnl_pct.toFixed(2)}%
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right', color: t.pnl_usd >= 0 ? '#22ab94' : '#f7525f' }}>
                        {t.pnl_usd > 0 ? '+' : ''}{t.pnl_usd.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
