export default function OmiPage() {
  const webhookBase = window.location.origin;

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-1">OMI Wearable Integration</h2>
      <p className="text-sm text-muted-foreground mb-6">Verbinde dein OMI Wearable Device mit JARVIS</p>

      <div className="space-y-4 max-w-2xl">
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="font-semibold text-sm mb-2">1. OMI App installieren</div>
          <p className="text-[13px] text-muted-foreground">Lade die OMI App herunter und erstelle ein Konto.</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <div className="font-semibold text-sm mb-3">2. Webhook URLs eintragen</div>
          <p className="text-[13px] text-muted-foreground mb-4">Kopiere diese URLs in die OMI App unter Settings → Webhooks:</p>
          <div className="space-y-3">
            {[
              { label: 'Memory Webhook', path: '/omi/memory' },
              { label: 'Transcript Webhook', path: '/omi/transcript' },
              { label: 'Audio Webhook (optional)', path: '/omi/audio' },
              { label: 'Chat Tools Manifest', path: '/.well-known/omi-tools.json' },
              { label: 'Setup Status URL', path: '/omi/setup-status' },
            ].map(({ label, path }) => (
              <div key={path}>
                <label className="text-xs text-muted-foreground">{label}</label>
                <input
                  className="w-full bg-jarvis-elevated border border-border rounded-lg px-3 py-2 text-sm font-mono text-foreground outline-none cursor-pointer"
                  readOnly
                  value={`${webhookBase}${path}`}
                  onClick={(e) => { (e.target as HTMLInputElement).select(); navigator.clipboard?.writeText(`${webhookBase}${path}`); }}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <div className="font-semibold text-sm mb-2">3. Triggers aktivieren</div>
          <p className="text-[13px] text-muted-foreground">Aktiviere in der OMI App: Memory Creation, Real-time Transcript, und Chat Tools.</p>
        </div>

        <div className="border border-primary/30 rounded-lg p-4 bg-primary/5">
          <div className="text-[13px] text-primary font-semibold">Was passiert dann?</div>
          <p className="text-[13px] text-muted-foreground mt-1">
            Alles was du sagst und hörst wird automatisch in JARVIS verarbeitet:
            Kontakte, Geburtstage, Termine, Entscheidungen, Ideen — alles wird gespeichert.
            Sprich einfach "Hey JARVIS" und dein Befehl wird ausgeführt.
          </p>
        </div>
      </div>
    </div>
  );
}
