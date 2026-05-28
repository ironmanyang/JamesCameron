export function useWorkspaceLocalHelpers({
  state,
  assetUrl,
  formatShotAnchorOverridesDisplayWithCharacters,
  getAutoReferenceSummaryWithAssets,
  formatSceneLabelWithScenes
}) {
  function getJobById(jobId) {
    const normalizedJobId = String(jobId || "").trim();
    if (!normalizedJobId) {
      return null;
    }
    if (state.selectedJob?.id === normalizedJobId) {
      return state.selectedJob;
    }
    return state.jobs.find((item) => item.id === normalizedJobId) || null;
  }

  function getRemoteTaskId(task) {
    if (!task || typeof task !== "object") {
      return "";
    }
    return String(task.id || task.task_id || task.job_id || "").trim();
  }

  function getRemoteTaskIdByJob(job) {
    return String(job?.remote?.task_id || "").trim();
  }

  function getLinkedRemoteTaskIds(jobs = state.jobs) {
    return [...new Set((jobs || []).map((item) => getRemoteTaskIdByJob(item)).filter(Boolean))];
  }

  function getRemoteTaskLinkedJob(task) {
    const taskId = getRemoteTaskId(task);
    if (!taskId) {
      return null;
    }
    if (getRemoteTaskIdByJob(state.selectedJob) === taskId) {
      return state.selectedJob;
    }
    return state.jobs.find((item) => getRemoteTaskIdByJob(item) === taskId) || null;
  }

  function getRemoteTaskStatus(task) {
    return String(task?.status || task?.state || "").trim() || "unknown";
  }

  function isShotSelectedForBatch(shotId) {
    return state.selectedShotIds.includes(String(shotId || "").trim());
  }

  function toggleShotSelection(shotId, checked = null) {
    const normalizedShotId = String(shotId || "").trim();
    if (!normalizedShotId) {
      return;
    }

    const hasShot = state.selectedShotIds.includes(normalizedShotId);
    const shouldSelect = typeof checked === "boolean" ? checked : !hasShot;
    if (shouldSelect && !hasShot) {
      state.selectedShotIds = [...state.selectedShotIds, normalizedShotId];
    } else if (!shouldSelect && hasShot) {
      state.selectedShotIds = state.selectedShotIds.filter((item) => item !== normalizedShotId);
    }
  }

  function selectAllShotsForBatch() {
    state.selectedShotIds = state.shots.map((item) => item.id).filter(Boolean);
  }

  function clearShotSelection() {
    state.selectedShotIds = [];
  }

  function getShotBatchSubmittableCount(batch) {
    return (batch?.items || []).filter((item) => ["draft_ready", "failed"].includes(String(item?.status || "").trim())).length;
  }

  function getBatchCompletedItems(batch) {
    return (batch?.items || []).filter((item) => {
      const job = getJobById(item.job_id);
      return Boolean(job?.result?.video_path || job?.result?.cover_path);
    });
  }

  function getBatchJobVideoUrl(jobId) {
    return assetUrl(getJobById(jobId)?.result?.video_path || "");
  }

  function getBatchJobCoverUrl(jobId) {
    return assetUrl(getJobById(jobId)?.result?.cover_path || "");
  }

  function formatShotAnchorOverridesDisplay(anchorStrategy, characterIds = []) {
    return formatShotAnchorOverridesDisplayWithCharacters(anchorStrategy, characterIds, state.characters);
  }

  function getAutoReferenceSummary(characterIds, sceneId) {
    return getAutoReferenceSummaryWithAssets(characterIds, sceneId, state.characters, state.scenes);
  }

  function formatSceneLabel(sceneId) {
    return formatSceneLabelWithScenes(sceneId, state.scenes);
  }

  return {
    getJobById,
    getRemoteTaskId,
    getRemoteTaskIdByJob,
    getLinkedRemoteTaskIds,
    getRemoteTaskLinkedJob,
    getRemoteTaskStatus,
    isShotSelectedForBatch,
    toggleShotSelection,
    selectAllShotsForBatch,
    clearShotSelection,
    getShotBatchSubmittableCount,
    getBatchCompletedItems,
    getBatchJobVideoUrl,
    getBatchJobCoverUrl,
    formatShotAnchorOverridesDisplay,
    getAutoReferenceSummary,
    formatSceneLabel
  };
}
