import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

// Debounce hook for SMILES validation
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

export default function HomePage() {
  const navigate = useNavigate();

  const [smiles, setSmiles] = useState('');
  const [moleculeName, setMoleculeName] = useState('');
  const [target, setTarget] = useState('');
  const [indication, setIndication] = useState('');

  const [validation, setValidation] = useState<any>(null);
  const [validating, setValidating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lookingUpName, setLookingUpName] = useState(false);
  const [autoFilledNotice, setAutoFilledNotice] = useState('');
  const [error, setError] = useState('');

  const debouncedSmiles = useDebounce(smiles, 600);
  const debouncedMoleculeName = useDebounce(moleculeName, 600);

  // Auto-lookup SMILES from Molecule Name
  useEffect(() => {
    const trimmedName = debouncedMoleculeName.trim();
    if (!trimmedName || trimmedName.length < 2) return;
    
    // Only auto-fill if smiles is empty or was previously auto-filled
    setLookingUpName(true);
    api.nameToSmiles(trimmedName)
      .then(res => {
        if (res.found && res.smiles) {
          setSmiles(res.smiles);
          setAutoFilledNotice(`✨ Auto-populated SMILES from PubChem for "${trimmedName}"`);
        }
      })
      .catch(() => {})
      .finally(() => setLookingUpName(false));
  }, [debouncedMoleculeName]);

  // Auto-validate on SMILES change
  useEffect(() => {
    if (!debouncedSmiles.trim()) { setValidation(null); return; }
    setValidating(true);
    api.validateSmiles(debouncedSmiles)
      .then(v => setValidation(v))
      .catch(() => setValidation({ valid: false, error: 'Validation failed' }))
      .finally(() => setValidating(false));
  }, [debouncedSmiles]);

  const handleManualNameLookup = async () => {
    if (!moleculeName.trim()) return;
    setLookingUpName(true);
    setAutoFilledNotice('');
    try {
      const res = await api.nameToSmiles(moleculeName.strip ? moleculeName.trim() : moleculeName);
      if (res.found && res.smiles) {
        setSmiles(res.smiles);
        setAutoFilledNotice(`✨ Found & filled SMILES for "${moleculeName}"`);
      } else {
        setError(`Could not find SMILES for "${moleculeName}". Please paste SMILES manually.`);
      }
    } catch (err: any) {
      setError('Name lookup failed');
    } finally {
      setLookingUpName(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!smiles.trim()) return;
    if (validation && !validation.valid) return;

    setSubmitting(true);
    setError('');
    try {
      const result = await api.submitMolecule({ smiles, molecule_name: moleculeName, target, indication });
      navigate(`/workspace/${result.id}`);
    } catch (err: any) {
      setError(err.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const loadExample = (exSmiles: string, exTarget: string, exIndication: string, exName: string) => {
    setSmiles(exSmiles);
    setTarget(exTarget);
    setIndication(exIndication);
    setMoleculeName(exName);
    setAutoFilledNotice('');
  };


  return (
    <div className="animate-fadeInUp">
      {/* Hero Section */}
      <div style={{ textAlign: 'center', marginBottom: '3rem', padding: '2rem 0' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '0.4rem 1rem', borderRadius: 999, background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)', marginBottom: '1.25rem' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', display: 'inline-block', animation: 'pulse 2s infinite' }} />
          <span style={{ fontSize: '0.8rem', color: '#818cf8', fontWeight: 600 }}>AI-Assisted FTO Screening</span>
        </div>
        <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.1, marginBottom: '1rem' }}>
          <span className="text-gradient">Discover Patent Risk</span><br />
          <span style={{ color: 'var(--color-text-primary)' }}>Before It Discovers You</span>
        </h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--color-text-secondary)', maxWidth: 560, margin: '0 auto', lineHeight: 1.7 }}>
          Submit a molecule, get AI-ranked patents with grounded explanations, and generate a structured Freedom-to-Operate report in minutes.
        </p>
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.75rem' }}>
          ⚠️ Screening aid only — not legal advice. Consult a patent attorney for formal FTO opinions.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        {/* Submission Form */}
        <div className="card card-padding-lg">
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Submit Molecule</h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>Enter a SMILES string and optional context to start your FTO screen.</p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Molecule name (Type name to auto-fill SMILES) */}
            <div className="form-group">
              <label className="form-label" htmlFor="name-input">
                Molecule Name <span style={{ color: 'var(--color-primary-light)', fontSize: '0.75rem', fontWeight: 600 }}>(Type a drug name to auto-fill SMILES)</span>
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  id="name-input"
                  className="form-input"
                  placeholder="e.g. Aspirin, Imatinib, Ibuprofen, Sildenafil, Paracetamol"
                  value={moleculeName}
                  onChange={e => {
                    setMoleculeName(e.target.value);
                    setAutoFilledNotice('');
                  }}
                />
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleManualNameLookup}
                  disabled={lookingUpName || !moleculeName.trim()}
                  style={{ flexShrink: 0, padding: '0 1rem' }}
                >
                  {lookingUpName ? <div className="spinner spinner-sm" /> : '🔍 Auto-Fill SMILES'}
                </button>
              </div>
              {lookingUpName && <span className="form-hint" style={{ color: 'var(--color-primary-light)', display: 'flex', alignItems: 'center', gap: 6 }}><div className="spinner" style={{ width: 14, height: 14 }} /> Looking up SMILES for "{moleculeName}" in PubChem...</span>}
              {autoFilledNotice && <span className="form-success" style={{ fontWeight: 700 }}>{autoFilledNotice}</span>}
            </div>

            {/* SMILES */}
            <div className="form-group">
              <label className="form-label" htmlFor="smiles-input">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
                Molecule SMILES <span style={{ color: '#ef4444', marginLeft: 2 }}>*</span>
              </label>
              <textarea
                id="smiles-input"
                className={`form-input form-textarea ${validation ? (validation.valid ? 'success' : 'error') : ''}`}
                placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O  (Auto-filled when you type a Molecule Name above)"
                value={smiles}
                onChange={e => { setSmiles(e.target.value); setAutoFilledNotice(''); }}
                rows={3}
                style={{ minHeight: 90 }}
                required
              />
              {validating && <span className="form-hint" style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div className="spinner" style={{ width: 14, height: 14 }} /> Validating SMILES structure...</span>}
              {!validating && validation && validation.valid && (
                <span className="form-success">
                  ✓ Valid SMILES
                  {validation.molecular_formula && ` · ${validation.molecular_formula}`}
                  {validation.molecular_weight && ` · MW: ${validation.molecular_weight} g/mol`}
                </span>
              )}
              {!validating && validation && !validation.valid && (
                <span className="form-error">✗ {validation.error}</span>
              )}
              <span className="form-hint">Auto-filled from Molecule Name above, or edit/paste SMILES manually</span>
            </div>


            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              {/* Target */}
              <div className="form-group">
                <label className="form-label" htmlFor="target-input">
                  Biological Target <span className="optional">(optional)</span>
                </label>
                <input id="target-input" className="form-input" placeholder="e.g. EGFR kinase, COX-2" value={target} onChange={e => setTarget(e.target.value)} />
                <span className="form-hint">Improves target-match scoring</span>
              </div>

              {/* Indication */}
              <div className="form-group">
                <label className="form-label" htmlFor="indication-input">
                  Disease / Indication <span className="optional">(optional)</span>
                </label>
                <input id="indication-input" className="form-input" placeholder="e.g. non-small cell lung cancer" value={indication} onChange={e => setIndication(e.target.value)} />
                <span className="form-hint">Improves disease-match scoring</span>
              </div>
            </div>

            {error && (
              <div style={{ padding: '0.875rem 1rem', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)', color: '#f87171', fontSize: '0.875rem' }}>
                ⚠ {error}
              </div>
            )}

            <button
              type="submit"
              id="submit-btn"
              className="btn btn-primary btn-xl"
              disabled={submitting || !smiles.trim() || (validation && !validation.valid)}
              style={{ marginTop: '0.5rem' }}
            >
              {submitting ? (
                <><div className="spinner" /> Analyzing...</>
              ) : (
                <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg> Start FTO Analysis</>
              )}
            </button>
          </form>
        </div>

        {/* Right Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* 2D Structure Preview */}
          {validation?.valid && validation?.structure_svg && (
            <div className="card card-padding-sm animate-fadeIn">
              <div className="section-header" style={{ marginBottom: '0.75rem', paddingBottom: '0.5rem' }}>
                <span className="section-title" style={{ fontSize: '0.85rem' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                  2D Structure Preview
                </span>
              </div>
              <div className="molecule-viewer">
                <div dangerouslySetInnerHTML={{ __html: validation.structure_svg }} style={{ width: '100%' }} />
              </div>
              {validation.num_atoms && (
                <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                  {[
                    { label: 'Formula', value: validation.molecular_formula },
                    { label: 'MW', value: validation.molecular_weight ? `${validation.molecular_weight} g/mol` : null },
                    { label: 'Atoms', value: validation.num_atoms },
                  ].filter(i => i.value).map(item => (
                    <div key={item.label} style={{ flex: '1 1 auto', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{item.label}</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--color-primary-light)' }}>{item.value}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Example Molecules */}
          <div className="card card-padding-sm">
            <div className="section-header" style={{ marginBottom: '0.75rem', paddingBottom: '0.5rem' }}>
              <span className="section-title" style={{ fontSize: '0.85rem' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 12l2 2 4-4"/><path d="M21 12c0 4.97-4.03 9-9 9S3 16.97 3 12 7.03 3 12 3s9 4.03 9 9z"/></svg>
                Example Molecules
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {[
                { name: 'Aspirin', smiles: 'CC(=O)Oc1ccccc1C(=O)O', target: 'COX-1, COX-2', indication: 'pain, inflammation', color: '#6366f1' },
                { name: 'Ibuprofen', smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O', target: 'COX-2', indication: 'anti-inflammatory', color: '#06b6d4' },
                { name: 'Caffeine', smiles: 'Cn1cnc2c1c(=O)n(c(=O)n2C)C', target: 'adenosine receptor', indication: 'CNS stimulant', color: '#10b981' },
                { name: 'Sildenafil', smiles: 'CCCc1nn(C)c2c(=O)[nH]c(-c3cc(S(=O)(=O)N4CCN(CC4)C)ccc3OCC)nc12', target: 'PDE5', indication: 'erectile dysfunction, PAH', color: '#f59e0b' },
              ].map(ex => (
                <button
                  key={ex.name}
                  className="btn btn-ghost btn-sm"
                  style={{ justifyContent: 'flex-start', gap: 8, textAlign: 'left' }}
                  onClick={() => loadExample(ex.smiles, ex.target, ex.indication, ex.name)}
                >
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: ex.color, flexShrink: 0 }} />
                  <span style={{ fontWeight: 600, color: 'var(--color-text-primary)', minWidth: 80 }}>{ex.name}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ex.smiles.substring(0, 30)}...</span>
                </button>
              ))}
            </div>
          </div>

          {/* Pipeline overview */}
          <div className="card card-padding-sm">
            <div className="section-header" style={{ marginBottom: '0.75rem', paddingBottom: '0.5rem' }}>
              <span className="section-title" style={{ fontSize: '0.85rem' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                Analysis Pipeline
              </span>
            </div>
            {[
              { step: '01', label: 'SMILES Validation', icon: '✓', color: '#10b981' },
              { step: '02', label: 'Molecular Fingerprinting', icon: '🔬', color: '#6366f1' },
              { step: '03', label: 'Parallel Patent Retrieval', icon: '⚡', color: '#f59e0b' },
              { step: '04', label: 'Hybrid Relevance Ranking', icon: '📊', color: '#06b6d4' },
              { step: '05', label: 'AI Grounded Explanations', icon: '🤖', color: '#8b5cf6' },
              { step: '06', label: 'Risk Report Generation', icon: '📋', color: '#ef4444' },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.4rem 0', borderBottom: i < 5 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}>
                <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: item.color, fontWeight: 700, minWidth: 28 }}>{item.step}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
