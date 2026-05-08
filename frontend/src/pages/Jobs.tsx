import { useEffect, useState, useCallback } from 'react';
import { getJobs, createJob, runJob, getJob, getConnections, getRules, queryJob, shareJob, getAuditLog } from '../services/api';
import type { MaskingJob, JobCreate, Connection, MaskingRule, JobStatus, AuditLogEntry } from '../types';
import type { ToastType } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';

interface Props { addToast: (msg: string, type?: ToastType) => void; }

const statusBadge: Record<JobStatus, string> = {
  pending:   'badge-pending',
  running:   'badge-warning',
  completed: 'badge-success',
  failed:    'badge-danger',
};

function formatDate(d: string | null) {
  if (!d) return '—';
  return new Date(d).toLocaleString();
}

export default function Jobs({ addToast }: Props) {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<MaskingJob[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [rules, setRules] = useState<MaskingRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedConn, setSelectedConn] = useState('');
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState<Set<string>>(new Set());
  
  // DDM Preview state
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState<Record<string, unknown>[]>([]);
  const [previewIsMasked, setPreviewIsMasked] = useState<boolean>(false);
  const [previewingJob, setPreviewingJob] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Share state
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareEmail, setShareEmail] = useState('');
  const [sharingJob, setSharingJob] = useState<MaskingJob | null>(null);
  const [sharing, setSharing] = useState(false);

  // Audit state
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditingJob, setAuditingJob] = useState<string | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [j, c, r] = await Promise.all([getJobs(), getConnections(), getRules()]);
      setJobs(j); setConnections(c); setRules(r);
    } catch { addToast('Could not load data', 'error'); }
    finally { setLoading(false); }
  }, [addToast]);

  useEffect(() => { load(); }, [load]);

  const getConnectionName = (id: string) =>
    connections.find(c => c.id === id)?.name ?? id.slice(0, 8) + '…';

  const toggleRule = (id: string) =>
    setSelectedRules(prev => prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]);

  const filteredRules = rules.filter(r => r.connection_id === selectedConn);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConn)            { addToast('Select a connection', 'error'); return; }
    if (selectedRules.length < 1) { addToast('Select at least one rule', 'error'); return; }
    setSaving(true);
    try {
      await createJob({ connection_id: selectedConn, rule_ids: selectedRules } as JobCreate);
      addToast('Job created', 'success');
      setShowModal(false);
      setSelectedConn(''); setSelectedRules([]);
      load();
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to create job', 'error');
    } finally { setSaving(false); }
  };

  const handleRun = async (job: MaskingJob) => {
    setRunning(prev => new Set(prev).add(job.id));
    try {
      await runJob(job.id);
      addToast('Job started in background', 'info');
      // Poll until status changes
      const poll = async () => {
        const updated = await getJob(job.id);
        setJobs(prev => prev.map(j => j.id === job.id ? updated : j));
        if (updated.status === 'running' || updated.status === 'pending') {
          setTimeout(poll, 2000);
        } else {
          setRunning(prev => { const s = new Set(prev); s.delete(job.id); return s; });
          if (updated.status === 'completed')
            addToast(`Job completed — ${updated.records_processed} records masked`, 'success');
          else if (updated.status === 'failed')
            addToast(`Job failed: ${updated.error_message}`, 'error');
        }
      };
      setTimeout(poll, 1500);
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to run job', 'error');
      setRunning(prev => { const s = new Set(prev); s.delete(job.id); return s; });
    }
  };

  const handlePreview = async (jobId: string) => {
    setPreviewingJob(jobId);
    setShowPreviewModal(true);
    setPreviewLoading(true);
    setPreviewData([]);
    setPreviewIsMasked(false);
    
    try {
      const response = await queryJob(jobId);
      setPreviewData(response.data || []);
      setPreviewIsMasked(response.is_masked);
      addToast(`Showing data (${response.is_masked ? 'Masked for normal user' : 'Unmasked for Owner/Admin'})`, 'info');
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to query data', 'error');
      setShowPreviewModal(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleShareSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sharingJob || !shareEmail) return;
    setSharing(true);
    try {
      await shareJob(sharingJob.id, shareEmail);
      addToast(`Job shared with ${shareEmail}`, 'success');
      setShareEmail('');
      setShowShareModal(false);
      load();
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to share job', 'error');
    } finally {
      setSharing(false);
    }
  };

  const handleShowAudit = async (jobId: string) => {
    setAuditingJob(jobId);
    setShowAuditModal(true);
    setAuditLoading(true);
    setAuditLogs([]);
    try {
      const logs = await getAuditLog(jobId);
      setAuditLogs(logs);
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to load audit logs', 'error');
      setShowAuditModal(false);
    } finally {
      setAuditLoading(false);
    }
  };

  return (
    <div className="page-content">
      <div className="card">
        <div className="card-header">
          <h2>Masking Jobs</h2>
          <button id="btn-add-job" className="btn btn-primary" onClick={() => setShowModal(true)}>
            + New Job
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">▶</div>
            <h3>No jobs yet</h3>
            <p>Create a job to apply masking rules to a database connection.</p>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>Create Job</button>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Connection</th>
                  <th>Rules</th>
                  <th>Status</th>
                  <th>Records</th>
                  <th>Started</th>
                  <th>Completed</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(j => (
                  <tr key={j.id}>
                    <td><span className="cell-primary">{getConnectionName(j.connection_id)}</span></td>
                    <td>{j.rule_ids.length} rule{j.rule_ids.length !== 1 ? 's' : ''}</td>
                    <td>
                      <span className={`badge ${statusBadge[j.status]}`}>
                        {j.status}
                      </span>
                    </td>
                    <td>{j.records_processed.toLocaleString()}</td>
                    <td style={{ fontSize: 12 }}>{formatDate(j.started_at)}</td>
                    <td style={{ fontSize: 12 }}>{formatDate(j.completed_at)}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          className="btn btn-secondary"
                          onClick={() => handlePreview(j.id)}
                          title="Query as normal user (Dynamic Data Masking)"
                        >
                          👁 Query DDM
                        </button>
                        {(user?.id === j.owner_id || user?.role === 'admin') && (
                          <>
                            <button
                              className="btn btn-secondary"
                              onClick={() => { setSharingJob(j); setShowShareModal(true); }}
                              title="Share with other users"
                            >
                              👥 Share
                            </button>
                            <button
                              className="btn btn-secondary"
                              onClick={() => handleShowAudit(j.id)}
                              title="View audit logs"
                            >
                              📋 Audit Log
                            </button>
                          </>
                        )}
                        {(j.status === 'pending' || j.status === 'failed') && (
                          <button
                            id={`btn-run-job-${j.id}`}
                            className="btn btn-success"
                            disabled={running.has(j.id)}
                            onClick={() => handleRun(j)}
                            title="Apply masks permanently to the database (Static Data Masking)"
                          >
                            {running.has(j.id) ? <><span className="spinner" /> Running…</> : '▶ Permanent SDM'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Masking Job</h2>
              <button className="modal-close" id="btn-close-job-modal" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="job-conn">Connection</label>
                  <select id="job-conn" value={selectedConn}
                    onChange={e => { setSelectedConn(e.target.value); setSelectedRules([]); }}>
                    <option value="">Select a connection…</option>
                    {connections.map(c => (
                      <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
                    ))}
                  </select>
                </div>

                {selectedConn && (
                  <div className="form-group">
                    <label>Select Rules</label>
                    {filteredRules.length === 0 ? (
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', padding: '8px 0' }}>
                        No rules for this connection. Create rules first.
                      </p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 200, overflowY: 'auto', padding: '4px 0' }}>
                        {filteredRules.map(r => (
                          <label key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 14, color: 'var(--text-secondary)' }}>
                            <input
                              type="checkbox"
                              id={`check-rule-${r.id}`}
                              checked={selectedRules.includes(r.id)}
                              onChange={() => toggleRule(r.id)}
                              style={{ accentColor: 'var(--color-accent)', width: 16, height: 16 }}
                            />
                            <span>
                              <strong style={{ color: 'var(--text-primary)' }}>{r.name}</strong>
                              &nbsp;·&nbsp;{r.target_table}.{r.target_column}
                            </span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" id="btn-submit-job" className="btn btn-primary" disabled={saving}>
                  {saving ? <><span className="spinner" />Creating…</> : 'Create Job'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showPreviewModal && previewingJob && (
        <div className="modal-overlay" onClick={() => setShowPreviewModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
            <div className="modal-header">
              <h2>Dynamic Query Preview</h2>
              <button className="modal-close" onClick={() => setShowPreviewModal(false)}>×</button>
            </div>
            <div style={{ padding: '0 24px' }}>
              <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
                <span className={`badge ${previewIsMasked ? 'badge-warning' : 'badge-success'}`}>
                  {previewIsMasked ? '🔒 Data is Masked (User)' : '🔓 Data is Unmasked (Owner/Admin)'}
                </span>
              </div>
              
              {previewLoading ? (
                <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></div>
              ) : previewData.length === 0 ? (
                <div className="empty-state">
                  <p>No records found.</p>
                </div>
              ) : (
                <div className="table-wrapper" style={{ maxHeight: '400px', overflow: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        {Object.keys(previewData[0]).map(k => (
                          <th key={k}>{k}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((v, j) => (
                            <td key={j}>{String(v)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowPreviewModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {showShareModal && sharingJob && (
        <div className="modal-overlay" onClick={() => setShowShareModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Share Job</h2>
              <button className="modal-close" onClick={() => setShowShareModal(false)}>×</button>
            </div>
            <form onSubmit={handleShareSubmit}>
              <div className="form-group" style={{ padding: '0 24px' }}>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>
                  Users you share this job with will be able to query it, but they will only see <strong>masked data</strong>.
                </p>
                <label>User Email</label>
                <input
                  type="email"
                  value={shareEmail}
                  onChange={e => setShareEmail(e.target.value)}
                  placeholder="user@example.com"
                  required
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowShareModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={sharing}>
                  {sharing ? <><span className="spinner" />Sharing…</> : 'Share'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAuditModal && auditingJob && (
        <div className="modal-overlay" onClick={() => setShowAuditModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
            <div className="modal-header">
              <h2>Audit Log</h2>
              <button className="modal-close" onClick={() => setShowAuditModal(false)}>×</button>
            </div>
            <div style={{ padding: '0 24px' }}>
              {auditLoading ? (
                <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></div>
              ) : auditLogs.length === 0 ? (
                <div className="empty-state">
                  <p>No queries have been made yet.</p>
                </div>
              ) : (
                <div className="table-wrapper" style={{ maxHeight: '400px', overflow: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>User Email</th>
                        <th>Role</th>
                        <th>Action</th>
                        <th>Data Masked?</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLogs.map(log => (
                        <tr key={log.id}>
                          <td>{formatDate(log.timestamp)}</td>
                          <td>{log.user_email}</td>
                          <td>{log.user_role}</td>
                          <td>{log.action}</td>
                          <td>
                            <span className={`badge ${log.is_masked ? 'badge-warning' : 'badge-success'}`}>
                              {log.is_masked ? 'Yes (Masked)' : 'No (Original)'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowAuditModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
