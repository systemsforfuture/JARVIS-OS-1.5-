import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { Task } from "@/lib/types";
import { Clock, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

type PipelineColumn = 'pending' | 'in_progress' | 'completed' | 'failed';

const COLUMNS: { key: PipelineColumn; label: string; icon: React.ReactNode; color: string; borderColor: string }[] = [
  { key: 'pending', label: 'WARTESCHLANGE', icon: <Clock className="w-3.5 h-3.5" />, color: 'text-jarvis-warning', borderColor: 'border-jarvis-warning/30' },
  { key: 'in_progress', label: 'IN BEARBEITUNG', icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />, color: 'text-primary', borderColor: 'border-primary/30' },
  { key: 'completed', label: 'ERLEDIGT', icon: <CheckCircle2 className="w-3.5 h-3.5" />, color: 'text-jarvis-success', borderColor: 'border-jarvis-success/30' },
  { key: 'failed', label: 'FEHLGESCHLAGEN', icon: <AlertCircle className="w-3.5 h-3.5" />, color: 'text-jarvis-error', borderColor: 'border-jarvis-error/30' },
];

function TaskCard({ task }: { task: Task }) {
  const priorityColor = task.priority <= 1 ? 'bg-jarvis-error/15 text-jarvis-error' : task.priority <= 2 ? 'bg-jarvis-warning/15 text-jarvis-warning' : 'bg-muted text-muted-foreground';
  
  return (
    <div className="hud-card rounded-lg p-3.5 hover:hud-glow transition-all group">
      <div className="text-sm font-semibold mb-2 leading-tight">{task.title}</div>
      <div className="flex items-center gap-2 flex-wrap">
        {task.agent_slug && (
          <span className="text-[10px] font-mono bg-primary/10 border border-primary/20 text-primary px-1.5 py-0.5 rounded">
            {task.agent_slug.toUpperCase()}
          </span>
        )}
        <span className={`text-[10px] font-display font-semibold tracking-wider px-1.5 py-0.5 rounded ${priorityColor}`}>
          P{task.priority}
        </span>
        {task.tokens_used > 0 && (
          <span className="text-[10px] font-mono text-muted-foreground">
            {Number(task.tokens_used).toLocaleString()} tok
          </span>
        )}
      </div>
      {task.created_at && (
        <div className="text-[10px] font-mono text-muted-foreground mt-2">
          {new Date(task.created_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
        </div>
      )}
    </div>
  );
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Task[]>('/api/tasks?limit=50')
      .then(data => { if (Array.isArray(data)) setTasks(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const grouped = COLUMNS.map(col => ({
    ...col,
    tasks: tasks.filter(t => {
      if (col.key === 'in_progress') return t.status === 'in_progress' || t.status === 'running';
      return t.status === col.key;
    }),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <div className="w-1 h-6 bg-jarvis-warning rounded-full" />
        <h2 className="font-display text-xs font-bold tracking-[0.2em]">TASK PIPELINE</h2>
        <span className="text-[10px] font-mono text-muted-foreground ml-2">{tasks.length} Tasks</span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
        </div>
      ) : tasks.length === 0 ? (
        <div className="hud-card rounded-xl p-16 text-center">
          <div className="text-4xl mb-3 opacity-30">⚡</div>
          <div className="font-display text-xs tracking-[0.15em] text-muted-foreground">KEINE TASKS IN DER PIPELINE</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 items-start">
          {grouped.map(col => (
            <div key={col.key} className={`rounded-xl border ${col.borderColor} bg-card/50 overflow-hidden`}>
              {/* Column Header */}
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <div className={`flex items-center gap-2 ${col.color}`}>
                  {col.icon}
                  <span className="font-display text-[10px] font-bold tracking-[0.12em]">{col.label}</span>
                </div>
                <span className={`text-[11px] font-mono font-bold ${col.color}`}>{col.tasks.length}</span>
              </div>
              {/* Tasks */}
              <div className="p-2 space-y-2 min-h-[120px] max-h-[70vh] overflow-y-auto">
                {col.tasks.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-[10px] font-display tracking-wider text-muted-foreground/50">LEER</div>
                  </div>
                ) : (
                  col.tasks.map(task => <TaskCard key={task.id} task={task} />)
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
