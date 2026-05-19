# Backend

FastAPI service entry lives in `main.py`.

Storage contract:

- [docs/local-storage-spec.md](../../docs/local-storage-spec.md)

Suggested next modules:

- `app/api` for HTTP routes
- `app/services` for model providers
- `app/storage` for local file-based manifests
- `app/schemas` for request and response models

Current implemented API/storage scope:

- `series`
- `episodes`
- `characters`
- `scenes`
- `storyboards`
- `snapshots`
- `jobs`

Video provider env contract:

- `VIDEO_PROVIDER_NAME`
- `VIDEO_PROVIDER_MODEL`
- `VIDEO_PROVIDER_SUBMIT_MODE`
- `VIDEO_PROVIDER_BASE_URL`
- `VIDEO_PROVIDER_PATH`
- `VIDEO_PROVIDER_STATUS_PATH`
- `VIDEO_PROVIDER_STATUS_METHOD`
- `VIDEO_PROVIDER_API_KEY`
- `VIDEO_PROVIDER_TIMEOUT_SECONDS`
- `VIDEO_PROVIDER_RESULT_STATUS_PATH`
- `VIDEO_PROVIDER_RESULT_VIDEO_URL_PATH`
- `VIDEO_PROVIDER_RESULT_COVER_URL_PATH`
- `VIDEO_PROVIDER_READY_VALUES`
- `VIDEO_PROVIDER_FAILED_VALUES`
- `VIDEO_PROVIDER_DOWNLOAD_ASSETS`

Job submit lifecycle:

- `POST /api/jobs/from-snapshot` creates a local prepared job
- `POST /api/jobs/{job_id}/submit` submits an existing prepared job
- `POST /api/jobs/{job_id}/refresh` refreshes a submitted job and downloads completed assets into local `output/`
- raw provider responses are persisted under `output/<series>/jobs/_responses/`
