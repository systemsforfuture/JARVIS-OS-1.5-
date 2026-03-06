import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { Task } from "@/lib/types";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Task[]>('/api/tasks?limit=50')
      .then(data => { if (Array.isArray(data)) setTasks(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const statusBadge = (status: string) => {
    const cls = status === 'completed' ? 'bg-jarvis-success/15 text-jarvis-success' :
                status === 'pending' ? 'bg-jarvis-warning/15 text-jarvis-warning' :
                status === 'failed' ? 'bg-jarvis-error/15 text-jarvis-error' :
                'bg-primary/15 text-primary';
    return <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${cls}`}>{status}</span>;
  };

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-6">Tasks</h2>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-muted-foreground">Lade...</div>
        ) : tasks.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-5xl opacity-50 mb-4">✅</div>
            <div className="text-muted-foreground">Keine Tasks vorhanden</div>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-jarvis-elevated">
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Task</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Agent</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Prio</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tokens</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Erstellt</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map(t => (
                <tr key={t.id} className="border-t border-border hover:bg-jarvis-hover transition-colors">
                  <td className="p-3 text-sm">{t.title}</td>
                  <td className="p-3 text-sm text-muted-foreground">{t.agent_slug || '-'}</td>
                  <td className="p-3">{statusBadge(t.status)}</td>
                  <td className="p-3 text-sm">P{t.priority}</td>
                  <td className="p-3 text-xs font-mono text-muted-foreground">{t.tokens_used ? Number(t.tokens_used).toLocaleString() : '-'}</td>
                  <td className="p-3 text-xs font-mono text-muted-foreground">{t.created_at ? new Date(t.created_at).toLocaleDateString('de-DE') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
