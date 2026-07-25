import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api, ReportResponse } from '../services/api';

function RiskBanner({ recommendation, riskScore, rationale }: { recommendation?: string; riskScore?: number; rationale?: string }) {
  const isHigh = recommendation?.includes('High');
  const isReview = recommendation?.includes('Expert');
  const isLow = recommendation?.includes('Low');

  const color = isHigh ? 'var(--color-risk-high)' : isReview ? 'var(--color-risk-review)' : 'var(--color-risk-low)';
  const bg = isHigh ? 'var(--color-risk-high-bg)' : isReview ? 'var(--color-risk-review-bg)' : 'var(--color-risk-low-bg)';
  const icon = isHigh ? '⚠' : isReview ? '⚡' : '✓';

  return (
    <div style={{ padding: '1.5rem', background: bg, border: `1px solid ${color}33`, borderRadius: 'var(--radius-lg)', marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.75rem' }}>{icon}</span>
          <div>
            <div style={{ fontSize: '0.72rem', color: color, textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>Final Recommendation</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 900, color: color, letterSpacing: '-0.02em' }}>{recommendation}</div>
          </div>
        </div>
        {riskScore !== undefined && (
          <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Risk Score</div>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color, fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
              {Math.round((riskScore || 0) * 100)}<span style={{ fontSize: '1rem' }}>%</span>
            </div>
          </div>
        )}
      </div>
      {rationale && <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>{rationale}</p>}
      <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
        ⚠️ <strong>Legal Disclaimer:</strong> This report is a preliminary AI-assisted screening tool and does not constitute a formal Freedom-to-Operate opinion or legal advice. Consult a qualified patent attorney before making product development or commercialization decisions.
      </div>
    </div>
  );
}

function ReportSection({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="card" style={{ marginBottom: '1rem', overflow: 'hidden' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{ width: '100%', padding: '1rem 1.25rem', background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10, textAlign: 'left' }}
      >
        <span style={{ fontSize: '1.1rem' }}>{icon}</span>
        <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-primary)' }}>{title}</span>
        <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div style={{ padding: '0 1.25rem 1.25rem', borderTop: '1px solid var(--color-border)' }}>
          {children}
        </div>
      )}
    </div>
  );
}

