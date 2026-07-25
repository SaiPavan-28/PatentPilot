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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {analyses.map(a => (
              <div
                key={a.id}
                className="card card-padding"
                style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer', transition: 'all var(--transition-fast)' }}
                onClick={() => a.status === 'complete' ? navigate(a.risk_level ? `/report/${a.id}` : `/workspace/${a.id}`) : navigate(`/workspace/${a.id}`)}
              >
                {/* Status */}
                <div style={{ textAlign: 'center', minWidth: 60 }}>
                  <div className={`status-dot ${a.status}`} style={{ margin: '0 auto 4px' }} />
                  <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>{a.status}</span>
                </div>

                {/* Main info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--color-primary-light)' }}>
                      {a.id.substring(0, 8)}...
                    </span>
                    {a.molecule_name && <span style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontSize: '0.9rem' }}>{a.molecule_name}</span>}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--color-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
                    {a.smiles}
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', marginTop: 4, flexWrap: 'wrap' }}>
                    {a.target && <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>🎯 {a.target}</span>}
                    {a.indication && <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>🏥 {a.indication}</span>}
                  </div>
                </div>

                {/* Stats */}
                <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexShrink: 0, flexWrap: 'wrap' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-primary-light)' }}>{a.patent_count}</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>patents</div>
                  </div>
                  {a.risk_score !== null && a.risk_score !== undefined && (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: a.risk_score >= 0.75 ? 'var(--color-risk-high)' : a.risk_score >= 0.4 ? 'var(--color-risk-review)' : 'var(--color-risk-low)' }}>
                        {Math.round(a.risk_score * 100)}%
                      </div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>risk</div>
                    </div>
                  )}
                  <RiskPill risk={a.risk_level} />
                </div>

                {/* Date + Arrow */}
                <div style={{ textAlign: 'right', flexShrink: 0, minWidth: 80 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {a.created_at ? new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                  </div>
                  <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>→</span>
                </div>
              </div>
            ))}
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
