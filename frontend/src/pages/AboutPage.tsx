import React from 'react';
import { Link } from 'react-router-dom';

export default function AboutPage() {
  return (
    <div className="animate-fadeInUp" style={{ maxWidth: 1000, margin: '0 auto', paddingBottom: '3rem' }}>
      {/* Hero Header */}
      <div style={{ textAlign: 'center', marginBottom: '3rem', padding: '2rem 0' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '0.4rem 1rem', borderRadius: 999, background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)', marginBottom: '1.25rem' }}>
          <span style={{ fontSize: '0.8rem', color: '#818cf8', fontWeight: 600 }}>🔬 Autonomous FTO & Patent Intelligence Platform</span>
        </div>
        <h1 style={{ fontSize: 'clamp(2.2rem, 5vw, 3.5rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.15, marginBottom: '1rem' }}>
          <span className="text-gradient">About PatentPilot</span><br />
          <span style={{ color: 'var(--color-text-primary)' }}>AI-Assisted Freedom-to-Operate Screening</span>
        </h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--color-text-secondary)', maxWidth: 680, margin: '0 auto', lineHeight: 1.7 }}>
          PatentPilot empowers pharmaceutical researchers, medicinal chemists, and IP analysts to evaluate potential patent risks, assess compound novelty, and accelerate Freedom-to-Operate (FTO) screening using multi-agent AI and structural bioinformatics.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1.75rem' }}>
          <Link to="/" className="btn btn-primary btn-lg" style={{ fontWeight: 700 }}>+ Start FTO Screening</Link>
          <Link to="/history" className="btn btn-secondary btn-lg">📋 View History</Link>
        </div>
      </div>

      {/* Core Mission & Value Proposition */}
      <div className="card card-padding-lg" style={{ marginBottom: '2rem', background: 'linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(6,182,212,0.04) 100%)', border: '1px solid rgba(99,102,241,0.2)' }}>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>🚀</span> What is PatentPilot?
        </h2>
        <p style={{ fontSize: '0.95rem', color: 'var(--color-text-secondary)', lineHeight: 1.7, marginBottom: '1.25rem' }}>
          In drug discovery, identifying patent barriers early is critical to avoiding costly litigation and wasted R&D investment. Traditional FTO searches require manual queries across fragmented databases and expensive legal reviews. 
        </p>
        <p style={{ fontSize: '0.95rem', color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
          <strong>PatentPilot automated this entire pipeline</strong> by integrating 2D structural Tanimoto fingerprint searching, biological target/disease context mapping, and LLM-grounded explainability into a single unified platform.
        </p>
      </div>

      {/* Multi-Agent AI Architecture */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>🤖 Multi-Agent AI Architecture</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>PatentPilot operates using four specialized, collaborative AI agents:</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '1rem' }}>
          {[
            {
              title: 'Retrieval Agent',
              icon: '🔍',
              color: '#06b6d4',
              desc: 'Queries PubChem & Europe PMC in parallel, builds expanded chemical vocabularies, and enforces strict verification rules.'
            },
            {
              title: 'Explanation Agent',
              icon: '🧠',
              color: '#6366f1',
              desc: 'Uses Groq LLM (Llama 3.1) to generate per-patent structural/functional explanations grounded strictly in claims and abstracts.'
            },
            {
              title: 'Scorer & Decision Agent',
              icon: '📊',
              color: '#10b981',
              desc: 'Calculates 5-component hybrid overlap scores and assigns risk categories (Low, Requires Expert Review, High Risk).'
            },
            {
              title: 'Report Agent',
              icon: '📋',
              color: '#f59e0b',
              desc: 'Assembles structured Patentability Reports with Executive Summaries, Novelty Concerns, and Manual Review Checklists.'
            }
          ].map(agent => (
            <div key={agent.title} className="card card-padding" style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>{agent.icon}</span>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: agent.color, margin: 0 }}>{agent.title}</h3>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', lineHeight: 1.6, margin: 0 }}>
                {agent.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 5-Pillar Hybrid Scoring Methodology */}
      <div className="card card-padding-lg" style={{ marginBottom: '2.5rem' }}>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>⚖️</span> Documented Scoring Methodology
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '1.5rem' }}>
          PatentPilot computes a deterministic <strong>Overall Overlap Score</strong> using a weighted 5-pillar hybrid scoring model:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ background: 'rgba(99,102,241,0.08)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(99,102,241,0.2)' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--color-primary-light)', fontFamily: 'var(--font-mono)' }}>40%</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: 4 }}>Chemical Structure</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>Tanimoto 2D Morgan Fingerprint similarity via PubChem search</div>
          </div>

          <div style={{ background: 'rgba(6,182,212,0.08)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(6,182,212,0.2)' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#06b6d4', fontFamily: 'var(--font-mono)' }}>25%</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: 4 }}>Biological Target</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>Alignment of protein/gene/receptor target annotations</div>
          </div>

          <div style={{ background: 'rgba(168,85,247,0.08)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(168,85,247,0.2)' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#a855f7', fontFamily: 'var(--font-mono)' }}>20%</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: 4 }}>Semantic Overlap</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>TF-IDF Cosine Similarity across patent abstracts & claims</div>
          </div>

          <div style={{ background: 'rgba(16,185,129,0.08)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(16,185,129,0.2)' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#10b981', fontFamily: 'var(--font-mono)' }}>10%</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: 4 }}>Disease Indication</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>Therapeutic area and disease keyword matching</div>
          </div>
        </div>

        {/* Risk Thresholds */}
        <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem 1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '0.5rem' }}>Decision Thresholds:</div>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.82rem' }}>
            <span>🟢 <strong>Low Patent Risk</strong> (&lt; 40% Overlap)</span>
            <span>🟡 <strong>Requires Expert Review</strong> (40% – 74% Overlap)</span>
            <span>🔴 <strong>High Patent Risk</strong> (≥ 75% Overlap)</span>
          </div>
        </div>
      </div>

      {/* Tech Stack & External Databases */}
      <div className="card card-padding-lg" style={{ marginBottom: '2.5rem' }}>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>🌐</span> Data Sources & Core Tech Stack
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-light)', marginBottom: '0.5rem' }}>Integrated Patent & Chemical Databases:</h3>
            <ul style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.8, paddingLeft: '1.2rem' }}>
              <li><strong>PubChem PUG REST API:</strong> Chemical structure identification, SMILES lookup, and 2D fast Tanimoto similarity.</li>
              <li><strong>Europe PMC API:</strong> Full-text patent searching with core abstracts and publication metadata.</li>
              <li><strong>Google Patents & USPTO:</strong> Verification links and direct patent document references.</li>
            </ul>
          </div>

          <div>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-light)', marginBottom: '0.5rem' }}>AI & Engineering Architecture:</h3>
            <ul style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.8, paddingLeft: '1.2rem' }}>
              <li><strong>Groq LLM Engine (Llama 3.1 8B):</strong> Grounded per-patent explanations and structured report synthesis.</li>
              <li><strong>FastAPI & SQLite:</strong> Asynchronous Python backend with background task execution.</li>
              <li><strong>React, TypeScript & Vite:</strong> Responsive, modern SPA user interface.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Legal Disclaimer */}
      <div style={{ padding: '1.25rem', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 'var(--radius-lg)', textAlign: 'center' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#f59e0b', marginBottom: '0.35rem' }}>
          ⚠️ Legal & Screening Disclaimer
        </div>
        <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', lineHeight: 1.6, margin: 0, maxWidth: 800, marginLeft: 'auto', marginRight: 'auto' }}>
          PatentPilot is designed as an AI-assisted screening and decision-support tool. It does not replace formal Freedom-to-Operate opinions, patent landscaping, or legal counsel provided by registered patent attorneys and IP specialists.
        </p>
      </div>
    </div>
  );
}
