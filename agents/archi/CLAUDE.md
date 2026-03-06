# CLAUDE.md — Mission Control Project Instructions

## Project
Mission Control Dashboard for SYSTEMS™ Empire — 13 digital companies under one roof.
Internal tool. No external users. Dark mode only. Mobile responsive.

## Stack
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS
- Backend: Node.js + Express (server.js, Port 3001)
- No database — Filesystem-based (JSON files, Markdown queues)
- No auth — Internal network only

## Architecture
```
src/pages/           → One file per route (e.g., SalesPage.tsx)
src/components/      → Shared UI components
server.js            → Express backend, all /api/* endpoints
dist/                → Build output (never edit manually)
```

## Code Style

### TypeScript
- Explicit types always. No `any`. No `as unknown as X`.
- Use interfaces for data shapes, types for unions/aliases.
- Prefer `const` over `let`. Never `var`.

### React Components
- Functional components + hooks only. No classes.
- One component per file. Max 200 lines.
- Props interface above component. Default export.
- Pattern:
```tsx
interface Props {
  title: string;
  items: Item[];
  onSelect?: (id: string) => void;
}

export default function MyComponent({ title, items, onSelect }: Props) {
  const [filter, setFilter] = useState('');

  const filtered = useMemo(
    () => items.filter(i => i.name.includes(filter)),
    [items, filter]
  );

  if (!items.length) return <EmptyState message="No items" />;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      {/* content */}
    </div>
  );
}
```

### Tailwind
- Dark mode is DEFAULT. Base: `bg-gray-950 text-gray-100`
- Cards: `bg-gray-800/60 border border-gray-700/50 rounded-xl`
- Accent: `text-blue-400`, `bg-blue-500/10`
- Status colors: green-400 (good), yellow-400 (warn), red-400 (error)
- Always mobile responsive: Use `sm:`, `md:`, `lg:` breakpoints

### API Endpoints
- All routes under `/api/`
- Response format: `{ success: boolean, data: T, timestamp: number }`
- Error format: `{ success: false, error: string, code: string }`
- Validate all query params. Never trust input.
- Pattern:
```js
app.get('/api/leads', (req, res) => {
  try {
    const company = typeof req.query.company === 'string' ? req.query.company : undefined;
    const limit = Math.min(parseInt(req.query.limit) || 50, 500);
    // ... read from filesystem
    res.json({ success: true, data: leads, timestamp: Date.now() });
  } catch (error) {
    console.error('[/api/leads]', error);
    res.status(500).json({ success: false, error: 'Internal error', code: 'LEADS_ERROR' });
  }
});
```

## Domain Types
```typescript
// These are the core types of the Empire. Use them everywhere.

type CompanyId = 'systems' | 'dwmuc' | 'wrana-holding' | 'wac' | 'sfe' |
  'dealio' | 'snip' | 'devcode' | 'leadjet' | 'business-market' |
  'vesnaink' | 'easyseven' | 'elanseven';

interface Lead {
  id: string;
  name: string;
  email: string;
  company: string;           // Which of our 13 companies
  source: string;             // Where the lead came from
  score: number;              // 0-100
  stage: 'new' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost';
  assignedTo?: string;        // Agent ID (donald, donna, etc.)
  createdAt: string;
  updatedAt: string;
}

interface Agent {
  id: string;                 // e.g., 'jarvis', 'archi', 'donna'
  name: string;               // Display name
  emoji: string;
  role: string;
  team: string;               // e.g., 'DEV', 'BACKOFFICE', 'SALES'
  status: 'active' | 'idle' | 'error' | 'offline';
  lastSeen?: string;
  currentTask?: string;
  model: string;              // e.g., 'haiku-4.5', 'sonnet-4.5'
}

interface Task {
  id: string;                 // e.g., 'MC-042'
  title: string;
  description: string;
  team: string;
  assignedTo: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'new' | 'in-progress' | 'review' | 'done' | 'rejected';
  createdAt: string;
  deadline?: string;
}

interface Company {
  id: CompanyId;
  name: string;
  status: 'pre-revenue' | 'traction' | 'revenue' | 'scaling';
  revenue: number;
  customers: number;
  tier: 1 | 2 | 3;
}
```

## Filesystem Paths
```
/data/agents/                          → All agent configs and queues
/data/agents/scripts/                  → Shared scripts (tg-send, brain-*, pipeline-manager)
/data/agents/_DAILY-REPORTS/[TEAM]/    → Daily reports per team
/data/agents/DEV/ARCHITECT/tasks/      → Dev team task queue
/data/unternehmen/[FIRMA]/_SALES/      → Sales pipeline per company
/data/mission-control/repo/            → This project
```

## Commands
```bash
# Dev
npm run dev                    # Vite dev server on :5173

# Build
npm run build                  # Production build to dist/

# Server
node server.js                 # Express on :3001 (serves API + static)

# Deploy (production)
cd /data/mission-control/repo/
git pull && npm run build && pm2 restart server
```

## Rules
1. Build must be clean — 0 errors, 0 warnings.
2. No console.log in production code. Use proper error logging.
3. No hardcoded secrets, URLs, or IDs. Use constants or env vars.
4. Every API endpoint validates input and returns consistent format.
5. Every page must work on mobile (test at 375px width).
6. Existing features must not break. Always verify after changes.
