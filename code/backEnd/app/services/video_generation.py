import base64
import mimetypes
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from app.storage.common import relative_to_series_root, write_bytes_atomic
from app.storage.job_store import create_job, get_job, save_job_remote_response, update_job
from app.storage.series_store import get_series_path
from app.storage.snapshot_store import get_snapshot


SEEDANCE_RATIO_VALUES = {"21:9", "1:1", "16:9", "3:4", "4:3", "9:16", "adaptive"}
SEEDANCE_RESOLUTION_VALUES = {"480p", "720p", "1080p"}
SEEDANCE_READY_STATUSES = {"succeeded"}
SEEDANCE_FAILED_STATUSES = {"failed", "error", "cancelled", "canceled", "rejected"}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_provider_defaults() -> dict[str, Any]:
    return {
        "name": os.getenv("VIDEO_PROVIDER_NAME", "doubao-seedance-2-0").strip() or "doubao-seedance-2-0",
        "model": os.getenv("VIDEO_PROVIDER_MODEL", "doubao-seedance-2-0-260128").strip() or "doubao-seedance-2-0-260128",
        "submit_mode": os.getenv("VIDEO_PROVIDER_SUBMIT_MODE", "generic_http").strip() or "generic_http",
        "api_kind": "ark_content_generation_tasks",
        "base_url": os.getenv("VIDEO_PROVIDER_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").strip()
        or "https://ark.cn-beijing.volces.com/api/v3",
        "path": os.getenv("VIDEO_PROVIDER_PATH", "/contents/generations/tasks").strip() or "/contents/generations/tasks",
        "status_path": os.getenv("VIDEO_PROVIDER_STATUS_PATH", "/contents/generations/tasks/{task_id}").strip()
        or "/contents/generations/tasks/{task_id}",
        "api_key": os.getenv("VIDEO_PROVIDER_API_KEY", "").strip(),
        "timeout_seconds": _to_int(os.getenv("VIDEO_PROVIDER_TIMEOUT_SECONDS", "300"), 300),
        "download_assets": os.getenv("VIDEO_PROVIDER_DOWNLOAD_ASSETS", "true").strip().lower() not in {"0", "false", "no"},
    }


def _merge_provider_settings(override: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(_get_provider_defaults())
    for key, value in (override or {}).items():
        if value not in (None, ""):
            merged[key] = value
    return merged


def _job_provider_payload(provider: dict[str, Any], request_body: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": provider.get("name", ""),
        "model": provider.get("model", ""),
        "submit_mode": provider.get("submit_mode", "generic_http"),
        "api_kind": provider.get("api_kind", "ark_content_generation_tasks"),
        "base_url": provider.get("base_url", ""),
        "path": provider.get("path", "/"),
        "status_path": provider.get("status_path", ""),
        "timeout_seconds": provider.get("timeout_seconds", 300),
        "download_assets": provider.get("download_assets", True),
        "request_body": request_body,
    }


def _normalize_seedance_mode(value: Any) -> str:
    mode = _clean_text(value) or "reference_image"
    if mode == "first_frame":
        return "first_last_frame"
    if mode in {"text_only", "reference_image", "first_last_frame"}:
        return mode
    return "reference_image"


def _normalize_seedance_ratio(value: Any) -> str:
    ratio = _clean_text(value) or "16:9"
    if ratio not in SEEDANCE_RATIO_VALUES:
        raise ValueError(f"不支持的视频比例：{ratio}")
    return ratio


def _normalize_seedance_resolution(value: Any) -> str:
    resolution = _clean_text(value) or "1080p"
    if resolution not in SEEDANCE_RESOLUTION_VALUES:
        raise ValueError(f"不支持的分辨率：{resolution}")
    return resolution


def _normalize_seedance_duration(value: Any) -> int:
    duration = _to_int(value, 5)
    if duration < 1 or duration > 15:
        raise ValueError(f"视频时长必须在 1-15 秒之间，当前为 {duration}")
    return duration


def _normalize_seedance_count(value: Any) -> int:
    count = _to_int(value, 1)
    if count < 1 or count > 4:
        raise ValueError(f"生成数量必须在 1-4 条之间，当前为 {count}")
    return count


def _normalize_seedance_watermark(value: Any) -> bool:
    return bool(value)


def _normalize_seedance_generate_audio(value: Any) -> bool:
    return bool(value)


def _collect_media_references(prompt_package: dict[str, Any]) -> list[dict[str, Any]]:
    media_references = prompt_package.get("media_references") or []
    if media_references:
        return [dict(item) for item in media_references if isinstance(item, dict)]

    return [
        {
            "type": "image",
            "path": image_path,
            "role": "reference_image",
            "source_kind": "legacy",
            "source_id": "",
            "source_name": "",
        }
        for image_path in (prompt_package.get("reference_images") or [])
        if _clean_text(image_path)
    ]


def _infer_seedance_mode(
    video_payload: dict[str, Any],
    prompt_package: dict[str, Any],
    media_references: list[dict[str, Any]],
) -> str:
    configured_mode = _normalize_seedance_mode(
        video_payload.get("mode") or ((prompt_package.get("assembled_from") or {}).get("mode", ""))
    )
    if configured_mode in {"text_only", "reference_image", "first_last_frame"}:
        return configured_mode

    roles = {_clean_text(item.get("role", "")) for item in media_references}
    if "first_frame" in roles or "last_frame" in roles:
        return "first_last_frame"
    if any(_clean_text(item.get("path", "")) for item in media_references):
        return "reference_image"
    return "text_only"


def _build_seedance_content(
    *,
    prompt_text: str,
    mode: str,
    media_references: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt_text}]
    image_references = [item for item in media_references if _clean_text(item.get("type", "")).lower() == "image"]

    if mode == "text_only":
        return content

    if mode == "reference_image":
        for item in image_references:
            path = _clean_text(item.get("path", ""))
            if not path:
                continue
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": path,
                    },
                }
            )
        return content

    if mode == "first_last_frame":
        first_frame = next((item for item in image_references if _clean_text(item.get("role", "")) == "first_frame"), None)
        last_frame = next((item for item in image_references if _clean_text(item.get("role", "")) == "last_frame"), None)
        if first_frame is None:
            raise ValueError("首尾帧生成模式缺少首帧图片")

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": _clean_text(first_frame.get("path", "")),
                },
                "role": "first_frame",
            }
        )

        if last_frame is not None and _clean_text(last_frame.get("path", "")):
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _clean_text(last_frame.get("path", "")),
                    },
                    "role": "last_frame",
                }
            )

        return content

    raise ValueError(f"不支持的 Seedance 输入模式：{mode}")


