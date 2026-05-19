# Local Storage Spec

## Goal

This project uses local files only.

- No database
- No browser cache as source of truth
- All business data must be recoverable from disk
- One series is one isolated workspace

The root storage directory is:

```text
output/
```

## Design Rules

1. All entities use file-based manifests as the source of truth.
2. Binary files such as images, audio, and videos are referenced by relative paths in manifests.
3. Each entity has a stable `id` and a human-readable `name`.
4. Regeneration must create a new version record instead of silently overwriting business metadata.
5. Video generation consumes a fixed snapshot package, not mutable latest state.
6. Paths stored in JSON must be relative to the current series root.
7. Frontend rendering must read from backend APIs backed by local files, not from browser-local state.

## Root Structure

```text
output/
  _system/
    storage_manifest.json
  {series_slug}/
    series.json
    episodes/
    characters/
    scenes/
    props/
    storyboards/
    snapshots/
    jobs/
    outputs/
    trash/
```

## System Level

`output/_system/storage_manifest.json`

Purpose:

- stores storage spec version
- stores global defaults
- can later store migration info

Suggested shape:

```json
{
  "storage_version": "1.0.0",
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "series_root": "output",
  "notes": "Local file storage manifest for AI video workflow"
}
```

## Series Structure

Each series is isolated under:

```text
output/{series_slug}/
```

Example:

```text
output/dark-night-chase/
  series.json
  episodes/
  characters/
  scenes/
  props/
  storyboards/
  snapshots/
  jobs/
  outputs/
  trash/
```

### `series.json`

Purpose:

- series-level metadata
- visual defaults
- provider defaults
- current working pointers

Suggested shape:

```json
{
  "id": "series_dark_night_chase",
  "slug": "dark-night-chase",
  "name": "暗夜追踪",
  "description": "悬疑短剧系列",
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "status": "active",
  "defaults": {
    "aspect_ratio": "16:9",
    "style": "cinematic realism",
    "resolution": "1080p",
    "language": "zh-CN"
  },
  "providers": {
    "script_llm": "deepseek",
    "image_model": "gpt-image",
    "video_model": ""
  },
  "pointers": {
    "current_episode_id": "",
    "current_storyboard_id": ""
  }
}
```

## Episodes

Path:

```text
output/{series_slug}/episodes/{episode_id}/
```

Files:

```text
episode.json
script.raw.txt
script.parsed.json
script.versions/
```

### `episode.json`

Purpose:

- episode metadata
- multi-act structure
- processing status

Suggested shape:

```json
{
  "id": "ep_001",
  "series_id": "series_dark_night_chase",
  "episode_number": 1,
  "name": "第1集",
  "status": "draft",
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "script": {
    "raw_text_path": "episodes/ep_001/script.raw.txt",
    "parsed_path": "episodes/ep_001/script.parsed.json",
    "latest_version": 1
  }
}
```

### `script.parsed.json`

Purpose:

- normalized script structure
- source for character extraction and scene extraction

Suggested top-level fields:

```json
{
  "episode_id": "ep_001",
  "title": "第1集",
  "acts": [],
  "scenes": [],
  "extracted_entities": {
    "characters": [],
    "scenes": [],
    "props": []
  },
  "source_version": 1
}
```

## Characters

Path:

```text
output/{series_slug}/characters/{character_id}/
```

Files:

```text
character.json
bible.json
refs/
generated/
versions/
```

### `character.json`

Purpose:

- character identity
- stable visual anchors
- links to reference assets

Suggested shape:

```json
{
  "id": "char_nan_zhu",
  "name": "男主",
  "aliases": [],
  "series_id": "series_dark_night_chase",
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "status": "approved",
  "anchors": {
    "biology": "",
    "face": "",
    "hair": "",
    "costume": "",
    "palette": "",
    "aura": ""
  },
  "bible_path": "characters/char_nan_zhu/bible.json",
  "reference_images": {
    "front": "characters/char_nan_zhu/refs/front_v001.png",
    "side": "characters/char_nan_zhu/refs/side_v001.png",
    "back": "characters/char_nan_zhu/refs/back_v001.png",
    "sheet": "characters/char_nan_zhu/refs/sheet_v001.png"
  },
  "latest_version": 1
}
```

