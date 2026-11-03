import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  // Don't let a missing .env.local crash the ENTIRE app build - that would
  // also take down features (single-asset/portfolio analysis) that have
  // nothing to do with auth. Fall back to a syntactically valid placeholder
  // URL so createClient() doesn't throw; auth calls will just fail with a
  // clear network error until real credentials are set.
  console.warn(
    "NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY is missing from .env.local - " +
    "auth features (sign in, save portfolio) will not work until these are set."
  );
}

export const supabase = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseAnonKey || "placeholder-anon-key"
);
