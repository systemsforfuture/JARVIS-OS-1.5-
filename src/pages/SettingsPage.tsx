import { useState, useEffect } from "react";
import { api, clearToken } from "@/lib/api";

export default function SettingsPage() {
  const [keys, setKeys] = useState<any[]>([]);

  useEffect(() => {
    api('/api/keys').then(data => { if (Array.isArray(data)) setKeys(data); }).catch(() => {});
  }, []);

  const syncAll = async () => {
    await api('/api/agents/sync-all', { method: 'POST' }).catch(() => {});
  };

  const logout = () => {
    clearToken();
    window.location.reload();
  };

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-6">Einstellungen</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="text-sm font-medium text-muted-foreground mb-4">API Keys Status</div>
          {keys.length === 0 ? (
            <p className="text-[13px] text-muted-foreground">Keys werden über die .env Datei konfiguriert.</p>
          ) : (
            <div className="space-y-0">
              {keys.map((k, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                  <span className="text-[13px]">{k.service}</span>
                  <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${k.is_set ? 'bg-jarvis-success/15 text-jarvis-success' : 'bg-jarvis-warning/15 text-jarvis-warning'}`}>
                    {k.is_set ? 'gesetzt' : 'fehlt'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <div className="text-sm font-medium text-muted-foreground mb-4">System</div>
          <div className="text-sm text-muted-foreground leading-relaxed space-y-1">
            <div>Version: <span className="font-mono">v1.5.0</span></div>
            <div>Dashboard: <span className="font-mono">React + Vite</span></div>
            <div>Database: <span className="font-mono">PostgreSQL 16</span></div>
            <div>Cache: <span className="font-mono">Redis 7</span></div>
            <div>AI Router: <span className="font-mono">LiteLLM</span></div>
            <div>Agents: <span className="font-mono">OpenClaw</span></div>
            <div>Workflows: <span className="font-mono">N8N</span></div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <div className="text-sm font-medium text-muted-foreground mb-4">Aktionen</div>
          <div className="flex flex-col gap-2 mt-2">
            <button onClick={syncAll} className="text-sm text-muted-foreground border border-border px-4 py-2 rounded-lg hover:bg-jarvis-hover transition-colors">
              Alle Agents sync
            </button>
            <button onClick={logout} className="text-sm bg-jarvis-error text-white px-4 py-2 rounded-lg hover:opacity-90 transition-opacity">
              Abmelden
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
