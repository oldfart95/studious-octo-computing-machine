import type { GalleryItem, HistoryEntry, ImportManifest, ModelRef, Preset, StyleBlock } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  presets: () => request<Preset[]>("/api/presets"),
  styleBlocks: () => request<StyleBlock[]>("/api/style-blocks"),
  models: () => request<ModelRef[]>("/api/models"),
  history: () => request<HistoryEntry[]>("/api/history"),
  gallery: () => request<GalleryItem[]>("/api/gallery"),
  imports: () => request<ImportManifest[]>("/api/imports"),
  run: (body: unknown) =>
    request<HistoryEntry>("/api/run", {
      method: "POST",
      body: JSON.stringify(body)
    }),
  runBatch: (body: unknown) =>
    request<HistoryEntry[]>("/api/batch", {
      method: "POST",
      body: JSON.stringify(body)
    }),
  importModel: (url: string, dryRun = false) =>
    request(`/api/import-model?url=${encodeURIComponent(url)}&dry_run=${dryRun}`, {
      method: "POST"
    })
};
