import { cn } from "@/lib/utils";

export function Surface({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("glass-panel rounded-[28px]", className)}>{children}</div>;
}
