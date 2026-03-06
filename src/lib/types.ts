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
  skills: string[];
  reports_to?: string;
  system_prompt?: string;
  tools?: string[];
  temperature?: number;
  max_tokens?: number;
  openclaw_synced?: boolean;
  openclaw_synced_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Skill {
  slug: string;
  name: string;
  description: string;
  category: string;
  requires_key: string | null;
  agents: string[];
  enabled: boolean;
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
  {
    slug: 'jarvis', emoji: '🧠', name: 'JARVIS', role: 'Chief Intelligence Operator',
    tier: 0, model: 'tier0-kimi', team: 'command', status: 'active',
    reports_to: 'DOM',
    skills: ['web-search', 'memory-store', 'memory-recall', 'task-create', 'task-delegate', 'telegram-send', 'analytics', 'github'],
  },
  {
    slug: 'elon', emoji: '📊', name: 'ELON', role: 'Analyst & Systemoptimierer',
    tier: 0, model: 'tier0-kimi', team: 'intelligence', status: 'active',
    reports_to: 'jarvis',
    skills: ['data-analysis', 'kpi-tracking', 'competitive-intel', 'market-research', 'bottleneck-finder', 'weekly-report'],
  },
  {
    slug: 'steve', emoji: '📢', name: 'STEVE', role: 'Marketing & Content Lead',
    tier: 1, model: 'tier1-sonnet', team: 'marketing', status: 'active',
    reports_to: 'jarvis',
    skills: ['content-creation', 'social-media-post', 'seo-analysis', 'video-scripts', 'ad-copy', 'brand-voice-check', 'email-newsletter', 'linkedin-post', 'twitter-post'],
  },
  {
    slug: 'donald', emoji: '💰', name: 'DONALD', role: 'Sales & Revenue Lead',
    tier: 1, model: 'tier1-sonnet', team: 'sales', status: 'active',
    reports_to: 'jarvis',
    skills: ['lead-generation', 'lead-qualification', 'email-outreach', 'linkedin-outreach', 'crm-hubspot', 'crm-airtable', 'proposal-writer', 'followup-sequences', 'pipeline-tracker', 'revenue-reporting'],
  },
  {
    slug: 'archi', emoji: '🛠', name: 'ARCHI', role: 'Dev & Infrastructure Lead',
    tier: 2, model: 'tier1-sonnet', team: 'development', status: 'active',
    reports_to: 'jarvis',
    skills: ['code-generation', 'code-review', 'bug-analysis', 'github-issues', 'github-prs', 'docker-manage', 'deploy', 'security-scan'],
  },
  {
    slug: 'donna', emoji: '📋', name: 'DONNA', role: 'Backoffice & Operations Lead',
    tier: 1, model: 'tier1-haiku', team: 'operations', status: 'active',
    reports_to: 'jarvis',
    skills: ['email-management', 'calendar-manage', 'document-creation', 'invoice-create', 'process-docs', 'compliance-check', 'meeting-notes'],
  },
  {
    slug: 'iris', emoji: '🎨', name: 'IRIS', role: 'Design & Creative Lead',
    tier: 1, model: 'tier1-sonnet', team: 'marketing', status: 'active',
    reports_to: 'jarvis',
    skills: ['brand-design', 'visual-identity', 'marketing-visuals', 'pitch-deck', 'ui-ux-specs', 'design-qa', 'social-media-graphics', 'presentation-design', 'infographic', 'icon-design', 'color-system', 'typography'],
  },
  {
    slug: 'satoshi', emoji: '₿', name: 'SATOSHI', role: 'Crypto & Trading Specialist',
    tier: 1, model: 'tier1-sonnet', team: 'crypto', status: 'standby',
    reports_to: 'jarvis',
    skills: ['portfolio-tracking', 'market-analysis', 'defi-strategy', 'risk-management', 'on-chain-analysis', 'whale-tracking', 'token-research', 'yield-farming', 'arbitrage-detection', 'sentiment-analysis'],
  },
  {
    slug: 'felix', emoji: '🤝', name: 'FELIX', role: 'Customer Success Lead',
    tier: 1, model: 'tier1-sonnet', team: 'customer-success', status: 'active',
    reports_to: 'jarvis',
    skills: ['customer-onboarding', 'support-response', 'health-scoring', 'churn-prevention', 'upsell-identification', 'feedback-analysis', 'satisfaction-surveys', 'ticket-management', 'escalation-handling', 'knowledge-base', 'customer-training'],
  },
  {
    slug: 'andreas', emoji: '🎯', name: 'ANDREAS', role: 'Customer Success SFE',
    tier: 2, model: 'tier1-haiku', team: 'customer-success', status: 'active',
    reports_to: 'jarvis',
    skills: ['process-docs', 'task-coordination', 'compliance-check', 'sfe-processes', 'performance-tracking', 'coaching-programs', 'playbook-creation', 'crm-optimization', 'benchmarking', 'sales-enablement', 'training-material'],
  },
];

