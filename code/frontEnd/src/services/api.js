import { computed, ref } from "vue";

const JSON_HEADERS = {
  "Content-Type": "application/json"
};

const activeRequestCount = ref(0);

export const isApiBusy = computed(() => activeRequestCount.value > 0);
export const apiBusyText = computed(() =>
  activeRequestCount.value > 1 ? `正在处理 ${activeRequestCount.value} 个请求...` : "请求处理中..."
);

function requestLabel(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  return `${method} ${path}`;
}

function extractMessage(value) {
  if (!value) {
    return "";
  }
  if (typeof value === "string") {
    return value.trim();
  }
  if (Array.isArray(value)) {
    return value.map((item) => extractMessage(item)).filter(Boolean).join("；");
  }
  if (typeof value === "object") {
    return [
      extractMessage(value.detail),
      extractMessage(value.message),
      extractMessage(value.error),
      extractMessage(value.raw_text),
      extractMessage(value.errors)
    ]
      .filter(Boolean)
      .join("；");
  }
  return String(value).trim();
}

async function parsePayload(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json().catch(() => null);
  }

  const text = await response.text().catch(() => "");
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return { raw_text: text };
  }
}

function buildHttpError(response, payload, path, options = {}) {
  const label = requestLabel(path, options);
  const payloadMessage = extractMessage(payload);
  const fallback = `${label} failed: ${response.status} ${response.statusText}`.trim();
  return new Error(payloadMessage ? `${payloadMessage} (${label})` : fallback);
}

function buildNetworkError(error, path, options = {}) {
  const label = requestLabel(path, options);
  const originalMessage =
    error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown network error";
  return new Error(`${label} failed: ${originalMessage}`, error instanceof Error ? { cause: error } : undefined);
}

async function request(path, options = {}) {
  activeRequestCount.value += 1;

  try {
    const response = await fetch(path, options);
    const payload = await parsePayload(response);

    if (!response.ok) {
      throw buildHttpError(response, payload, path, options);
    }

    return payload ?? {};
  } catch (error) {
    if (error instanceof Error && !/^TypeError\b/.test(error.name)) {
      throw error;
    }
    throw buildNetworkError(error, path, options);
  } finally {
    activeRequestCount.value = Math.max(0, activeRequestCount.value - 1);
  }
}

export function listSeries() {
  return request("/api/series");
}

