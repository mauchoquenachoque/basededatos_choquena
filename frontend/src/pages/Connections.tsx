import { useEffect, useState } from 'react';
import { getConnections, createConnection, deleteConnection, discoverPii, createRule } from '../services/api';
import type { Connection, ConnectionCreate, RuleCreate } from '../types';
import type { ToastType } from '../hooks/useToast';

interface Props {
  addToast: (msg: string, type?: ToastType) => void;
}

const defaultForm: ConnectionCreate = {
  name: '', type: 'postgres', host: 'localhost',
  port: 5432, database: '', username: '', password: ''
};

export default function Connections({ addToast }: Props) {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<ConnectionCreate>(defaultForm);
  const [saving, setSaving] = useState(false);

  // Discover PII state
  const [showDiscoverModal, setShowDiscoverModal] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [suggestions, setSuggestions] = useState<RuleCreate[]>([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState<number[]>([]);
  const [creatingSuggestions, setCreatingSuggestions] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setConnections(await getConnections()); }
    catch { addToast('Could not load connections', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleTypeChange = (t: ConnectionCreate['type']) => {
    let port = 5432;
    if (t === 'mongodb') port = 27017;
    if (t === 'mysql') port = 3306;
    setForm(prev => ({ ...prev, type: t, port }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await createConnection(form);
      addToast('Connection created successfully', 'success');
      setShowModal(false);
      setForm(defaultForm);
      load();
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to create connection', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Delete connection "${name}"?`)) return;
    try {
      await deleteConnection(id);
      addToast(`Connection "${name}" deleted`, 'success');
      load();
    } catch { addToast('Failed to delete connection', 'error'); }
  };

  const handleDiscover = async (id: string) => {
    setDiscovering(true);
    setShowDiscoverModal(true);
    setSuggestions([]);
    setSelectedSuggestions([]);
    try {
      const data = await discoverPii(id);
      setSuggestions(data);
      setSelectedSuggestions(data.map((_, idx) => idx)); // select all by default
      if (data.length === 0) {
        addToast('No PII columns detected', 'info');
      }
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Discovery failed', 'error');
      setShowDiscoverModal(false);
    } finally {
      setDiscovering(false);
    }
  };

  const toggleSuggestion = (idx: number) => {
    setSelectedSuggestions(prev => prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]);
  };

  const handleCreateSuggestions = async () => {
    setCreatingSuggestions(true);
    try {
      const selectedRules = selectedSuggestions.map(idx => suggestions[idx]);
      for (const rule of selectedRules) {
        await createRule(rule);
      }
      addToast(`${selectedRules.length} rules created successfully`, 'success');
      setShowDiscoverModal(false);
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to create rules', 'error');
    } finally {
      setCreatingSuggestions(false);
    }
  };

  return (
    <div className="page-content">
      <div className="card">
        <div className="card-header">
          <h2>Database Connections</h2>
          <button id="btn-add-connection" className="btn btn-primary" onClick={() => setShowModal(true)}>
            + Add Connection
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></div>
        ) : connections.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⬡</div>
            <h3>No connections yet</h3>
            <p>Add your first PostgreSQL or MongoDB connection to get started.</p>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>Add Connection</button>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Host</th>
                  <th>Database</th>
                  <th>Username</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {connections.map(c => (
                  <tr key={c.id}>
                    <td><span className="cell-primary">{c.name}</span></td>
                    <td>
                      <span className={`badge ${c.type === 'postgres' ? 'badge-info' : c.type === 'mysql' ? 'badge-warning' : 'badge-success'}`}>
                        {c.type === 'postgres' ? 'PostgreSQL' : c.type === 'mysql' ? 'MySQL' : 'MongoDB'}
                      </span>
                    </td>
                    <td>{c.host}:{c.port}</td>
                    <td>{c.database}</td>
                    <td>{c.username}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          className="btn btn-secondary btn-icon"
                          onClick={() => handleDiscover(c.id)}
                          title="Discover PII data"
                        >🔍</button>
                        <button
                          className="btn btn-danger btn-icon"
                          onClick={() => handleDelete(c.id, c.name)}
                          title="Delete connection"
                          id={`btn-delete-conn-${c.id}`}
                        >✕</button>
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
              <h2>New Connection</h2>
              <button className="modal-close" id="btn-close-conn-modal" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="conn-name">Connection Name</label>
                  <input id="conn-name" required value={form.name}
                    onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                    placeholder="e.g. Production DB" />
                </div>
                <div className="form-group">
                  <label htmlFor="conn-type">Database Type</label>
                  <select id="conn-type" value={form.type}
                    onChange={e => handleTypeChange(e.target.value as ConnectionCreate['type'])}>
                    <option value="postgres">PostgreSQL</option>
                    <option value="mysql">MySQL / MariaDB</option>
                    <option value="mongodb">MongoDB</option>
                  </select>
                </div>
                <div className="form-grid form-grid-2">
                  <div className="form-group">
                    <label htmlFor="conn-host">Host</label>
                    <input id="conn-host" required value={form.host}
                      onChange={e => setForm(p => ({ ...p, host: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label htmlFor="conn-port">Port</label>
                    <input id="conn-port" type="number" required value={form.port}
                      onChange={e => setForm(p => ({ ...p, port: Number(e.target.value) }))} />
                  </div>
                </div>
                <div className="form-group">
                  <label htmlFor="conn-database">Database Name</label>
                  <input id="conn-database" required value={form.database}
                    onChange={e => setForm(p => ({ ...p, database: e.target.value }))}
                    placeholder="mydb" />
                </div>
                <div className="form-grid form-grid-2">
                  <div className="form-group">
                    <label htmlFor="conn-user">Username</label>
                    <input id="conn-user" required value={form.username}
                      onChange={e => setForm(p => ({ ...p, username: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label htmlFor="conn-pass">Password</label>
                    <input id="conn-pass" type="password" required value={form.password}
                      onChange={e => setForm(p => ({ ...p, password: e.target.value }))} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" id="btn-submit-connection" className="btn btn-primary" disabled={saving}>
                  {saving ? <><span className="spinner" />Saving…</> : 'Save Connection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showDiscoverModal && (
        <div className="modal-overlay" onClick={() => setShowDiscoverModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
            <div className="modal-header">
              <h2>Discover PII</h2>
              <button className="modal-close" onClick={() => setShowDiscoverModal(false)}>×</button>
            </div>
            <div style={{ padding: '0 24px' }}>
              {discovering ? (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <div className="spinner" style={{ margin: '0 auto' }} />
                  <p style={{ marginTop: 16 }}>Scanning schema for sensitive data...</p>
                </div>
              ) : suggestions.length === 0 ? (
                <div className="empty-state">
                  <p>No PII columns detected in this connection.</p>
                </div>
              ) : (
                <>
                  <p style={{ marginBottom: 16 }}>We found {suggestions.length} columns that might contain sensitive data. Select the ones you want to create masking rules for.</p>
                  <div className="table-wrapper" style={{ maxHeight: '400px', overflow: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th style={{ width: 40 }}></th>
                          <th>Table</th>
                          <th>Column</th>
                          <th>Suggested Strategy</th>
                        </tr>
                      </thead>
                      <tbody>
                        {suggestions.map((s, idx) => (
                          <tr key={idx}>
                            <td>
                              <input 
                                type="checkbox" 
                                checked={selectedSuggestions.includes(idx)} 
                                onChange={() => toggleSuggestion(idx)} 
                                style={{ accentColor: 'var(--color-accent)', width: 16, height: 16 }}
                              />
                            </td>
                            <td>{s.target_table}</td>
                            <td><strong>{s.target_column}</strong></td>
                            <td><span className="badge badge-info">{s.strategy}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDiscoverModal(false)}>Close</button>
              {!discovering && suggestions.length > 0 && (
                <button 
                  className="btn btn-primary" 
                  onClick={handleCreateSuggestions}
                  disabled={selectedSuggestions.length === 0 || creatingSuggestions}
                >
                  {creatingSuggestions ? <><span className="spinner" />Creating…</> : `Create ${selectedSuggestions.length} Rules`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