// All skills from skills/*.json — used as fallback when API not available
export const SKILLS_REGISTRY: Skill[] = [
  // Global
  { slug: 'web-search', name: 'Web-Suche', description: 'Internet-Recherche in Echtzeit', category: 'global', requires_key: null, agents: ['all'], enabled: true },
  { slug: 'memory-store', name: 'Memory speichern', description: 'Fakten und Kontext dauerhaft speichern', category: 'global', requires_key: null, agents: ['all'], enabled: true },
  { slug: 'memory-recall', name: 'Memory abrufen', description: 'Gespeicherte Fakten aus der Datenbank abrufen', category: 'global', requires_key: null, agents: ['all'], enabled: true },
  { slug: 'task-create', name: 'Task erstellen', description: 'Neue Aufgabe für einen Agent erstellen', category: 'global', requires_key: null, agents: ['all'], enabled: true },
  { slug: 'task-delegate', name: 'Task delegieren', description: 'Aufgabe an einen anderen Agent weitergeben', category: 'global', requires_key: null, agents: ['jarvis', 'elon'], enabled: true },
  { slug: 'telegram-send', name: 'Telegram senden', description: 'Nachricht via Telegram Bot senden', category: 'global', requires_key: 'TELEGRAM_BOT_TOKEN', agents: ['jarvis', 'elon'], enabled: false },
  { slug: 'email-send', name: 'E-Mail senden', description: 'E-Mail versenden', category: 'global', requires_key: null, agents: ['donna', 'steve', 'donald', 'felix'], enabled: true },

  // Analytics
  { slug: 'data-analysis', name: 'Datenanalyse', description: 'Daten analysieren, Muster erkennen, visualisieren', category: 'analytics', requires_key: null, agents: ['elon'], enabled: true },
  { slug: 'kpi-tracking', name: 'KPI Tracking', description: 'Key Performance Indicators überwachen und reporten', category: 'analytics', requires_key: null, agents: ['elon'], enabled: true },
  { slug: 'competitive-intel', name: 'Competitive Intel', description: 'Wettbewerber beobachten und analysieren', category: 'analytics', requires_key: null, agents: ['elon'], enabled: true },
  { slug: 'market-research', name: 'Marktforschung', description: 'Marktanalyse, Trends und Opportunities erkennen', category: 'analytics', requires_key: null, agents: ['elon'], enabled: true },
  { slug: 'bottleneck-finder', name: 'Bottleneck Finder', description: 'Engpässe in Prozessen, Budget und Zeit identifizieren', category: 'analytics', requires_key: null, agents: ['elon'], enabled: true },
  { slug: 'weekly-report', name: 'Wochenbericht', description: 'Wöchentlichen Gesamtbericht für DOM erstellen', category: 'analytics', requires_key: null, agents: ['elon', 'jarvis'], enabled: true },

  // Marketing
  { slug: 'content-creation', name: 'Content erstellen', description: 'Texte, Posts, Artikel, Newsletter schreiben', category: 'marketing', requires_key: null, agents: ['steve', 'iris'], enabled: true },
  { slug: 'social-media-post', name: 'Social Media Post', description: 'Automatisch auf Social Media posten', category: 'marketing', requires_key: 'INSTAGRAM_TOKEN', agents: ['steve'], enabled: false },
  { slug: 'seo-analysis', name: 'SEO-Analyse', description: 'Keywords, Rankings und SEO-Optimierung', category: 'marketing', requires_key: null, agents: ['steve'], enabled: true },
  { slug: 'video-scripts', name: 'Video-Skripte', description: 'Skripte für YouTube, Reels, TikTok', category: 'marketing', requires_key: null, agents: ['steve', 'iris'], enabled: true },
  { slug: 'ad-copy', name: 'Ad Copy', description: 'Werbetexte für Google Ads, Meta Ads', category: 'marketing', requires_key: null, agents: ['steve'], enabled: true },
  { slug: 'brand-voice-check', name: 'Brand Voice Check', description: 'Prüfen ob Content der Markenidentität entspricht', category: 'marketing', requires_key: null, agents: ['steve', 'iris'], enabled: true },
  { slug: 'email-newsletter', name: 'Newsletter', description: 'Newsletter erstellen und versenden', category: 'marketing', requires_key: null, agents: ['steve'], enabled: true },
  { slug: 'linkedin-post', name: 'LinkedIn Post', description: 'LinkedIn-Beitrag erstellen und posten', category: 'marketing', requires_key: 'LINKEDIN_TOKEN', agents: ['steve'], enabled: false },
  { slug: 'twitter-post', name: 'X/Twitter Post', description: 'Tweet oder Thread erstellen und posten', category: 'marketing', requires_key: 'TWITTER_BEARER_TOKEN', agents: ['steve'], enabled: false },

  // Sales
  { slug: 'lead-generation', name: 'Lead-Generierung', description: 'Potenzielle Kunden über LinkedIn, Web-Research finden', category: 'sales', requires_key: null, agents: ['donald'], enabled: true },
  { slug: 'lead-qualification', name: 'Lead-Qualifizierung', description: 'Leads nach BANT/MEDDIC bewerten und priorisieren', category: 'sales', requires_key: null, agents: ['donald'], enabled: true },
  { slug: 'email-outreach', name: 'E-Mail Outreach', description: 'Personalisierte Cold E-Mails erstellen und senden', category: 'sales', requires_key: null, agents: ['donald'], enabled: true },
  { slug: 'linkedin-outreach', name: 'LinkedIn Outreach', description: 'LinkedIn-Nachrichten und Connection Requests', category: 'sales', requires_key: 'LINKEDIN_TOKEN', agents: ['donald'], enabled: false },
  { slug: 'crm-hubspot', name: 'HubSpot CRM', description: 'Kontakte, Deals und Pipeline in HubSpot verwalten', category: 'sales', requires_key: 'HUBSPOT_API_KEY', agents: ['donald'], enabled: false },
  { slug: 'crm-airtable', name: 'Airtable CRM', description: 'Airtable als leichtgewichtiges CRM nutzen', category: 'sales', requires_key: 'AIRTABLE_API_KEY', agents: ['donald'], enabled: false },
  { slug: 'proposal-writer', name: 'Angebote schreiben', description: 'Professionelle Proposals und Angebote erstellen', category: 'sales', requires_key: null, agents: ['donald'], enabled: true },
  { slug: 'followup-sequences', name: 'Follow-up Sequenzen', description: 'Automatische Follow-up E-Mail-Ketten', category: 'sales', requires_key: null, agents: ['donald'], enabled: true },
  { slug: 'pipeline-tracker', name: 'Pipeline Tracker', description: 'Sales Pipeline überwachen und forecasen', category: 'sales', requires_key: null, agents: ['donald'], enabled: true },
  { slug: 'revenue-reporting', name: 'Revenue Reports', description: 'MRR, ARR, CAC, LTV Berichte erstellen', category: 'sales', requires_key: null, agents: ['donald', 'elon'], enabled: true },

  // Development
  { slug: 'code-generation', name: 'Code generieren', description: 'Code in jeder Sprache schreiben und generieren', category: 'development', requires_key: null, agents: ['archi'], enabled: true },
  { slug: 'code-review', name: 'Code Review', description: 'Code analysieren, Bugs finden, Verbesserungen vorschlagen', category: 'development', requires_key: null, agents: ['archi'], enabled: true },
  { slug: 'bug-analysis', name: 'Bug-Analyse', description: 'Fehler analysieren und Lösungsvorschläge machen', category: 'development', requires_key: null, agents: ['archi'], enabled: true },
  { slug: 'github-issues', name: 'GitHub Issues', description: 'Issues erstellen, labeln, zuweisen und verwalten', category: 'development', requires_key: null, agents: ['archi'], enabled: true },
  { slug: 'github-prs', name: 'GitHub PRs', description: 'Pull Requests erstellen und reviewen', category: 'development', requires_key: null, agents: ['archi'], enabled: true },
  { slug: 'docker-manage', name: 'Docker Management', description: 'Container starten, stoppen, logs lesen, debuggen', category: 'development', requires_key: null, agents: ['archi'], enabled: true },
  { slug: 'deploy', name: 'Deployment', description: 'Code auf Staging/Production deployen', category: 'development', requires_key: null, agents: ['archi'], enabled: true },
  { slug: 'security-scan', name: 'Security Scan', description: 'Sicherheitsanalyse und Vulnerability-Check', category: 'development', requires_key: null, agents: ['archi'], enabled: true },

  // Operations
  { slug: 'email-management', name: 'E-Mail Management', description: 'Postfach verwalten, triagieren, beantworten', category: 'operations', requires_key: null, agents: ['donna'], enabled: true },
  { slug: 'calendar-manage', name: 'Kalender', description: 'Google Calendar Termine planen und koordinieren', category: 'operations', requires_key: null, agents: ['donna'], enabled: true },
  { slug: 'document-creation', name: 'Dokumente erstellen', description: 'Dokumente, Templates, SOPs erstellen', category: 'operations', requires_key: null, agents: ['donna'], enabled: true },
  { slug: 'invoice-create', name: 'Rechnungen', description: 'Rechnungen erstellen und versenden', category: 'operations', requires_key: null, agents: ['donna'], enabled: true },
  { slug: 'process-docs', name: 'Prozess-Docs', description: 'SOPs und Prozesse dokumentieren', category: 'operations', requires_key: null, agents: ['donna', 'andreas'], enabled: true },
  { slug: 'compliance-check', name: 'Compliance Check', description: 'DSGVO und regulatorische Compliance prüfen', category: 'operations', requires_key: null, agents: ['donna', 'andreas'], enabled: true },
  { slug: 'meeting-notes', name: 'Meeting Notes', description: 'Meeting-Notizen erstellen und Action Items tracken', category: 'operations', requires_key: null, agents: ['donna'], enabled: true },

  // Crypto
  { slug: 'portfolio-tracking', name: 'Portfolio Tracking', description: 'Crypto-Portfolio Performance überwachen', category: 'crypto', requires_key: null, agents: ['satoshi'], enabled: true },
  { slug: 'market-analysis', name: 'Markt-Analyse', description: 'Krypto-Markt analysieren, Trends erkennen', category: 'crypto', requires_key: null, agents: ['satoshi'], enabled: true },
  { slug: 'defi-strategy', name: 'DeFi Strategy', description: 'DeFi-Strategien entwickeln und bewerten', category: 'crypto', requires_key: null, agents: ['satoshi'], enabled: true },
  { slug: 'risk-management', name: 'Risk Management', description: 'Portfolio-Risiko bewerten, Stop-Loss setzen', category: 'crypto', requires_key: null, agents: ['satoshi'], enabled: true },
];

// Category metadata
export const SKILL_CATEGORIES: Record<string, { label: string; color: string; icon: string }> = {
  global: { label: 'Global', color: 'text-primary', icon: '🌐' },
  analytics: { label: 'Analytics & Intelligence', color: 'text-jarvis-purple', icon: '📊' },
  marketing: { label: 'Marketing & Content', color: 'text-jarvis-gold', icon: '📢' },
  sales: { label: 'Sales & Revenue', color: 'text-jarvis-success', icon: '💰' },
  development: { label: 'Development & DevOps', color: 'text-jarvis-cyan', icon: '🛠' },
  operations: { label: 'Operations & Backoffice', color: 'text-muted-foreground', icon: '📋' },
  crypto: { label: 'Crypto & Trading', color: 'text-jarvis-warning', icon: '₿' },
};
