import { useState, useEffect } from "react";
import { AGENT_DEFAULTS } from "@/lib/types";
import { api } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { AgentCard } from "@/components/AgentCard";
import { useNavigate } from "react-router-dom";
import { Bot, CheckSquare, Brain, MessageSquare, Zap, Coins, ArrowRight, Send } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const LIVE_EVENTS = [
  { agent: "ELON", action: "Analyse abgeschlossen", detail: "Q1 Revenue Report", time: "vor 2m" },
  { agent: "STEVE", action: "Content erstellt", detail: "LinkedIn Post Draft", time: "vor 5m" },
  { agent: "ARCHI", action: "Deployment erfolgreich", detail: "v1.5.2 → Production", time: "vor 8m" },
  { agent: "DONALD", action: "Lead qualifiziert", detail: "Enterprise-Anfrage #847", time: "vor 12m" },
  { agent: "DONNA", action: "Report generiert", detail: "Weekly Ops Summary", time: "vor 15m" },
  { agent: "JARVIS", action: "Optimierung gefunden", detail: "Prompt-Effizienz +12%", time: "vor 18m" },
  { agent: "IRIS", action: "Design Review", detail: "Landing Page v3", time: "vor 22m" },
  { agent: "FELIX", action: "Ticket gelöst", detail: "Support #1203", time: "vor 25m" },
];