export default function ReportPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!analysisId) return;
    api.getReport(analysisId)
      .then(r => { setReport(r); setLoading(false); })
      .catch(async () => {
        // Try to generate it
        setGenerating(true);
        try {
          const r = await api.generateReport(analysisId);
          setReport(r);
        } catch (e: any) {
          setError(e.message);
        } finally {
          setGenerating(false);
          setLoading(false);
        }
      });
  }, [analysisId]);

  if (loading || generating) {
    return (
      <div className="animate-fadeIn" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <div className="spinner spinner-lg" style={{ margin: '0 auto 1.5rem' }} />
        <h2>{generating ? 'Generating Report...' : 'Loading Report...'}</h2>
        <p style={{ color: 'var(--color-text-secondary)', marginTop: '0.5rem' }}>
          {generating ? 'AI is assembling your patentability report. This takes 15–30 seconds.' : 'Fetching your report...'}
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card card-padding animate-fadeIn" style={{ textAlign: 'center', borderColor: 'rgba(239,68,68,0.3)' }}>
        <p style={{ color: '#f87171' }}>⚠ {error}</p>
        <Link to={`/workspace/${analysisId}`} className="btn btn-secondary" style={{ marginTop: '1rem' }}>← Back to Workspace</Link>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="animate-fadeInUp">
      {/* Header */}
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <Link to={`/workspace/${analysisId}`} className="btn btn-ghost btn-sm">← Workspace</Link>
          </div>
          <h1 className="page-title">Patentability Report</h1>
          <p className="page-subtitle">
            Generated: {report.generated_at ? new Date(report.generated_at).toLocaleString() : 'Just now'}
            {' · '}Analysis: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-primary-light)' }}>{analysisId?.substring(0, 8)}...</span>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-ghost btn-sm" onClick={() => window.print()}>🖨 Print / PDF</button>
          <Link to="/history" className="btn btn-ghost btn-sm">📋 History</Link>
        </div>
      </div>

      {/* Risk Banner */}
      <RiskBanner
        recommendation={report.recommendation}
        riskScore={report.risk_score}
        rationale={report.recommendation_rationale}
      />

      {/* Scoring Methodology */}
      {report.scoring_methodology_explanation && (
        <div style={{ padding: '0.875rem 1rem', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
          <span style={{ color: 'var(--color-primary-light)', fontWeight: 700 }}>📊 Scoring: </span>
          {report.scoring_methodology_explanation}
        </div>
      )}

      {/* Executive Summary */}
      <ReportSection title="Executive Summary" icon="📝">
        <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', lineHeight: 1.8, marginTop: '1rem', whiteSpace: 'pre-wrap' }}>
          {report.executive_summary}
        </p>
      </ReportSection>

      {/* Key Evidence */}
      {report.key_evidence && report.key_evidence.length > 0 && (
        <ReportSection title="Key Evidence" icon="🔍">
          <ul style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', listStyle: 'none' }}>
            {report.key_evidence.map((e, i) => (
              <li key={i} style={{ display: 'flex', gap: 10, padding: '0.6rem 0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                <span style={{ color: 'var(--color-primary-light)', fontWeight: 700, minWidth: 20 }}>{i + 1}.</span>
                {e}
              </li>
            ))}
          </ul>
        </ReportSection>
      )}

      {/* Key Similar Patents */}
      {report.key_similar_patents && report.key_similar_patents.length > 0 && (
        <ReportSection title="Key Similar Patents" icon="📑">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
            {report.key_similar_patents.map((p: any, i) => {
              const score = p.overall_score || 0;
              const scoreColor = score >= 0.75 ? 'var(--color-risk-high)' : score >= 0.4 ? 'var(--color-risk-review)' : 'var(--color-risk-low)';
              return (
                <div key={i} style={{ display: 'flex', gap: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', alignItems: 'flex-start' }}>
                  <div style={{ flexShrink: 0, textAlign: 'center', minWidth: 70 }}>
                    <div style={{ fontSize: '1.4rem', fontWeight: 900, color: scoreColor, fontFamily: 'var(--font-mono)' }}>{Math.round(score * 100)}%</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>overlap</div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-accent)', fontSize: '0.8rem', fontWeight: 700, marginBottom: 4 }}>{p.patent_number}</div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '0.25rem' }}>{p.title}</div>
                    {p.key_concern && <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{p.key_concern}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </ReportSection>
      )}

      {/* Novelty Concerns */}
      {report.novelty_concerns && report.novelty_concerns.length > 0 && (
        <ReportSection title="Potential Novelty Concerns" icon="⚠">
          <ul style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', listStyle: 'none' }}>
            {report.novelty_concerns.map((c, i) => (
              <li key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                <span style={{ color: 'var(--color-risk-review)', flexShrink: 0 }}>⚠</span>
                {c}
              </li>
            ))}
          </ul>
        </ReportSection>
      )}

      {/* Potential Novel Regions */}
      {report.potential_novel_regions && (
        <ReportSection title="Potential Novel Molecule Regions" icon="✨">
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.7, marginTop: '1rem' }}>
            {report.potential_novel_regions}
          </p>
        </ReportSection>
      )}

      {/* Recommended Next Actions */}
      {report.recommended_next_actions && report.recommended_next_actions.length > 0 && (
        <ReportSection title="Recommended Next Actions" icon="➡">
          <ol style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', paddingLeft: '1.25rem' }}>
            {report.recommended_next_actions.map((a, i) => (
              <li key={i} style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>{a}</li>
            ))}
          </ol>
        </ReportSection>
      )}

      {/* Manual Review Checklist */}
      {report.manual_review_checklist && report.manual_review_checklist.length > 0 && (
        <ReportSection title="Manual Review Checklist" icon="☑">
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {report.manual_review_checklist.map((item, i) => (
              <label key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', cursor: 'pointer', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                <input type="checkbox" style={{ marginTop: 3, accentColor: 'var(--color-primary)', flexShrink: 0 }} />
                {item}
              </label>
            ))}
          </div>
        </ReportSection>
      )}

      {/* Confidence note */}
      {report.confidence_score !== undefined && (
        <div style={{ textAlign: 'center', marginTop: '1.5rem', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
            Overall Assessment Confidence: <strong style={{ color: 'var(--color-text-secondary)' }}>{Math.round((report.confidence_score || 0) * 100)}%</strong>
            {' · '}Based on data completeness of retrieved patents and researcher inputs provided.
          </span>
        </div>
      )}
    </div>
  );
}
