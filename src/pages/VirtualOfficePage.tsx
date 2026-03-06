import { useState, useEffect, useRef, Suspense, useMemo } from "react";
import { AGENT_DEFAULTS, Agent } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, MessageSquare, CheckSquare, Zap, Users, Eye } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Text, RoundedBox, Environment, ContactShadows, Float } from "@react-three/drei";
import * as THREE from "three";

/* ── Agent positions in 3D space ── */
const DESK_POSITIONS: Record<string, [number, number, number]> = {
  jarvis:  [0, 0, 0],
  elon:    [-4, 0, -3],
  steve:   [-6, 0, 1],
  iris:    [-6, 0, 3.5],
  donald:  [-2, 0, 4],
  donna:   [3, 0, 4],
  archi:   [4, 0, -3],
  satoshi: [6, 0, 1],
  felix:   [2, 0, -4],
  andreas: [5, 0, -5],
};

const ZONE_CONFIGS: { id: string; label: string; color: string; position: [number, number, number]; size: [number, number] }[] = [
  { id: 'command', label: 'COMMAND', color: '#0ea5e9', position: [0, 0.01, 0], size: [3, 3] },
  { id: 'intelligence', label: 'ANALYTICS', color: '#a855f7', position: [-4, 0.01, -3], size: [3, 2.5] },
  { id: 'marketing', label: 'MARKETING', color: '#f59e0b', position: [-6, 0.01, 2.25], size: [3, 4] },
  { id: 'sales', label: 'SALES', color: '#22c55e', position: [-2, 0.01, 4], size: [3, 2.5] },
  { id: 'operations', label: 'OPERATIONS', color: '#a855f7', position: [3, 0.01, 4], size: [3, 2.5] },
  { id: 'development', label: 'DEV LAB', color: '#06b6d4', position: [4, 0.01, -3], size: [3, 2.5] },
  { id: 'crypto', label: 'CRYPTO', color: '#eab308', position: [6, 0.01, 1], size: [3, 2.5] },
  { id: 'customer-success', label: 'SUCCESS', color: '#14b8a6', position: [3.5, 0.01, -4.5], size: [4, 2.5] },
];

const AGENT_COLORS: Record<string, string> = {
  jarvis: '#0ea5e9', elon: '#a855f7', steve: '#f59e0b', donald: '#22c55e',
  archi: '#06b6d4', donna: '#a855f7', iris: '#ec4899', satoshi: '#eab308',
  felix: '#14b8a6', andreas: '#14b8a6',
};

/* ── 3D Desk Component ── */
function Desk({ position, agentColor }: { position: [number, number, number]; agentColor: string }) {
  return (
    <group position={position}>
      {/* Desk surface */}
      <RoundedBox args={[1.6, 0.06, 0.8]} position={[0, 0.75, 0]} radius={0.02} smoothness={4}>
        <meshStandardMaterial color="#2a2a3e" metalness={0.3} roughness={0.6} />
      </RoundedBox>
      {/* Legs */}
      {[[-0.7, 0, -0.3], [0.7, 0, -0.3], [-0.7, 0, 0.3], [0.7, 0, 0.3]].map((leg, i) => (
        <mesh key={i} position={[leg[0], 0.375, leg[2]]}>
          <cylinderGeometry args={[0.03, 0.03, 0.75, 8]} />
          <meshStandardMaterial color="#1a1a2e" metalness={0.5} roughness={0.4} />
        </mesh>
      ))}
      {/* Monitor */}
      <group position={[0, 1.15, -0.2]}>
        {/* Screen frame */}
        <RoundedBox args={[0.7, 0.45, 0.03]} radius={0.01} smoothness={4}>
          <meshStandardMaterial color="#111122" metalness={0.6} roughness={0.3} />
        </RoundedBox>
        {/* Screen glow */}
        <mesh position={[0, 0, 0.016]}>
          <planeGeometry args={[0.62, 0.37]} />
          <meshStandardMaterial color={agentColor} emissive={agentColor} emissiveIntensity={0.5} transparent opacity={0.9} />
        </mesh>
        {/* Monitor stand */}
        <mesh position={[0, -0.3, 0.1]}>
          <cylinderGeometry args={[0.02, 0.04, 0.2, 8]} />
          <meshStandardMaterial color="#222" metalness={0.6} roughness={0.4} />
        </mesh>
      </group>
      {/* Keyboard */}
      <RoundedBox args={[0.5, 0.02, 0.18]} position={[0, 0.79, 0.15]} radius={0.005} smoothness={2}>
        <meshStandardMaterial color="#1a1a28" metalness={0.2} roughness={0.7} />
      </RoundedBox>
    </group>
  );
}

