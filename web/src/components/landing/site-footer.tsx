import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="px-6 pb-8 pt-6 md:px-10 lg:px-14">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 rounded-[28px] border border-white/10 bg-white/[0.03] px-6 py-6 text-sm text-slate-400 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="font-[var(--font-display)] text-lg text-white">DocuMind</p>
          <p className="mt-1">Upload documents, ask questions, and review the supporting source.</p>
        </div>
        <div className="flex flex-wrap items-center gap-5">
          <Link href="/" className="transition hover:text-white">
            Home
          </Link>
          <Link href="/workspace" className="transition hover:text-white">
            Workspace
          </Link>
          <a href="#how-it-works" className="transition hover:text-white">
            How it works
          </a>
        </div>
      </div>
    </footer>
  );
}
