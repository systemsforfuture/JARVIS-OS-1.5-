---
summary: "ARCHI Code-Standards — Clean Code, Patterns, TypeScript, React, Node, Python, Docker"
read_when:
  - Before writing ANY code
  - Before code review
  - When setting up new project
---

# CODE-STANDARDS.md — Wie ich Code schreibe

## Philosophie

> "Code wird einmal geschrieben und hundertmal gelesen. Schreib für den Leser, nicht für den Compiler."

Jede Zeile Code muss:
1. **Sofort verständlich** sein — ohne Kommentar, ohne Kontext
2. **Einen Zweck** haben — keine toten Zeilen, keine "für später"
3. **Production-ready** sein — Error Handling, Edge Cases, Logging

---

## 1. UNIVERSAL RULES (alle Sprachen)

### Naming
```
VARIABLEN:  Was sie ENTHALTEN     → userEmail, invoiceTotal, isActive
FUNKTIONEN: Was sie TUN           → fetchLeads(), calculateRevenue(), sendInvoice()
BOOLEANS:   Frage die JA/NEIN ist → isValid, hasAccess, canEdit, shouldRetry
KONSTANTEN: SCREAMING_SNAKE       → MAX_RETRIES, API_TIMEOUT, DEFAULT_LIMIT
```

**Verboten:** `data`, `info`, `temp`, `tmp`, `x`, `val`, `item`, `stuff`, `handler` (ohne Kontext)

### Funktionen
- **Max 30 Zeilen.** Länger? → Aufteilen.
- **Max 3 Parameter.** Mehr? → Object-Parameter.
- **Single Responsibility.** Eine Funktion = eine Aufgabe.
- **Keine Seiteneffekte** wo nicht erwartet. Getter verändert nichts. Setter returned nichts.
- **Early Return** statt tiefe Verschachtelung:

```typescript
// ❌ SCHLECHT
function processLead(lead: Lead) {
  if (lead) {
    if (lead.email) {
      if (lead.score > 50) {
        // ... actual logic buried 3 levels deep
      }
    }
  }
}

// ✅ GUT
function processLead(lead: Lead) {
  if (!lead) return;
  if (!lead.email) return;
  if (lead.score <= 50) return;
  // ... actual logic at top level
}
```

### Error Handling
```
REGEL 1: Nie errors schlucken (catch ohne action)
REGEL 2: Immer den KONTEXT loggen (was war der Input? welche Operation?)
REGEL 3: Fail gracefully — User sieht "Fehler aufgetreten", Logs zeigen Details
REGEL 4: Retry-Logic für Network Calls (3 Versuche, exponential backoff)
REGEL 5: Kein throw ohne catch. Kein catch ohne log.
```

### Kommentare
```
ÜBERFLÜSSIG: // increment counter    → der Code sagt es bereits
NÜTZLICH:    // DEALIO hat Sonder-Directory-Struktur (Bug-Fix 26.02.2026)
PFLICHT:     // TODO: [TASK-ID] Implement rate limiting before launch
VERBOTEN:    // HACK: this somehow works, don't touch
```

### Keine Magic Numbers/Strings
```typescript
// ❌
if (response.status === 429) { await sleep(60000); }

// ✅
const RATE_LIMIT_STATUS = 429;
const RATE_LIMIT_COOLDOWN_MS = 60_000;
if (response.status === RATE_LIMIT_STATUS) {
  await sleep(RATE_LIMIT_COOLDOWN_MS);
}
```

---

## 2. TYPESCRIPT / JAVASCRIPT

### Type System
```typescript
// Immer explizite Typen — KEIN any
interface Lead {
  id: string;
  name: string;
  email: string;
  score: number;
  stage: 'new' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost';
  firma: string;
  createdAt: Date;
}

// Utility Types nutzen
type LeadUpdate = Partial<Pick<Lead, 'score' | 'stage'>>;
type LeadSummary = Pick<Lead, 'id' | 'name' | 'score'>;
```

### Async / Await
```typescript
// ❌ Callback Hell oder .then Ketten
fetch(url).then(r => r.json()).then(data => { ... }).catch(e => { ... });

// ✅ Async/Await mit Error Handling
async function fetchLeads(company?: string): Promise<Lead[]> {
  try {
    const url = company ? `/api/leads?company=${company}` : '/api/leads';
    const response = await fetch(url);
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('[fetchLeads] Failed:', { company, error });
    return []; // Graceful fallback
  }
}
```

### Null Safety
```typescript
// Optional Chaining + Nullish Coalescing
const userName = lead?.contact?.name ?? 'Unknown';
const score = lead?.score ?? 0;
```

---

## 3. REACT / FRONTEND

### Component-Struktur
```
1 Component = 1 Datei
Max 200 Zeilen pro Component (darüber → aufteilen)
Funktionale Components + Hooks (KEINE Klassen)
```

### Component-Pattern
```tsx
interface AgentCardProps {
  agent: Agent;
  onSelect?: (id: string) => void;
}

export default function AgentCard({ agent, onSelect }: AgentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Event Handler oben, Render unten
  const handleClick = () => onSelect?.(agent.id);

  // Early return für Edge Cases
  if (!agent) return null;

  return (
    <div className="rounded-lg bg-gray-800 p-4" onClick={handleClick}>
      <h3 className="text-lg font-semibold">{agent.name}</h3>
      {isExpanded && <AgentDetails agent={agent} />}
    </div>
  );
}
```