/* ── 3D Agent Figure ── */
function AgentFigure({ agent, position, isSelected, onClick, color }: {
  agent: Agent; position: [number, number, number]; isSelected: boolean; onClick: () => void; color: string;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const isActive = agent.status === 'active';

  useFrame(({ clock }) => {
    if (groupRef.current) {
      // Subtle idle animation
      groupRef.current.position.y = position[1] + Math.sin(clock.elapsedTime * 1.5 + position[0]) * 0.02;
    }
    if (glowRef.current) {
      const mat = glowRef.current.material as THREE.MeshStandardMaterial;
      mat.emissiveIntensity = isSelected ? 1.5 + Math.sin(clock.elapsedTime * 3) * 0.5 : 0.3;
    }
  });

  return (
    <group ref={groupRef} position={position} onClick={(e) => { e.stopPropagation(); onClick(); }}>
      {/* Selection ring */}
      {isSelected && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
          <ringGeometry args={[0.6, 0.75, 32]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2} transparent opacity={0.6} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Ground glow */}
      <mesh ref={glowRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
        <circleGeometry args={[0.5, 32]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.3} transparent opacity={0.3} />
      </mesh>

      {/* Chair */}
      <group position={[0, 0, 0.5]}>
        <mesh position={[0, 0.4, 0]}>
          <boxGeometry args={[0.4, 0.05, 0.4]} />
          <meshStandardMaterial color="#1e293b" metalness={0.3} roughness={0.7} />
        </mesh>
        <mesh position={[0, 0.6, -0.18]}>
          <boxGeometry args={[0.38, 0.4, 0.04]} />
          <meshStandardMaterial color="#334155" metalness={0.2} roughness={0.8} />
        </mesh>
        {/* Chair legs */}
        {[[-0.15, 0, -0.15], [0.15, 0, -0.15], [-0.15, 0, 0.15], [0.15, 0, 0.15]].map((l, i) => (
          <mesh key={i} position={[l[0], 0.2, l[2]]}>
            <cylinderGeometry args={[0.015, 0.015, 0.4, 6]} />
            <meshStandardMaterial color="#0f172a" metalness={0.6} roughness={0.3} />
          </mesh>
        ))}
      </group>

      {/* Body - torso */}
      <mesh position={[0, 1.1, 0.4]}>
        <capsuleGeometry args={[0.15, 0.3, 4, 8]} />
        <meshStandardMaterial color={color} metalness={0.1} roughness={0.8} />
      </mesh>

      {/* Head */}
      <mesh position={[0, 1.6, 0.4]}>
        <sphereGeometry args={[0.14, 16, 16]} />
        <meshStandardMaterial color="#f0d0a0" roughness={0.9} />
      </mesh>

      {/* Arms */}
      <mesh position={[-0.22, 1.0, 0.25]} rotation={[0.5, 0, 0.2]}>
        <capsuleGeometry args={[0.05, 0.25, 4, 6]} />
        <meshStandardMaterial color={color} metalness={0.1} roughness={0.8} />
      </mesh>
      <mesh position={[0.22, 1.0, 0.25]} rotation={[0.5, 0, -0.2]}>
        <capsuleGeometry args={[0.05, 0.25, 4, 6]} />
        <meshStandardMaterial color={color} metalness={0.1} roughness={0.8} />
      </mesh>

      {/* Floating name label */}
      <Float speed={2} floatIntensity={0.1} rotationIntensity={0}>
        <group position={[0, 2.1, 0.4]}>
          {/* Label background */}
          <mesh>
            <planeGeometry args={[1.1, 0.3]} />
            <meshStandardMaterial color="#0f172a" transparent opacity={0.85} />
          </mesh>
          <Text
            position={[0, 0.02, 0.01]}
            fontSize={0.12}
            color="white"
            font="/fonts/orbitron.woff"
            anchorX="center"
            anchorY="middle"
            letterSpacing={0.08}
          >
            {agent.name}
          </Text>
          {/* Status indicator text */}
          <Text
            position={[0, -0.08, 0.01]}
            fontSize={0.06}
            color={isActive ? '#22c55e' : agent.status === 'standby' ? '#f59e0b' : '#ef4444'}
            anchorX="center"
            anchorY="middle"
          >
            {agent.status.toUpperCase()}
          </Text>
          {/* Emoji */}
          <Text
            position={[0, 0.25, 0.01]}
            fontSize={0.2}
            anchorX="center"
            anchorY="middle"
          >
            {agent.emoji}
          </Text>
        </group>
      </Float>

      {/* Status light on desk */}
      <pointLight
        position={[0, 0.9, 0]}
        color={isActive ? '#22c55e' : '#ef4444'}
        intensity={isActive ? 0.5 : 0.1}
        distance={2}
      />
    </group>
  );
}

/* ── Floor Zone ── */
function FloorZone({ position, size, color, label }: {
  position: [number, number, number]; size: [number, number]; color: string; label: string;
}) {
  return (
    <group position={position}>
      {/* Zone carpet */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[size[0], size[1]]} />
        <meshStandardMaterial color={color} transparent opacity={0.08} />
      </mesh>
      {/* Zone border */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.001, 0]}>
        <ringGeometry args={[Math.min(size[0], size[1]) * 0.45, Math.min(size[0], size[1]) * 0.48, 4]} />
        <meshStandardMaterial color={color} transparent opacity={0.15} side={THREE.DoubleSide} />
      </mesh>
      {/* Label */}
      <Text
        position={[0, 0.02, size[1] * 0.35]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.18}
        color={color}
        anchorX="center"
        anchorY="middle"
        letterSpacing={0.15}
        fillOpacity={0.4}
      >
        {label}
      </Text>
    </group>
  );
}

/* ── Office Walls ── */
function OfficeWalls() {
  return (
    <group>
      {/* Back wall */}
      <mesh position={[0, 2, -7]} >
        <boxGeometry args={[20, 4, 0.1]} />
        <meshStandardMaterial color="#151525" metalness={0.1} roughness={0.9} />
      </mesh>
      {/* Left wall */}
      <mesh position={[-10, 2, 0]} rotation={[0, Math.PI / 2, 0]}>
        <boxGeometry args={[14, 4, 0.1]} />
        <meshStandardMaterial color="#181828" metalness={0.1} roughness={0.9} />
      </mesh>
      {/* Wall accent lights */}
      {[-6, -2, 2, 6].map((x, i) => (
        <group key={i}>
          <mesh position={[x, 3.2, -6.9]}>
            <boxGeometry args={[1.5, 0.05, 0.05]} />
            <meshStandardMaterial color="#0ea5e9" emissive="#0ea5e9" emissiveIntensity={2} />
          </mesh>
          <pointLight position={[x, 3, -6.5]} color="#0ea5e9" intensity={0.3} distance={4} />
        </group>
      ))}
      {/* Window panels on back wall */}
      {[-5, 0, 5].map((x, i) => (
        <mesh key={i} position={[x, 2.2, -6.94]}>
          <planeGeometry args={[2.5, 2]} />
          <meshStandardMaterial color="#0a1628" emissive="#061224" emissiveIntensity={0.3} metalness={0.8} roughness={0.2} />
        </mesh>
      ))}
    </group>
  );
}

/* ── Decorative Elements ── */
function OfficePlant({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      {/* Pot */}
      <mesh position={[0, 0.2, 0]}>
        <cylinderGeometry args={[0.15, 0.12, 0.4, 8]} />
        <meshStandardMaterial color="#8B4513" roughness={0.9} />
      </mesh>
      {/* Leaves */}
      {[0, 1, 2, 3, 4].map((i) => (
        <mesh key={i} position={[Math.cos(i * 1.25) * 0.15, 0.5 + i * 0.08, Math.sin(i * 1.25) * 0.15]} rotation={[0.3, i * 1.25, 0.2]}>
          <sphereGeometry args={[0.12, 8, 8]} />
          <meshStandardMaterial color="#22c55e" roughness={0.8} />
        </mesh>
      ))}
    </group>
  );
}

/* ── JARVIS Core Hologram ── */
function JarvisHologram() {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = clock.elapsedTime * 0.5;
      const scale = 1 + Math.sin(clock.elapsedTime * 2) * 0.05;
      meshRef.current.scale.setScalar(scale);
    }
    if (ringRef.current) {
      ringRef.current.rotation.y = -clock.elapsedTime * 0.8;
      ringRef.current.rotation.x = Math.sin(clock.elapsedTime * 0.3) * 0.1;
    }
  });

  return (
    <group position={[0, 2.5, 0]}>
      {/* Core sphere */}
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[0.3, 1]} />
        <meshStandardMaterial color="#0ea5e9" emissive="#0ea5e9" emissiveIntensity={3} wireframe transparent opacity={0.7} />
      </mesh>
      {/* Outer ring */}
      <mesh ref={ringRef}>
        <torusGeometry args={[0.6, 0.02, 8, 32]} />
        <meshStandardMaterial color="#0ea5e9" emissive="#0ea5e9" emissiveIntensity={2} transparent opacity={0.5} />
      </mesh>
      {/* Second ring */}
      <mesh rotation={[Math.PI / 3, 0, 0]}>
        <torusGeometry args={[0.5, 0.015, 8, 32]} />
        <meshStandardMaterial color="#a855f7" emissive="#a855f7" emissiveIntensity={2} transparent opacity={0.4} />
      </mesh>
      {/* Light source */}
      <pointLight color="#0ea5e9" intensity={2} distance={8} />
      {/* Label */}
      <Text
        position={[0, 0.9, 0]}
        fontSize={0.15}
        color="#0ea5e9"
        anchorX="center"
        anchorY="middle"
        letterSpacing={0.2}
      >
        JARVIS CORE
      </Text>
    </group>
  );
}

