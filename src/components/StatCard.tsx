interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  colorClass?: string;
  icon?: React.ReactNode;
}

export function StatCard({ title, value, subtitle, colorClass = 'text-primary', icon }: StatCardProps) {
  return (
    <div className="hud-card rounded-lg p-5 transition-all hover:hud-glow group">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[10px] font-display font-semibold tracking-[0.15em] text-muted-foreground uppercase">{title}</div>
        {icon && <div className={`${colorClass} opacity-50 group-hover:opacity-100 transition-opacity`}>{icon}</div>}
      </div>
      <div className={`text-3xl font-display font-bold ${colorClass}`}>{value}</div>
      {subtitle && <div className="text-xs text-muted-foreground mt-1.5 font-body">{subtitle}</div>}
    </div>
  );
}
