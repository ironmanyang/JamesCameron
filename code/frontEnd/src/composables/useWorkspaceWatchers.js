import { watch } from "vue";

export function useWorkspaceWatchers({
  state,
  forms,
  inlineEditing,
  characterSourceFiles,
  characterSourceInput,
  filteredStoryboards,
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
  loadRemoteTaskDetail,
  getRemoteTaskIdByJob,
  applyShotModeRules,
  normalizeShotAnchorOverrides,
  cancelEpisodeEdit,
  cancelCharacterEdit,
  cancelSceneEdit,
  cancelShotEdit,
  defaultParsedScript,
  boot
}) {
  watch(
    () => state.selectedSeriesSlug,
    async (seriesSlug, previousSeriesSlug) => {
      if (seriesSlug !== previousSeriesSlug) {
        state.selectedEpisodeId = "";
        state.selectedStoryboardId = "";
        state.selectedShotId = "";
        state.selectedShotIds = [];
        state.selectedShotBatchId = "";
        state.selectedCharacterId = "";
        state.selectedSceneId = "";
        state.selectedJobId = "";
        state.selectedRemoteTaskId = "";
        state.characters = [];
        state.scenes = [];
        state.storyboards = [];
        state.shots = [];
        state.shotBatches = [];
        state.jobs = [];
        state.remoteTasks = [];
        state.selectedCharacterIds = [];
        state.selectedCharacterBible = null;
        state.selectedScenePackage = null;
        state.selectedShotBatch = null;
        state.selectedJob = null;
        state.selectedSnapshot = null;
        state.selectedRemoteTask = null;
        forms.shotSceneId = "";
        state.rawScript = "";
        state.parsedScriptText = JSON.stringify(defaultParsedScript(""), null, 2);
        cancelEpisodeEdit();
        cancelCharacterEdit();
        cancelSceneEdit();
        cancelShotEdit();
      }
      await loadEpisodes(seriesSlug);
      await loadProductionData(seriesSlug);
    }
  );

  watch(
    filteredStoryboards,
    (items) => {
      if (!items.some((item) => item.id === state.selectedStoryboardId)) {
        state.selectedStoryboardId = items[0]?.id || "";
      }
    },
    { immediate: true }
  );

  watch(
    () => state.selectedStoryboardId,
    async (storyboardId) => {
      cancelShotEdit();
      await loadShotsForStoryboard(state.selectedSeriesSlug, storyboardId);
      await loadShotBatchesForStoryboard(state.selectedSeriesSlug, storyboardId);
    }
  );

  watch(
    () => [state.selectedSeriesSlug, state.selectedEpisodeId],
    async ([seriesSlug, episodeId]) => {
      await loadEpisodeScripts(seriesSlug, episodeId);
    }
  );

  watch(
    () => state.selectedCharacterId,
    async (characterId) => {
      characterSourceFiles.value = [];
      if (characterSourceInput.value) {
        characterSourceInput.value.value = "";
      }
      await loadCharacterBible(state.selectedSeriesSlug, characterId);
    }
  );

  watch(
    () => state.selectedSceneId,
    async (sceneId) => {
      await loadScenePackage(state.selectedSeriesSlug, sceneId);
    }
  );

  watch(
    () => state.selectedJobId,
    async (jobId) => {
      await loadJobDetail(state.selectedSeriesSlug, jobId);
      const job = state.jobs.find((item) => item.id === jobId) || null;
      await loadSnapshotDetail(state.selectedSeriesSlug, job?.snapshot_id || "");
      const remoteTaskId = getRemoteTaskIdByJob(job);
      if (remoteTaskId) {
        state.selectedRemoteTaskId = remoteTaskId;
      }
    }
  );

  watch(
    () => state.selectedShotBatchId,
    async (batchId) => {
      await loadShotBatchDetail(state.selectedSeriesSlug, state.selectedStoryboardId, batchId);
    }
  );

  watch(
    () => state.selectedRemoteTaskId,
    async (taskId) => {
      await loadRemoteTaskDetail(state.selectedSeriesSlug, taskId);
    }
  );

  watch(
    () => forms.shotInputMode,
    () => {
      applyShotModeRules(forms);
    }
  );

  watch(
    () => inlineEditing.shotInputMode,
    () => {
      applyShotModeRules(inlineEditing);
    }
  );

  watch(
    () => [...state.selectedCharacterIds],
    (characterIds) => {
      forms.shotAnchorOverrides = normalizeShotAnchorOverrides(forms.shotAnchorOverrides, characterIds);
    }
  );

  watch(
    () => [...inlineEditing.shotCharacterIds],
    (characterIds) => {
      inlineEditing.shotAnchorOverrides = normalizeShotAnchorOverrides(
        inlineEditing.shotAnchorOverrides,
        characterIds
      );
    }
  );

  boot();
}
