interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  colorClass?: string;
}

export function StatCard({ title, value, subtitle, colorClass = 'text-primary' }: StatCardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-5 transition-all hover:border-muted-foreground/30 hover:-translate-y-px">
      <div className="text-sm font-medium text-muted-foreground mb-3">{title}</div>
      <div className={`text-[32px] font-bold font-mono ${colorClass}`}>{value}</div>
      {subtitle && <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>}
    </div>
  );
}