### `bible.json`

Purpose:

- expanded character bible
- prompt data
- regeneration history

Suggested top-level fields:

```json
{
  "character_id": "char_nan_zhu",
  "version": 1,
  "brief": "",
  "bible": {},
  "visual_prompts": {},
  "notes": [],
  "generated_from": {
    "episode_ids": ["ep_001"]
  }
}
```

## Scenes

Path:

```text
output/{series_slug}/scenes/{scene_id}/
```

Files:

```text
scene.json
refs/
generated/
versions/
```

### `scene.json`

Purpose:

- scene definition
- visual continuity
- multi-view references

Suggested shape:

```json
{
  "id": "scene_001",
  "name": "废弃仓库",
  "series_id": "series_dark_night_chase",
  "episode_id": "ep_001",
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "status": "approved",
  "description": "",
  "visual_profile": {
    "time": "深夜",
    "weather": "",
    "lighting": "",
    "palette": "",
    "style": ""
  },
  "reference_images": {
    "establishing": "scenes/scene_001/refs/establishing_v001.png",
    "closeup": "scenes/scene_001/refs/closeup_v001.png",
    "bird_eye": "scenes/scene_001/refs/bird_eye_v001.png",
    "detail": "scenes/scene_001/refs/detail_v001.png"
  },
  "latest_version": 1
}
```

## Props

Props are first-class assets because consistency often breaks on clothing, weapons, phones, bags, and accessories.

Path:

```text
output/{series_slug}/props/{prop_id}/
```

Files:

```text
prop.json
refs/
versions/
```

### `prop.json`

Suggested shape:

```json
{
  "id": "prop_black_phone",
  "name": "黑色手机",
  "series_id": "series_dark_night_chase",
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "description": "",
  "reference_images": [],
  "latest_version": 1
}
```

## Storyboards

Path:

```text
output/{series_slug}/storyboards/{storyboard_id}/
```

Files:

```text
storyboard.json
shots/
```

### `storyboard.json`

Purpose:

- one approved shot plan for one episode

Suggested shape:

```json
{
  "id": "sb_ep_001_v001",
  "series_id": "series_dark_night_chase",
  "episode_id": "ep_001",
  "version": 1,
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "status": "draft",
  "shot_ids": ["shot_001", "shot_002"]
}
```

### `shots/{shot_id}.json`

Purpose:

- execution-ready shot card

Suggested shape:

```json
{
  "id": "shot_001",
  "storyboard_id": "sb_ep_001_v001",
  "scene_id": "scene_001",
  "characters": ["char_nan_zhu"],
  "props": ["prop_black_phone"],
  "script_source": {
    "episode_id": "ep_001",
    "scene_index": 1,
    "shot_index": 1
  },
  "dialogue": [],
  "visual": {
    "aspect_ratio": "16:9",
    "style": "cinematic realism",
    "resolution": "1080p",
    "shot_size": "wide",
    "camera_angle": "eye_level",
    "camera_movement": "push_in",
    "lens": "35mm",
    "depth_of_field": "medium",
    "lighting": "moody practical light",
    "palette": "warm_low_saturation",
    "duration_seconds": 5
  },
  "prompt_package": {
    "positive": "",
    "negative": "",
    "reference_images": []
  },
  "status": "draft"
}
```

## Snapshots

Snapshots freeze the exact input package used for generation.

Path:

```text
output/{series_slug}/snapshots/{snapshot_id}/
```

Files:

```text
snapshot.json
bundle/
```

### `snapshot.json`

Purpose:

- reproducibility
- rollback
- audit trail

Suggested shape:

```json
{
  "id": "snap_shot_001_v001",
  "series_id": "series_dark_night_chase",
  "storyboard_id": "sb_ep_001_v001",
  "shot_id": "shot_001",
  "created_at": "2026-05-19T08:00:00Z",
  "inputs": {
    "shot_card_path": "storyboards/sb_ep_001_v001/shots/shot_001.json",
    "character_paths": [
      "characters/char_nan_zhu/character.json"
    ],
    "scene_paths": [
      "scenes/scene_001/scene.json"
    ],
    "prop_paths": [
      "props/prop_black_phone/prop.json"
    ]
  },
  "resolved_assets": {
    "images": [],
    "audio": []
  },
  "provider_payload": {
    "model": "",
    "request_body": {}
  }
}
```

