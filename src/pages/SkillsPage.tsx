import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function SkillsPage() {
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api('/api/skills')
      .then(data => { if (Array.isArray(data)) setSkills(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-6">Skills Registry</h2>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-muted-foreground">Lade...</div>
        ) : skills.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-5xl opacity-50 mb-4">⚡</div>
            <div className="text-muted-foreground">Skills werden beim ersten Start registriert.</div>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-jarvis-elevated">
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Skill</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Kategorie</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Beschreibung</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">API Key</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody>
              {skills.map((s, i) => (
                <tr key={i} className="border-t border-border hover:bg-jarvis-hover transition-colors">
                  <td className="p-3 text-sm font-medium">{s.name}</td>
                  <td className="p-3"><span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">{s.category}</span></td>
                  <td className="p-3 text-sm text-muted-foreground">{s.description || ''}</td>
                  <td className="p-3 text-[11px] font-mono text-muted-foreground">{s.requires_key || '-'}</td>
                  <td className="p-3">
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${s.enabled ? 'bg-jarvis-success/15 text-jarvis-success' : 'bg-jarvis-error/15 text-jarvis-error'}`}>
                      {s.enabled ? 'aktiv' : 'inaktiv'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
