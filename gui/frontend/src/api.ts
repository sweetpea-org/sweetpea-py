import type { Check, Model } from "./model";

export type Row = Record<string, string | number | null>;
export type Rendered = { code: string; check: Check };
export type Parsed = { model: Model; check: Check } | { error: string; line: number | null };
export type Sampled = { sequences: Row[][]; log: string } | { error: string };

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

export const api = {
  render: (model: Model) => post<Rendered>("/api/render", model),
  parse: (code: string) => post<Parsed>("/api/parse", { code }),
  synthesize: (model: Model) => post<Sampled>("/api/synthesize", model),
};
