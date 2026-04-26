export function SectionHeading({
  eyebrow,
  title,
  body
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="max-w-2xl">
      <p className="mb-3 text-xs uppercase tracking-[0.28em] text-accent/80">{eyebrow}</p>
      <h2 className="font-[var(--font-display)] text-3xl font-semibold tracking-tight text-white md:text-4xl">
        {title}
      </h2>
      <p className="mt-4 text-base leading-7 text-slate-300 md:text-lg">{body}</p>
    </div>
  );
}
