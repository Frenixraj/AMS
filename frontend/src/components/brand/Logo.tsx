import { cn } from "@/lib/utils";

import logo from "@/assets/brand/logo.png";

type LogoProps = {
  className?: string;
  /** Image height class, e.g. h-8 / h-16 */
  imgClassName?: string;
  showTagline?: boolean;
};

/**
 * AssetFlow wordmark (transparent logo). Use on light surfaces.
 */
export function Logo({ className, imgClassName, showTagline = false }: LogoProps) {
  return (
    <div className={cn("flex flex-col items-start", className)}>
      <img
        src={logo}
        alt="AssetFlow"
        className={cn("h-9 w-auto object-contain", imgClassName)}
        decoding="async"
      />
      {showTagline && (
        <span className="mt-1 text-[10px] font-medium uppercase tracking-[0.2em] text-slate-600">
          Track · Manage · Optimize
        </span>
      )}
    </div>
  );
}
