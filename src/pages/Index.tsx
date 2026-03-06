import { motion } from "framer-motion";
import JarvisCore from "@/components/JarvisCore";
import SystemStatus from "@/components/SystemStatus";

const Index = () => {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden jarvis-grid-bg">
      {/* Scan line effect */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-jarvis-glow to-transparent opacity-20"
          animate={{ y: ["-100%", "100vh"] }}
          transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
        />
      </div>

      {/* Header */}
      <motion.div
        className="text-center mb-8 md:mb-12"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-bold tracking-[0.2em] jarvis-glow-text text-foreground">
          JARVIS OS
        </h1>
        <motion.p
          className="font-mono text-xs md:text-sm tracking-[0.4em] text-muted-foreground mt-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
        >
          JUST A RATHER VERY INTELLIGENT SYSTEM — v1.5
        </motion.p>
      </motion.div>

      {/* Core animation */}
      <motion.div
        className="mb-8 md:mb-12"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.3, duration: 1, type: "spring" }}
      >
        <JarvisCore />
      </motion.div>

      {/* System status panel */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.6 }}
      >
        <SystemStatus />
      </motion.div>

      {/* Bottom status bar */}
      <motion.div
        className="absolute bottom-0 left-0 right-0 border-t border-jarvis-panel-border bg-jarvis-panel/80 backdrop-blur-sm px-6 py-3 flex justify-between items-center font-mono text-[10px] md:text-xs text-muted-foreground"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5, duration: 0.5 }}
      >
        <span>JARVIS OS // BEREIT FÜR GITHUB SYNC</span>
        <span className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-jarvis-success" />
          ALLE SYSTEME AKTIV
        </span>
      </motion.div>
    </div>
  );
};

export default Index;