def _build_seedance_request_body(provider: dict[str, Any], prompt_package: dict[str, Any]) -> dict[str, Any]:
    video_payload = prompt_package.get("video_payload") or {}
    media_references = _collect_media_references(prompt_package)
    prompt_text = _clean_text(video_payload.get("prompt") or prompt_package.get("positive", ""))
    if not prompt_text:
        raise ValueError("镜头包缺少可提交的提示词")

    mode = _infer_seedance_mode(video_payload, prompt_package, media_references)
    request_body = {
        "model": _clean_text(provider.get("model", "")),
        "content": _build_seedance_content(prompt_text=prompt_text, mode=mode, media_references=media_references),
        "ratio": _normalize_seedance_ratio(video_payload.get("ratio") or video_payload.get("aspect_ratio", "")),
        "resolution": _normalize_seedance_resolution(video_payload.get("resolution", "")),
        "duration": _normalize_seedance_duration(video_payload.get("duration") or video_payload.get("duration_seconds", 5)),
        "count": _normalize_seedance_count(video_payload.get("count", 1)),
        "generate_audio": _normalize_seedance_generate_audio(video_payload.get("generate_audio", False)),
        "watermark": _normalize_seedance_watermark(video_payload.get("watermark", False)),
    }

    if mode == "first_last_frame":
        request_body["return_last_frame"] = True

    return request_body


