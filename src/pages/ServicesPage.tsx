import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { ServiceStatus } from "@/lib/types";

const SERVICE_NAMES: Record<string, { label: string; icon: string }> = {
  database: { label: 'PostgreSQL', icon: '🗄️' },
  redis: { label: 'Redis Cache', icon: '⚡' },
  openclaw: { label: 'OpenClaw', icon: '🤖' },
  n8n: { label: 'N8N Workflows', icon: '🔄' },
  litellm: { label: 'LiteLLM Router', icon: '🧠' },
};

export default function ServicesPage() {
  const [services, setServices] = useState<Record<string, ServiceStatus>>({});
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api<Record<string, ServiceStatus>>('/api/system/services')
      .then(setServices)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const statusBadge = (status: string) => {
    const cls = status === 'ok' ? 'bg-jarvis-success/15 text-jarvis-success' :
                status === 'error' ? 'bg-jarvis-error/15 text-jarvis-error' :
                status === 'disabled' ? 'bg-primary/15 text-primary' :
                'bg-jarvis-warning/15 text-jarvis-warning';
    return <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${cls}`}>{status}</span>;
  };

  const dotCls = (status: string) =>
    status === 'ok' ? 'bg-jarvis-success' :
    status === 'error' ? 'bg-jarvis-error' :
    status === 'disabled' ? 'bg-muted-foreground' :
    'bg-jarvis-warning';

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-1">System Services</h2>
      <p className="text-sm text-muted-foreground mb-6">Status aller verbundenen Services</p>

      {loading ? (
        <div className="p-12 text-center text-muted-foreground">Lade...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 mb-6">
          {Object.entries(services).map(([key, svc]) => {
            const info = SERVICE_NAMES[key] || { label: key, icon: '⚙️' };
            const details: string[] = [];
            if (svc.version) details.push(`v${svc.version}`);
            if (svc.size_mb) details.push(`${svc.size_mb} MB`);
            if (svc.memory) details.push(svc.memory);
            if (svc.url) details.push(svc.url);

            return (
              <div key={key} className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-2 font-semibold text-[13px] mb-2">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${dotCls(svc.status)}`} />
                  <span>{info.icon} {info.label}</span>
                </div>
                <div className="mb-1">{statusBadge(svc.status)}</div>
                {details.length > 0 && (
                  <div className="text-xs text-muted-foreground font-mono">{details.join(' | ')}</div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <button onClick={load} className="text-sm text-muted-foreground border border-border px-3 py-1.5 rounded-lg hover:bg-jarvis-hover transition-colors">
        Aktualisieren
      </button>
    </div>
  );
}
