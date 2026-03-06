// JARVIS 1.5 — Types & Constants

export interface Agent {
  slug: string;
  name: string;
  role: string;
  emoji: string;
  tier: number;
  model: string;
  team: string;
  status: 'active' | 'standby' | 'disabled';
  system_prompt?: string;
  tools?: string[];
  temperature?: number;
  max_tokens?: number;
  openclaw_synced?: boolean;
  openclaw_synced_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  id: string;
  title: string;
  agent_slug: string;
  status: string;
  priority: number;
  tokens_used: number;
  cost_cents: number;
  created_at: string;
}

export interface MemoryEntry {
  id: string;
  agent_slug: string;
  type: string;
  key: string;
  value: string;
  created_at: string;
}

export interface LearningEntry {
  id: string;
  agent_slug: string;
  event_type: string;
  description: string;
  impact_score: number;
  created_at: string;
}

export interface Conversation {
  conversation_id: string;
  channel: string;
  agents: string[];
  message_count: number;
  started_at: string;
  last_message_at: string;
}

export interface ServiceStatus {
  status: 'ok' | 'error' | 'unreachable' | 'disabled';
  version?: string;
  size_mb?: number;
  memory?: string;
  url?: string;
}

export const AGENT_EMOJIS: Record<string, string> = {
  jarvis: '🧠', elon: '📊', steve: '📢', donald: '💰',
  archi: '🛠', donna: '📋', iris: '🎨',
  satoshi: '₿', felix: '🤝', andreas: '🎯'
};

export const AGENT_DEFAULTS: Agent[] = [
  { slug:'jarvis', emoji:'🧠', name:'JARVIS', role:'Chief Intelligence Operator', tier:1, model:'tier0-kimi', team:'command', status:'active' },
  { slug:'elon', emoji:'📊', name:'ELON', role:'Analyst & Systemoptimierer', tier:1, model:'tier1-sonnet', team:'intelligence', status:'active' },
  { slug:'steve', emoji:'📢', name:'STEVE', role:'Marketing & Content Lead', tier:2, model:'tier1-sonnet', team:'marketing', status:'active' },
  { slug:'donald', emoji:'💰', name:'DONALD', role:'Sales & Revenue Lead', tier:2, model:'tier1-sonnet', team:'sales', status:'active' },
  { slug:'archi', emoji:'🛠', name:'ARCHI', role:'Dev & Infrastructure Lead', tier:2, model:'tier1-sonnet', team:'development', status:'active' },
  { slug:'donna', emoji:'📋', name:'DONNA', role:'Backoffice & Operations Lead', tier:2, model:'tier1-haiku', team:'operations', status:'active' },
  { slug:'iris', emoji:'🎨', name:'IRIS', role:'Design & Creative Lead', tier:2, model:'tier1-sonnet', team:'marketing', status:'active' },
  { slug:'satoshi', emoji:'₿', name:'SATOSHI', role:'Crypto & Trading Specialist', tier:2, model:'tier1-sonnet', team:'crypto', status:'standby' },
  { slug:'felix', emoji:'🤝', name:'FELIX', role:'Customer Success Lead', tier:2, model:'tier1-haiku', team:'customer-success', status:'active' },
  { slug:'andreas', emoji:'🎯', name:'ANDREAS', role:'Customer Success SFE', tier:3, model:'tier1-haiku', team:'customer-success', status:'active' },
];
