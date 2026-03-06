import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { MemoryEntry } from "@/lib/types";

const FILTERS = ['', 'fact', 'decision', 'preference'] as const;
const LABELS: Record<string, string> = { '': 'Alle', fact: 'Facts', decision: 'Decisions', preference: 'Preferences' };

export default function MemoryPage() {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const url = filter ? `/api/memory?type=${filter}&limit=50` : '/api/memory?limit=50';
    api<MemoryEntry[]>(url)
      .then(data => { if (Array.isArray(data)) setEntries(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-6">Agent Memory & Knowledge</h2>

      <div className="flex gap-2 mb-4">
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${filter === f ? 'bg-primary text-primary-foreground' : 'text-muted-foreground border border-border hover:bg-jarvis-hover'}`}
          >
            {LABELS[f]}
          </button>
        ))}
      </div>

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-muted-foreground">Lade...</div>
        ) : entries.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-5xl opacity-50 mb-4">🧠</div>
            <div className="text-muted-foreground">Noch keine Memory-Einträge. Agents speichern automatisch wichtige Fakten.</div>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-jarvis-elevated">
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Agent</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Typ</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Key</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Value</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Datum</th>
              </tr>
            </thead>
            <tbody>
              {entries.map(m => (
                <tr key={m.id} className="border-t border-border hover:bg-jarvis-hover transition-colors">
                  <td className="p-3 text-sm">{m.agent_slug}</td>
                  <td className="p-3"><span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">{m.type}</span></td>
                  <td className="p-3 text-sm font-medium">{m.key || ''}</td>
                  <td className="p-3 text-sm text-muted-foreground max-w-[300px] truncate">{m.value}</td>
                  <td className="p-3 text-xs font-mono text-muted-foreground">{m.created_at ? new Date(m.created_at).toLocaleDateString('de-DE') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
