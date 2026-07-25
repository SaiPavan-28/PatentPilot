import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api, Patent } from '../services/api';

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  const barClass = value >= 0.6 ? 'high' : value >= 0.4 ? 'medium' : 'low';
  return (
    <div className="score-bar-container">
      <div className="score-bar-label">
        <span className="score-bar-label-text">{label}</span>
        <span className="score-bar-value" style={{ color }}>{pct}%</span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

function RiskBadge({ score }: { score: number }) {
  if (score >= 0.75) return <span className="risk-badge high">⚠ High Risk ({(score * 100).toFixed(0)}%)</span>;
  if (score >= 0.40) return <span className="risk-badge review">⚡ Review ({(score * 100).toFixed(0)}%)</span>;
  return <span className="risk-badge low">✓ Low ({(score * 100).toFixed(0)}%)</span>;
}

function PatentCard({
  patent,
  onStatusChange,
}: {
  patent: Patent;
  onStatusChange: (patentId: string, status: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [status, setStatus] = useState(patent.review_status || 'unreviewed');
  const [updating, setUpdating] = useState(false);

  const handleStatusChange = async (newStatus: string) => {
    setUpdating(true);
    try {
      await api.updateReviewStatus(patent.id, newStatus);
      setStatus(newStatus);
      onStatusChange(patent.id, newStatus);
    } catch (e) {
      console.error('Status update failed', e);
    } finally {
      setUpdating(false);
    }
  };

  const overallScore = patent.scores?.overall_score || 0;
  let scoreColor = 'var(--color-risk-low)';
  if (overallScore >= 0.75) scoreColor = 'var(--color-risk-high)';
  else if (overallScore >= 0.4) scoreColor = 'var(--color-risk-review)';

  return (
    <div className={`patent-card ${status !== 'unreviewed' ? status : ''}`}>
      {/* Card Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.875rem' }}>
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ fontSize: '0.85rem' }}>
            <strong>Patent Number:</strong> <a href={patent.patent_url || `https://patents.google.com/patent/${patent.patent_number}`} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-primary-dark)' }}>{patent.patent_number}</a>
          </div>
          <div style={{ fontSize: '0.85rem' }}>
            <strong>Title:</strong> <span style={{ color: 'var(--color-text-primary)' }}>{patent.title || 'N/A'}</span>
          </div>
          <div style={{ fontSize: '0.85rem' }}>
            <strong>Assignee:</strong> <span style={{ color: 'var(--color-text-secondary)' }}>{patent.assignee || 'N/A'}</span>
          </div>
          <div style={{ fontSize: '0.85rem' }}>
            <strong>Publication Date:</strong> <span style={{ color: 'var(--color-text-secondary)' }}>{patent.publication_date || 'N/A'}</span>
          </div>
          <div style={{ fontSize: '0.85rem' }}>
            <strong>Source:</strong> <span className="badge badge-secondary" style={{ marginLeft: 4 }}>{patent.source}</span>
          </div>
          {/* Strict Verification Section */}
          <div style={{ fontSize: '0.75rem', marginTop: 8, display: 'flex', flexDirection: 'column', gap: 2, padding: '8px', backgroundColor: 'var(--color-bg-alt)', borderRadius: '4px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 2 }}>Verification Status:</div>
            {patent.verification_status?.surechembl && <span style={{ color: '#10b981' }}>✓ Verified by SureChEMBL</span>}
            {patent.verification_status?.patentsview && <span style={{ color: '#10b981' }}>✓ Metadata verified by PatentsView</span>}
            {patent.verification_status?.pubchem && <span style={{ color: '#10b981' }}>✓ Verified by PubChem</span>}
            {patent.verification_status?.google_patents && <span style={{ color: '#10b981' }}>✓ Official Patent Link Validated</span>}
            <div style={{ display: 'flex', gap: 12, marginTop: 6, paddingTop: 6, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              {patent.pdf_url && <a href={patent.pdf_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>📄 PDF</a>}
              {patent.uspto_url && <a href={patent.uspto_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>🏛 USPTO</a>}
              {patent.epo_url && <a href={patent.epo_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>🇪🇺 EPO</a>}
            </div>
          </div>
        </div>

        {/* Overall Score */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, flexShrink: 0 }}>
          <svg width="64" height="64" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="26" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
            <circle
              cx="32" cy="32" r="26"
              fill="none" stroke={scoreColor} strokeWidth="6"
              strokeDasharray={`${2 * Math.PI * 26 * overallScore} ${2 * Math.PI * 26}`}
              strokeLinecap="round"
              transform="rotate(-90 32 32)"
              style={{ transition: 'stroke-dasharray 1s ease' }}
            />
            <text x="32" y="37" textAnchor="middle" fill={scoreColor} fontSize="13" fontFamily="var(--font-mono)" fontWeight="800">
              {Math.round(overallScore * 100)}%
            </text>
          </svg>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: scoreColor, textAlign: 'center', marginTop: 4 }}>Similarity Score</span>
        </div>
      </div>

      {/* Score Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.875rem' }}>
        <ScoreBar label="Chemical" value={patent.scores?.chemical_similarity || 0} color="#6366f1" />
        <ScoreBar label="Target" value={patent.scores?.target_match || 0} color="#06b6d4" />
        <ScoreBar label="Disease" value={patent.scores?.disease_match || 0} color="#10b981" />
        <ScoreBar label="Semantic" value={patent.scores?.semantic_relevance || 0} color="#f59e0b" />
      </div>

      {/* Evidence Flags */}
      {patent.scores?.evidence_flags && patent.scores.evidence_flags.length > 0 && (
        <div className="evidence-list" style={{ marginBottom: '0.875rem' }}>
          {patent.scores.evidence_flags.slice(0, expanded ? undefined : 3).map((flag, i) => (
            <div key={i} className="evidence-item">{flag}</div>
          ))}
        </div>
      )}

      {/* Abstract is now strictly only available inside expanded view per user request */}

      {/* Expanded Content */}
      {expanded && (
        <div style={{ marginBottom: '0.875rem' }}>
          {patent.abstract && (
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>Abstract</div>
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>{patent.abstract}</p>
            </div>
          )}

          {/* AI Explanation */}
          {patent.explanation && (
            <div style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-primary-light)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>🤖</span> AI Analysis
              </div>
              {[
                { key: 'why_retrieved', label: 'Why Retrieved' },
                { key: 'similar_regions', label: 'Similar Regions' },
                { key: 'possible_novelty_overlap', label: 'Possible Novelty Overlap' },
                { key: 'confidence', label: 'Confidence' },
                { key: 'risk_level', label: 'Risk Level' },
              ].map(({ key, label }) => (
                patent.explanation![key as keyof typeof patent.explanation] && (
                  <div key={key} style={{ marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.2rem' }}>{label}</div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                      {patent.explanation![key as keyof typeof patent.explanation] as string}
                    </p>
                  </div>
                )
              ))}
              {patent.explanation.key_concerns && patent.explanation.key_concerns.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.25rem' }}>Key Concerns</div>
                  {patent.explanation.key_concerns.map((c, i) => (
                    <div key={i} style={{ fontSize: '0.8rem', color: '#f87171', marginBottom: 4 }}>⚠ {c}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Footer Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '0.5rem', flexWrap: 'wrap' }}>
        <div className="review-status-buttons" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {['reviewed', 'flagged', 'dismissed'].map(s => (
            <button
              key={s}
              className={`review-btn ${s} ${status === s ? 'active' : ''}`}
              onClick={() => handleStatusChange(status === s ? 'unreviewed' : s)}
              disabled={updating}
            >
              {s === 'reviewed' ? '✓' : s === 'flagged' ? '⚑' : '✕'} {s}
            </button>
          ))}
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setExpanded(!expanded)}
            style={{ fontWeight: 600, border: '1px solid var(--color-border)', marginLeft: '0.5rem' }}
          >
            {expanded ? '▲ Collapse' : '▼ Expand'}
          </button>
        </div>
      </div>
    </div>
  );
}

function SkeletonPatentCard() {
  return (
    <div className="card card-padding" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div className="skeleton skeleton-text w-1-4" />
      <div className="skeleton skeleton-text w-3-4" />
      <div className="skeleton skeleton-text w-1-2" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' }}>
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 32 }} />)}
      </div>
    </div>
  );
}

export default function WorkspacePage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState<any>(null);
  const [patents, setPatents] = useState<Patent[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingDone, setProcessingDone] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('overall_score');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterScore, setFilterScore] = useState('');
  const [generating, setGenerating] = useState(false);

  const fetchData = useCallback(async () => {
    if (!analysisId) return;
    try {
      const data = await api.getPatents(analysisId, filterStatus ? { status_filter: filterStatus } : undefined);
      setPatents(data.patents || []);
      setAnalysis(data);
      if (data.analysis_status === 'complete' || data.analysis_status === 'error') {
        setProcessingDone(true);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  }, [analysisId, filterStatus]);

  // Poll while processing
  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      if (!processingDone) fetchData();
    }, 2500);
    return () => clearInterval(interval);
  }, [fetchData, processingDone]);

  const handleStatusChange = (patentId: string, newStatus: string) => {
    setPatents(prev => prev.map(p => p.id === patentId ? { ...p, review_status: newStatus } : p));
  };

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      await api.generateReport(analysisId!);
      navigate(`/report/${analysisId}`);
    } catch (err: any) {
      alert('Report generation failed: ' + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const sortedPatents = [...patents].sort((a, b) => {
    if (sortBy === 'overall_score') return (b.scores?.overall_score || 0) - (a.scores?.overall_score || 0);
    if (sortBy === 'publication_date') return (b.publication_date || '').localeCompare(a.publication_date || '');
    if (sortBy === 'chemical_similarity') return (b.scores?.chemical_similarity || 0) - (a.scores?.chemical_similarity || 0);
    return 0;
  });

  let filteredPatents = filterStatus
    ? sortedPatents.filter(p => p.review_status === filterStatus)
    : sortedPatents;

  if (filterScore) {
    filteredPatents = filteredPatents.filter(p => {
      const s = p.scores?.overall_score || 0;
      if (filterScore === 'high') return s >= 0.75;
      if (filterScore === 'medium') return s >= 0.40 && s < 0.75;
      if (filterScore === 'low') return s < 0.40;
      return true;
    });
  }

  const isProcessing = analysis?.analysis_status === 'processing';

  return (
    <div className="animate-fadeInUp">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <Link to="/" className="btn btn-secondary btn-sm">← Back</Link>
            <div className="divider" style={{ height: 20, width: 1, margin: '0 4px' }} />
            <div className="flex items-center gap-2">
              <div className={`status-dot ${analysis?.analysis_status || 'pending'}`} />
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', textTransform: 'capitalize' }}>
                {isProcessing ? 'Retrieving & analyzing patents...' : `${analysis?.analysis_status || 'pending'}`}
              </span>
            </div>
          </div>
          <h1 className="page-title">Patent Review Workspace</h1>
          <p className="page-subtitle">Analysis ID: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-primary-light)' }}>{analysisId?.substring(0, 8)}...</span></p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {processingDone && patents.length > 0 && (
            <button className="btn btn-primary" onClick={handleGenerateReport} disabled={generating}>
              {generating ? <><div className="spinner" /> Generating...</> : '📋 Generate Report'}
            </button>
          )}
        </div>
      </div>

      {/* Processing skeleton */}
      {isProcessing && (
        <div>
          <div className="card card-padding" style={{ marginBottom: '1rem', textAlign: 'center', padding: '2rem' }}>
            <div className="spinner spinner-lg" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ marginBottom: '0.5rem' }}>Analyzing Patents...</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
              Running parallel retrieval from PubChem & PatentsView, ranking by hybrid similarity, and generating AI explanations. This takes 30–90 seconds.
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
              {['🔬 Fingerprinting', '⚡ Retrieving', '📊 Ranking', '🤖 Explaining'].map((step, i) => (
                <div key={i} style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{step}</div>
              ))}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: '1rem' }}>
            {[...Array(4)].map((_, i) => <SkeletonPatentCard key={i} />)}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card card-padding" style={{ borderColor: 'rgba(239,68,68,0.3)', textAlign: 'center', color: '#f87171' }}>
          <p>⚠ {error}</p>
        </div>
      )}

      {/* Results */}
      {processingDone && !error && (
        <>
          {/* Stats + Filters */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <div className="card card-padding-sm" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-primary-light)' }}>{patents.length}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>Patents Found</span>
              </div>
              {['flagged', 'reviewed', 'dismissed'].map(s => {
                const count = patents.filter(p => p.review_status === s).length;
                return count > 0 ? (
                  <div key={s} className="card card-padding-sm" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: s === 'flagged' ? 'var(--color-risk-review)' : s === 'reviewed' ? 'var(--color-risk-low)' : 'var(--color-text-muted)' }}>{count}</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', textTransform: 'capitalize' }}>{s}</span>
                  </div>
                ) : null;
              })}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value)}
                style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '0.4rem 0.75rem', color: 'var(--color-text-primary)', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                <option value="overall_score">Sort: Overlap Score</option>
                <option value="chemical_similarity">Sort: Chemical Similarity</option>
                <option value="publication_date">Sort: Date</option>
              </select>
              <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '0.4rem 0.75rem', color: 'var(--color-text-primary)', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                <option value="">Status Filter: All</option>
                <option value="unreviewed">Unreviewed</option>
                <option value="flagged">Flagged</option>
                <option value="reviewed">Reviewed</option>
                <option value="dismissed">Dismissed</option>
              </select>
              <select
                value={filterScore}
                onChange={e => setFilterScore(e.target.value)}
                style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '0.4rem 0.75rem', color: 'var(--color-text-primary)', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                <option value="">Score Filter: All</option>
                <option value="high">High Risk (≥ 75%)</option>
                <option value="medium">Medium Risk (40-74%)</option>
                <option value="low">Low Risk (&lt; 40%)</option>
              </select>
            </div>
          </div>

          {filteredPatents.length === 0 ? (
            <div className="empty-state card">
              <div className="empty-state-icon">🔍</div>
              <h3>No patents found</h3>
              <p>{patents.length > 0 ? 'No patents match the current filter.' : 'No relevant patents were found for this molecule. This may indicate low patent risk.'}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {/* Group Patents by Risk Level */}
              {(() => {
                const high = filteredPatents.filter(p => (p.scores?.overall_score || 0) >= 0.75);
                const medium = filteredPatents.filter(p => {
                  const s = p.scores?.overall_score || 0;
                  return s >= 0.40 && s < 0.75;
                });
                const low = filteredPatents.filter(p => (p.scores?.overall_score || 0) < 0.40);

                const renderGroup = (title: string, group: Patent[], color: string) => {
                  if (group.length === 0) return null;
                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: color, display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: `2px solid ${color}`, paddingBottom: '0.25rem' }}>
                        {title} ({group.length})
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem', alignItems: 'flex-start' }}>
                        {group.map(patent => (
                          <PatentCard key={patent.id} patent={patent} onStatusChange={handleStatusChange} />
                        ))}
                      </div>
                    </div>
                  );
                };

                return (
                  <>
                    {renderGroup('⚠ High Risk (≥ 75% Overlap)', high, 'var(--color-risk-high)')}
                    {renderGroup('⚡ Review Needed (40% - 74% Overlap)', medium, 'var(--color-risk-review)')}
                    {renderGroup('✓ Low Risk (< 40% Overlap)', low, 'var(--color-risk-low)')}
                  </>
                );
              })()}
            </div>
          )}

          {processingDone && patents.length > 0 && (
            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              <button className="btn btn-primary btn-lg" onClick={handleGenerateReport} disabled={generating}>
                {generating ? <><div className="spinner" /> Generating Report...</> : '📋 Generate Patentability Report →'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
