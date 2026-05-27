# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack and entrypoints

Local file-driven AI video workflow. **No database** — all business state lives on disk under `output/`.

- Backend: FastAPI in [code/backEnd/](code/backEnd/), entry [main.py](code/backEnd/main.py), serves on `127.0.0.1:8000`. Mounts `output/` as `/output` static dir.
- Frontend: Vue 3 + Vite + Element Plus in [code/frontEnd/](code/frontEnd/), serves on `127.0.0.1:8080`. Vite proxies `/api` and `/output` to `127.0.0.1:8000` ([vite.config.js](code/frontEnd/vite.config.js)).
- Frontend is essentially one giant SFC: [src/App.vue](code/frontEnd/src/App.vue) (~8.3k lines) calling [src/services/api.js](code/frontEnd/src/services/api.js).

## Common commands

Root-level Windows scripts wrap both processes:

- `start.bat` — kills :8000/:8080, launches uvicorn + `npm run dev` hidden via [start_hidden.ps1](start_hidden.ps1), waits for both to be HTTP-ready, opens the frontend URL. Logs go to `backend.dev.log` / `frontend.dev.log` (and `*.err.log`) at repo root.
- `restart.bat` / `stop.bat` — restart-all and kill-all.

Run components manually (note: shell here is **bash on Windows** — use forward slashes, `/dev/null`, not Windows shell idioms):

```bash
# backend
cd code/backEnd && pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# frontend
cd code/frontEnd && npm install
npm run dev      # vite dev on :8080
npm run build    # production build into dist/
```

There is **no test suite and no linter configured**. Do not invent commands like `pytest` / `eslint` — they are not set up. If verification is needed, exercise the running app via the dev servers and the on-disk artifacts under `output/`.

## Architecture: the pipeline

The work model is a layered, resumable pipeline. Each layer freezes its inputs before the next runs, so any step can be retried without losing context. Understanding this is essential before touching any service or store:

```
series → episode → (script raw → script parsed)
                 ↘ characters (→ bible.json + character_bible_sheet.jpg)
                 ↘ scenes     (→ prompt_package.json + scene_reference_sheet.jpg)
                 ↘ storyboard → shots
                                  → shot_package / scene_package   (assembled prompt + refs)
                                  → snapshot                       (frozen submission inputs)
                                  → job (local draft)
                                       → submit → remote task (Doubao Seedance / ARK)
                                       → refresh → downloads assets into outputs/
```

Two production modes on a storyboard:

- `shot_pipeline` (分镜生产) — one job per shot.
- `scene_direct` (场景直出) — one job per whole scene; uses [scene_video_assembly.py](code/backEnd/app/services/scene_video_assembly.py) instead of [shot_assembly.py](code/backEnd/app/services/shot_assembly.py).

Batch flow (`shot_batch_*`) exists alongside single-shot flow and is its own service+store ([shot_batch_generation.py](code/backEnd/app/services/shot_batch_generation.py), [shot_batch_store.py](code/backEnd/app/storage/shot_batch_store.py)). Batch = N independent jobs, NOT one combined video.

## Backend layout (`code/backEnd/app/`)

Three layers, each with one module per entity:

- [api/](code/backEnd/app/api/) — FastAPI routers (`series`, `episodes`, `characters`, `scenes`, `storyboards`, `snapshots`, `jobs`). Routers are thin: validate Pydantic body, delegate to a service or store, translate `FileNotFoundError` → 404 and `ValueError` → 400.
- [services/](code/backEnd/app/services/) — orchestration and outbound HTTP. `deepseek.py` (script parsing), `character_generation.py` / `scene_generation.py` (gpt-image), `shot_assembly.py` / `scene_video_assembly.py` (build prompt packages), `shot_batch_generation.py`, `video_generation.py` (Doubao Seedance / generic HTTP video provider).
- [storage/](code/backEnd/app/storage/) — disk I/O. Per-entity stores plus shared helpers in [common.py](code/backEnd/app/storage/common.py) and ID/slug rules in [naming.py](code/backEnd/app/storage/naming.py).

When adding a new entity, follow the `api/X.py` + `services/X_*.py` + `storage/X_store.py` split and register the router in [main.py](code/backEnd/main.py).

## Storage contract — read this before touching disk

Authoritative spec: [docs/local-storage-spec.md](docs/local-storage-spec.md). Critical invariants:

1. **`output/` is the single source of truth.** Browser/in-memory state is never authoritative. Frontend must always re-read via API.
2. **Every series is a self-contained workspace** at `output/{series_slug}/`, with subdirs `episodes/ characters/ scenes/ storyboards/ snapshots/ jobs/ outputs/{images,videos,audio,exports}/ trash/`.
3. **All paths inside JSON manifests are relative to the series root**, POSIX-style — never absolute, never backslashed. Use `relative_to_series_root()` from [common.py](code/backEnd/app/storage/common.py).
4. **All writes are atomic** — use `write_json_atomic` / `write_text_atomic` / `write_bytes_atomic` from [common.py](code/backEnd/app/storage/common.py). Never write directly with `open(..., "w")` for manifests; tmp-file-then-replace prevents half-written JSON.
5. **IDs and slugs come from [naming.py](code/backEnd/app/storage/naming.py).** Don't hand-roll: `slugify` + `ensure_unique_slug` for series, `make_entity_id` for `char_*`/`scene_*` (name-based with `_2`/`_3` collision suffix), `next_numeric_id` / `next_episode_id` for `ep_001` / `shot_001` style. Slug is set on creation and **never mutated** afterward — renaming a series only updates `name`, not the directory.
6. **Referential integrity is enforced on delete.** Stores reject deletion when an entity is still referenced (episode ← scenes/storyboards, character ← shots, scene ← shots, storyboard ← snapshots/jobs, shot ← snapshots/jobs, job ← remote `task_id`). Match this pattern when adding new entity relationships.
7. Generated artifacts that are versioned: characters keep `versions/bible_vNNN.json` + `generated/vNNN/`, scenes keep `versions/scene_vNNN.json` + `generated/vNNN/`, snapshots are append-only by design. The "current" pointer files (`bible.json`, `prompt_package.json`, `refs/*_sheet.jpg`) may be overwritten; the versioned copies must not.

## Provider configuration

Backend loads [code/backEnd/.env](code/backEnd/.env) via `python-dotenv` at startup. **`.env` is gitignored and contains live API keys** — never echo its contents back in chat output, never commit it, and don't paste keys into commit messages or PRs.

Provider env contract documented in [code/backEnd/README.md](code/backEnd/README.md):

- `DEEPSEEK_*` — script parsing LLM
- `GPT_IMAGE_*` — character / scene reference image generation
- `VIDEO_PROVIDER_*` — generic HTTP video provider, defaults targeting Doubao Seedance 2.0 (ARK). Supports `submit / status / list / delete` paths and configurable JSON paths for parsing remote responses.

## Conventions worth matching

- All user-facing text in code, docs, and error messages is **Simplified Chinese**. Match this when adding new endpoints or UI strings.
- Backend HTTP errors: raise `FileNotFoundError` from stores (→ 404 in API layer) and `ValueError` for business-rule violations (→ 400). Don't raise `HTTPException` from inside services or stores.
- Frontend never builds backend URLs by hand — it calls helpers in [api.js](code/frontEnd/src/services/api.js), which routes through Vite proxy in dev and through FastAPI's static mount in prod.
- Logs at repo root (`backend.dev.log`, `frontend.dev.log`, etc.) are written by `start.bat` and rotate by overwrite. They are gitignored — don't commit them.