function JarvisOrb() {
  return (
    <div className="relative w-28 h-28 flex items-center justify-center">
      {/* Outer glow rings */}
      <motion.div
        className="absolute inset-0 rounded-full border border-primary/20"
        animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.1, 0.3] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute inset-2 rounded-full border border-primary/25"
        animate={{ scale: [1, 1.1, 1], opacity: [0.4, 0.15, 0.4] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
      />
      <motion.div
        className="absolute inset-4 rounded-full border border-primary/30"
        animate={{ scale: [1, 1.08, 1], opacity: [0.5, 0.2, 0.5] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 1 }}
      />

      {/* Core orb */}
      <motion.div
        className="relative w-16 h-16 rounded-full flex items-center justify-center"
        style={{
          background: 'radial-gradient(circle at 40% 35%, hsl(199 89% 60% / 0.4), hsl(199 89% 48% / 0.15) 60%, transparent 80%)',
          boxShadow: '0 0 40px 10px hsl(199 89% 48% / 0.15), inset 0 0 20px hsl(199 89% 60% / 0.1)',
        }}
        animate={{
          boxShadow: [
            '0 0 40px 10px hsl(199 89% 48% / 0.15), inset 0 0 20px hsl(199 89% 60% / 0.1)',
            '0 0 60px 15px hsl(199 89% 48% / 0.25), inset 0 0 30px hsl(199 89% 60% / 0.15)',
            '0 0 40px 10px hsl(199 89% 48% / 0.15), inset 0 0 20px hsl(199 89% 60% / 0.1)',
          ],
        }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      >
        {/* Inner light */}
        <motion.div
          className="w-6 h-6 rounded-full bg-primary/50"
          style={{ filter: 'blur(4px)' }}
          animate={{ scale: [0.8, 1.1, 0.8], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
        />
      </motion.div>

      {/* Floating particles */}
      {[...Array(5)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-primary/60"
          style={{
            top: `${20 + Math.random() * 60}%`,
            left: `${20 + Math.random() * 60}%`,
          }}
          animate={{
            y: [0, -8, 0],
            x: [0, (i % 2 === 0 ? 4 : -4), 0],
            opacity: [0.3, 0.8, 0.3],
          }}
          transition={{
            duration: 2 + i * 0.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.4,
          }}
        />
      ))}
    </div>
  );
}

function LiveFeed() {
  const [visibleIndex, setVisibleIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleIndex(prev => (prev + 1) % LIVE_EVENTS.length);
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  const visible = [
    LIVE_EVENTS[visibleIndex % LIVE_EVENTS.length],
    LIVE_EVENTS[(visibleIndex + 1) % LIVE_EVENTS.length],
    LIVE_EVENTS[(visibleIndex + 2) % LIVE_EVENTS.length],
  ];

  return (
    <div className="space-y-1.5 overflow-hidden">
      <AnimatePresence mode="popLayout">
        {visible.map((event, i) => (
          <motion.div
            key={`${event.agent}-${event.action}-${visibleIndex + i}`}
            initial={{ opacity: 0, x: 20, height: 0 }}
            animate={{ opacity: 1 - i * 0.25, x: 0, height: 'auto' }}
            exit={{ opacity: 0, x: -20, height: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="flex items-center gap-3 text-sm py-1.5"
          >
            <span className="text-[10px] font-display font-bold tracking-wider text-primary w-16 shrink-0">{event.agent}</span>
            <span className="text-foreground/80 truncate flex-1">{event.action}</span>
            <span className="text-[10px] text-muted-foreground font-mono shrink-0">{event.time}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [agents, setAgents] = useState(AGENT_DEFAULTS);
  const [chatInput, setChatInput] = useState("");

  useEffect(() => {
    api('/api/stats').then(setStats).catch(() => {});
    api('/api/agents').then(data => {
      if (Array.isArray(data) && data.length > 0) setAgents(data as any);
    }).catch(() => {});
  }, []);

  const activeAgents = agents.filter(a => a.status === 'active').length;
  const topAgents = agents.filter(a => a.status === 'active').slice(0, 6);

  const handleChat = () => {
    if (chatInput.trim()) {
      navigate('/chat');
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero: JARVIS Command Center */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="hud-card rounded-xl overflow-hidden relative"
      >
        {/* Background grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(hsl(199 89% 48%) 1px, transparent 1px),
              linear-gradient(90deg, hsl(199 89% 48%) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />

        <div className="relative z-10 p-6 flex flex-col lg:flex-row items-center gap-6">
          {/* Left: JARVIS Orb + Quick Chat */}
          <div className="flex flex-col items-center gap-3 shrink-0">
            <JarvisOrb />
            <div className="text-[10px] font-display tracking-[0.25em] text-primary/70 font-semibold">
              J.A.R.V.I.S.
            </div>
          </div>

          {/* Center: Live Activity Feed */}
          <div className="flex-1 min-w-0 w-full">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-1 h-4 bg-primary rounded-full" />
              <h2 className="font-display text-[10px] font-bold tracking-[0.2em] text-primary">LIVE ACTIVITY</h2>
              <motion.div
                className="w-1.5 h-1.5 rounded-full bg-primary"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </div>
            <LiveFeed />

            {/* Quick chat input */}
            <div className="mt-4 flex items-center gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleChat()}
                  placeholder="Ask JARVIS anything..."
                  className="w-full bg-jarvis-elevated/80 border border-primary/15 rounded-lg px-4 py-2.5 text-sm font-body placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all"
                />
              </div>
              <button
                onClick={handleChat}
                className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center hover:bg-primary/20 hover:border-primary/40 transition-all"
              >
                <Send className="w-4 h-4 text-primary" />
              </button>
            </div>
          </div>

          {/* Right: Quick Stats */}
          <div className="shrink-0 hidden xl:flex flex-col gap-2 text-right">
            {[
              { label: 'AGENTS', value: activeAgents, color: 'text-primary' },
              { label: 'TASKS', value: stats?.tasks?.total ?? 0, color: 'text-jarvis-success' },
              { label: 'LEARNINGS', value: stats?.learnings ?? 0, color: 'text-jarvis-purple' },
            ].map(s => (
              <div key={s.label} className="flex items-center gap-3 justify-end">
                <span className="text-[9px] font-display tracking-[0.15em] text-muted-foreground">{s.label}</span>
                <span className={`text-lg font-display font-bold ${s.color}`}>{s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { title: "Agents", value: stats?.agents?.active ?? activeAgents, subtitle: "aktiv", color: "text-primary", icon: <Bot className="w-4 h-4" /> },
          { title: "Tasks", value: stats?.tasks?.total ?? 0, subtitle: `${stats?.tasks?.completed ?? 0} erledigt`, color: "text-jarvis-success", icon: <CheckSquare className="w-4 h-4" /> },
          { title: "Learnings", value: stats?.learnings ?? 0, subtitle: "Self-Improvement", color: "text-jarvis-purple", icon: <Brain className="w-4 h-4" /> },
          { title: "Gespräche", value: stats?.conversations ?? 0, subtitle: "gespeichert", color: "text-jarvis-cyan", icon: <MessageSquare className="w-4 h-4" /> },
          { title: "Skills", value: stats?.skills?.enabled ?? 0, subtitle: `von ${stats?.skills?.total ?? 0}`, color: "text-jarvis-gold", icon: <Zap className="w-4 h-4" /> },
          { title: "Tokens", value: Number(stats?.tasks?.total_tokens ?? 0).toLocaleString(), subtitle: `${((stats?.tasks?.total_cost ?? 0) / 100).toFixed(2)} €`, color: "text-primary", icon: <Coins className="w-4 h-4" /> },
        ].map((s, i) => (
          <motion.div
            key={s.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 + i * 0.05 }}
          >
            <StatCard {...s} colorClass={s.color} />
          </motion.div>
        ))}
      </div>

      {/* Agent Team */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.5 }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-1 h-5 bg-jarvis-cyan rounded-full" />
            <h3 className="font-display text-[10px] font-bold tracking-[0.15em]">AGENT TEAM</h3>
          </div>
          <button
            onClick={() => navigate('/agents')}
            className="text-[11px] font-display tracking-wider text-muted-foreground border border-border px-3 py-1.5 rounded hover:bg-jarvis-hover hover:border-primary/30 hover:text-primary transition-all flex items-center gap-1.5"
          >
            ALLE AGENTS <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {topAgents.map((agent, i) => (
            <motion.div
              key={agent.slug}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.6 + i * 0.05 }}
            >
              <AgentCard agent={agent} onClick={() => navigate('/agents')} />
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
