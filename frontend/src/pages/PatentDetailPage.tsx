import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { api, Patent } from '../services/api';

function ScoreRing({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  const r = 30;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <svg width="80" height="80" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        <circle
          cx="40" cy="40" r={r}
          fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 40 40)"
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
        <text x="40" y="45" textAnchor="middle" fill={color} fontSize="14" fontFamily="monospace" fontWeight="800">
          {pct}%
        </text>
      </svg>
      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-text-secondary)', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</span>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', marginBottom: '1.25rem' }}>
      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: '1.1rem' }}>{icon}</span> {title}
      </div>
      {children}
    </div>
  );
}

export default function PatentDetailPage() {
  const { analysisId, patentId } = useParams<{ analysisId: string; patentId: string }>();
  const navigate = useNavigate();
  const [patent, setPatent] = useState<Patent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!analysisId || !patentId) return;
    api.getPatents(analysisId).then(data => {
      const found = data.patents.find(p => p.id === patentId);
      if (found) {
        setPatent(found);
      } else {
        setError('Patent not found');
      }
    }).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, [analysisId, patentId]);

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
      <div className="spinner spinner-lg" />
    </div>
  );

  if (error || !patent) return (
    <div className="card card-padding" style={{ textAlign: 'center', color: '#f87171' }}>⚠ {error || 'Patent not found'}</div>
  );

  const overallScore = patent.scores?.overall_score || 0;
  let scoreColor = 'var(--color-risk-low)';
  if (overallScore >= 0.75) scoreColor = 'var(--color-risk-high)';
  else if (overallScore >= 0.4) scoreColor = 'var(--color-risk-review)';
  else if (overallScore < 0.20) scoreColor = '#ef4444';

  const patentUrl = patent.patent_url || `https://patents.google.com/patent/${patent.patent_number}`;

  return (
    <div className="animate-fadeInUp">
      {/* Header */}
      <div className="page-header" style={{ marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>← Back</button>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>Patent Detail View</span>
          </div>
          <h1 className="page-title" style={{ fontSize: '1.4rem', lineHeight: 1.3 }}>
            {patent.title || 'Patent Detail'}
          </h1>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            <a href={patentUrl} target="_blank" rel="noopener noreferrer"
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--color-primary-light)', textDecoration: 'none', fontWeight: 700 }}>
              🔗 {patent.patent_number}
            </a>
            <span className="badge badge-secondary">{patent.source}</span>
            {patent.publication_date && (
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>📅 {patent.publication_date}</span>
            )}
            {patent.assignee && (
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>🏢 {patent.assignee}</span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <a href={patentUrl} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">
            View on Google Patents ↗
          </a>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.25rem', alignItems: 'flex-start' }}>
        {/* Left Column */}
        <div>
          {/* Abstract */}
          <Section title="Abstract" icon="📄">
            {patent.abstract && patent.abstract.length > 5 ? (
              <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', lineHeight: 1.75, margin: 0 }}>
                {patent.abstract}
              </p>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', fontStyle: 'italic', margin: 0 }}>
                Abstract not available in database. &nbsp;
                <a href={patentUrl} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)', textDecoration: 'underline' }}>
                  View full patent on Google Patents →
                </a>
              </p>
            )}
          </Section>

          {/* AI Analysis */}
          {patent.explanation && (
            <Section title="AI Analysis" icon="🤖">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {[
                  { key: 'why_retrieved', label: 'Why Retrieved', color: '#6366f1' },
                  { key: 'similar_regions', label: 'Similar Structural Regions', color: '#06b6d4' },
                  { key: 'possible_novelty_overlap', label: 'Possible Novelty Overlap', color: '#f59e0b' },
                  { key: 'confidence', label: 'Confidence Assessment', color: '#10b981' },
                  { key: 'risk_level', label: 'Risk Level', color: '#ef4444' },
                ].map(({ key, label, color }) =>
                  patent.explanation![key as keyof typeof patent.explanation] ? (
                    <div key={key} style={{ padding: '0.875rem', background: `rgba(${color === '#6366f1' ? '99,102,241' : color === '#06b6d4' ? '6,182,212' : color === '#f59e0b' ? '245,158,11' : color === '#10b981' ? '16,185,129' : '239,68,68'},0.06)`, borderRadius: 'var(--radius-md)', borderLeft: `3px solid ${color}` }}>
                      <div style={{ fontSize: '0.72rem', fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.35rem' }}>{label}</div>
                      <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.6, margin: 0 }}>
                        {patent.explanation![key as keyof typeof patent.explanation] as string}
                      </p>
                    </div>
                  ) : null
                )}
                {patent.explanation.key_concerns && patent.explanation.key_concerns.length > 0 && (
                  <div style={{ padding: '0.875rem', background: 'rgba(239,68,68,0.06)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid #ef4444' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>Key Concerns</div>
                    {patent.explanation.key_concerns.map((c, i) => (
                      <div key={i} style={{ fontSize: '0.875rem', color: '#f87171', marginBottom: 6 }}>⚠ {c}</div>
                    ))}
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Evidence Flags */}
          {patent.scores?.evidence_flags && patent.scores.evidence_flags.length > 0 && (
            <Section title="Evidence Flags" icon="🚩">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {patent.scores.evidence_flags.map((flag, i) => (
                  <div key={i} className="evidence-item">{flag}</div>
                ))}
              </div>
            </Section>
          )}

          {/* Links */}
          <Section title="External Links" icon="🌐">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
              <a href={patentUrl} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">📋 Google Patents</a>
              {patent.pdf_url && <a href={patent.pdf_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">📄 PDF</a>}
              {patent.uspto_url && <a href={patent.uspto_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">🏛 USPTO</a>}
              {patent.epo_url && <a href={patent.epo_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">🇪🇺 EPO</a>}
            </div>
          </Section>
        </div>

        {/* Right Column — Scores */}
        <div>
          {/* Overall Score */}
          <div className="card card-padding" style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
              Overall Similarity Score
            </div>
            <svg width="100" height="100" viewBox="0 0 100 100" style={{ margin: '0 auto 0.75rem', display: 'block' }}>
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
              <circle
                cx="50" cy="50" r="40"
                fill="none" stroke={scoreColor} strokeWidth="10"
                strokeDasharray={`${2 * Math.PI * 40 * overallScore} ${2 * Math.PI * 40}`}
                strokeLinecap="round"
                transform="rotate(-90 50 50)"
                style={{ transition: 'stroke-dasharray 1s ease' }}
              />
              <text x="50" y="57" textAnchor="middle" fill={scoreColor} fontSize="20" fontFamily="monospace" fontWeight="800">
                {Math.round(overallScore * 100)}%
              </text>
            </svg>
            <span style={{ fontSize: '0.875rem', fontWeight: 700, color: scoreColor }}>
              {overallScore >= 0.75 ? '⚠ High Risk' : overallScore >= 0.4 ? '⚡ Review Needed' : '✓ Low Risk'}
            </span>
          </div>

          {/* Score Breakdown */}
          <div className="card card-padding" style={{ marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
              Score Breakdown
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', justifyItems: 'center' }}>
              <ScoreRing label="Chemical" value={patent.scores?.chemical_similarity || 0} color="#6366f1" />
              <ScoreRing label="Target" value={patent.scores?.target_match || 0} color="#06b6d4" />
              <ScoreRing label="Disease" value={patent.scores?.disease_match || 0} color="#10b981" />
              <ScoreRing label="Semantic" value={patent.scores?.semantic_relevance || 0} color="#f59e0b" />
            </div>
          </div>

          {/* Verification Status */}
          <div className="card card-padding" style={{ marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
              Verification
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {patent.verification_status?.pubchem && <span style={{ fontSize: '0.8rem', color: '#10b981' }}>✓ Verified by PubChem</span>}
              {patent.verification_status?.surechembl && <span style={{ fontSize: '0.8rem', color: '#10b981' }}>✓ Verified by SureChEMBL</span>}
              {patent.verification_status?.google_patents && <span style={{ fontSize: '0.8rem', color: '#10b981' }}>✓ Official Patent Link</span>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
