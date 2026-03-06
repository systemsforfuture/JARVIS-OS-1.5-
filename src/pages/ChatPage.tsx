import { useState, useRef, useEffect } from "react";
import { AGENT_EMOJIS } from "@/lib/types";
import { sendWSMessage, onWSMessage } from "@/lib/api";

interface ChatMessage {
  agent: string;
  content: string;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { agent: 'jarvis', content: 'JARVIS 1.5 bereit. Alle 10 Agents aktiv. Wie kann ich helfen?', timestamp: new Date().toISOString() },
  ]);
  const [input, setInput] = useState('');
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsub = onWSMessage((data) => {
      if (data.type === 'chat') {
        setMessages(prev => [...prev, data]);
      }
    });
    return unsub;
  }, []);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = () => {
    if (!input.trim()) return;
    const msg: ChatMessage = { agent: 'DOM', content: input, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, msg]);
    sendWSMessage({ type: 'chat', content: input });
    setInput('');
  };

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-6">Chat mit JARVIS</h2>
      <div className="flex flex-col" style={{ height: 'calc(100vh - 200px)', maxHeight: '800px' }}>
        <div className="flex-1 overflow-y-auto space-y-3 pb-4">
          {messages.map((msg, i) => {
            const emoji = msg.agent === 'DOM' ? '👤' : (AGENT_EMOJIS[msg.agent] || '🤖');
            const time = new Date(msg.timestamp).toLocaleTimeString('de-DE');
            return (
              <div key={i} className="flex gap-3 py-3">
                <div className="w-9 h-9 rounded-lg bg-jarvis-elevated flex items-center justify-center text-lg shrink-0">
                  {emoji}
                </div>
                <div className="flex-1">
                  <div className="text-[13px] font-semibold mb-1">{(msg.agent || 'SYSTEM').toUpperCase()}</div>
                  <div className="text-sm text-muted-foreground leading-relaxed">{msg.content}</div>
                  <div className="text-[11px] text-muted-foreground/60 font-mono mt-1">{time}</div>
                </div>
              </div>
            );
          })}
          <div ref={messagesEnd} />
        </div>

        <div className="flex gap-2 pt-4 border-t border-border">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="Nachricht an JARVIS... (@agent für Delegation)"
            className="flex-1 bg-card border border-border rounded-lg px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
          />
          <button onClick={send} className="bg-primary text-primary-foreground px-5 py-3 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
            Senden
          </button>
        </div>
      </div>
    </div>
  );
}
