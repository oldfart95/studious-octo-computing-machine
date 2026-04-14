import { useEffect, useState } from "react";
import { api } from "./api";
import type { GalleryItem, HistoryEntry, ImportManifest, ModelRef, Preset, StyleBlock } from "./types";

const defaultParameters = {
  width: 1024,
  height: 1024,
  steps: 28,
  cfg: 6,
  sampler: "euler",
  scheduler: "normal",
  seed: -1,
  batch_size: 1
};

type TabKey = "create" | "history" | "gallery" | "imports";

export default function App() {
  const [tab, setTab] = useState<TabKey>("create");
  const [presets, setPresets] = useState<Preset[]>([]);
  const [styleBlocks, setStyleBlocks] = useState<StyleBlock[]>([]);
  const [models, setModels] = useState<ModelRef[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [gallery, setGallery] = useState<GalleryItem[]>([]);
  const [imports, setImports] = useState<ImportManifest[]>([]);
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [stylePrompt, setStylePrompt] = useState("");
  const [selectedPreset, setSelectedPreset] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [lockedBlocks, setLockedBlocks] = useState<string[]>([]);
  const [batchText, setBatchText] = useState('[\n  {\n    "preset": "ritual-card",\n    "prompt": "cathedral engine"\n  }\n]');
  const [importUrl, setImportUrl] = useState("");
  const [importStatus, setImportStatus] = useState("");
  const [runStatus, setRunStatus] = useState("");
  const [parameters, setParameters] = useState(defaultParameters);

  useEffect(() => {
    void Promise.all([api.presets(), api.styleBlocks(), api.models(), api.history(), api.gallery(), api.imports()]).then(
      ([presetData, styleData, modelData, historyData, galleryData, importData]) => {
        setPresets(presetData);
        setStyleBlocks(styleData);
        setModels(modelData);
        setHistory(historyData.reverse());
        setGallery(galleryData.reverse());
        setImports(importData.reverse());
        if (presetData[0]) {
          setSelectedPreset(presetData[0].name);
          setSelectedModel(presetData[0].checkpoint);
          setNegativePrompt(presetData[0].negative_prompt);
          setStylePrompt(presetData[0].style_prompt);
          setLockedBlocks(presetData[0].locked_style_blocks);
          setParameters(presetData[0].parameters);
        }
      }
    );
  }, []);

  async function submitRun() {
    setRunStatus("Queueing generation...");
    const payload = {
      prompt,
      negative_prompt: negativePrompt,
      style_prompt: stylePrompt,
      preset: selectedPreset || undefined,
      checkpoint: selectedModel || undefined,
      locked_style_blocks: lockedBlocks,
      parameters
    };
    const result = await api.run(payload);
    setRunStatus(`Queued job ${result.id}`);
    const nextHistory = await api.history();
    setHistory(nextHistory.reverse());
  }

  async function submitBatch() {
    setRunStatus("Queueing batch...");
    const parsed = JSON.parse(batchText) as Array<Record<string, unknown>>;
    await api.runBatch(parsed);
    setRunStatus(`Queued ${parsed.length} jobs`);
    const nextHistory = await api.history();
    setHistory(nextHistory.reverse());
  }

  async function submitImport() {
    setImportStatus("Importing to quarantine...");
    const result = await api.importModel(importUrl, false);
    setImportStatus(`Imported ${String((result as { filename?: string }).filename ?? "asset")}`);
    const nextImports = await api.imports();
    setImports(nextImports.reverse());
  }

  function loadPreset(name: string) {
    setSelectedPreset(name);
    const preset = presets.find((item) => item.name === name);
    if (!preset) {
      return;
    }
    setSelectedModel(preset.checkpoint);
    setNegativePrompt(preset.negative_prompt);
    setStylePrompt(preset.style_prompt);
    setLockedBlocks(preset.locked_style_blocks);
    setParameters(preset.parameters);
  }

  return (
    <div className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Local-first image generation</p>
          <h1>GenUI</h1>
          <p className="lede">Calm, touch-friendly ComfyUI control for daily use across desktop, phone, and tablet over your tailnet.</p>
        </div>
        <nav className="tabs">
          {(["create", "history", "gallery", "imports"] as TabKey[]).map((item) => (
            <button key={item} className={tab === item ? "tab active" : "tab"} onClick={() => setTab(item)}>
              {item}
            </button>
          ))}
        </nav>
      </header>

      {tab === "create" && (
        <main className="panel-grid">
          <section className="panel primary">
            <div className="panel-header">
              <h2>Create</h2>
              <span>{runStatus}</span>
            </div>
            <label>
              Preset
              <select value={selectedPreset} onChange={(event) => loadPreset(event.target.value)}>
                <option value="">No preset</option>
                {presets.map((preset) => (
                  <option key={preset.name} value={preset.name}>
                    {preset.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Model
              <select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)}>
                <option value="">Auto from preset</option>
                {models
                  .filter((model) => model.category === "checkpoint")
                  .map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              Positive prompt
              <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={6} />
            </label>
            <label>
              Style prompt
              <textarea value={stylePrompt} onChange={(event) => setStylePrompt(event.target.value)} rows={4} />
            </label>
            <label>
              Negative prompt
              <textarea value={negativePrompt} onChange={(event) => setNegativePrompt(event.target.value)} rows={4} />
            </label>
            <div className="chip-wrap">
              {styleBlocks.map((block) => {
                const enabled = lockedBlocks.includes(block.name);
                return (
                  <button
                    key={block.name}
                    className={enabled ? "chip active" : "chip"}
                    onClick={() =>
                      setLockedBlocks((current) =>
                        enabled ? current.filter((item) => item !== block.name) : [...current, block.name]
                      )
                    }
                  >
                    {enabled ? "Locked" : "Unlock"} {block.name}
                  </button>
                );
              })}
            </div>
            <div className="parameter-grid">
              <Stepper label="W" value={parameters.width} onChange={(value) => setParameters({ ...parameters, width: value })} />
              <Stepper label="H" value={parameters.height} onChange={(value) => setParameters({ ...parameters, height: value })} />
              <Stepper label="Steps" value={parameters.steps} onChange={(value) => setParameters({ ...parameters, steps: value })} />
              <Stepper label="CFG" value={parameters.cfg} step={0.5} onChange={(value) => setParameters({ ...parameters, cfg: value })} />
              <Stepper label="Seed" value={parameters.seed} onChange={(value) => setParameters({ ...parameters, seed: value })} />
              <Stepper label="Batch" value={parameters.batch_size} onChange={(value) => setParameters({ ...parameters, batch_size: value })} />
            </div>
            <button className="cta" onClick={() => void submitRun()}>
              Queue Generation
            </button>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Batch Jobs</h2>
              <span>JSON list</span>
            </div>
            <textarea className="code-box" value={batchText} onChange={(event) => setBatchText(event.target.value)} rows={16} />
            <button className="secondary" onClick={() => void submitBatch()}>
              Queue Batch
            </button>
            <div className="helper-card">
              <h3>Locked prompt sections</h3>
              <p>Use the style block chips above to keep reusable visual language attached until you manually remove it.</p>
            </div>
          </section>
        </main>
      )}

      {tab === "history" && (
        <main className="stack">
          {history.map((item) => (
            <article className="history-card" key={item.id}>
              <div className="history-head">
                <div>
                  <strong>{item.request.preset || item.workflow_mode}</strong>
                  <p>{new Date(item.created_at).toLocaleString()}</p>
                </div>
                <button
                  className="secondary small"
                  onClick={() => {
                    setPrompt(item.request.prompt);
                    setNegativePrompt(item.request.negative_prompt);
                    setStylePrompt(item.request.style_prompt);
                    setSelectedPreset(item.request.preset || "");
                    setLockedBlocks(item.request.locked_style_blocks);
                    setParameters(item.request.parameters);
                    setTab("create");
                  }}
                >
                  Re-run
                </button>
              </div>
              <p>{item.prompt_compiled}</p>
              <small>Seed {item.request.parameters.seed} | Steps {item.request.parameters.steps} | CFG {item.request.parameters.cfg}</small>
            </article>
          ))}
        </main>
      )}

      {tab === "gallery" && (
        <main className="gallery-grid">
          {gallery.map((item) => (
            <figure className="gallery-card" key={item.path}>
              <img src={item.url} alt={item.name} loading="lazy" />
              <figcaption>{item.name}</figcaption>
            </figure>
          ))}
        </main>
      )}

      {tab === "imports" && (
        <main className="panel-grid">
          <section className="panel primary">
            <div className="panel-header">
              <h2>Model Import</h2>
              <span>{importStatus}</span>
            </div>
            <label>
              Source URL
              <textarea
                value={importUrl}
                onChange={(event) => setImportUrl(event.target.value)}
                rows={5}
                placeholder="Paste a Civitai page, Hugging Face file, or direct safetensors URL"
              />
            </label>
            <button className="cta" onClick={() => void submitImport()}>
              Import Safely
            </button>
            <div className="helper-card">
              <h3>Safe preview off by default</h3>
              <p>Imported metadata previews stay out of the main gallery. Review them only in a dedicated import-review flow you intentionally open later.</p>
            </div>
          </section>
          <section className="panel">
            <div className="panel-header">
              <h2>Import Review</h2>
              <span>{imports.length}</span>
            </div>
            <div className="model-list">
              {imports.map((item) => (
                <div key={item.id} className="import-card">
                  <strong>{item.filename}</strong>
                  <span>{item.probable_asset_type || "unknown"}</span>
                  <small>Source: {item.source_url}</small>
                  <small>File type guess: {item.file_type_guess || "unknown"}</small>
                  <small>Base model guess: {item.base_model_guess || "unknown"}</small>
                  <small>Trigger words: {item.trigger_words.join(", ") || "none found"}</small>
                  <small>Tags: {item.tags.join(", ") || "none found"}</small>
                  <small>Safe preview: manual reveal only</small>
                  <small>{item.needs_review ? "Needs review" : "Validated"}</small>
                </div>
              ))}
            </div>
            <div className="panel-header import-models-header">
              <h2>Installed Models</h2>
              <span>{models.length}</span>
            </div>
            <div className="model-list">
              {models.map((model) => (
                <div key={model.name} className="model-row">
                  <strong>{model.name}</strong>
                  <span>{model.category}</span>
                </div>
              ))}
            </div>
          </section>
        </main>
      )}
    </div>
  );
}

type StepperProps = {
  label: string;
  value: number;
  step?: number;
  onChange: (value: number) => void;
};

function Stepper({ label, value, step = 1, onChange }: StepperProps) {
  return (
    <label className="stepper">
      <span>{label}</span>
      <div className="stepper-row">
        <button onClick={() => onChange(Number((value - step).toFixed(2)))}>-</button>
        <input value={value} onChange={(event) => onChange(Number(event.target.value))} />
        <button onClick={() => onChange(Number((value + step).toFixed(2)))}>+</button>
      </div>
    </label>
  );
}
