import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface OnboardingData {
  company_name: string;
  company_domain: string;
  language: string;
  social_accounts: Record<string, string>;
  api_keys: Record<string, string>;
  model_config: Record<string, string>;
  integrations: Record<string, string>;
  telegram_config: Record<string, string>;
}

const defaultData: OnboardingData = {
  company_name: '', company_domain: '', language: 'de',
  social_accounts: {}, api_keys: {}, model_config: {}, integrations: {}, telegram_config: {},
};

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<OnboardingData>(defaultData);

  useEffect(() => {
    api('/api/onboarding/status').then(status => {
      setData({
        company_name: status?.company?.name || '',
        company_domain: status?.company?.domain || '',
        language: status?.company?.language || 'de',
        social_accounts: status?.social || {},
        api_keys: status?.apis || {},
        model_config: status?.models || {},
        integrations: status?.integrations || {},
        telegram_config: status?.telegram || {},
      });
    }).catch(() => {});
  }, []);

  const update = (field: string, value: any) => setData(prev => ({ ...prev, [field]: value }));
  const updateNested = (field: string, key: string, value: string) =>
    setData(prev => ({ ...prev, [field]: { ...(prev as any)[field], [key]: value } }));

  const save = async () => {
    try {
      await api('/api/onboarding/save', { method: 'POST', body: data });
    } catch {}
  };

  const inputCls = "w-full bg-jarvis-elevated border border-border rounded-lg px-3 py-2.5 text-sm font-mono text-foreground outline-none focus:border-primary transition-colors";

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-1">Setup Wizard</h2>
      <p className="text-sm text-muted-foreground mb-6">Verbinde deine Accounts, APIs und Services — alles an einem Ort.</p>

      <div className="flex gap-2 mb-6 flex-wrap">
        {[
          { n: 1, label: '1. Firma' },
          { n: 2, label: '2. Social Media' },
          { n: 3, label: '3. API Keys' },
          { n: 4, label: '4. AI Modelle' },
          { n: 5, label: '5. Integrationen' },
          { n: 6, label: '6. Telegram' },
        ].map(s => (
          <button
            key={s.n}
            onClick={() => setStep(s.n)}
            className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${step === s.n ? 'border-primary text-primary' : 'border-border text-muted-foreground hover:bg-jarvis-hover'}`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="bg-card border border-border rounded-lg p-6 max-w-[600px]">
        {step === 1 && (
          <div className="space-y-4">
            <div className="text-sm font-medium text-muted-foreground mb-4">Firmendaten</div>
            <div>
              <label className="text-[13px] text-muted-foreground block mb-1">Firmenname</label>
              <input className={inputCls} value={data.company_name} onChange={e => update('company_name', e.target.value)} placeholder="SYSTEMS™" />
            </div>
            <div>
              <label className="text-[13px] text-muted-foreground block mb-1">Domain</label>
              <input className={inputCls} value={data.company_domain} onChange={e => update('company_domain', e.target.value)} placeholder="architectofscale.com" />
            </div>
            <div>
              <label className="text-[13px] text-muted-foreground block mb-1">Sprache</label>
              <select className={inputCls} value={data.language} onChange={e => update('language', e.target.value)}>
                <option value="de">Deutsch</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <div className="text-sm font-medium text-muted-foreground mb-4">Social Media Accounts</div>
            {[
              { key: 'instagram', label: 'Instagram', ph: '@username' },
              { key: 'linkedin', label: 'LinkedIn', ph: 'Company Page URL' },
              { key: 'twitter', label: 'Twitter / X', ph: '@handle' },
              { key: 'facebook', label: 'Facebook', ph: 'Page URL' },
              { key: 'tiktok', label: 'TikTok', ph: '@username' },
              { key: 'youtube', label: 'YouTube', ph: 'Channel URL' },
            ].map(s => (
              <div key={s.key} className="flex items-center gap-3">
                <label className="text-[13px] text-muted-foreground w-24">{s.label}</label>
                <input className={`${inputCls} flex-1`} value={data.social_accounts[s.key] || ''} onChange={e => updateNested('social_accounts', s.key, e.target.value)} placeholder={s.ph} />
              </div>
            ))}
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <div className="text-sm font-medium text-muted-foreground mb-1">API Keys</div>
            <p className="text-[13px] text-muted-foreground mb-4">Deine API Keys werden sicher in der .env gespeichert.</p>
            {[
              { key: 'anthropic', label: 'Anthropic', ph: 'sk-ant-...' },
              { key: 'openai', label: 'OpenAI', ph: 'sk-...' },
              { key: 'groq', label: 'Groq', ph: 'gsk_...' },
              { key: 'hubspot', label: 'HubSpot', ph: 'pat-...' },
              { key: 'airtable', label: 'Airtable', ph: 'pat...' },
              { key: 'postiz', label: 'Postiz', ph: 'API Key' },
            ].map(a => (
              <div key={a.key} className="flex items-center gap-3">
                <label className="text-[13px] text-muted-foreground w-28">{a.label}</label>
                <input type="password" className={`${inputCls} flex-1`} value={data.api_keys[a.key] || ''} onChange={e => updateNested('api_keys', a.key, e.target.value)} placeholder={a.ph} />
              </div>
            ))}
          </div>
        )}

        {step === 4 && (
          <div className="space-y-3">
            <div className="text-sm font-medium text-muted-foreground mb-1">AI Modell-Konfiguration</div>
            <p className="text-[13px] text-muted-foreground mb-4">Smart Routing: Boss + Leader auf Sonnet, Worker auf Ollama (kostenlos).</p>
            {[
              { key: 'sonnet', label: 'Sonnet Model', ph: 'claude-sonnet-4-20250514' },
              { key: 'haiku', label: 'Haiku Model', ph: 'claude-haiku-4-5-20251001' },
              { key: 'ollama', label: 'Ollama Model', ph: 'llama3.1:8b' },
              { key: 'groq', label: 'Groq Model', ph: 'llama-3.1-70b-versatile' },
              { key: 'ollama_url', label: 'Ollama URL', ph: 'http://host.docker.internal:11434' },
            ].map(m => (
              <div key={m.key} className="flex items-center gap-3">
                <label className="text-[13px] text-muted-foreground w-32">{m.label}</label>
                <input className={`${inputCls} flex-1`} value={data.model_config[m.key] || ''} onChange={e => updateNested('model_config', m.key, e.target.value)} placeholder={m.ph} />
              </div>
            ))}
          </div>
        )}

        {step === 5 && (
          <div className="space-y-3">
            <div className="text-sm font-medium text-muted-foreground mb-1">Service-Integrationen</div>
            <p className="text-[13px] text-muted-foreground mb-4">URLs der Services auf deinem VPS.</p>
            {[
              { key: 'openclaw_url', label: 'OpenClaw URL', ph: 'http://localhost:8080' },
              { key: 'n8n_url', label: 'N8N URL', ph: 'http://localhost:5678' },
              { key: 'postiz_url', label: 'Postiz URL', ph: 'http://localhost:4200' },
              { key: 'litellm_url', label: 'LiteLLM URL', ph: 'http://jarvis-litellm:4000' },
            ].map(i => (
              <div key={i.key} className="flex items-center gap-3">
                <label className="text-[13px] text-muted-foreground w-28">{i.label}</label>
                <input className={`${inputCls} flex-1`} value={data.integrations[i.key] || ''} onChange={e => updateNested('integrations', i.key, e.target.value)} placeholder={i.ph} />
              </div>
            ))}
          </div>
        )}

        {step === 6 && (
          <div className="space-y-3">
            <div className="text-sm font-medium text-muted-foreground mb-1">Telegram Konfiguration</div>
            <p className="text-[13px] text-muted-foreground mb-4">Verbinde Telegram um mit deinem Team zu kommunizieren.</p>
            {[
              { key: 'bot_token', label: 'Bot Token', ph: '123456:ABC-DEF...', type: 'password' },
              { key: 'chat_id', label: 'Chat ID', ph: '-100...' },
              { key: 'group_id', label: 'Group ID', ph: '-100... (optional)' },
            ].map(t => (
              <div key={t.key} className="flex items-center gap-3">
                <label className="text-[13px] text-muted-foreground w-28">{t.label}</label>
                <input type={t.type || 'text'} className={`${inputCls} flex-1`} value={data.telegram_config[t.key] || ''} onChange={e => updateNested('telegram_config', t.key, e.target.value)} placeholder={t.ph} />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-3 mt-5">
        {step > 1 && (
          <button onClick={() => setStep(step - 1)} className="text-sm text-muted-foreground border border-border px-4 py-2 rounded-lg hover:bg-jarvis-hover transition-colors">
            Zurück
          </button>
        )}
        {step < 6 ? (
          <button onClick={() => setStep(step + 1)} className="text-sm bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:opacity-90 transition-opacity">
            Weiter
          </button>
        ) : (
          <button onClick={save} className="text-sm bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:opacity-90 transition-opacity">
            Speichern & Aktivieren
          </button>
        )}
      </div>
    </div>
  );
}
