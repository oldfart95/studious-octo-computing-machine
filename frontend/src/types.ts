export type Parameters = {
  width: number;
  height: number;
  steps: number;
  cfg: number;
  sampler: string;
  scheduler: string;
  seed: number;
  batch_size: number;
};

export type Preset = {
  name: string;
  workflow_mode: "txt2img-standard" | "txt2img-lora" | "art-card-batch";
  checkpoint: string;
  loras: Array<{ name: string; strength_model?: number; strength_clip?: number } | string>;
  positive_prefix: string;
  negative_prompt: string;
  style_prompt: string;
  locked_style_blocks: string[];
  parameters: Parameters;
};

export type StyleBlock = {
  name: string;
  prompt: string;
  locked: boolean;
  tags: string[];
};

export type ModelRef = {
  name: string;
  category: string;
  path: string;
};

export type HistoryEntry = {
  id: string;
  created_at: string;
  status: string;
  prompt_compiled: string;
  negative_compiled: string;
  workflow_mode: string;
  comfy_prompt_id?: string;
  request: {
    prompt: string;
    negative_prompt: string;
    style_prompt: string;
    preset?: string;
    checkpoint?: string;
    locked_style_blocks: string[];
    parameters: Parameters;
  };
  output_files: string[];
};

export type GalleryItem = {
  name: string;
  path: string;
  url: string;
};

export type ImportManifest = {
  id: string;
  source_url: string;
  filename: string;
  sha256: string;
  probable_asset_type: string;
  file_type_guess: string;
  base_model_guess: string;
  trigger_words: string[];
  tags: string[];
  needs_review: boolean;
  safe_preview_default: boolean;
  duplicate_of?: string | null;
};
