import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from app.storage.common import relative_to_series_root, utc_now_iso, write_bytes_atomic
from app.storage.job_store import create_job, get_job, save_job_remote_response, update_job
from app.storage.series_store import get_series_path
from app.storage.snapshot_store import get_snapshot


def _get_provider_defaults() -> dict[str, Any]:
    return {
        "name": os.getenv("VIDEO_PROVIDER_NAME", "manual").strip() or "manual",
        "model": os.getenv("VIDEO_PROVIDER_MODEL", "").strip(),
        "submit_mode": os.getenv("VIDEO_PROVIDER_SUBMIT_MODE", "manual").strip() or "manual",
        "base_url": os.getenv("VIDEO_PROVIDER_BASE_URL", "").strip(),
        "path": os.getenv("VIDEO_PROVIDER_PATH", "").strip() or "/",
        "api_key": os.getenv("VIDEO_PROVIDER_API_KEY", "").strip(),
        "timeout_seconds": int(os.getenv("VIDEO_PROVIDER_TIMEOUT_SECONDS", "300")),
        "status_path": os.getenv("VIDEO_PROVIDER_STATUS_PATH", "").strip(),
        "status_method": os.getenv("VIDEO_PROVIDER_STATUS_METHOD", "GET").strip().upper() or "GET",
        "result_status_path": os.getenv("VIDEO_PROVIDER_RESULT_STATUS_PATH", "status").strip() or "status",
        "result_video_url_path": os.getenv("VIDEO_PROVIDER_RESULT_VIDEO_URL_PATH", "video_url").strip() or "video_url",
        "result_cover_url_path": os.getenv("VIDEO_PROVIDER_RESULT_COVER_URL_PATH", "cover_url").strip() or "cover_url",
        "ready_values": os.getenv("VIDEO_PROVIDER_READY_VALUES", "succeeded,completed,success,finished,done,ready").strip(),
        "failed_values": os.getenv("VIDEO_PROVIDER_FAILED_VALUES", "failed,error,cancelled,canceled,rejected").strip(),
        "download_assets": os.getenv("VIDEO_PROVIDER_DOWNLOAD_ASSETS", "true").strip().lower() not in {"0", "false", "no"},
    }


def _merge_provider_settings(override: dict[str, Any] | None = None) -> dict[str, Any]:
    defaults = _get_provider_defaults()
    override = override or {}
    merged = dict(defaults)
    for key, value in override.items():
        if value is not None and value != "":
            merged[key] = value
    return merged


def _job_provider_payload(provider: dict[str, Any], request_body: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": provider.get("name", ""),
        "model": provider.get("model", ""),
        "submit_mode": provider.get("submit_mode", "manual"),
        "base_url": provider.get("base_url", ""),
        "path": provider.get("path", "/"),
        "status_path": provider.get("status_path", ""),
        "status_method": provider.get("status_method", "GET"),
        "result_status_path": provider.get("result_status_path", "status"),
        "result_video_url_path": provider.get("result_video_url_path", "video_url"),
        "result_cover_url_path": provider.get("result_cover_url_path", "cover_url"),
        "ready_values": provider.get("ready_values", ""),
        "failed_values": provider.get("failed_values", ""),
        "download_assets": provider.get("download_assets", True),
        "request_body": request_body,
    }