### State Management
```
LOCAL STATE  (useState)    → UI-State: isOpen, isLoading, filterValue
LIFTED STATE (props)       → Shared zwischen 2-3 Components
CONTEXT      (useContext)  → App-weite Daten: Theme, User, Config
KEIN Redux/Zustand         → Zu komplex für unser Setup. Context reicht.
```

### Styling (Tailwind)
```
IMMER: Dark Mode Support (bg-gray-800, text-gray-100 etc.)
IMMER: Mobile Responsive (sm:, md:, lg: Breakpoints)
IMMER: Hover/Focus States für interaktive Elemente
NIE:   Inline Styles
NIE:   !important
NIE:   Eigene CSS-Dateien wenn Tailwind reicht
```

### Performance
```
useMemo     → Für teure Berechnungen (Filtering, Sorting)
useCallback → Für Event Handler die als Props weitergegeben werden
React.memo  → Für Components die sich selten ändern
Lazy Loading → Für Routes und schwere Components
```

---

## 4. NODE.JS / BACKEND

### API Design
```typescript
// RESTful Conventions
GET    /api/leads              → Liste aller Leads
GET    /api/leads?company=X    → Gefiltert nach Firma
GET    /api/leads/:id          → Einzelner Lead
POST   /api/leads              → Lead erstellen
PUT    /api/leads/:id          → Lead komplett updaten
PATCH  /api/leads/:id          → Lead teilweise updaten
DELETE /api/leads/:id          → Lead löschen (soft delete!)

// Response Format — IMMER konsistent
{
  "success": true,
  "data": { ... },
  "timestamp": 1708771200000
}

// Error Response
{
  "success": false,
  "error": "Lead not found",
  "code": "LEAD_NOT_FOUND",
  "timestamp": 1708771200000
}
```

### Input Validation
```typescript
// JEDER Endpoint validiert Input. Trust nothing.
app.get('/api/leads', (req, res) => {
  const company = typeof req.query.company === 'string' ? req.query.company : undefined;
  const stage = typeof req.query.stage === 'string' ? req.query.stage : undefined;
  const limit = Math.min(parseInt(req.query.limit) || 50, 500); // Cap at 500
  // ...
});
```

### Middleware Pattern
```
Request → Auth → Validate → Rate Limit → Handler → Response
                                            ↓
                                     Error Handler → Error Response + Log
```

---

## 5. PYTHON (Brain, Scripts, Automation)

```python
# Type Hints IMMER
def search_brain(query: str, collection: str = "knowledge", limit: int = 5) -> list[dict]:
    """Semantische Suche im Brain System."""
    ...

# Docstrings für public Functions
# f-Strings statt .format() oder %
# Context Managers für Files/Connections
with open(filepath, 'r') as f:
    data = json.load(f)

# Kein bare except
try:
    result = api_call()
except requests.RequestException as e:
    logger.error(f"API call failed: {e}")
    raise
```

---

## 6. DOCKER

### Dockerfile
```dockerfile
# Multi-stage Build wenn möglich
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

# Non-root User
USER node

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1

EXPOSE 3001
CMD ["node", "dist/server.js"]
```

### docker-compose
```yaml
# Immer:
- Resource Limits (mem_limit, cpus)
- Health Checks
- Restart Policy (unless-stopped)
- Named Volumes (nicht bind mounts in prod)
- Logging Config
```

---

## 7. SECURITY IN CODE

```
□ Keine Secrets im Code — .env oder Vault
□ .gitignore korrekt (node_modules, .env, dist, *.log)
□ Input Validation auf JEDEM Endpoint
□ SQL Injection Prevention (Parameterized Queries)
□ XSS Prevention (React escaped by default, aber raw HTML prüfen)
□ CORS korrekt (nicht * in Production)
□ Rate Limiting auf öffentlichen Endpoints
□ Dependency Audit (npm audit regelmäßig)
□ Keine eval(), keine dynamischen require()
□ Kein console.log mit sensitiven Daten
```

---

## 8. PERFORMANCE TARGETS

| Was | Target | Messen |
|---|---|---|
| API Response | < 500ms (Standard), < 200ms (Simple GET) | `curl -w "%{time_total}"` |
| Page Load | < 2s (First Contentful Paint) | Lighthouse |
| Bundle Size | < 500KB gzipped | `npm run build` output |
| Docker Start | < 30s | `time docker-compose up` |
| DB Query | < 100ms | Query logging |
| Build Time | < 30s | CI/CD Pipeline |

---

## 9. DEFINITION OF DONE

Bevor Code als "fertig" gilt:
```
□ TypeScript kompiliert clean (0 Errors, 0 Warnings)
□ Build successful
□ Kein console.log in Production Code
□ Error Handling vollständig (keine unhandled promises)
□ Input Validation auf allen Endpoints
□ Dark Mode getestet
□ Mobile Responsive getestet
□ Keine Hardcoded Secrets
□ Keine TODO/FIXME ohne Task-ID
□ Commit Message nach Convention
□ Delivery Report geschrieben
```

_CODE-STANDARDS.md ist lebendig. Neue Patterns gelernt → update it._
