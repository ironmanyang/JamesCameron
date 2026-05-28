import {
  getCharacterBible,
  getHealth,
  getJob,
  getRemoteVideoTask,
  getSnapshot,
  getShotBatch,
  getParsedScript,
  getRawScript,
  getScenePromptPackage,
  listCharacters,
  listEpisodes,
  listSnapshots,
  listJobs,
  listRemoteVideoTasks,
  listScenes,
  listSeries,
  listShots,
  listShotBatches,
  listStoryboards
} from "../services/api";

export function useWorkspaceReadActions({
  health,
  state,
  forms,
  loading,
  selectedEpisode,
  filteredStoryboards,
  syncAssetCounts,
  setError,
  defaultParsedScript,
  getLinkedRemoteTaskIds,
  getRemoteTaskId
}) {
  const requestSeeds = {
    episodeScripts: 0,
    production: 0,
    shots: 0,
    characterBible: 0,
    scenePackage: 0,
    jobDetail: 0,
    snapshotDetail: 0,
    shotBatch: 0,
    shotBatchDetail: 0,
    remoteTask: 0,
    remoteTaskDetail: 0
  };

  async function loadHealth() {
    try {
      const data = await getHealth();
      health.value = data.status || "unknown";
    } catch (error) {
      health.value = "offline";
      setError(error);
    }
  }

  async function loadSeries() {
    loading.series = true;
    try {
      const data = await listSeries();
      state.series = data.items || [];
      if (!state.selectedSeriesSlug && state.series.length) {
        state.selectedSeriesSlug = state.series[0].slug;
      }
    } catch (error) {
      setError(error);
    } finally {
      loading.series = false;
    }
  }

  async function loadEpisodes(seriesSlug) {
    if (!seriesSlug) {
      state.episodes = [];
      state.selectedEpisodeId = "";
      return;
    }

    loading.episodes = true;
    try {
      const data = await listEpisodes(seriesSlug);
      state.episodes = data.items || [];
      if (!state.episodes.some((item) => item.id === state.selectedEpisodeId)) {
        state.selectedEpisodeId = state.episodes[0]?.id || "";
      }
    } catch (error) {
      setError(error);
    } finally {
      loading.episodes = false;
    }
  }

  async function loadJobDetail(seriesSlug, jobId) {
    const requestId = ++requestSeeds.jobDetail;
    if (!seriesSlug || !jobId) {
      state.selectedJob = null;
      return;
    }

    loading.jobDetail = true;
    state.selectedJob = null;
    try {
      const response = await getJob(seriesSlug, jobId);
      if (
        requestId !== requestSeeds.jobDetail ||
        seriesSlug !== state.selectedSeriesSlug ||
        jobId !== state.selectedJobId
      ) {
        return;
      }
      state.selectedJob = response.item || null;
    } catch (error) {
      if (
        requestId !== requestSeeds.jobDetail ||
        seriesSlug !== state.selectedSeriesSlug ||
        jobId !== state.selectedJobId
      ) {
        return;
      }
      state.selectedJob = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.jobDetail) {
        loading.jobDetail = false;
      }
    }
  }

  async function loadSnapshotDetail(seriesSlug, snapshotId) {
    const requestId = ++requestSeeds.snapshotDetail;
    if (!seriesSlug || !snapshotId) {
      state.selectedSnapshotId = "";
      state.selectedSnapshot = null;
      return;
    }

    loading.snapshotDetail = true;
    state.selectedSnapshot = null;
    try {
      const response = await getSnapshot(seriesSlug, snapshotId);
      if (requestId !== requestSeeds.snapshotDetail || seriesSlug !== state.selectedSeriesSlug) {
        return;
      }
      state.selectedSnapshot = response.item || null;
    } catch (error) {
      if (requestId !== requestSeeds.snapshotDetail || seriesSlug !== state.selectedSeriesSlug) {
        return;
      }
      state.selectedSnapshot = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.snapshotDetail) {
        loading.snapshotDetail = false;
      }
    }
  }

  async function loadRemoteTasks(seriesSlug, preferredTaskId = "") {
    const requestId = ++requestSeeds.remoteTask;
    const linkedTaskIds = getLinkedRemoteTaskIds();
    if (!seriesSlug || !linkedTaskIds.length) {
      state.remoteTasks = [];
      state.selectedRemoteTaskId = "";
      state.selectedRemoteTask = null;
      return;
    }

    loading.remoteTasks = true;
    const desiredTaskId = preferredTaskId || state.selectedRemoteTaskId;
    try {
      const response = await listRemoteVideoTasks(seriesSlug, {
        page_size: Math.max(20, linkedTaskIds.length),
        task_ids: linkedTaskIds
      });
      if (requestId !== requestSeeds.remoteTask || seriesSlug !== state.selectedSeriesSlug) {
        return;
      }
      const remoteItems = Array.isArray(response.items)
        ? response.items
        : Array.isArray(response.data)
          ? response.data
          : Array.isArray(response.tasks)
            ? response.tasks
            : [];
      state.remoteTasks = remoteItems;
      state.selectedRemoteTaskId = state.remoteTasks.some((item) => getRemoteTaskId(item) === desiredTaskId)
        ? desiredTaskId
        : getRemoteTaskId(state.remoteTasks[0]) || "";
      if (!state.selectedRemoteTaskId) {
        state.selectedRemoteTask = null;
      }
    } catch (error) {
      if (requestId !== requestSeeds.remoteTask || seriesSlug !== state.selectedSeriesSlug) {
        return;
      }
      state.remoteTasks = [];
      state.selectedRemoteTaskId = "";
      state.selectedRemoteTask = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.remoteTask) {
        loading.remoteTasks = false;
      }
    }
  }

  async function loadProductionData(seriesSlug) {
    const requestId = ++requestSeeds.production;
    if (!seriesSlug) {
      state.characters = [];
      state.scenes = [];
      state.storyboards = [];
      state.snapshots = [];
      state.jobs = [];
      state.remoteTasks = [];
      state.shots = [];
      state.shotBatches = [];
      state.selectedCharacterId = "";
      state.selectedSceneId = "";
      state.selectedStoryboardId = "";
      state.selectedShotId = "";
      state.selectedShotIds = [];
      state.selectedShotBatchId = "";
      state.selectedSnapshotId = "";
      state.selectedJobId = "";
      state.selectedRemoteTaskId = "";
      state.selectedCharacterBible = null;
      state.selectedScenePackage = null;
      state.selectedShotBatch = null;
      state.selectedJob = null;
      state.selectedRemoteTask = null;
      syncAssetCounts();
      return;
    }

    loading.production = true;
    try {
      const [characters, scenes, storyboards, snapshots, jobs] = await Promise.all([
        listCharacters(seriesSlug),
        listScenes(seriesSlug),
        listStoryboards(seriesSlug),
        listSnapshots(seriesSlug),
        listJobs(seriesSlug)
      ]);

      if (requestId !== requestSeeds.production || seriesSlug !== state.selectedSeriesSlug) {
        return;
      }

      state.characters = characters.items || [];
      state.scenes = scenes.items || [];
      state.storyboards = storyboards.items || [];
      state.snapshots = snapshots.items || [];
      state.jobs = jobs.items || [];
      syncAssetCounts();

      if (!state.characters.some((item) => item.id === state.selectedCharacterId)) {
        state.selectedCharacterId = state.characters[0]?.id || "";
      }
      if (!state.scenes.some((item) => item.id === state.selectedSceneId)) {
        state.selectedSceneId = state.scenes[0]?.id || "";
      }
      if (!filteredStoryboards.value.some((item) => item.id === state.selectedStoryboardId)) {
        state.selectedStoryboardId = filteredStoryboards.value[0]?.id || "";
      }
      if (!state.jobs.some((item) => item.id === state.selectedJobId)) {
        state.selectedJobId = state.jobs[0]?.id || "";
      }
      if (!state.snapshots.some((item) => item.id === state.selectedSnapshotId)) {
        state.selectedSnapshotId = "";
        state.selectedSnapshot = null;
      }
      if (!state.scenes.some((item) => item.id === forms.shotSceneId)) {
        forms.shotSceneId = state.scenes[0]?.id || "";
      }
      state.selectedCharacterIds = state.selectedCharacterIds.filter((item) =>
        state.characters.some((character) => character.id === item)
      );
      if (state.selectedJobId) {
        await loadJobDetail(seriesSlug, state.selectedJobId);
      } else {
        state.selectedJob = null;
      }
      if (state.selectedSnapshotId) {
        await loadSnapshotDetail(seriesSlug, state.selectedSnapshotId);
      } else {
        state.selectedSnapshot = null;
      }
      await loadRemoteTasks(seriesSlug, state.selectedRemoteTaskId);
    } catch (error) {
      if (requestId !== requestSeeds.production || seriesSlug !== state.selectedSeriesSlug) {
        return;
      }
      setError(error);
    } finally {
      if (requestId === requestSeeds.production) {
        loading.production = false;
      }
    }
  }

  async function loadShotsForStoryboard(seriesSlug, storyboardId, preferredShotId = "") {
    const requestId = ++requestSeeds.shots;
    if (!seriesSlug || !storyboardId) {
      state.shots = [];
      state.selectedShotId = "";
      state.selectedShotIds = [];
      return;
    }

    const desiredShotId = preferredShotId || state.selectedShotId;
    loading.shots = true;
    state.shots = [];
    try {
      const data = await listShots(seriesSlug, storyboardId);
      if (
        requestId !== requestSeeds.shots ||
        seriesSlug !== state.selectedSeriesSlug ||
        storyboardId !== state.selectedStoryboardId
      ) {
        return;
      }
      state.shots = data.items || [];
      state.selectedShotIds = state.selectedShotIds.filter((item) => state.shots.some((shot) => shot.id === item));
      state.selectedShotId = state.shots.some((item) => item.id === desiredShotId)
        ? desiredShotId
        : state.shots[0]?.id || "";
    } catch (error) {
      if (
        requestId !== requestSeeds.shots ||
        seriesSlug !== state.selectedSeriesSlug ||
        storyboardId !== state.selectedStoryboardId
      ) {
        return;
      }
      setError(error);
    } finally {
      if (requestId === requestSeeds.shots) {
        loading.shots = false;
      }
    }
  }

  async function loadShotBatchesForStoryboard(seriesSlug, storyboardId, preferredBatchId = "") {
    const requestId = ++requestSeeds.shotBatch;
    if (!seriesSlug || !storyboardId) {
      state.shotBatches = [];
      state.selectedShotBatchId = "";
      state.selectedShotBatch = null;
      return;
    }

    const desiredBatchId = preferredBatchId || state.selectedShotBatchId;
    loading.shotBatches = true;
    try {
      const response = await listShotBatches(seriesSlug, storyboardId);
      if (
        requestId !== requestSeeds.shotBatch ||
        seriesSlug !== state.selectedSeriesSlug ||
        storyboardId !== state.selectedStoryboardId
      ) {
        return;
      }
      state.shotBatches = response.items || [];
      state.selectedShotBatchId = state.shotBatches.some((item) => item.id === desiredBatchId)
        ? desiredBatchId
        : state.shotBatches[0]?.id || "";
      if (!state.selectedShotBatchId) {
        state.selectedShotBatch = null;
      }
    } catch (error) {
      if (
        requestId !== requestSeeds.shotBatch ||
        seriesSlug !== state.selectedSeriesSlug ||
        storyboardId !== state.selectedStoryboardId
      ) {
        return;
      }
      state.shotBatches = [];
      state.selectedShotBatchId = "";
      state.selectedShotBatch = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.shotBatch) {
        loading.shotBatches = false;
      }
    }
  }

  async function loadEpisodeScripts(seriesSlug, episodeId) {
    const requestId = ++requestSeeds.episodeScripts;
    if (!seriesSlug || !episodeId) {
      state.rawScript = "";
      state.parsedScriptText = JSON.stringify(defaultParsedScript(""), null, 2);
      return;
    }

    loading.scripts = true;
    state.rawScript = "";
    state.parsedScriptText = JSON.stringify(defaultParsedScript(selectedEpisode.value?.name || ""), null, 2);
    try {
      const [raw, parsed] = await Promise.all([
        getRawScript(seriesSlug, episodeId),
        getParsedScript(seriesSlug, episodeId)
      ]);

      if (
        requestId !== requestSeeds.episodeScripts ||
        seriesSlug !== state.selectedSeriesSlug ||
        episodeId !== state.selectedEpisodeId
      ) {
        return;
      }

      state.rawScript = raw.content || "";
      const parsedContent =
        parsed.content && Object.keys(parsed.content).length
          ? parsed.content
          : defaultParsedScript(selectedEpisode.value?.name || "");
      state.parsedScriptText = JSON.stringify(parsedContent, null, 2);
    } catch (error) {
      if (
        requestId !== requestSeeds.episodeScripts ||
        seriesSlug !== state.selectedSeriesSlug ||
        episodeId !== state.selectedEpisodeId
      ) {
        return;
      }
      setError(error);
    } finally {
      if (requestId === requestSeeds.episodeScripts) {
        loading.scripts = false;
      }
    }
  }

  async function loadCharacterBible(seriesSlug, characterId) {
    const requestId = ++requestSeeds.characterBible;
    if (!seriesSlug || !characterId) {
      state.selectedCharacterBible = null;
      return;
    }

    loading.characterBible = true;
    state.selectedCharacterBible = null;
    try {
      const response = await getCharacterBible(seriesSlug, characterId);
      if (
        requestId !== requestSeeds.characterBible ||
        seriesSlug !== state.selectedSeriesSlug ||
        characterId !== state.selectedCharacterId
      ) {
        return;
      }
      state.selectedCharacterBible = response.item || null;
    } catch (error) {
      if (
        requestId !== requestSeeds.characterBible ||
        seriesSlug !== state.selectedSeriesSlug ||
        characterId !== state.selectedCharacterId
      ) {
        return;
      }
      state.selectedCharacterBible = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.characterBible) {
        loading.characterBible = false;
      }
    }
  }

  async function loadScenePackage(seriesSlug, sceneId) {
    const requestId = ++requestSeeds.scenePackage;
    if (!seriesSlug || !sceneId) {
      state.selectedScenePackage = null;
      return;
    }

    loading.scenePackage = true;
    state.selectedScenePackage = null;
    try {
      const response = await getScenePromptPackage(seriesSlug, sceneId);
      if (
        requestId !== requestSeeds.scenePackage ||
        seriesSlug !== state.selectedSeriesSlug ||
        sceneId !== state.selectedSceneId
      ) {
        return;
      }
      state.selectedScenePackage = response.item || null;
    } catch (error) {
      if (
        requestId !== requestSeeds.scenePackage ||
        seriesSlug !== state.selectedSeriesSlug ||
        sceneId !== state.selectedSceneId
      ) {
        return;
      }
      state.selectedScenePackage = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.scenePackage) {
        loading.scenePackage = false;
      }
    }
  }

  async function loadShotBatchDetail(seriesSlug, storyboardId, batchId) {
    const requestId = ++requestSeeds.shotBatchDetail;
    if (!seriesSlug || !storyboardId || !batchId) {
      state.selectedShotBatch = null;
      return;
    }

    loading.shotBatches = true;
    state.selectedShotBatch = null;
    try {
      const response = await getShotBatch(seriesSlug, storyboardId, batchId);
      if (
        requestId !== requestSeeds.shotBatchDetail ||
        seriesSlug !== state.selectedSeriesSlug ||
        storyboardId !== state.selectedStoryboardId ||
        batchId !== state.selectedShotBatchId
      ) {
        return;
      }
      state.selectedShotBatch = response.item || null;
    } catch (error) {
      if (
        requestId !== requestSeeds.shotBatchDetail ||
        seriesSlug !== state.selectedSeriesSlug ||
        storyboardId !== state.selectedStoryboardId ||
        batchId !== state.selectedShotBatchId
      ) {
        return;
      }
      state.selectedShotBatch = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.shotBatchDetail) {
        loading.shotBatches = false;
      }
    }
  }

  async function loadRemoteTaskDetail(seriesSlug, taskId) {
    const requestId = ++requestSeeds.remoteTaskDetail;
    if (!seriesSlug || !taskId) {
      state.selectedRemoteTask = null;
      return;
    }

    loading.remoteTaskDetail = true;
    state.selectedRemoteTask = null;
    try {
      const response = await getRemoteVideoTask(seriesSlug, taskId);
      if (
        requestId !== requestSeeds.remoteTaskDetail ||
        seriesSlug !== state.selectedSeriesSlug ||
        taskId !== state.selectedRemoteTaskId
      ) {
        return;
      }
      state.selectedRemoteTask = response || null;
    } catch (error) {
      if (
        requestId !== requestSeeds.remoteTaskDetail ||
        seriesSlug !== state.selectedSeriesSlug ||
        taskId !== state.selectedRemoteTaskId
      ) {
        return;
      }
      state.selectedRemoteTask = null;
      setError(error);
    } finally {
      if (requestId === requestSeeds.remoteTaskDetail) {
        loading.remoteTaskDetail = false;
      }
    }
  }

  async function boot() {
    await loadHealth();
    await loadSeries();
    loading.boot = false;
  }

  return {
    loadHealth,
    loadSeries,
    loadEpisodes,
    loadProductionData,
    loadShotsForStoryboard,
    loadShotBatchesForStoryboard,
    loadEpisodeScripts,
    loadCharacterBible,
    loadScenePackage,
    loadJobDetail,
    loadSnapshotDetail,
    loadShotBatchDetail,
    loadRemoteTasks,
    loadRemoteTaskDetail,
    boot
  };
}
