import { useEffect, useState } from 'react';
import { getRules, createRule, deleteRule, getConnections } from '../services/api';
import type { MaskingRule, RuleCreate, Connection } from '../types';
import type { ToastType } from '../hooks/useToast';

interface Props { addToast: (msg: string, type?: ToastType) => void; }

const strategyLabels: Record<string, string> = {
  substitution: 'Substitution',
  hashing:      'Hashing (SHA-256)',
  redaction:    'Redaction',
  nullification:'Nullification',
  fpe:          'Format-Preserving Encryption (Pseudo)',
  perturbation: 'Data Perturbation (Variance)',
};

const defaultForm: RuleCreate = {
  name: '', connection_id: '', target_table: '',
  target_column: '', strategy: 'hashing', strategy_options: {}
};

export default function Rules({ addToast }: Props) {
  const [rules, setRules] = useState<MaskingRule[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<RuleCreate>(defaultForm);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [r, c] = await Promise.all([getRules(), getConnections()]);
      setRules(r); setConnections(c);
    } catch { addToast('Could not load data', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const getConnectionName = (id: string) =>
    connections.find(c => c.id === id)?.name ?? id.slice(0, 8) + '…';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await createRule(form);
      addToast('Rule created successfully', 'success');
      setShowModal(false);
      setForm(defaultForm);
      load();
    } catch (err: unknown) {
      addToast((err as Error).message ?? 'Failed to create rule', 'error');
    } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this rule?')) return;
    try {
      await deleteRule(id);
      addToast('Rule deleted', 'success');
      load();
    } catch { addToast('Failed to delete rule', 'error'); }
  };

  return (
    <div className="page-content">
      <div className="card">
        <div className="card-header">
          <h2>Masking Rules</h2>
          <button id="btn-add-rule" className="btn btn-primary" onClick={() => setShowModal(true)}>
            + New Rule
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></div>
        ) : rules.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">◉</div>
            <h3>No masking rules yet</h3>
            <p>Create a rule to define how a specific column should be masked.</p>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>Create Rule</button>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Connection</th>
                  <th>Table / Collection</th>
                  <th>Column</th>
                  <th>Strategy</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rules.map(r => (
                  <tr key={r.id}>
                    <td><span className="cell-primary">{r.name}</span></td>
                    <td>{getConnectionName(r.connection_id)}</td>
                    <td><code style={{ fontSize: 12, color: 'var(--color-accent-2)' }}>{r.target_table}</code></td>
                    <td><code style={{ fontSize: 12, color: 'var(--color-success)' }}>{r.target_column}</code></td>
                    <td>
                      <span className="badge badge-info">{strategyLabels[r.strategy] ?? r.strategy}</span>
                    </td>
                    <td>
                      <button className="btn btn-danger btn-icon" id={`btn-del-rule-${r.id}`}
                        onClick={() => handleDelete(r.id)} title="Delete rule">✕</button>
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
              <h2>New Masking Rule</h2>
              <button className="modal-close" id="btn-close-rule-modal" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="rule-name">Rule Name</label>
                  <input id="rule-name" required value={form.name}
                    onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                    placeholder="e.g. Mask email column" />
                </div>
                <div className="form-group">
                  <label htmlFor="rule-conn">Connection</label>
                  <select id="rule-conn" required value={form.connection_id}
                    onChange={e => setForm(p => ({ ...p, connection_id: e.target.value }))}>
                    <option value="">Select a connection…</option>
                    {connections.map(c => (
                      <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
                    ))}
                  </select>
                </div>
                <div className="form-grid form-grid-2">
                  <div className="form-group">
                    <label htmlFor="rule-table">Table / Collection</label>
                    <input id="rule-table" required value={form.target_table}
                      onChange={e => setForm(p => ({ ...p, target_table: e.target.value }))}
                      placeholder="users" />
                  </div>
                  <div className="form-group">
                    <label htmlFor="rule-column">Column / Field</label>
                    <input id="rule-column" required value={form.target_column}
                      onChange={e => setForm(p => ({ ...p, target_column: e.target.value }))}
                      placeholder="email" />
                  </div>
                </div>
                <div className="form-group">
                  <label htmlFor="rule-strategy">Masking Strategy</label>
                  <select id="rule-strategy" value={form.strategy}
                    onChange={e => setForm(p => ({ ...p, strategy: e.target.value as RuleCreate['strategy'] }))}>
                    {Object.entries(strategyLabels).map(([v, l]) => (
                      <option key={v} value={v}>{l}</option>
                    ))}
                  </select>
                </div>
                {form.strategy === 'substitution' && (
                  <div className="form-group">
                    <label htmlFor="rule-provider">Faker Provider</label>
                    <input id="rule-provider" placeholder="e.g. name, email, phone_number"
                      onChange={e => setForm(p => ({ ...p, strategy_options: { provider: e.target.value } }))} />
                  </div>
                )}
                {form.strategy === 'hashing' && (
                  <div className="form-group">
                    <label htmlFor="rule-salt">Salt (optional)</label>
                    <input id="rule-salt" placeholder="Optional salt for determinism"
                      onChange={e => setForm(p => ({ ...p, strategy_options: { salt: e.target.value } }))} />
                  </div>
                )}
                {form.strategy === 'fpe' && (
                  <div className="form-group">
                    <label htmlFor="rule-fpe-seed">FPE Seed</label>
                    <input id="rule-fpe-seed" placeholder="Optional seed for determinism"
                      onChange={e => setForm(p => ({ ...p, strategy_options: { seed: e.target.value } }))} />
                  </div>
                )}
                {form.strategy === 'perturbation' && (
                  <div className="form-grid form-grid-2">
                    <div className="form-group">
                      <label htmlFor="rule-pert-type">Variance Type</label>
                      <select id="rule-pert-type" value={form.strategy_options?.variance_type as string ?? 'percentage'}
                        onChange={e => setForm(p => ({ ...p, strategy_options: { ...p.strategy_options, variance_type: e.target.value } }))}>
                        <option value="percentage">Percentage</option>
                        <option value="days">Days</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label htmlFor="rule-pert-val">Variance Value (+/-)</label>
                      <input id="rule-pert-val" type="number" defaultValue={10} placeholder="e.g. 10"
                        onChange={e => setForm(p => ({ ...p, strategy_options: { ...p.strategy_options, variance_value: parseFloat(e.target.value) } }))} />
                    </div>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" id="btn-submit-rule" className="btn btn-primary" disabled={saving}>
                  {saving ? <><span className="spinner" />Saving…</> : 'Save Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
