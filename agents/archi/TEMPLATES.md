---
summary: "ARCHI Code Templates — Copy-paste Boilerplate für neue Pages, Components, APIs"
read_when:
  - When creating new pages
  - When creating new components
  - When adding API endpoints
---

# TEMPLATES.md — Fertige Vorlagen

## 1. NEUE PAGE (Dashboard Route)

```tsx
// src/pages/[Name]Page.tsx
import { useState, useEffect, useMemo } from 'react';

interface PageData {
  // Define your data shape
  items: Item[];
  stats: { total: number; active: number };
}

export default function [Name]Page() {
  const [data, setData] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000); // Auto-refresh 30s
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const res = await fetch('/api/[endpoint]');
      if (!res.ok) throw new Error(`API Error: ${res.status}`);
      const json = await res.json();
      if (json.success) setData(json.data);
      else throw new Error(json.error);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-gray-400 animate-pulse">Laden...</div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400">
        {error}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold">[Title]</h1>
        <input
          type="text"
          placeholder="Filter..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm
                     focus:outline-none focus:border-blue-500 w-full sm:w-64"
        />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total" value={data?.stats.total ?? 0} />
        <StatCard label="Active" value={data?.stats.active ?? 0} color="green" />
      </div>

      {/* Main Content */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl overflow-hidden">
        {/* Table or List */}
      </div>
    </div>
  );
}

function StatCard({ label, value, color = 'blue' }: {
  label: string;
  value: number;
  color?: 'blue' | 'green' | 'yellow' | 'red';
}) {
  const colors = {
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    green: 'text-green-400 bg-green-500/10 border-green-500/20',
    yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    red: 'text-red-400 bg-red-500/10 border-red-500/20',
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm opacity-70">{label}</div>
    </div>
  );
}
```

**Danach in App.tsx registrieren:**
```tsx
import [Name]Page from './pages/[Name]Page';
// In Routes: <Route path="/[route]" element={<[Name]Page />} />
```

---

## 2. SHARED COMPONENT

```tsx
// src/components/[Name].tsx
interface [Name]Props {
  // Required props
  title: string;
  // Optional props with defaults
  variant?: 'default' | 'compact';
  className?: string;
}

export default function [Name]({
  title,
  variant = 'default',
  className = '',
}: [Name]Props) {
  return (
    <div className={`bg-gray-800/60 border border-gray-700/50 rounded-xl p-4 ${className}`}>
      <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
      {/* Content */}
    </div>
  );
}
```

---

## 3. API ENDPOINT (Express)

```javascript
// In server.js — neuen Endpoint hinzufügen

// GET /api/[resource]
app.get('/api/[resource]', (req, res) => {
  try {
    // 1. Input validieren
    const company = typeof req.query.company === 'string' ? req.query.company : undefined;
    const limit = Math.min(parseInt(req.query.limit) || 50, 500);

    // 2. Daten lesen (Filesystem)
    const dataPath = path.join(__dirname, 'data', '[resource]');
    if (!fs.existsSync(dataPath)) {
      return res.json({ success: true, data: [], timestamp: Date.now() });
    }

    let items = [];
    const files = fs.readdirSync(dataPath).filter(f => f.endsWith('.json'));
    for (const file of files) {
      const content = JSON.parse(fs.readFileSync(path.join(dataPath, file), 'utf8'));
      items.push(content);
    }

    // 3. Filtern
    if (company) {
      items = items.filter(item => item.company === company);
    }

    // 4. Response
    res.json({
      success: true,
      data: items.slice(0, limit),
      total: items.length,
      timestamp: Date.now()
    });

  } catch (error) {
    console.error('[/api/[resource]]', error);
    res.status(500).json({
      success: false,
      error: 'Internal error',
      code: '[RESOURCE]_ERROR',
      timestamp: Date.now()
    });
  }
});
```

---

## 4. DATA TABLE COMPONENT

