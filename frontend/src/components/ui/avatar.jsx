import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { cn } from "../../lib/utils";

export function Avatar({ className, ...props }) {
  return (
    <AvatarPrimitive.Root
      className={cn(
        "inline-flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-slate-800 bg-slate-900",
        className,
      )}
      {...props}
    />
  );
}

export function AvatarImage({ className, ...props }) {
  return (
    <AvatarPrimitive.Image
      className={cn("h-full w-full object-cover", className)}
      {...props}
    />
  );
}

export function AvatarFallback({ className, ...props }) {
  return (
    <AvatarPrimitive.Fallback
      className={cn("text-xs font-medium text-slate-400", className)}
      {...props}
    />
  );
}