/* ── Connection Lines between agents ── */
function ConnectionLines({ agents }: { agents: Agent[] }) {
  const linesRef = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (linesRef.current) {
      linesRef.current.children.forEach((child, i) => {
        const mat = (child as THREE.Line).material as THREE.LineBasicMaterial;
        if (mat) mat.opacity = 0.15 + Math.sin(clock.elapsedTime * 2 + i) * 0.1;
      });
    }
  });

  const lines = useMemo(() => {
    const jarvisPos = DESK_POSITIONS.jarvis;
    return agents.filter(a => a.slug !== 'jarvis' && a.status === 'active').map(a => {
      const pos = DESK_POSITIONS[a.slug];
      if (!pos) return null;
      const points = [
        new THREE.Vector3(jarvisPos[0], 1.5, jarvisPos[2]),
        new THREE.Vector3((jarvisPos[0] + pos[0]) / 2, 2.5, (jarvisPos[2] + pos[2]) / 2),
        new THREE.Vector3(pos[0], 1.5, pos[2]),
      ];
      const curve = new THREE.QuadraticBezierCurve3(points[0], points[1], points[2]);
      return curve.getPoints(20);
    }).filter(Boolean);
  }, [agents]);

  return (
    <group ref={linesRef}>
      {lines.map((pts, i) => (
        <line key={i}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={pts!.length}
              array={new Float32Array(pts!.flatMap(p => [p.x, p.y, p.z]))}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#0ea5e9" transparent opacity={0.2} />
        </line>
      ))}
    </group>
  );
}

