import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const StatusLine = ({ label, value, delay }: { label: string; value: string; delay: number }) => (
  <motion.div
    className="flex justify-between font-mono text-xs md:text-sm"
    initial={{ opacity: 0, x: -10 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay, duration: 0.4 }}
  >
    <span className="text-muted-foreground uppercase tracking-widest">{label}</span>
    <span className="text-foreground">{value}</span>
  </motion.div>
);

const SystemStatus = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (d: Date) =>
    d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return (
    <div className="border border-jarvis-panel-border bg-jarvis-panel rounded jarvis-panel-glow p-4 md:p-6 space-y-3 w-full max-w-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 rounded-full bg-jarvis-success animate-pulse" />
        <span className="font-display text-xs tracking-[0.3em] text-foreground uppercase">System Status</span>
      </div>
      <StatusLine label="Version" value="1.5.0" delay={0.2} />
      <StatusLine label="Status" value="ONLINE" delay={0.4} />
      <StatusLine label="Uhrzeit" value={formatTime(time)} delay={0.6} />
      <StatusLine label="CPU" value="12.4%" delay={0.8} />
      <StatusLine label="Speicher" value="2.1 GB / 16 GB" delay={1.0} />
      <StatusLine label="Netzwerk" value="VERBUNDEN" delay={1.2} />
    </div>
  );
};

export default SystemStatus;
