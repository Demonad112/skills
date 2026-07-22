export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-300 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200 px-4 py-3 text-sm">
      {message}
    </div>
  );
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-lg border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4 ${className}`}
    >
      {children}
    </div>
  );
}

export function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-gray-500">{label}</span>
      <span className="text-2xl font-semibold">{value}</span>
    </Card>
  );
}
