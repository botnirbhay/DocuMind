import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef } from "react";

import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-full transition-all duration-200 disabled:pointer-events-none disabled:opacity-45",
  {
    variants: {
      variant: {
        primary:
          "bg-[linear-gradient(135deg,#67d4ff_0%,#5aa0ff_55%,#726bff_100%)] text-slate-950 hover:scale-[1.01] shadow-[0_10px_35px_rgba(90,160,255,0.32)]",
        secondary:
          "border border-white/[0.12] bg-white/[0.04] text-slate-100 hover:border-white/[0.18] hover:bg-white/[0.07]",
        ghost: "text-slate-300 hover:bg-white/[0.05] hover:text-white"
      },
      size: {
        sm: "px-3 py-2 text-sm",
        md: "px-4 py-2.5 text-sm",
        lg: "px-5 py-3 text-sm font-medium"
      }
    },
    defaultVariants: {
      variant: "primary",
      size: "md"
    }
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, ...props },
  ref
) {
  return <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />;
});
