const JSON_HEADERS = {
  "Content-Type": "application/json"
};

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = payload.detail || payload.message || `Request failed: ${response.status}`;
    throw new Error(message);
  }

  return payload;
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

export async function uploadCharacterSourceImages(seriesSlug, characterId, files) {
  const formData = new FormData();
  formData.append("series_slug", seriesSlug);
  Array.from(files || []).forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(`/api/characters/${characterId}/source-images`, {
    method: "POST",
    body: formData
  });
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = payload.detail || payload.message || `Request failed: ${response.status}`;
    throw new Error(message);
  }

  return payload;
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

export function createSnapshot(data) {
  return request("/api/snapshots", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data)
  });
}

export function getSnapshot(seriesSlug, snapshotId) {
  return request(`/api/snapshots/${snapshotId}?series_slug=${encodeURIComponent(seriesSlug)}`);
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