## Jobs

Path:

```text
output/{series_slug}/jobs/{job_id}.json
```

Purpose:

- queue state
- provider response state
- retry state
- final output linkage

Suggested shape:

```json
{
  "id": "job_20260519_0001",
  "series_id": "series_dark_night_chase",
  "snapshot_id": "snap_shot_001_v001",
  "type": "video_generation",
  "status": "queued",
  "created_at": "2026-05-19T08:00:00Z",
  "updated_at": "2026-05-19T08:00:00Z",
  "attempt": 1,
  "provider": {
    "name": "seedance",
    "model": ""
  },
  "remote": {
    "task_id": "",
    "raw_response_path": ""
  },
  "result": {
    "video_path": "",
    "cover_path": "",
    "metrics": {}
  },
  "error": {
    "message": "",
    "code": ""
  }
}
```

## Outputs

Path:

```text
output/{series_slug}/outputs/
  images/
  videos/
  audio/
  exports/
```

Suggested usage:

- `images/` for approved keyframes and derived stills
- `videos/` for shot-level clips
- `audio/` for uploaded reference audio or generated voice/music
- `exports/` for merged scene-level or episode-level deliverables

Recommended naming:

```text
videos/{shot_id}_v001.mp4
images/{shot_id}_cover_v001.png
exports/{episode_id}_cut_v001.mp4
```

## Trash

Path:

```text
output/{series_slug}/trash/
```

Purpose:

- soft delete
- operator recovery

Rules:

1. Delete means move to `trash/`, not immediate permanent removal.
2. Keep original relative path in delete metadata.
3. Later a cleanup job can permanently purge old trash.

## Naming Rules

### IDs

Use stable ASCII IDs:

- `series_dark_night_chase`
- `ep_001`
- `scene_001`
- `char_nan_zhu`
- `prop_black_phone`
- `shot_001`

### Slugs

- folder-safe
- lowercase
- words joined by `-`

Example:

```text
dark-night-chase
```

### Versions

Use fixed-width numeric versions:

```text
v001
v002
v003
```

## File Rules

1. JSON uses UTF-8.
2. All timestamps use ISO 8601 UTC strings.
3. Paths in manifests must use `/`.
4. Large binaries must never be embedded into JSON.
5. A manifest can reference only files inside its own series root.

## Write Rules

1. Write JSON atomically.
2. Create parent directories before write.
3. When regenerating assets, update `latest_version` only after new files are safely written.
4. Never overwrite source script text without writing a new version.
5. Snapshot writes must be immutable after creation.

## Read Rules

1. Backend is the only component allowed to read disk directly.
2. Frontend reads through API only.
3. The backend should rebuild in-memory indexes by scanning `output/` at startup.

## Recommended API Mapping

Storage design should align with backend API modules:

- `series` -> create/list/update `series.json`
- `episodes` -> save raw script and parsed script
- `characters` -> manage `character.json` and `bible.json`
- `scenes` -> manage `scene.json`
- `props` -> manage `prop.json`
- `storyboards` -> manage shot cards
- `snapshots` -> freeze generation package
- `jobs` -> track long-running generation tasks
- `outputs` -> expose downloadable files

## Minimum MVP Scope

For the first implementation, only these paths are required:

```text
output/
  _system/storage_manifest.json
  {series_slug}/
    series.json
    episodes/{episode_id}/episode.json
    episodes/{episode_id}/script.raw.txt
    episodes/{episode_id}/script.parsed.json
    characters/{character_id}/character.json
    characters/{character_id}/bible.json
    scenes/{scene_id}/scene.json
    storyboards/{storyboard_id}/storyboard.json
    storyboards/{storyboard_id}/shots/{shot_id}.json
    snapshots/{snapshot_id}/snapshot.json
    jobs/{job_id}.json
    outputs/videos/
```

This is enough to support:

- series selection
- script parsing
- character generation
- scene generation
- shot configuration
- reproducible video generation

