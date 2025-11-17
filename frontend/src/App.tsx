import { useState, useEffect } from 'react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RankedItem {
  item_id: string;
  score: number;
}

interface MetricsSummary {
  total_requests: number;
  avg_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
}

function App() {
  const [activeTab, setActiveTab] = useState<'rank' | 'dashboard'>('rank');
  const [isHealthy, setIsHealthy] = useState(false);
  
  // Ranking state
  const [userId, setUserId] = useState('user_001');
  const [itemIds, setItemIds] = useState('N1\nN2\nN3\nN4\nN5');
  const [impressions, setImpressions] = useState('42');
  const [avgHour, setAvgHour] = useState('14');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<RankedItem[] | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Dashboard state
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      setIsHealthy(res.ok);
    } catch {
      setIsHealthy(false);
    }
  };

  const handleRank = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const items = itemIds.split('\n').map(s => s.trim()).filter(Boolean);
      
      const res = await fetch(`${API_URL}/rank`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          item_ids: items,
          user_features: {},
          context_features: {
            impressions: parseFloat(impressions) || 0,
            avg_hour: parseFloat(avgHour) || 0
          }
        })
      });

      if (!res.ok) throw new Error(`Error: ${res.status}`);
      
      const data = await res.json();
      setResults(data.ranked_items);
      setLatency(data.latency_ms);
    } catch (err: any) {
      setError(err.message || 'Failed to rank items');
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const res = await fetch(`${API_URL}/metrics/summary`);
      if (res.ok) setMetrics(await res.json());
    } catch {}
  };

  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadMetrics();
      const interval = setInterval(loadMetrics, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  return (
    <div style={{ minHeight: '100vh', padding: '20px' }}>
      {/* Header */}
      <header style={{ maxWidth: '1200px', margin: '0 auto 40px', textAlign: 'center' }} className="animate-in">
        <h1 style={{ fontSize: '48px', fontWeight: '800', marginBottom: '12px', background: 'linear-gradient(135deg, #818cf8 0%, #6366f1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          FeedRanker
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '18px' }}>
          AI-Powered Feed Ranking System
        </p>
        <div style={{ marginTop: '16px' }}>
          <span className={`badge ${isHealthy ? 'badge-success' : 'badge-danger'}`}>
            {isHealthy ? '● Online' : '● Offline'}
          </span>
        </div>
      </header>

      {/* Tabs */}
      <div style={{ maxWidth: '1200px', margin: '0 auto 32px', display: 'flex', gap: '12px', justifyContent: 'center' }}>
        <button 
          onClick={() => setActiveTab('rank')}
          style={{ 
            background: activeTab === 'rank' ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' : 'rgba(30, 41, 59, 0.5)',
            padding: '10px 28px'
          }}
        >
          🎯 Rank Items
        </button>
        <button 
          onClick={() => setActiveTab('dashboard')}
          style={{ 
            background: activeTab === 'dashboard' ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' : 'rgba(30, 41, 59, 0.5)',
            padding: '10px 28px'
          }}
        >
          📊 Dashboard
        </button>
      </div>

      {/* Content */}
      <main style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {activeTab === 'rank' && (
          <div className="animate-in" style={{ display: 'grid', gap: '24px', gridTemplateColumns: results ? '1fr 1fr' : '1fr' }}>
            {/* Ranking Form */}
            <div className="card">
              <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '24px' }}>Rank Feed Items</h2>
              <form onSubmit={handleRank} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px' }}>User ID</label>
                  <input type="text" value={userId} onChange={e => setUserId(e.target.value)} />
                </div>
                
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px' }}>Item IDs (one per line)</label>
                  <textarea value={itemIds} onChange={e => setItemIds(e.target.value)} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px' }}>Impressions</label>
                    <input type="number" value={impressions} onChange={e => setImpressions(e.target.value)} />
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px' }}>Avg Hour</label>
                    <input type="number" value={avgHour} onChange={e => setAvgHour(e.target.value)} min="0" max="23" />
                  </div>
                </div>

                <button type="submit" disabled={loading || !isHealthy} style={{ marginTop: '8px', fontSize: '16px' }}>
                  {loading ? <span className="spinner" /> : '🚀 Rank Items'}
                </button>

                {error && (
                  <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: 'var(--danger)' }}>
                    {error}
                  </div>
                )}
              </form>
            </div>

            {/* Results */}
            {results && (
              <div className="card animate-in">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                  <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Ranked Results</h2>
                  {latency && <span className="badge badge-success">{latency.toFixed(1)}ms</span>}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {results.map((item, idx) => (
                    <div key={item.item_id} className="card" style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontWeight: '700', fontSize: '18px' }}>#{idx + 1}</span>
                        <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>{item.item_id}</span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${item.score * 100}%` }} />
                      </div>
                      <div style={{ marginTop: '6px', textAlign: 'right', fontSize: '12px', color: 'var(--text-muted)' }}>
                        Score: {item.score.toFixed(4)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="animate-in" style={{ display: 'grid', gap: '24px', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
            {metrics ? (
              <>
                <div className="card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '40px', fontWeight: '800', color: 'var(--primary)', marginBottom: '8px' }}>
                    {metrics.total_requests}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Total Requests</div>
                </div>
                
                <div className="card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '40px', fontWeight: '800', color: 'var(--success)', marginBottom: '8px' }}>
                    {metrics.avg_latency_ms.toFixed(1)}ms
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Avg Latency</div>
                </div>
                
                <div className="card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '40px', fontWeight: '800', color: 'var(--warning)', marginBottom: '8px' }}>
                    {metrics.min_latency_ms.toFixed(1)}ms
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Min Latency</div>
                </div>
                
                <div className="card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '40px', fontWeight: '800', color: 'var(--danger)', marginBottom: '8px' }}>
                    {metrics.max_latency_ms.toFixed(1)}ms
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Max Latency</div>
                </div>
              </>
            ) : (
              <div className="card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '60px' }}>
                <div className="spinner" style={{ margin: '0 auto 16px' }} />
                <p style={{ color: 'var(--text-muted)' }}>Loading metrics...</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ maxWidth: '1200px', margin: '60px auto 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
        <p>Powered by LambdaMART + Deep CTR Ensemble</p>
      </footer>
    </div>
  );
}

export default App;