/* ── Scene ── */
function OfficeScene({ agents, selectedAgent, onSelectAgent }: {
  agents: Agent[]; selectedAgent: string | null; onSelectAgent: (slug: string) => void;
}) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.15} />
      <directionalLight position={[8, 12, 5]} intensity={0.6} color="#e0e8ff" castShadow shadow-mapSize={[1024, 1024]} />
      <directionalLight position={[-5, 8, -3]} intensity={0.2} color="#a0b0ff" />
      <pointLight position={[0, 5, 0]} intensity={0.4} color="#0ea5e9" distance={15} />

      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[24, 18]} />
        <meshStandardMaterial color="#0c0c1a" metalness={0.3} roughness={0.8} />
      </mesh>

      {/* Floor grid pattern */}
      <gridHelper args={[24, 24, '#1e293b', '#111827']} position={[0, 0.005, 0]} />

      {/* Walls */}
      <OfficeWalls />

      {/* Zones */}
      {ZONE_CONFIGS.map(z => (
        <FloorZone key={z.id} position={z.position} size={z.size} color={z.color} label={z.label} />
      ))}

      {/* Desks & Agents */}
      {agents.map(agent => {
        const pos = DESK_POSITIONS[agent.slug];
        if (!pos) return null;
        const color = AGENT_COLORS[agent.slug] || '#888';
        return (
          <group key={agent.slug}>
            <Desk position={pos} agentColor={color} />
            <AgentFigure
              agent={agent}
              position={pos}
              isSelected={selectedAgent === agent.slug}
              onClick={() => onSelectAgent(agent.slug)}
              color={color}
            />
          </group>
        );
      })}

      {/* JARVIS Core Hologram */}
      <JarvisHologram />

      {/* Connection Lines */}
      <ConnectionLines agents={agents} />

      {/* Decorative plants */}
      <OfficePlant position={[-9, 0, -5]} />
      <OfficePlant position={[9, 0, -5]} />
      <OfficePlant position={[-9, 0, 5]} />
      <OfficePlant position={[9, 0, 5]} />

      {/* Contact shadows for realism */}
      <ContactShadows position={[0, 0, 0]} opacity={0.4} scale={30} blur={2} far={6} color="#000020" />

      {/* Camera controls */}
      <OrbitControls
        makeDefault
        minPolarAngle={0.3}
        maxPolarAngle={Math.PI / 2.2}
        minDistance={5}
        maxDistance={25}
        enableDamping
        dampingFactor={0.05}
        target={[0, 0, 0]}
      />
    </>
  );
}

