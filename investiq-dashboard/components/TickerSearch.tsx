"use client";

import { useState, FormEvent } from "react";

export function TickerSearch({
  onSearch,
  loading,
  placeholder,
  buttonText,
  loadingText,
}: {
  onSearch: (ticker: string) => void;
  loading: boolean;
  placeholder: string;
  buttonText: string;
  loadingText: string;
}) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim().toUpperCase();
    if (trimmed) onSearch(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full max-w-md">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="flex-1 bg-panel border border-hairline rounded-md px-4 py-2.5 text-sm font-mono
                   text-ink placeholder:text-muted-dim outline-none
                   focus:border-signal-amber/60 focus:ring-1 focus:ring-signal-amber/30
                   transition-colors"
        disabled={loading}
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="px-5 py-2.5 rounded-md bg-panel-raised border border-hairline text-sm font-medium
                   text-ink hover:border-signal-amber/50 hover:text-signal-amber
                   disabled:opacity-40 disabled:hover:border-hairline disabled:hover:text-ink
                   transition-colors whitespace-nowrap"
      >
        {loading ? loadingText : buttonText}
      </button>
    </form>
  );
}