```tsx
// Wiederverwendbare Tabelle für alle Dashboard-Seiten
interface Column<T> {
  key: keyof T;
  label: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
}

export default function DataTable<T extends { id: string }>({
  data, columns, emptyMessage = 'Keine Daten', onRowClick
}: DataTableProps<T>) {
  if (!data.length) {
    return (
      <div className="text-center py-12 text-gray-500">{emptyMessage}</div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-700/50">
            {columns.map(col => (
              <th key={String(col.key)}
                  className="text-left text-xs font-medium text-gray-400 uppercase px-4 py-3">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.id}
                onClick={() => onRowClick?.(row)}
                className="border-b border-gray-800 hover:bg-gray-800/40 cursor-pointer transition">
              {columns.map(col => (
                <td key={String(col.key)} className={`px-4 py-3 ${col.className ?? ''}`}>
                  {col.render
                    ? col.render(row[col.key], row)
                    : String(row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 5. STATUS BADGE COMPONENT

```tsx
const STATUS_CONFIG = {
  active:   { label: 'Active',   bg: 'bg-green-500/10',  text: 'text-green-400',  dot: 'bg-green-400' },
  idle:     { label: 'Idle',     bg: 'bg-gray-500/10',   text: 'text-gray-400',   dot: 'bg-gray-400' },
  error:    { label: 'Error',    bg: 'bg-red-500/10',    text: 'text-red-400',    dot: 'bg-red-400' },
  offline:  { label: 'Offline',  bg: 'bg-gray-500/10',   text: 'text-gray-600',   dot: 'bg-gray-600' },
  new:      { label: 'Neu',      bg: 'bg-blue-500/10',   text: 'text-blue-400',   dot: 'bg-blue-400' },
  won:      { label: 'Won',      bg: 'bg-green-500/10',  text: 'text-green-400',  dot: 'bg-green-400' },
  lost:     { label: 'Lost',     bg: 'bg-red-500/10',    text: 'text-red-400',    dot: 'bg-red-400' },
} as const;

type StatusKey = keyof typeof STATUS_CONFIG;

export default function StatusBadge({ status }: { status: StatusKey }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.idle;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}
```

---

## 6. FETCH HOOK (Wiederverwendbar)

```tsx
// src/hooks/useFetch.ts
import { useState, useEffect, useCallback } from 'react';

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFetch<T>(
  url: string,
  refreshInterval?: number
): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${res.status}`);
      const json = await res.json();
      if (json.success) {
        setData(json.data);
        setError(null);
      } else {
        throw new Error(json.error ?? 'API Error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
    if (refreshInterval) {
      const id = setInterval(fetchData, refreshInterval);
      return () => clearInterval(id);
    }
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Usage:
// const { data, loading, error } = useFetch<Lead[]>('/api/leads', 30_000);
```

---

## 7. BASH SCRIPT (Agent-Tool)

```bash
#!/bin/bash
# /data/agents/scripts/[name].sh
# Beschreibung: [Was dieses Script tut]

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/data/agents/logs/[name].log"

# Functions
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
die() { log "ERROR: $*"; exit 1; }

# Validation
[[ $# -lt 1 ]] && die "Usage: $0 <param>"

# Main
main() {
  local param="$1"
  log "Starting with param=$param"

  # ... actual logic ...

  log "Done"
}

main "$@"
```

---

## USAGE RULES

1. **Neue Page?** → Template 1 kopieren, `[Name]` ersetzen, in App.tsx Route hinzufügen.
2. **Neues Component?** → Template 2 kopieren. Props-Interface zuerst definieren.
3. **Neuer API Endpoint?** → Template 3 in server.js einfügen. Input validieren!
4. **Tabelle?** → DataTable Component (Template 4) nutzen. Nicht jede Page eigene Tabelle.
5. **Status anzeigen?** → StatusBadge (Template 5). Farben konsistent halten.
6. **Daten fetchen?** → useFetch Hook (Template 6). Nicht jede Page eigenes useEffect.

_Templates werden bei neuen Patterns ergänzt._