/* ── Agent Detail Popup ── */
function AgentPopup({ agent, onClose, onNavigate }: {
  agent: Agent; onClose: () => void; onNavigate: (path: string) => void;
}) {
  const color = AGENT_COLORS[agent.slug] || '#888';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 10, scale: 0.95 }}
      className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 w-80 rounded-xl overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, hsl(var(--card)), hsl(220 18% 6%))',
        border: `1px solid ${color}40`,
        boxShadow: `0 0 40px ${color}20, 0 20px 60px rgba(0,0,0,0.6)`,
      }}
    >
      <div style={{ height: '2px', background: `linear-gradient(90deg, transparent, ${color}, transparent)` }} />
      <div className="p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 rounded-full flex items-center justify-center text-2xl" style={{
            background: `radial-gradient(circle, ${color}40, hsl(var(--card)) 70%)`,
            border: `2px solid ${color}`,
          }}>
            {agent.emoji}
          </div>
          <div className="flex-1">
            <h3 className="font-display text-sm font-bold tracking-wider text-foreground">{agent.name}</h3>
            <p className="text-[11px] font-body text-muted-foreground">{agent.role}</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">✕</button>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[8px] font-display text-muted-foreground tracking-wider">STATUS</div>
            <div className="text-[11px] font-display font-bold capitalize" style={{ color }}>{agent.status}</div>
          </div>
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[8px] font-display text-muted-foreground tracking-wider">TIER</div>
            <div className="text-[11px] font-display font-bold" style={{ color }}>T{agent.tier}</div>
          </div>
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[8px] font-display text-muted-foreground tracking-wider">SKILLS</div>
            <div className="text-[11px] font-display font-bold" style={{ color }}>{agent.skills.length}</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-1 mb-3">
          {agent.skills.slice(0, 5).map(s => (
            <span key={s} className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{
              background: `${color}15`, border: `1px solid ${color}25`, color,
            }}>{s}</span>
          ))}
          {agent.skills.length > 5 && <span className="text-[8px] text-muted-foreground">+{agent.skills.length - 5}</span>}
        </div>

        <div className="flex gap-1.5">
          <button onClick={() => onNavigate('/chat')} className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg text-[10px] font-display tracking-wider transition-all hover:brightness-125" style={{ background: `${color}15`, border: `1px solid ${color}25`, color }}>
            <MessageSquare className="w-3.5 h-3.5" /> CHAT
          </button>
          <button onClick={() => onNavigate('/tasks')} className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg text-[10px] font-display tracking-wider transition-all hover:brightness-125" style={{ background: 'hsl(var(--jarvis-success) / 0.1)', border: '1px solid hsl(var(--jarvis-success) / 0.2)', color: 'hsl(var(--jarvis-success))' }}>
            <CheckSquare className="w-3.5 h-3.5" /> TASKS
          </button>
          <button onClick={() => onNavigate('/agents')} className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg text-[10px] font-display tracking-wider transition-all hover:brightness-125" style={{ background: 'hsl(var(--jarvis-purple) / 0.1)', border: '1px solid hsl(var(--jarvis-purple) / 0.2)', color: 'hsl(var(--jarvis-purple))' }}>
            <Zap className="w-3.5 h-3.5" /> INFO
          </button>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Main Page ── */
