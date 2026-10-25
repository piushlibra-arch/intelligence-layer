import React, { useState, useEffect } from 'react';
import { ShieldAlert, Filter, History } from 'lucide-react';
import { getAuditRecords, getSessions, getInterventions } from '../api/client';
import type { InterventionDecision } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { formatDate } from '../utils/format';
import './InterventionHistory.css';

export const InterventionHistory: React.FC = () => {
  const [decisions, setDecisions] = useState<InterventionDecision[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'decisions' | 'audit'>('decisions');

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true);
        // Load sessions to fetch their interventions
        const sessionsRes = await getSessions();
        const allDecisions: InterventionDecision[] = [];

        // Fetch interventions for available sessions
        for (const s of sessionsRes.data.slice(0, 10)) {
          try {
            const intRes = await getInterventions(s.id);
            allDecisions.push(...intRes.data);
          } catch {
            // ignore
          }
        }

        // Fetch audit logs
        const auditRes = await getAuditRecords();

        setDecisions(allDecisions.sort((a, b) => new Date(b.decided_at).getTime() - new Date(a.decided_at).getTime()));
        setAuditLogs(auditRes.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch intervention history');
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  if (loading) return <LoadingSpinner message="Loading intervention records and audit trails..." />;
  if (error) return <ErrorDisplay message={error} />;

  const filteredDecisions = decisions.filter((d) => {
    if (selectedFilter === 'all') return true;
    return d.action_type === selectedFilter;
  });

  return (
    <div className="interventions-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Intervention & Audit Trails</h1>
          <p className="page-subtitle">
            Immutable records of every automated behavioural assessment, recommended action, and decision justification.
          </p>
        </div>

        <div className="view-toggle-strip">
          <button
            className={`toggle-btn ${activeTab === 'decisions' ? 'toggle-btn--active' : ''}`}
            onClick={() => setActiveTab('decisions')}
          >
            <ShieldAlert size={16} />
            <span>Intervention Decisions ({decisions.length})</span>
          </button>
          <button
            className={`toggle-btn ${activeTab === 'audit' ? 'toggle-btn--active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <History size={16} />
            <span>System Audit Records ({auditLogs.length})</span>
          </button>
        </div>
      </div>

      {activeTab === 'decisions' ? (
        <div className="card">
          <div className="card-header">
            <div className="filter-group">
              <Filter size={16} className="filter-icon" />
              <label>Filter by Action:</label>
              <select
                value={selectedFilter}
                onChange={(e) => setSelectedFilter(e.target.value)}
                className="filter-select"
              >
                <option value="all">All Actions</option>
                <option value="cooldown_offer">Voluntary Cooldown</option>
                <option value="warning">Advisory Warning</option>
                <option value="review_recommendation">Plan Review</option>
                <option value="session_protection_simulation">Protection Simulation</option>
                <option value="monitor">Active Monitor</option>
              </select>
            </div>
            <span className="card-tag">Shadow Mode Simulated</span>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action Type</th>
                  <th>Recommendation Headline</th>
                  <th>Justification / Reason</th>
                  <th>Status</th>
                  <th>Engine</th>
                </tr>
              </thead>
              <tbody>
                {filteredDecisions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-6 text-muted">
                      No intervention decisions recorded yet. Replay a scenario to generate decisions.
                    </td>
                  </tr>
                ) : (
                  filteredDecisions.map((dec) => (
                    <tr key={dec.id}>
                      <td className="font-mono text-xs">{formatDate(dec.decided_at)}</td>
                      <td>
                        <StatusBadge type="action" value={dec.action_type} />
                      </td>
                      <td>
                        <strong>{dec.action_details?.headline as string || 'Advisory'}</strong>
                      </td>
                      <td className="text-secondary text-sm">
                        {dec.action_details?.reason as string || dec.action_details?.message as string || ''}
                      </td>
                      <td>
                        <span className="sim-pill">Simulated</span>
                      </td>
                      <td className="font-mono text-xs">v{dec.engine_version}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-header">
            <h3>Event & Decision Audit Trail</h3>
            <span className="card-tag font-mono">Immutable</span>
          </div>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Entity Type</th>
                  <th>Entity ID</th>
                  <th>Action</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-6 text-muted">
                      No audit records found.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td className="font-mono text-xs">{formatDate(log.timestamp)}</td>
                      <td>
                        <span className="entity-badge">{log.entity_type}</span>
                      </td>
                      <td className="font-mono text-xs text-muted">{log.entity_id}</td>
                      <td>
                        <span className="action-badge">{log.action}</span>
                      </td>
                      <td className="font-mono text-xs">
                        {JSON.stringify(log.details)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
