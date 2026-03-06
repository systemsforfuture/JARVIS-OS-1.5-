import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { SKILLS_REGISTRY, SKILL_CATEGORIES } from "@/lib/types";
import type { Skill } from "@/lib/types";
import { motion } from "framer-motion";
import { Zap, Lock, Check, Search } from "lucide-react";

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>(SKILLS_REGISTRY);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api('/api/skills')
      .then(data => { if (Array.isArray(data) && data.length > 0) setSkills(data as Skill[]); })
      .catch(() => {});
  }, []);

  const filtered = search
    ? skills.filter(s =>
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.description.toLowerCase().includes(search.toLowerCase()) ||
        s.category.toLowerCase().includes(search.toLowerCase()) ||
        s.agents.some(a => a.toLowerCase().includes(search.toLowerCase()))
      )
    : skills;

  const categories = Object.keys(SKILL_CATEGORIES);
  const grouped = categories
    .map(cat => ({
      key: cat,
      ...SKILL_CATEGORIES[cat],
      skills: filtered.filter(s => s.category === cat),
    }))
    .filter(g => g.skills.length > 0);

  const totalEnabled = skills.filter(s => s.enabled).length;
  const totalKeys = skills.filter(s => s.requires_key && !s.enabled).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <div className="w-1 h-6 bg-jarvis-gold rounded-full" />
          <h2 className="font-display text-xs font-bold tracking-[0.2em]">SKILLS REGISTRY</h2>
          <span className="text-[10px] font-mono text-muted-foreground ml-2">
            {totalEnabled}/{skills.length} aktiv
          </span>
          {totalKeys > 0 && (
            <span className="text-[10px] font-mono text-jarvis-warning ml-1">
              · {totalKeys} brauchen API Key
            </span>
          )}
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Skill suchen..."
            className="bg-jarvis-elevated border border-border rounded-lg pl-9 pr-4 py-2 text-sm font-body placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all w-64"
          />
        </div>
      </div>

      {/* Category Groups */}
      {grouped.map((group, gi) => (
        <motion.div
          key={group.key}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: gi * 0.05 }}
        >
          <div className={`flex items-center gap-2 mb-3 pb-2 border-b border-border`}>
            <span className="text-lg">{group.icon}</span>
            <h3 className={`font-display text-[10px] font-semibold tracking-[0.15em] uppercase ${group.color}`}>
              {group.label}
            </h3>
            <span className="text-[10px] font-mono text-muted-foreground">{group.skills.length}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {group.skills.map(skill => (
              <div
                key={skill.slug}
                className={`hud-card rounded-lg p-4 transition-all hover:hud-glow ${!skill.enabled ? 'opacity-60' : ''}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Zap className={`w-3.5 h-3.5 ${skill.enabled ? 'text-jarvis-gold' : 'text-muted-foreground'}`} />
                    <span className="text-sm font-semibold">{skill.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {skill.requires_key && (
                      <span className="text-[9px] font-mono bg-jarvis-warning/10 border border-jarvis-warning/20 text-jarvis-warning px-1.5 py-0.5 rounded flex items-center gap-1">
                        <Lock className="w-2.5 h-2.5" />
                        KEY
                      </span>
                    )}
                    <span className={`w-5 h-5 rounded flex items-center justify-center ${skill.enabled ? 'bg-jarvis-success/15 text-jarvis-success' : 'bg-muted text-muted-foreground'}`}>
                      {skill.enabled ? <Check className="w-3 h-3" /> : <span className="w-1.5 h-1.5 rounded-full bg-current" />}
                    </span>
                  </div>
                </div>
                <p className="text-[12px] text-muted-foreground mb-3 leading-relaxed">{skill.description}</p>
                <div className="flex gap-1.5 flex-wrap">
                  {skill.agents.map(agent => (
                    <span key={agent} className="text-[9px] font-display font-semibold tracking-wider bg-primary/8 border border-primary/15 text-primary/80 px-1.5 py-0.5 rounded">
                      {agent.toUpperCase()}
                    </span>
                  ))}
                  {skill.requires_key && (
                    <span className="text-[9px] font-mono text-muted-foreground/60">
                      {skill.requires_key}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
