import { computed } from "vue";
import {
  buildSeedanceRequestSummary,
  normalizeSeedanceRequestBodyForDisplay,
  normalizeStoryboardProductionMode
} from "../utils/formatters";

export function useWorkspaceDerived({ state, loading, assetUrl, getJobById, getRemoteTaskId }) {
  const selectedSeries = computed(() => state.series.find((item) => item.slug === state.selectedSeriesSlug) || null);
  const selectedEpisode = computed(() => state.episodes.find((item) => item.id === state.selectedEpisodeId) || null);
  const selectedCharacter = computed(
    () => state.characters.find((item) => item.id === state.selectedCharacterId) || null
  );
  const selectedScene = computed(() => state.scenes.find((item) => item.id === state.selectedSceneId) || null);
  const filteredStoryboards = computed(() =>
    state.storyboards.filter((item) => !state.selectedEpisodeId || item.episode_id === state.selectedEpisodeId)
  );
  const selectedStoryboard = computed(
    () => filteredStoryboards.value.find((item) => item.id === state.selectedStoryboardId) || null
  );
  const selectedStoryboardProductionMode = computed(() =>
    normalizeStoryboardProductionMode(selectedStoryboard.value?.production_mode)
  );
  const selectedSceneDirectPackage = computed(() => selectedStoryboard.value?.scene_direct_package || null);
  const selectedShot = computed(() => state.shots.find((item) => item.id === state.selectedShotId) || null);
  const selectedShotBatchComputed = computed(() => {
    if (state.selectedShotBatch && state.selectedShotBatch.id === state.selectedShotBatchId) {
      return state.selectedShotBatch;
    }
    return state.shotBatches.find((item) => item.id === state.selectedShotBatchId) || null;
  });
  const seriesListPanelLoading = computed(() => loading.boot || loading.series || loading.updateSeries || loading.deleteSeries);
  const seriesCreatePanelLoading = computed(() => loading.createSeries);
  const episodesPanelLoading = computed(
    () =>
      loading.boot ||
      loading.production ||
      loading.episodes ||
      loading.createEpisode ||
      loading.updateEpisode ||
      loading.deleteEpisode
  );
  const rawScriptPanelLoading = computed(() => loading.boot || loading.scripts || loading.analyzeScript || loading.saveRaw);
  const parsedScriptPanelLoading = computed(
    () => loading.boot || loading.scripts || loading.analyzeScript || loading.saveParsed || loading.importParsedShot
  );
  const characterCreatePanelLoading = computed(
    () => loading.boot || loading.production || loading.createCharacter || loading.updateCharacter || loading.deleteCharacter
  );
  const sceneCreatePanelLoading = computed(
    () => loading.boot || loading.production || loading.createScene || loading.updateScene || loading.deleteScene
  );
  const characterLabPanelLoading = computed(
    () =>
      loading.boot ||
      loading.production ||
      loading.characterAssets ||
      loading.characterUpload ||
      loading.deleteCharacterSourceImage ||
      loading.characterBible
  );
  const sceneLabPanelLoading = computed(
    () => loading.boot || loading.production || loading.sceneAssets || loading.scenePackage
  );
  const storyboardConfigPanelLoading = computed(
    () =>
      loading.boot ||
      loading.production ||
      loading.shots ||
      loading.createStoryboard ||
      loading.deleteStoryboard ||
      loading.createShot ||
      loading.updateShot ||
      loading.deleteShot ||
      loading.clearShots ||
      loading.shotMediaUpload
  );
  const executionPanelLoading = computed(
    () =>
      loading.shotPackage ||
      loading.sceneDirectPackage ||
      loading.createRender ||
      loading.createSceneDirectTask ||
      loading.updateShot ||
      loading.createShotBatch ||
      loading.deleteShotBatch ||
      loading.clearShotBatches ||
      loading.retryShotBatch ||
      loading.submitShotBatch ||
      loading.refreshShotBatch
  );
  const storyboardListLoading = computed(() => loading.production && !filteredStoryboards.value.length);
  const storyboardDetailLoading = computed(
    () =>
      Boolean(state.selectedStoryboardId) &&
      (loading.production ||
        loading.shots ||
        loading.updateStoryboard ||
        loading.deleteStoryboard ||
        loading.createShot ||
        loading.updateShot ||
        loading.deleteShot ||
        loading.clearShots ||
        loading.shotMediaUpload ||
        loading.shotPackage ||
        loading.sceneDirectPackage ||
        loading.createRender ||
        loading.createSceneDirectTask)
  );
  const jobsListLoading = computed(
    () => (loading.production && !state.jobs.length) || loading.deleteJob || loading.clearJobs
  );
  const shotBatchesListLoading = computed(
    () =>
      loading.shotBatches ||
      loading.createShotBatch ||
      loading.deleteShotBatch ||
      loading.clearShotBatches ||
      loading.retryShotBatch ||
      loading.submitShotBatch ||
      loading.refreshShotBatch
  );
  const remoteTasksListLoading = computed(
    () => loading.remoteTasks || loading.remoteTaskDetail || loading.deleteRemoteTask
  );
  const snapshotsListLoading = computed(
    () => (loading.production && !state.snapshots.length) || loading.deleteSnapshot || loading.clearSnapshots
  );
  const jobDetailSectionLoading = computed(
    () =>
      Boolean(state.selectedJobId) &&
      (loading.jobDetail || loading.submitJob || loading.refreshJob)
  );
  const snapshotDetailSectionLoading = computed(
    () => Boolean(state.selectedSnapshotId) && loading.snapshotDetail
  );
  const selectedJobComputed = computed(() => {
    if (state.selectedJob && state.selectedJob.id === state.selectedJobId) {
      return state.selectedJob;
    }
    return state.jobs.find((item) => item.id === state.selectedJobId) || null;
  });
  const selectedRemoteTaskComputed = computed(() => {
    const selectedTask = state.selectedRemoteTask;
    const selectedTaskId = getRemoteTaskId(selectedTask);
    if (selectedTask && selectedTaskId && selectedTaskId === state.selectedRemoteTaskId) {
      return selectedTask;
    }
    return state.remoteTasks.find((item) => getRemoteTaskId(item) === state.selectedRemoteTaskId) || null;
  });
  const selectedShotPromptPackage = computed(() => selectedShot.value?.prompt_package || null);
  const selectedShotPromptVariants = computed(() => {
    const promptPackage = selectedShotPromptPackage.value || {};
    const rawVariants =
      promptPackage.prompt_variants && typeof promptPackage.prompt_variants === "object"
        ? promptPackage.prompt_variants
        : {};
    const fallbackTemplate = String(rawVariants.fallback_template || promptPackage.positive || "").trim();
    const aiRefined = String(rawVariants.ai_refined || "").trim();

    return {
      ai_refined: aiRefined,
      fallback_template: fallbackTemplate
    };
  });
  const selectedShotPromptVariant = computed(() => {
    const promptPackage = selectedShotPromptPackage.value || {};
    const variants = selectedShotPromptVariants.value;
    const selectedVariant = String(promptPackage.selected_prompt_variant || "").trim();

    if (selectedVariant === "ai_refined" && variants.ai_refined) {
      return "ai_refined";
    }
    if (selectedVariant === "fallback_template" && variants.fallback_template) {
      return "fallback_template";
    }
    if (variants.ai_refined && promptPackage.positive === variants.ai_refined) {
      return "ai_refined";
    }
    if (variants.fallback_template && promptPackage.positive === variants.fallback_template) {
      return "fallback_template";
    }
    if (variants.ai_refined) {
      return "ai_refined";
    }
    return "fallback_template";
  });
  const selectedShotPromptPreview = computed(
    () => selectedShotPromptVariants.value[selectedShotPromptVariant.value] || selectedShotPromptPackage.value?.positive || ""
  );
  const parsedScriptObject = computed(() => {
    try {
      return JSON.parse(state.parsedScriptText || "{}");
    } catch {
      return null;
    }
  });
  const parsedScriptReadableOutline = computed(() => parsedScriptObject.value?.readable_outline || null);
  const parsedScriptReadableScenes = computed(() => parsedScriptObject.value?.scenes || []);
  const selectedJobRequestBody = computed(() => normalizeSeedanceRequestBodyForDisplay(selectedJobComputed.value));
  const selectedJobRequestSummary = computed(() => buildSeedanceRequestSummary(selectedJobRequestBody.value));
  const selectedJobHasSubmittedRequest = computed(() => {
    const submittedRequestBody = selectedJobComputed.value?.provider?.submitted_request_body;
    return Boolean(
      submittedRequestBody &&
      typeof submittedRequestBody === "object" &&
      Object.keys(submittedRequestBody).length
    );
  });
  const selectedJobRequestText = computed(() => JSON.stringify(selectedJobRequestBody.value, null, 2));
  const selectedJobResponseText = computed(() =>
    JSON.stringify(selectedJobComputed.value?.remote?.raw_response || {}, null, 2)
  );
  const selectedJobVideoUrl = computed(() => assetUrl(selectedJobComputed.value?.result?.video_path || ""));
  const selectedJobCoverUrl = computed(() => assetUrl(selectedJobComputed.value?.result?.cover_path || ""));
  const selectedRemoteTaskText = computed(() => JSON.stringify(selectedRemoteTaskComputed.value || {}, null, 2));
  const selectedRemoteTaskVideoUrl = computed(() => {
    const content = selectedRemoteTaskComputed.value?.content || {};
    return String(content.video_url || content.url || "").trim();
  });
  const selectedRemoteTaskCoverUrl = computed(() => {
    const content = selectedRemoteTaskComputed.value?.content || {};
    return String(content.last_frame_url || content.cover_url || "").trim();
  });
  const selectedSnapshotImageCount = computed(
    () => state.selectedSnapshot?.resolved_assets?.images?.length || 0
  );
  const selectedCharacterImageEntries = computed(() => {
    const images = selectedCharacter.value?.reference_images || {};
    return [{ key: "sheet", label: "角色圣经拼图", path: images.sheet || "" }];
  });
  const selectedCharacterSourceEntries = computed(() =>
    (selectedCharacter.value?.source_images || []).map((item, index) => ({
      key: `${item.path || "source"}-${index}`,
      label: item.original_name || `参考图 ${index + 1}`,
      path: item.path || ""
    }))
  );
  const hasUploadedCharacterSourceImages = computed(() => selectedCharacterSourceEntries.value.length > 0);
  const selectedCharacterAnchorEntries = computed(() =>
    Object.entries(selectedCharacter.value?.anchors || {}).filter(([key]) =>
      ["face", "hair", "costume", "aura"].includes(key)
    )
  );
  const selectedSceneImageEntries = computed(() => {
    const images = selectedScene.value?.reference_images || {};
    return [{ key: "sheet", label: "场景参考拼图", path: images.sheet || "" }];
  });

  return {
    selectedSeries,
    selectedEpisode,
    selectedCharacter,
    selectedScene,
    filteredStoryboards,
    selectedStoryboard,
    selectedStoryboardProductionMode,
    selectedSceneDirectPackage,
    selectedShot,
    selectedShotBatchComputed,
    seriesListPanelLoading,
    seriesCreatePanelLoading,
    episodesPanelLoading,
    rawScriptPanelLoading,
    parsedScriptPanelLoading,
    characterCreatePanelLoading,
    sceneCreatePanelLoading,
    characterLabPanelLoading,
    sceneLabPanelLoading,
    storyboardConfigPanelLoading,
    executionPanelLoading,
    storyboardListLoading,
    storyboardDetailLoading,
    jobsListLoading,
    shotBatchesListLoading,
    remoteTasksListLoading,
    snapshotsListLoading,
    jobDetailSectionLoading,
    snapshotDetailSectionLoading,
    selectedJobComputed,
    selectedRemoteTaskComputed,
    selectedShotPromptPackage,
    selectedShotPromptVariants,
    selectedShotPromptVariant,
    selectedShotPromptPreview,
    parsedScriptObject,
    parsedScriptReadableOutline,
    parsedScriptReadableScenes,
    selectedJobRequestBody,
    selectedJobRequestSummary,
    selectedJobHasSubmittedRequest,
    selectedJobRequestText,
    selectedJobResponseText,
    selectedJobVideoUrl,
    selectedJobCoverUrl,
    selectedRemoteTaskText,
    selectedRemoteTaskVideoUrl,
    selectedRemoteTaskCoverUrl,
    selectedSnapshotImageCount,
    selectedCharacterImageEntries,
    selectedCharacterSourceEntries,
    hasUploadedCharacterSourceImages,
    selectedCharacterAnchorEntries,
    selectedSceneImageEntries
  };
}
