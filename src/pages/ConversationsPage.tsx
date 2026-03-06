import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AGENT_EMOJIS } from "@/lib/types";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMessages, setSelectedMessages] = useState<any[] | null>(null);

  useEffect(() => {
    api('/api/conversations?limit=30')
      .then(data => { if (Array.isArray(data)) setConversations(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const openConversation = async (id: string) => {
    try {
      const msgs = await api(`/api/conversations/${id}`);
      if (Array.isArray(msgs)) setSelectedMessages(msgs);
    } catch {}
  };

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-1">Conversations</h2>
      <p className="text-sm text-muted-foreground mb-6">Alle gespeicherten Gespräche — JARVIS vergisst nie</p>

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-muted-foreground">Lade...</div>
        ) : conversations.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-5xl opacity-50 mb-4">📝</div>
            <div className="text-muted-foreground">Noch keine Conversations gespeichert.</div>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-jarvis-elevated">
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Conversation</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Channel</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Agents</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Messages</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Start</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Letzte</th>
              </tr>
            </thead>
            <tbody>
              {conversations.map(c => (
                <tr key={c.conversation_id} className="border-t border-border hover:bg-jarvis-hover cursor-pointer transition-colors" onClick={() => openConversation(c.conversation_id)}>
                  <td className="p-3 text-xs font-mono">{(c.conversation_id || '').substring(0, 12)}...</td>
                  <td className="p-3"><span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">{c.channel || '-'}</span></td>
                  <td className="p-3 flex gap-1 flex-wrap">{(c.agents || []).filter(Boolean).map((a: string, i: number) => (
                    <span key={i} className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">{a}</span>
                  ))}</td>
                  <td className="p-3 text-sm font-mono">{c.message_count}</td>
                  <td className="p-3 text-xs font-mono text-muted-foreground">{c.started_at ? new Date(c.started_at).toLocaleString('de-DE') : '-'}</td>
                  <td className="p-3 text-xs font-mono text-muted-foreground">{c.last_message_at ? new Date(c.last_message_at).toLocaleString('de-DE') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Dialog open={!!selectedMessages} onOpenChange={() => setSelectedMessages(null)}>
        <DialogContent className="max-w-[700px] max-h-[85vh] overflow-y-auto bg-card border-border">
          <DialogHeader>
            <DialogTitle className="font-display text-2xl">Conversation</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 mt-4">
            {selectedMessages?.map((msg, i) => {
              const emoji = msg.role === 'user' ? '👤' : (AGENT_EMOJIS[msg.agent_slug] || '🤖');
              return (
                <div key={i} className="flex gap-3 py-2">
                  <div className="w-9 h-9 rounded-lg bg-jarvis-elevated flex items-center justify-center text-lg shrink-0">{emoji}</div>
                  <div className="flex-1">
                    <div className="text-[13px] font-semibold">{msg.role === 'user' ? 'USER' : (msg.agent_slug || 'JARVIS').toUpperCase()}</div>
                    <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                    <div className="text-[11px] text-muted-foreground/60 font-mono mt-1">
                      {msg.created_at ? new Date(msg.created_at).toLocaleString('de-DE') : ''}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