def build_video_request_from_snapshot(series_slug: str, snapshot_id: str, provider_override: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot = get_snapshot(series_slug, snapshot_id)
    if snapshot is None:
        raise FileNotFoundError(snapshot_id)

    provider = _merge_provider_settings(provider_override)
    prompt_package = ((snapshot.get("inputs") or {}).get("prompt_package") or {})
    request_body = _build_seedance_request_body(provider, prompt_package)

    return {
        "provider": provider,
        "request_body": request_body,
    }


def _provider_headers(provider: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = _clean_text(provider.get("api_key", ""))
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _is_remote_media_url(value: str) -> bool:
    normalized = _clean_text(value).lower()
    return normalized.startswith("http://") or normalized.startswith("https://") or normalized.startswith("asset://") or normalized.startswith("data:")


def _file_to_data_url(series_slug: str, file_path: str, fallback_mime: str) -> str:
    absolute_path = get_series_path(series_slug) / file_path
    if not absolute_path.exists():
        raise ValueError(f"本地素材不存在：{file_path}")

    mime_type = mimetypes.guess_type(absolute_path.name)[0] or fallback_mime
    encoded = base64.b64encode(absolute_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _materialize_request_body(series_slug: str, request_body: dict[str, Any]) -> dict[str, Any]:
    payload = dict(request_body)
    content_items: list[dict[str, Any]] = []

    for item in payload.get("content") or []:
        normalized_item = dict(item)
        item_type = _clean_text(normalized_item.get("type", ""))
        if item_type == "text":
            text = _clean_text(normalized_item.get("text", ""))
            if not text:
                continue
            normalized_item["text"] = text
        elif item_type == "image_url":
            image_url = dict(normalized_item.get("image_url") or {})
            url = _clean_text(image_url.get("url", ""))
            if not url:
                continue
            if not _is_remote_media_url(url):
                image_url["url"] = _file_to_data_url(series_slug, url, "image/jpeg")
            normalized_item["image_url"] = image_url
        else:
            raise ValueError(f"当前仅支持向 Seedance 提交 text 和 image_url 内容，收到：{item_type or 'unknown'}")

        content_items.append(normalized_item)

    payload["content"] = content_items
    return {key: value for key, value in payload.items() if value not in ("", None, [])}


def _provider_url(base_url: str, path: str) -> str:
    cleaned_base = base_url.rstrip("/")
    cleaned_path = path if path.startswith("/") else f"/{path}"
    return f"{cleaned_base}{cleaned_path}"


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
        raise ValueError(f"资源下载失败：{response.text}") from exc

    series_root = get_series_path(series_slug)
    relative_path = f"outputs/{output_subdir}/{file_stem}{_guess_extension(url, default_extension)}"
    absolute_path = series_root / relative_path
    write_bytes_atomic(absolute_path, response.content)
    return relative_to_series_root(absolute_path, series_root)


def _submit_seedance_task(provider: dict[str, Any], request_body: dict[str, Any]) -> dict[str, Any]:
    base_url = _clean_text(provider.get("base_url", "")).rstrip("/")
    path = _clean_text(provider.get("path", "/")) or "/"
    if not base_url:
        raise ValueError("缺少 VIDEO_PROVIDER_BASE_URL 配置")

    response = requests.post(
        _provider_url(base_url, path),
        headers=_provider_headers(provider),
        json=request_body,
        timeout=int(provider.get("timeout_seconds", 300)),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"Seedance 提交失败：{response.text}") from exc

    return response.json() if response.content else {}


def _fetch_seedance_task_status(provider: dict[str, Any], task_id: str) -> dict[str, Any]:
    base_url = _clean_text(provider.get("base_url", "")).rstrip("/")
    if not base_url:
        raise ValueError("缺少 VIDEO_PROVIDER_BASE_URL 配置")
    if not task_id:
        raise ValueError("任务远端 task_id 为空")

    status_path = _clean_text(provider.get("status_path", "")) or _clean_text(provider.get("path", "/")) or "/"
    resolved_path = status_path.replace("{task_id}", task_id) if "{task_id}" in status_path else f"{status_path.rstrip('/')}/{task_id}"

    response = requests.get(
        _provider_url(base_url, resolved_path),
        headers=_provider_headers(provider),
        timeout=int(provider.get("timeout_seconds", 300)),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"Seedance 状态查询失败：{response.text}") from exc

    return response.json() if response.content else {}


def _extract_seedance_remote_state(payload: dict[str, Any]) -> dict[str, Any]:
    remote_status = _clean_text(payload.get("status", ""))
    normalized_status = remote_status.lower()
    if normalized_status in SEEDANCE_READY_STATUSES:
        local_status = "completed"
    elif normalized_status in SEEDANCE_FAILED_STATUSES:
        local_status = "failed"
    else:
        local_status = "submitted"

    content = payload.get("content") or {}
    return {
        "remote_status": remote_status,
        "local_status": local_status,
        "video_url": _clean_text(content.get("video_url", "")),
        "cover_url": _clean_text(content.get("last_frame_url", "")) or _clean_text(content.get("cover_url", "")),
    }


def _finalize_submitted_job(series_slug: str, job_id: str, remote_payload: dict[str, Any]) -> dict[str, Any]:
    task_id = _clean_text(remote_payload.get("id") or remote_payload.get("task_id") or remote_payload.get("job_id") or "")
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
        raise ValueError("任务请求体为空")

    provider = _merge_provider_settings((job.get("provider") or {}))
    provider = _merge_provider_settings({**provider, **(provider_override or {})})
    submit_mode = _clean_text(provider.get("submit_mode", "generic_http")) or "generic_http"

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
        resolved_request_body = _materialize_request_body(series_slug, request_body)
        remote_payload = _submit_seedance_task(provider, resolved_request_body)
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
    submit_mode = _clean_text(provider.get("submit_mode", "generic_http")) or "generic_http"
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
    task_id = _clean_text(remote.get("task_id", ""))
    try:
        remote_payload = _fetch_seedance_task_status(provider, task_id)
        remote_state = _extract_seedance_remote_state(remote_payload)
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
                    default_extension=".png",
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
