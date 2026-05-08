import { useEffect, useState } from 'react';
import { getSummary } from '../services/api';
import type { Summary } from '../types';

interface StatItem {
  label: string;
  key: keyof Summary;
  icon: string;
  color: string;
}

const stats: StatItem[] = [
  { label: 'Connections',       key: 'total_connections',        icon: '⬡', color: 'rgba(99,102,241,0.15)' },
  { label: 'Masking Rules',     key: 'total_rules',              icon: '◉', color: 'rgba(34,211,165,0.12)' },
  { label: 'Jobs Run',          key: 'total_jobs',               icon: '▶', color: 'rgba(245,158,11,0.12)'  },
  { label: 'Records Masked',    key: 'total_records_processed',  icon: '🔒', color: 'rgba(244,63,94,0.12)'  },
];

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await getSummary();
      setSummary(data);
    } catch {
      // API might not be running yet; show zeros
      setSummary({ total_connections: 0, total_rules: 0, total_jobs: 0, total_records_processed: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="page-content">
      <div className="stats-grid">
        {stats.map(s => (
          <div key={s.key} className="stat-card">
            <div className="stat-icon" style={{ background: s.color }}>
              {s.icon}
            </div>
            <div className="stat-info">
              {loading
                ? <div className="spinner" />
                : <div className="stat-value">{summary?.[s.key] ?? 0}</div>
              }
              <div className="stat-label">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Getting Started</h2>
        </div>
        <ol style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 12, color: 'var(--text-secondary)', fontSize: 14 }}>
          <li><strong style={{ color: 'var(--text-primary)' }}>Add a Connection</strong> — Register your PostgreSQL or MongoDB database credentials.</li>
          <li><strong style={{ color: 'var(--text-primary)' }}>Create Masking Rules</strong> — Define which columns to mask and the masking strategy to apply.</li>
          <li><strong style={{ color: 'var(--text-primary)' }}>Run a Job</strong> — Create a job linking a connection + rules and trigger it. Watch records get masked in real-time.</li>
        </ol>
      </div>
    </div>
  );
}
