import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { StatCard } from "@/components/StatCard";

export default function LearningPage() {
  const [stats, setStats] = useState<any>(null);
  const [journal, setJournal] = useState<any[]>([]);
  const [improvements, setImprovements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api('/api/learning/stats').catch(() => null),
      api('/api/learning/journal?limit=20').catch(() => []),
      api('/api/improvements?limit=20').catch(() => []),
    ]).then(([s, j, imp]) => {
      setStats(s);
      if (Array.isArray(j)) setJournal(j);
      if (Array.isArray(imp)) setImprovements(imp);
    }).finally(() => setLoading(false));
  }, []);

  const eventColors: Record<string, string> = {
    success: 'bg-jarvis-success/15 text-jarvis-success',
    failure: 'bg-jarvis-error/15 text-jarvis-error',
    correction: 'bg-jarvis-warning/15 text-jarvis-warning',
    discovery: 'bg-primary/15 text-primary',
    optimization: 'bg-jarvis-purple/15 text-jarvis-purple',
    pattern_found: 'bg-jarvis-purple/15 text-jarvis-purple',
    skill_learned: 'bg-jarvis-success/15 text-jarvis-success',
  };

  const reviewImprovement = async (id: string, status: string) => {
    await api(`/api/improvements/${id}`, { method: 'PATCH', body: { status } }).catch(() => {});
    setImprovements(prev => prev.map(imp => imp.id === id ? { ...imp, status } : imp));
  };

  const journalTypes = stats?.journal_by_type || [];
  const totalLearnings = journalTypes.reduce((s: number, j: any) => s + parseInt(j.count || 0), 0);
  const avgImpact = journalTypes.length ? (journalTypes.reduce((s: number, j: any) => s + parseFloat(j.avg_impact || 0), 0) / journalTypes.length).toFixed(2) : '0';
  const pendingCount = (stats?.improvements || []).find((i: any) => i.status === 'pending')?.count || 0;

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-1">Self-Learning & Improvement</h2>
      <p className="text-sm text-muted-foreground mb-6">JARVIS lernt aus jedem Task und verbessert sich automatisch</p>

      {loading ? (
        <div className="p-12 text-center text-muted-foreground">Lade...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard title="Total Learnings" value={totalLearnings} colorClass="text-primary" />
            <StatCard title="Avg Impact Score" value={avgImpact} colorClass="text-jarvis-success" />
            <StatCard title="Pending Improvements" value={pendingCount} colorClass="text-jarvis-warning" />
            <StatCard title="Pattern Types" value={(stats?.patterns || []).length} colorClass="text-jarvis-purple" />
          </div>

          <h3 className="text-lg font-semibold mb-4">Learning Journal</h3>
          <div className="bg-card border border-border rounded-lg overflow-hidden mb-8">
            {journal.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">Learning Journal wird nach den ersten Tasks gefüllt.</div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="bg-jarvis-elevated">
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Agent</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Event</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Description</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Impact</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Datum</th>
                  </tr>
                </thead>
                <tbody>
                  {journal.map((j, i) => (
                    <tr key={i} className="border-t border-border hover:bg-jarvis-hover">
                      <td className="p-3 text-sm">{j.agent_slug || '-'}</td>
                      <td className="p-3"><span className={`text-[11px] font-medium px-2 py-0.5 rounded ${eventColors[j.event_type] || 'bg-primary/15 text-primary'}`}>{j.event_type}</span></td>
                      <td className="p-3 text-sm text-muted-foreground max-w-[400px] truncate">{j.description || ''}</td>
                      <td className="p-3 text-sm font-mono">{j.impact_score ? parseFloat(j.impact_score).toFixed(2) : '-'}</td>
                      <td className="p-3 text-xs font-mono text-muted-foreground">{j.created_at ? new Date(j.created_at).toLocaleString('de-DE') : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <h3 className="text-lg font-semibold mb-4">Improvement Queue</h3>
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            {improvements.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">Improvement-Vorschläge erscheinen nach ca. 50 Tasks.</div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="bg-jarvis-elevated">
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Typ</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Beschreibung</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Risiko</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Status</th>
                    <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Aktion</th>
                  </tr>
                </thead>
                <tbody>
                  {improvements.map((imp, i) => (
                    <tr key={i} className="border-t border-border hover:bg-jarvis-hover">
                      <td className="p-3"><span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">{imp.improvement_type || imp.type || '-'}</span></td>
                      <td className="p-3 text-sm text-muted-foreground max-w-[400px] truncate">{imp.description || ''}</td>
                      <td className="p-3">
                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${imp.risk_level === 'low' ? 'bg-jarvis-success/15 text-jarvis-success' : imp.risk_level === 'medium' ? 'bg-jarvis-warning/15 text-jarvis-warning' : 'bg-jarvis-error/15 text-jarvis-error'}`}>
                          {imp.risk_level || '-'}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${imp.status === 'applied' ? 'bg-jarvis-success/15 text-jarvis-success' : imp.status === 'pending' ? 'bg-jarvis-warning/15 text-jarvis-warning' : imp.status === 'rejected' ? 'bg-jarvis-error/15 text-jarvis-error' : 'bg-primary/15 text-primary'}`}>
                          {imp.status}
                        </span>
                      </td>
                      <td className="p-3">
                        {imp.status === 'pending' ? (
                          <div className="flex gap-2">
                            <button onClick={() => reviewImprovement(imp.id, 'approved')} className="bg-jarvis-success text-white px-2 py-1 rounded text-xs hover:opacity-90">Approve</button>
                            <button onClick={() => reviewImprovement(imp.id, 'rejected')} className="bg-jarvis-error text-white px-2 py-1 rounded text-xs hover:opacity-90">Reject</button>
                          </div>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
