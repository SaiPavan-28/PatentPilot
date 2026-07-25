import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, DashboardStats, AnalysisSummary } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const RISK_COLORS: Record<string, string> = {
  'High Patent Risk': '#ef4444',
  'Requires Expert Review': '#f59e0b',
  'Low Patent Risk': '#10b981',
  'Pending': '#6366f1',
};

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: string; color?: string }) {
  return (
    <div className="card card-padding" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
      <div style={{ fontSize: '2rem', width: 52, height: 52, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', flexShrink: 0 }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '2rem', fontWeight: 900, fontFamily: 'var(--font-mono)', color: color || 'var(--color-primary-light)', lineHeight: 1 }}>
          {value}
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>{label}</div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getDashboard()
      .then(s => { setStats(s); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="page-header"><div><h1 className="page-title">Analytics Dashboard</h1></div></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          {[...Array(4)].map((_, i) => <div key={i} className="card skeleton" style={{ height: 100 }} />)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          {[...Array(4)].map((_, i) => <div key={i} className="card skeleton" style={{ height: 250 }} />)}
        </div>
      </div>
    );
  }

  if (error) return <div className="card card-padding" style={{ color: '#f87171', textAlign: 'center' }}>⚠ {error}</div>;
  if (!stats) return null;

  const riskDist = Object.entries(stats.risk_distribution || {}).map(([name, value]) => ({ name, value }));
  const sourceDist = Object.entries(stats.source_distribution || {}).map(([name, value]) => ({ name, value }));

  const completedAnalyses = Object.values(stats.risk_distribution || {}).reduce((a, b) => a + b, 0);
  const highRiskCount = stats.risk_distribution?.['High Patent Risk'] || 0;
  const reviewCount = stats.risk_distribution?.['Requires Expert Review'] || 0;

  return (
    <div className="animate-fadeInUp">
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics Dashboard</h1>
          <p className="page-subtitle">Overview of all PatentPilot analyses and risk distribution.</p>
        </div>
        <Link to="/" className="btn btn-primary">+ New Analysis</Link>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.75rem' }}>
        <StatCard label="Total Analyses" value={stats.total_analyses} icon="🔬" color="var(--color-primary-light)" />
        <StatCard label="With Reports" value={completedAnalyses} icon="📋" color="var(--color-accent)" />
        <StatCard label="High Risk Findings" value={highRiskCount} icon="⚠" color="var(--color-risk-high)" />
        <StatCard label="Requires Review" value={reviewCount} icon="⚡" color="var(--color-risk-review)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>
        {/* Risk Distribution Pie */}
        <div className="card card-padding">
          <div className="section-header">
            <span className="section-title">Risk Distribution</span>
          </div>
          {riskDist.length === 0 || riskDist.every(d => d.value === 0) ? (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <div>📊</div>
              <p>Generate reports to see risk distribution</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={riskDist} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                  {riskDist.map((entry, i) => (
                    <Cell key={i} fill={RISK_COLORS[entry.name] || '#6366f1'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 8, color: 'var(--color-text-primary)', fontSize: '0.8rem' }}
                />
                <Legend
                  formatter={(value) => <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.78rem' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Source Distribution Bar */}
        <div className="card card-padding">
          <div className="section-header">
            <span className="section-title">Patent Source Distribution</span>
          </div>
          {sourceDist.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <div>📚</div>
              <p>Run analyses to see source breakdown</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={sourceDist} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="name" stroke="var(--color-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--color-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 8, color: 'var(--color-text-primary)', fontSize: '0.8rem' }}
                />
                <Bar dataKey="value" fill="url(#barGrad)" radius={[4, 4, 0, 0]} />
                <defs>
                  <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#06b6d4" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Targets */}
        <div className="card card-padding">
          <div className="section-header">
            <span className="section-title">🎯 Top Biological Targets</span>
          </div>
          {!stats.top_targets || stats.top_targets.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <p>No targets submitted yet. Add targets when submitting molecules for richer analysis.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginTop: '0.75rem' }}>
              {stats.top_targets.map((t, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--color-primary-light)', minWidth: 20 }}>#{i + 1}</span>
                  <span style={{ flex: 1, fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>{t.target}</span>
                  <span className="badge badge-primary">{t.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Indications */}
        <div className="card card-padding">
          <div className="section-header">
            <span className="section-title">🏥 Top Disease Indications</span>
          </div>
          {!stats.top_indications || stats.top_indications.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <p>No indications submitted yet.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginTop: '0.75rem' }}>
              {stats.top_indications.map((ind, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--color-accent)', minWidth: 20 }}>#{i + 1}</span>
                  <span style={{ flex: 1, fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>{ind.indication}</span>
                  <span className="badge badge-secondary">{ind.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card card-padding">
        <div className="section-header">
          <span className="section-title">🕒 Recent Activity</span>
          <Link to="/history" className="btn btn-ghost btn-sm">View All →</Link>
        </div>
        {!stats.recent_analyses || stats.recent_analyses.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem' }}>
            <div>🔬</div>
            <p>No analyses yet. <Link to="/">Submit your first molecule →</Link></p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
            {stats.recent_analyses.map((a: AnalysisSummary) => (
              <Link
                key={a.id}
                to={a.risk_level ? `/report/${a.id}` : `/workspace/${a.id}`}
                style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', textDecoration: 'none', transition: 'all var(--transition-fast)' }}
                className="card"
              >
                <div className={`status-dot ${a.status}`} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--color-text-muted)', minWidth: 70 }}>
                  {a.id.substring(0, 6)}...
                </span>
                <span style={{ fontSize: '0.875rem', color: 'var(--color-text-primary)', flex: 1, fontWeight: a.molecule_name ? 600 : 400 }}>
                  {a.molecule_name || a.smiles.substring(0, 40) + '...'}
                </span>
                {a.target && <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>{a.target}</span>}
                {a.risk_level && (
                  <span className={`badge ${a.risk_level.includes('High') ? 'badge-danger' : a.risk_level.includes('Expert') ? 'badge-warning' : 'badge-success'}`}>
                    {a.risk_level.includes('High') ? 'High Risk' : a.risk_level.includes('Expert') ? 'Review' : 'Low Risk'}
                  </span>
                )}
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', flexShrink: 0 }}>
                  {a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
