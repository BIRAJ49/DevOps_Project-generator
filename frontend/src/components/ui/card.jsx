import { cn } from "../../lib/utils";

export function Card({ className, ...props }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl shadow-slate-950/40",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }) {
  return <div className={cn("p-6 pb-0", className)} {...props} />;
}

export function CardContent({ className, ...props }) {
  return <div className={cn("p-6 pt-4", className)} {...props} />;
}

export function CardFooter({ className, ...props }) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}