export default function VirtualOfficePage() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState(AGENT_DEFAULTS);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  useEffect(() => {
    api('/api/agents').then(data => {
      if (Array.isArray(data) && data.length > 0) setAgents(data as any);
    }).catch(() => {});
  }, []);

  const selected = agents.find(a => a.slug === selectedAgent);
  const activeCount = agents.filter(a => a.status === 'active').length;

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col -m-6 relative" style={{ background: '#050510' }}>
      {/* Header bar */}
      <div className="h-12 flex items-center justify-between px-5 shrink-0 z-10 relative" style={{
        background: 'rgba(15,15,30,0.9)',
        borderBottom: '1px solid hsl(var(--border))',
        backdropFilter: 'blur(12px)',
      }}>
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors">
          <ChevronLeft className="w-4 h-4" />
          <span className="text-sm font-body font-semibold">Zurück</span>
        </button>
        <h1 className="font-display text-sm font-bold tracking-[0.15em] text-foreground">
          VIRTUAL OFFICE
        </h1>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-jarvis-success animate-pulse-dot" />
            <span className="text-[11px] font-mono text-jarvis-success">{activeCount}/{agents.length} ACTIVE</span>
          </div>
        </div>
      </div>

      {/* 3D Canvas */}
      <div className="flex-1 relative">
        <Canvas
          shadows
          camera={{ position: [12, 10, 12], fov: 45 }}
          gl={{ antialias: true, alpha: false }}
          style={{ background: '#050510' }}
        >
          <Suspense fallback={null}>
            <fog attach="fog" args={['#050510', 15, 35]} />
            <OfficeScene
              agents={agents}
              selectedAgent={selectedAgent}
              onSelectAgent={(slug) => setSelectedAgent(prev => prev === slug ? null : slug)}
            />
          </Suspense>
        </Canvas>

        {/* Team sidebar */}
        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="absolute top-4 left-4 z-20 w-48 rounded-xl overflow-hidden"
          style={{
            background: 'rgba(15,15,30,0.9)',
            border: '1px solid hsl(var(--border))',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          }}
        >
          <div className="p-3">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-3.5 h-3.5 text-primary" />
              <h3 className="font-display text-[11px] font-bold tracking-[0.1em] text-foreground">AGENT TEAMS</h3>
            </div>
            <div className="space-y-0.5">
              {agents.map(agent => {
                const color = AGENT_COLORS[agent.slug] || '#888';
                const isSelected = selectedAgent === agent.slug;
                return (
                  <button
                    key={agent.slug}
                    onClick={() => setSelectedAgent(prev => prev === agent.slug ? null : agent.slug)}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left transition-all"
                    style={{
                      background: isSelected ? `${color}15` : 'transparent',
                      border: isSelected ? `1px solid ${color}30` : '1px solid transparent',
                    }}
                  >
                    <span className="text-sm">{agent.emoji}</span>
                    <span className="font-display text-[10px] font-bold tracking-wider text-foreground flex-1">{agent.name}</span>
                    <div className="w-2 h-2 rounded-full shrink-0" style={{
                      backgroundColor: agent.status === 'active' ? '#22c55e' : agent.status === 'standby' ? '#f59e0b' : '#ef4444',
                      boxShadow: agent.status === 'active' ? '0 0 6px #22c55e' : 'none',
                    }} />
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Controls hint */}
        <div className="absolute bottom-4 right-4 z-20 flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{
          background: 'rgba(15,15,30,0.8)',
          border: '1px solid hsl(var(--border))',
          backdropFilter: 'blur(8px)',
        }}>
          <Eye className="w-3 h-3 text-muted-foreground" />
          <span className="text-[9px] font-mono text-muted-foreground">Drag: Rotate · Scroll: Zoom · Click: Select</span>
        </div>

        {/* Agent Detail Popup */}
        <AnimatePresence>
          {selected && (
            <AgentPopup
              agent={selected}
              onClose={() => setSelectedAgent(null)}
              onNavigate={(path) => navigate(path)}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