export function createSeries(data) {
  return request("/api/series", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function updateSeries(seriesSlug, data) {
  return request(`/api/series/${seriesSlug}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function deleteSeries(seriesSlug) {
  return request(`/api/series/${seriesSlug}`, {
    method: "DELETE"
  });
}

export function listEpisodes(seriesSlug) {
  return request(`/api/episodes?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function createEpisode(data) {
  return request("/api/episodes", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function updateEpisode(seriesSlug, episodeId, data) {
  return request(`/api/episodes/${episodeId}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      ...data
    })
  });
}

export function deleteEpisode(seriesSlug, episodeId) {
  return request(`/api/episodes/${episodeId}?series_slug=${encodeURIComponent(seriesSlug)}`, {
    method: "DELETE"
  });
}

export function getRawScript(seriesSlug, episodeId) {
  return request(`/api/episodes/${episodeId}/raw-script?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function saveRawScript(seriesSlug, episodeId, rawText) {
  return request(`/api/episodes/${episodeId}/raw-script`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      raw_text: rawText
    })
  });
}

export function getParsedScript(seriesSlug, episodeId) {
  return request(`/api/episodes/${episodeId}/parsed-script?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function saveParsedScript(seriesSlug, episodeId, parsedScript) {
  return request(`/api/episodes/${episodeId}/parsed-script`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      parsed_script: parsedScript
    })
  });
}

export function analyzeEpisodeScript(seriesSlug, episodeId) {
  return request(`/api/episodes/${episodeId}/analyze-script`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug
    })
  });
}

export function listCharacters(seriesSlug) {
  return request(`/api/characters?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function createCharacter(data) {
  return request("/api/characters", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function updateCharacter(seriesSlug, characterId, data) {
  return request(`/api/characters/${characterId}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      ...data
    })
  });
}

export function deleteCharacter(seriesSlug, characterId) {
  return request(`/api/characters/${characterId}?series_slug=${encodeURIComponent(seriesSlug)}`, {
    method: "DELETE"
  });
}

export function getCharacterBible(seriesSlug, characterId) {
  return request(`/api/characters/${characterId}/bible?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function generateCharacterAssets(seriesSlug, characterId, episodeIds = [], generationMode = "reference_plus_text") {
  return request(`/api/characters/${characterId}/generate-assets`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      episode_ids: episodeIds,
      generation_mode: generationMode
    })
  });
}

export function uploadCharacterSourceImages(seriesSlug, characterId, files) {
  const formData = new FormData();
  formData.append("series_slug", seriesSlug);
  Array.from(files || []).forEach((file) => {
    formData.append("files", file);
  });

  return request(`/api/characters/${characterId}/source-images`, {
    method: "POST",
    body: formData
  });
}

export function deleteCharacterSourceImage(seriesSlug, characterId, imagePath) {
  return request(
    `/api/characters/${characterId}/source-images?series_slug=${encodeURIComponent(seriesSlug)}&image_path=${encodeURIComponent(imagePath)}`,
    {
      method: "DELETE"
    }
  );
}

export function listScenes(seriesSlug) {
  return request(`/api/scenes?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function createScene(data) {
  return request("/api/scenes", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function updateScene(seriesSlug, sceneId, data) {
  return request(`/api/scenes/${sceneId}/meta`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      ...data
    })
  });
}

export function deleteScene(seriesSlug, sceneId) {
  return request(`/api/scenes/${sceneId}?series_slug=${encodeURIComponent(seriesSlug)}`, {
    method: "DELETE"
  });
}

export function getScenePromptPackage(seriesSlug, sceneId) {
  return request(`/api/scenes/${sceneId}/prompt-package?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function generateSceneAssets(seriesSlug, sceneId, episodeIds = []) {
  return request(`/api/scenes/${sceneId}/generate-assets`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      episode_ids: episodeIds
    })
  });
}

export function listStoryboards(seriesSlug) {
  return request(`/api/storyboards?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function createStoryboard(data) {
  return request("/api/storyboards", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function updateStoryboard(seriesSlug, storyboardId, storyboardData) {
  return request(`/api/storyboards/${storyboardId}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      storyboard_data: storyboardData
    })
  });
}

export function deleteStoryboard(seriesSlug, storyboardId) {
  return request(`/api/storyboards/${storyboardId}?series_slug=${encodeURIComponent(seriesSlug)}`, {
    method: "DELETE"
  });
}

export function listShots(seriesSlug, storyboardId) {
  return request(`/api/storyboards/${storyboardId}/shots?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function createShot(seriesSlug, storyboardId, data) {
  return request(`/api/storyboards/${storyboardId}/shots`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      ...data
    })
  });
}

export function updateShot(seriesSlug, storyboardId, shotId, shotData) {
  return request(`/api/storyboards/${storyboardId}/shots/${shotId}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      shot_data: shotData
    })
  });
}

export function deleteShot(seriesSlug, storyboardId, shotId) {
  return request(
    `/api/storyboards/${storyboardId}/shots/${shotId}?series_slug=${encodeURIComponent(seriesSlug)}`,
    {
      method: "DELETE"
    }
  );
}

export function assembleShotPackage(seriesSlug, storyboardId, shotId) {
  return request(`/api/storyboards/${storyboardId}/shots/${shotId}/assemble-package`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug
    })
  });
}

export function assembleScenePackage(seriesSlug, storyboardId, sceneId, scenePayload) {
  return request(`/api/storyboards/${storyboardId}/assemble-scene-package`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      scene_id: sceneId,
      scene_payload: scenePayload
    })
  });
}

export function uploadShotMediaImages(seriesSlug, storyboardId, target, files, shotId = "") {
  const formData = new FormData();
  formData.append("series_slug", seriesSlug);
  formData.append("target", target);
  if (shotId) {
    formData.append("shot_id", shotId);
  }
  Array.from(files || []).forEach((file) => {
    formData.append("files", file);
  });

  return request(`/api/storyboards/${storyboardId}/shot-media-images`, {
    method: "POST",
    body: formData
  });
}

export function createSnapshot(data) {
  return request("/api/snapshots", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function createSceneDirectSnapshot(data) {
  return request("/api/snapshots/scene-direct", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function listSnapshots(seriesSlug) {
  return request(`/api/snapshots?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function getSnapshot(seriesSlug, snapshotId) {
  return request(`/api/snapshots/${snapshotId}?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function deleteSnapshot(seriesSlug, snapshotId) {
  return request(`/api/snapshots/${snapshotId}?series_slug=${encodeURIComponent(seriesSlug)}`, {
    method: "DELETE"
  });
}

export function listJobs(seriesSlug) {
  return request(`/api/jobs?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function createJob(data) {
  return request("/api/jobs", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function createVideoJobFromSnapshot(data) {
  return request("/api/jobs/from-snapshot", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function getJob(seriesSlug, jobId) {
  return request(`/api/jobs/${jobId}?series_slug=${encodeURIComponent(seriesSlug)}`);
}

export function deleteJob(seriesSlug, jobId) {
  return request(`/api/jobs/${jobId}?series_slug=${encodeURIComponent(seriesSlug)}`, {
    method: "DELETE"
  });
}

export function submitJob(seriesSlug, jobId, provider = {}) {
  return request(`/api/jobs/${jobId}/submit`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      provider
    })
  });
}

export function refreshJob(seriesSlug, jobId, provider = {}) {
  return request(`/api/jobs/${jobId}/refresh`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      series_slug: seriesSlug,
      provider
    })
  });
}

export function getHealth() {
  return request("/api/health");
}
