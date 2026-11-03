"use client";

import { Lang } from "@/lib/i18n";

export function LanguageToggle({ lang, onChange }: { lang: Lang; onChange: (l: Lang) => void }) {
  return (
    <div className="inline-flex rounded-md border border-hairline bg-panel overflow-hidden text-xs font-mono">
      <button
        onClick={() => onChange("en")}
        className={`px-3 py-1.5 transition-colors ${
          lang === "en" ? "bg-panel-raised text-signal-amber" : "text-muted hover:text-ink"
        }`}
      >
        EN
      </button>
      <button
        onClick={() => onChange("ar")}
        className={`px-3 py-1.5 transition-colors ${
          lang === "ar" ? "bg-panel-raised text-signal-amber" : "text-muted hover:text-ink"
        }`}
      >
        عربي
      </button>
    </div>
  );
}
