import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, AnalysisSummary } from '../services/api';

function RiskPill({ risk }: { risk?: string }) {
  if (!risk) return <span className="badge badge-secondary">Pending</span>;
  if (risk.includes('High')) return <span className="badge badge-danger">High Risk</span>;
  if (risk.includes('Expert')) return <span className="badge badge-warning">Review</span>;
  return <span className="badge badge-success">Low Risk</span>;
}

export default function HistoryPage() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState<string | null>(null);


  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getHistory(page, 10, search || undefined);
      setAnalyses(data.items);
      setTotal(data.total);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('Delete this analysis and all its patents?')) return;
    setDeleting(id);
    try {
      await api.deleteAnalysis(id);
      setAnalyses(prev => prev.filter(a => a.id !== id));
      setTotal(t => t - 1);
    } catch (err: any) {
      alert('Delete failed: ' + err.message);
    } finally {
      setDeleting(null);
    }
  };

  useEffect(() => { fetchHistory(); }, [page, search]);


  const totalPages = Math.ceil(total / 10);

  return (
    <div className="animate-fadeInUp">
      <div className="page-header">
        <div>
          <h1 className="page-title">Analysis History</h1>
          <p className="page-subtitle">{total} total analyses — click any to reopen the full report.</p>
        </div>
        <Link to="/" className="btn btn-primary">+ New Analysis</Link>
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: '1.5rem', maxWidth: 420 }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }}>
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          className="form-input"
          placeholder="Search by SMILES, target, indication..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
          style={{ paddingLeft: 36 }}
        />
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="card card-padding" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <div className="skeleton" style={{ width: 80, height: 40, borderRadius: 8 }} />
              <div style={{ flex: 1 }}>
                <div className="skeleton skeleton-text w-3-4" />
                <div className="skeleton skeleton-text w-1-2" />
              </div>
              <div className="skeleton" style={{ width: 80, height: 28, borderRadius: 999 }} />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="card card-padding" style={{ textAlign: 'center', color: '#f87171' }}>⚠ {error}</div>
      ) : analyses.length === 0 ? (
        <div className="empty-state card">
          <div className="empty-state-icon">🔬</div>
          <h3>{search ? 'No matches found' : 'No analyses yet'}</h3>
          <p>{search ? 'Try a different search term.' : 'Submit a molecule to start your first FTO screen.'}</p>
          {!search && <Link to="/" className="btn btn-primary" style={{ marginTop: '0.75rem' }}>Submit Molecule →</Link>}
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {analyses.map(a => {
              const overallRisk = a.risk_score !== null && a.risk_score !== undefined ? Math.round(a.risk_score * 100) : null;
              const riskColor = overallRisk !== null ? (overallRisk >= 75 ? 'var(--color-risk-high)' : overallRisk >= 40 ? 'var(--color-risk-review)' : 'var(--color-risk-low)') : 'var(--color-text-muted)';
              const formattedDate = a.created_at ? new Date(a.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '';
              const formattedTime = a.created_at ? new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

              return (
                <div
                  key={a.id}
                  className="card card-padding"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1rem',
                    background: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-lg)',
                    transition: 'all 0.2s ease',
                    position: 'relative'
                  }}
                >
                  {/* Card Header: Molecule Name + ID + Date */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                        🧪 {a.molecule_name || 'Unnamed Compound'}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--color-primary-light)', background: 'rgba(99,102,241,0.1)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(99,102,241,0.2)' }}>
                        ID: {a.id.substring(0, 8)}
                      </span>
                      <div className={`status-dot ${a.status}`} style={{ margin: '0 4px' }} title={`Status: ${a.status}`} />
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>{a.status}</span>
                    </div>

                    {/* Date */}
                    <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span>📅</span> {formattedDate} {formattedTime && `· ${formattedTime}`}
                    </div>
                  </div>

                  {/* Body: SMILES, Target, Disease */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {/* SMILES */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem' }}>
                      <span style={{ fontWeight: 600, color: 'var(--color-text-secondary)', minWidth: 60 }}>SMILES:</span>
                      <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', background: 'rgba(0,0,0,0.2)', padding: '4px 8px', borderRadius: '4px', color: 'var(--color-text-primary)', wordBreak: 'break-all', flex: 1, border: '1px solid rgba(255,255,255,0.05)' }}>
                        {a.smiles}
                      </code>
                    </div>

                    {/* Target & Disease Pills */}
                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '2px' }}>
                      <span style={{ fontSize: '0.78rem', background: 'rgba(6,182,212,0.1)', color: '#06b6d4', padding: '3px 10px', borderRadius: 999, border: '1px solid rgba(6,182,212,0.2)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        🎯 Target: <strong>{a.target || 'N/A'}</strong>
                      </span>
                      <span style={{ fontSize: '0.78rem', background: 'rgba(16,185,129,0.1)', color: '#10b981', padding: '3px 10px', borderRadius: 999, border: '1px solid rgba(16,185,129,0.2)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        🏥 Disease: <strong>{a.indication || 'N/A'}</strong>
                      </span>
                    </div>
                  </div>

                  {/* Footer: Metrics (Total Patents, Risk %) + Actions (Report, Delete) */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                    {/* Metrics */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
                      {/* Total Patents */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--color-primary-light)' }}>{a.patent_count}</span>
                        <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Total Patents</span>
                      </div>

                      {/* Risk % */}
                      {overallRisk !== null && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', paddingLeft: '1rem', borderLeft: '1px solid rgba(255,255,255,0.1)' }}>
                          <span style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: riskColor }}>
                            {overallRisk}%
                          </span>
                          <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Risk</span>
                          <RiskPill risk={a.risk_level} />
                        </div>
                      )}
                    </div>

                    {/* Actions: Report Button & Delete Option */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => navigate(a.risk_level ? `/report/${a.id}` : `/workspace/${a.id}`)}
                        style={{ fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        📋 View Report →
                      </button>

                      <button
                        onClick={(e) => handleDelete(e, a.id)}
                        disabled={deleting === a.id}
                        title="Delete this analysis"
                        className="btn btn-sm"
                        style={{
                          background: 'rgba(239,68,68,0.12)',
                          border: '1px solid rgba(239,68,68,0.3)',
                          color: '#ef4444',
                          fontWeight: 700,
                          opacity: deleting === a.id ? 0.5 : 1,
                          cursor: 'pointer'
                        }}
                      >
                        {deleting === a.id ? '…' : '🗑 Delete'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>← Prev</button>
              {[...Array(totalPages)].map((_, i) => (
                <button key={i} className={`btn btn-sm ${page === i + 1 ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setPage(i + 1)}>
                  {i + 1}
                </button>
              ))}
              <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
