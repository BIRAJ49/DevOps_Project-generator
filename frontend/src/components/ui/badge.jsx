import { cn } from "../../lib/utils";

export function Badge({ className, ...props }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-medium text-slate-200",
        className,
      )}
      {...props}
    />
  );
}