def build_video_request_from_snapshot(series_slug: str, snapshot_id: str, provider_override: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot = get_snapshot(series_slug, snapshot_id)
    if snapshot is None:
        raise FileNotFoundError(snapshot_id)

    provider = _merge_provider_settings(provider_override)
    prompt_package = ((snapshot.get("inputs") or {}).get("prompt_package") or {})
    video_payload = prompt_package.get("video_payload") or {}
    shot_card_path = ((snapshot.get("inputs") or {}).get("shot_card_path") or "").replace("\\", "/")

    request_body = {
        "model": provider.get("model", ""),
        "prompt": video_payload.get("prompt") or prompt_package.get("positive", ""),
        "negative_prompt": video_payload.get("negative_prompt") or prompt_package.get("negative", ""),
        "reference_images": prompt_package.get("reference_images", []),
        "duration_seconds": video_payload.get("duration_seconds", 5),
        "aspect_ratio": video_payload.get("aspect_ratio", ""),
        "resolution": video_payload.get("resolution", ""),
        "metadata": {
            "series_slug": series_slug,
            "snapshot_id": snapshot_id,
            "shot_card_path": shot_card_path,
            "assembled_from": prompt_package.get("assembled_from", {}),
            "created_at": utc_now_iso(),
        },
    }

    return {
        "provider": provider,
        "request_body": request_body,
    }


def _provider_headers(provider: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = str(provider.get("api_key", "")).strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _provider_url(base_url: str, path: str) -> str:
    cleaned_base = base_url.rstrip("/")
    cleaned_path = path if path.startswith("/") else f"/{path}"
    return f"{cleaned_base}{cleaned_path}"


def _deep_get(payload: Any, dotted_path: str) -> Any:
    if not dotted_path:
        return None

    current = payload
    for part in dotted_path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
            continue
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
            continue
        return None
    return current


def _normalize_value_set(raw: Any) -> set[str]:
    if isinstance(raw, list):
        return {str(item).strip().lower() for item in raw if str(item).strip()}
    return {item.strip().lower() for item in str(raw or "").split(",") if item.strip()}


def _guess_extension(url: str, default_extension: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix:
        return suffix
    return default_extension


def _download_asset_to_series_output(
    series_slug: str,
    *,
    url: str,
    output_subdir: str,
    file_stem: str,
    default_extension: str,
    provider: dict[str, Any],
) -> str:
    if not url:
        return ""

    response = requests.get(
        url,
        headers=_provider_headers(provider),
        timeout=int(provider.get("timeout_seconds", 300)),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"Asset download failed: {response.text}") from exc

    series_root = get_series_path(series_slug)
    relative_path = f"outputs/{output_subdir}/{file_stem}{_guess_extension(url, default_extension)}"
    absolute_path = series_root / relative_path
    write_bytes_atomic(absolute_path, response.content)
    return relative_to_series_root(absolute_path, series_root)


def _submit_generic_http(provider: dict[str, Any], request_body: dict[str, Any]) -> dict[str, Any]:
    base_url = str(provider.get("base_url", "")).rstrip("/")
    path = str(provider.get("path", "/")).strip() or "/"
    if not base_url:
        raise ValueError("Missing VIDEO_PROVIDER_BASE_URL")

    response = requests.post(
        _provider_url(base_url, path),
        headers=_provider_headers(provider),
        json=request_body,
        timeout=int(provider.get("timeout_seconds", 300)),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"Video provider request failed: {response.text}") from exc

    return response.json() if response.content else {}


def _fetch_generic_http_status(provider: dict[str, Any], task_id: str) -> dict[str, Any]:
    base_url = str(provider.get("base_url", "")).rstrip("/")
    if not base_url:
        raise ValueError("Missing VIDEO_PROVIDER_BASE_URL")
    if not task_id:
        raise ValueError("Job remote task_id is empty")

    status_path = str(provider.get("status_path", "")).strip() or str(provider.get("path", "/")).strip() or "/"
    status_method = str(provider.get("status_method", "GET")).strip().upper() or "GET"
    if "{task_id}" in status_path:
        resolved_path = status_path.replace("{task_id}", task_id)
    elif status_method == "GET":
        resolved_path = f"{status_path.rstrip('/')}/{task_id}"
    else:
        resolved_path = status_path

    request_kwargs: dict[str, Any] = {
        "headers": _provider_headers(provider),
        "timeout": int(provider.get("timeout_seconds", 300)),
    }
    if status_method != "GET":
        request_kwargs["json"] = {"task_id": task_id}

    response = requests.request(
        status_method,
        _provider_url(base_url, resolved_path),
        **request_kwargs,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"Video status request failed: {response.text}") from exc

    return response.json() if response.content else {}


def _extract_remote_state(provider: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    remote_status = str(_deep_get(payload, str(provider.get("result_status_path", "status"))) or "").strip()
    ready_values = _normalize_value_set(provider.get("ready_values"))
    failed_values = _normalize_value_set(provider.get("failed_values"))
    normalized_status = remote_status.lower()

    if normalized_status in ready_values:
        local_status = "completed"
    elif normalized_status in failed_values:
        local_status = "failed"
    else:
        local_status = "submitted"

    return {
        "remote_status": remote_status,
        "local_status": local_status,
        "video_url": str(_deep_get(payload, str(provider.get("result_video_url_path", "video_url"))) or "").strip(),
        "cover_url": str(_deep_get(payload, str(provider.get("result_cover_url_path", "cover_url"))) or "").strip(),
    }


def _finalize_submitted_job(series_slug: str, job_id: str, remote_payload: dict[str, Any]) -> dict[str, Any]:
    task_id = remote_payload.get("task_id") or remote_payload.get("id") or remote_payload.get("job_id") or ""
    raw_response_path = save_job_remote_response(series_slug, job_id, remote_payload)
    return update_job(
        series_slug,
        job_id,
        {
            "status": "submitted",
            "remote": {
                "task_id": task_id,
                "raw_response_path": raw_response_path,
                "raw_response": remote_payload,
            },
            "error": {
                "message": "",
                "code": "",
            },
        },
    )


def _finalize_completed_job(
    series_slug: str,
    job_id: str,
    *,
    remote_payload: dict[str, Any],
    remote_status: str,
    video_path: str = "",
    cover_path: str = "",
) -> dict[str, Any]:
    raw_response_path = save_job_remote_response(series_slug, job_id, remote_payload)
    return update_job(
        series_slug,
        job_id,
        {
            "status": "completed",
            "remote": {
                "raw_response_path": raw_response_path,
                "raw_response": remote_payload,
                "status": remote_status,
            },
            "result": {
                "video_path": video_path,
                "cover_path": cover_path,
            },
            "error": {
                "message": "",
                "code": "",
            },
        },
    )


def _finalize_failed_job(
    series_slug: str,
    job_id: str,
    *,
    message: str,
    code: str,
    remote_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updates: dict[str, Any] = {
        "status": "failed",
        "error": {
            "message": message,
            "code": code,
        },
    }

    if remote_payload:
        raw_response_path = save_job_remote_response(series_slug, job_id, remote_payload)
        updates["remote"] = {
            "raw_response_path": raw_response_path,
            "raw_response": remote_payload,
        }

    return update_job(series_slug, job_id, updates)


def submit_video_job(series_slug: str, job_id: str, provider_override: dict[str, Any] | None = None) -> dict[str, Any]:
    job = get_job(series_slug, job_id)
    if job is None:
        raise FileNotFoundError(job_id)

    request_body = ((job.get("provider") or {}).get("request_body") or {})
    if not request_body:
        raise ValueError("Job request body is empty")

    provider = _merge_provider_settings((job.get("provider") or {}))
    provider = _merge_provider_settings({**provider, **(provider_override or {})})
    submit_mode = str(provider.get("submit_mode", "manual")).strip() or "manual"

    update_job(
        series_slug,
        job_id,
        {
            "provider": _job_provider_payload(provider, request_body),
            "status": "submitting" if submit_mode == "generic_http" else "prepared",
        },
    )

    if submit_mode != "generic_http":
        return update_job(
            series_slug,
            job_id,
            {
                "status": "prepared",
                "error": {
                    "message": f"Submit skipped: unsupported submit_mode {submit_mode}",
                    "code": "UNSUPPORTED_SUBMIT_MODE",
                },
            },
        )

    try:
        remote_payload = _submit_generic_http(provider, request_body)
        return _finalize_submitted_job(series_slug, job_id, remote_payload)
    except ValueError as exc:
        return _finalize_failed_job(
            series_slug,
            job_id,
            message=str(exc),
            code="SUBMIT_FAILED",
        )


def refresh_video_job(series_slug: str, job_id: str, provider_override: dict[str, Any] | None = None) -> dict[str, Any]:
    job = get_job(series_slug, job_id)
    if job is None:
        raise FileNotFoundError(job_id)

    provider = _merge_provider_settings((job.get("provider") or {}))
    provider = _merge_provider_settings({**provider, **(provider_override or {})})
    submit_mode = str(provider.get("submit_mode", "manual")).strip() or "manual"
    if submit_mode != "generic_http":
        return update_job(
            series_slug,
            job_id,
            {
                "error": {
                    "message": f"Refresh skipped: unsupported submit_mode {submit_mode}",
                    "code": "UNSUPPORTED_REFRESH_MODE",
                },
            },
        )

    remote = job.get("remote") or {}
    task_id = str(remote.get("task_id", "")).strip()
    try:
        remote_payload = _fetch_generic_http_status(provider, task_id)
        remote_state = _extract_remote_state(provider, remote_payload)
    except ValueError as exc:
        return _finalize_failed_job(
            series_slug,
            job_id,
            message=str(exc),
            code="REFRESH_FAILED",
        )

    if remote_state["local_status"] == "failed":
        return _finalize_failed_job(
            series_slug,
            job_id,
            message=f"Remote job failed with status {remote_state['remote_status'] or 'unknown'}",
            code="REMOTE_JOB_FAILED",
            remote_payload=remote_payload,
        )

    if remote_state["local_status"] != "completed":
        raw_response_path = save_job_remote_response(series_slug, job_id, remote_payload)
        return update_job(
            series_slug,
            job_id,
            {
                "status": "submitted",
                "remote": {
                    "task_id": task_id,
                    "status": remote_state["remote_status"],
                    "raw_response_path": raw_response_path,
                    "raw_response": remote_payload,
                },
                "error": {
                    "message": "",
                    "code": "",
                },
            },
        )

    video_path = job.get("result", {}).get("video_path", "") or ""
    cover_path = job.get("result", {}).get("cover_path", "") or ""
    if provider.get("download_assets", True):
        try:
            if remote_state["video_url"]:
                video_path = _download_asset_to_series_output(
                    series_slug,
                    url=remote_state["video_url"],
                    output_subdir="videos",
                    file_stem=job_id,
                    default_extension=".mp4",
                    provider=provider,
                )
            if remote_state["cover_url"]:
                cover_path = _download_asset_to_series_output(
                    series_slug,
                    url=remote_state["cover_url"],
                    output_subdir="images",
                    file_stem=f"{job_id}_cover",
                    default_extension=".jpg",
                    provider=provider,
                )
        except ValueError as exc:
            return _finalize_failed_job(
                series_slug,
                job_id,
                message=str(exc),
                code="DOWNLOAD_FAILED",
                remote_payload=remote_payload,
            )

    return _finalize_completed_job(
        series_slug,
        job_id,
        remote_payload=remote_payload,
        remote_status=remote_state["remote_status"],
        video_path=video_path,
        cover_path=cover_path,
    )


def create_video_job_from_snapshot(
    series_slug: str,
    snapshot_id: str,
    *,
    job_type: str = "video_generation",
    provider_override: dict[str, Any] | None = None,
    auto_submit: bool = False,
) -> dict[str, Any]:
    payload = build_video_request_from_snapshot(series_slug, snapshot_id, provider_override)
    provider = payload["provider"]
    request_body = payload["request_body"]

    job = create_job(
        series_slug=series_slug,
        snapshot_id=snapshot_id,
        job_type=job_type,
        provider=_job_provider_payload(provider, request_body),
        initial_status="prepared",
    )

    if not auto_submit:
        return job

    return submit_video_job(series_slug, job["id"], provider_override)
