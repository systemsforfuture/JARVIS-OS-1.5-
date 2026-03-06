import { motion } from "framer-motion";

const JarvisCore = () => {
  return (
    <div className="relative w-48 h-48 md:w-64 md:h-64">
      {/* Outer ring */}
      <motion.div
        className="absolute inset-0 rounded-full border-2 border-jarvis-glow-dim"
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      >
        <div className="absolute top-0 left-1/2 w-2 h-2 -translate-x-1/2 -translate-y-1 rounded-full bg-jarvis-glow" />
        <div className="absolute bottom-0 left-1/2 w-1.5 h-1.5 -translate-x-1/2 translate-y-0.5 rounded-full bg-jarvis-glow opacity-50" />
      </motion.div>

      {/* Middle ring */}
      <motion.div
        className="absolute inset-6 rounded-full border border-jarvis-glow-dim"
        animate={{ rotate: -360 }}
        transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
      >
        <div className="absolute top-1/2 right-0 w-1.5 h-1.5 translate-x-0.5 -translate-y-1/2 rounded-full bg-jarvis-glow" />
      </motion.div>

      {/* Inner ring */}
      <motion.div
        className="absolute inset-12 rounded-full border border-jarvis-glow-dim"
        animate={{ rotate: 360 }}
        transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
      />

      {/* Core glow */}
      <motion.div
        className="absolute inset-16 md:inset-20 rounded-full bg-jarvis-glow"
        animate={{ opacity: [0.3, 0.8, 0.3], scale: [0.9, 1.1, 0.9] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        style={{ filter: "blur(8px)" }}
      />
      <motion.div
        className="absolute inset-[4.5rem] md:inset-[5.5rem] rounded-full bg-jarvis-glow"
        animate={{ opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        style={{ filter: "blur(2px)" }}
      />
    </div>
  );
};

export default JarvisCore;
