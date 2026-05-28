<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  shotAnchorModeOptions,
  shotAspectRatioOptions,
  shotGenerationCountOptions,
  shotInputModeOptions,
  shotMovementOptions,
  shotResolutionOptions,
  shotSizeOptions,
  storyboardProductionModeOptions
} from "./constants/options";
import WorkspaceExecutionPanel from "./components/WorkspaceExecutionPanel.vue";
import WorkspaceHero from "./components/WorkspaceHero.vue";
import WorkspaceMainPanel from "./components/WorkspaceMainPanel.vue";
import WorkspaceSidebarLeft from "./components/WorkspaceSidebarLeft.vue";
import WorkspaceStoryboardPanel from "./components/WorkspaceStoryboardPanel.vue";
import { provideWorkspaceContext } from "./components/workspaceContext";
import { useWorkspaceDerived } from "./composables/useWorkspaceDerived";
import { useWorkspaceEditing } from "./composables/useWorkspaceEditing";
import { useWorkspaceLocalHelpers } from "./composables/useWorkspaceLocalHelpers";
import { useParsedScriptEditor } from "./composables/useParsedScriptEditor";
import {
  buildParsedCameraSummary,
  buildParsedShotDescription,
  buildSeedanceRequestSummary,
  buildShotAnchorStrategyPayload,
  buildShotDialoguePayload,
  buildShotMediaPayload,
  buildShotStoryPayload,
  countShotAnchorOverrides,
  firstNonEmptyText,
  formatAnchorKey,
  formatDialogueEntries,
  formatHealth,
  formatJobApiKind,
  getJobSeedanceSummary,
  formatJobOutputSummary,
  formatJobReferenceSummary,
  formatLegacyCameraSummary,
  formatPromptGenerationMode,
  formatPromptVariantLabel,
  formatProviderName,
  formatReadableField,
  formatSeedanceMode,
  formatShotAnchorMode,
  formatShotAspectRatio,
  formatShotBatchCounts,
  formatShotBatchProgress,
  formatShotInputMode,
  formatShotKeyword,
  formatShotMovement,
  formatShotResolution,
  formatShotSize,
  formatSnapshotSource,
  formatStatus,
  formatStoryboardProductionMode,
  getParsedShotDialogueEntries,
  getReadableSceneInfo,
  getReadableShotInfo,
  getShotAnchorOverrideValue,
  inferSeedanceModeFromContent,
  isFirstLastFrameMode,
  isReferenceMode,
  isTextOnlyMode,
  normalizeDialogueEntries,
  normalizeMatchText,
  normalizeSeedanceRequestBodyForDisplay,
  normalizeShotAnchorMode,
  normalizeShotAnchorOverrides,
  normalizeShotDuration,
  normalizeShotGenerationCount,
  normalizeShotInputMode,
  normalizeStoryboardProductionMode,
  parseCharacterText,
  parseDialogueText,
  parseMediaPaths,
  serializeCharacterEntries,
  serializeDialogueEntries,
  serializeMediaPaths,
  setShotAnchorOverrideValue
} from "./utils/formatters";
import {
  appendMediaPaths,
  applyShotModeRules,
  formatSceneLabel as formatSceneLabelWithScenes,
  formatShotAnchorOverridesDisplay as formatShotAnchorOverridesDisplayWithCharacters,
  getAutoReferenceSummary as getAutoReferenceSummaryWithAssets,
  getShotMediaEntries,
  removeShotMediaEntry,
  validateShotSource
} from "./utils/shotHelpers";
import {
  analyzeEpisodeScript,
  assembleShotPackage,
  assembleScenePackage,
  createCharacter,
  createEpisode,
  createScene,
  createSceneDirectSnapshot,
  createShotBatch,
  createSeries,
  createShot,
  createSnapshot,
  createStoryboard,
  createVideoJobFromSnapshot,
  clearShotBatches,
  clearShots,
  deleteCharacter,
  deleteCharacterSourceImage,
  deleteEpisode,
  deleteJob,
  deleteRemoteVideoTask,
  deleteSnapshot,
  deleteScene,
  deleteSeries,
  deleteShot,
  deleteShotBatch,
  deleteStoryboard,
  generateCharacterAssets,
  generateSceneAssets,
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
  listStoryboards,
  refreshJob,
  refreshShotBatch,
  retryFailedShotBatch,
  saveParsedScript,
  saveRawScript,
  submitShotBatch,
  submitJob,
  updateCharacter,
  updateEpisode,
  updateScene,
  updateStoryboard,
  updateShot,
  updateSeries,
  uploadCharacterSourceImages,
  uploadShotMediaImages
} from "./services/api";

const health = ref("checking");
const characterSourceFiles = ref([]);
const characterSourceInput = ref(null);
const parsedScriptViewMode = ref("readable");
const loadingSpinnerViewBox = "0 0 64 64";
const loadingSpinnerSvg = `
  <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="kling-loading-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#dffff2" stop-opacity="0.96" />
        <stop offset="45%" stop-color="#74ff52" stop-opacity="1" />
        <stop offset="100%" stop-color="#26d9ff" stop-opacity="0.94" />
      </linearGradient>
      <filter id="kling-loading-glow">
        <feGaussianBlur stdDeviation="1.8" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
    <g filter="url(#kling-loading-glow)">
      <circle cx="32" cy="32" r="18" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="5" />
      <path
        d="M32 14
           a18 18 0 0 1 0 36
           a18 18 0 0 1 0 -36"
        fill="none"
        stroke="url(#kling-loading-gradient)"
        stroke-linecap="round"
        stroke-width="5.5"
        stroke-dasharray="72 42"
      >
        <animateTransform
          attributeName="transform"
          type="rotate"
          from="0 32 32"
          to="360 32 32"
          dur="0.9s"
          repeatCount="indefinite"
        />
      </path>
      <circle cx="32" cy="32" r="4.8" fill="#dffff2" fill-opacity="0.92">
        <animate attributeName="r" values="4.2;5.2;4.2" dur="1.1s" repeatCount="indefinite" />
      </circle>
    </g>
  </svg>
`;
let episodeScriptsRequestSeed = 0;
let productionRequestSeed = 0;
let shotsRequestSeed = 0;
let characterBibleRequestSeed = 0;
let scenePackageRequestSeed = 0;
let jobDetailRequestSeed = 0;
let snapshotDetailRequestSeed = 0;
let shotBatchRequestSeed = 0;
let shotBatchDetailRequestSeed = 0;
let remoteTaskRequestSeed = 0;
let remoteTaskDetailRequestSeed = 0;

const loading = reactive({
  boot: true,
  series: false,
  episodes: false,
  scripts: false,
  production: false,
  shots: false,
  analyzeScript: false,
  saveRaw: false,
  saveParsed: false,
  createSeries: false,
  updateSeries: false,
  deleteSeries: false,
  createEpisode: false,
  updateEpisode: false,
  deleteEpisode: false,
  createCharacter: false,
  updateCharacter: false,
  deleteCharacter: false,
  createScene: false,
  updateScene: false,
  deleteScene: false,
  createStoryboard: false,
  updateStoryboard: false,
  createShot: false,
  updateShot: false,
  deleteShot: false,
  deleteStoryboard: false,
  createRender: false,
  characterAssets: false,
  characterUpload: false,
  shotMediaUpload: false,
  deleteCharacterSourceImage: false,
  characterBible: false,
  sceneAssets: false,
  scenePackage: false,
  shotPackage: false,
  sceneDirectPackage: false,
  importParsedShot: false,
  jobDetail: false,
  snapshotDetail: false,
  shotBatches: false,
  remoteTasks: false,
  remoteTaskDetail: false,
  deleteJob: false,
  deleteRemoteTask: false,
  deleteSnapshot: false,
  clearJobs: false,
  clearSnapshots: false,
  createSceneDirectTask: false,
  createShotBatch: false,
  deleteShotBatch: false,
  clearShotBatches: false,
  clearShots: false,
  retryShotBatch: false,
  submitShotBatch: false,
  refreshShotBatch: false,
  submitJob: false,
  refreshJob: false
});

const forms = reactive({
  seriesName: "",
  seriesDescription: "",
  episodeName: "",
  characterName: "",
  characterBrief: "",
  sceneName: "",
  sceneDescription: "",
  shotSceneId: "",
  shotInputMode: "reference_image",
  shotGenerateAudio: true,
  shotAspectRatio: "16:9",
  shotResolution: "1080p",
  shotGenerationCount: 1,
  shotFirstFramePath: "",
  shotLastFramePath: "",
  shotReferenceImagesText: "",
  shotSize: "medium",
  shotMovement: "static",
  shotDuration: 5,
  shotPalette: "",
  shotLighting: "",
  shotStoryDescription: "",
  shotStoryEmotion: "",
  shotStoryBeat: "",
  shotStoryDialogue: "",
  shotStoryRawExcerpt: "",
  shotAnchorMode: "auto",
  shotAnchorOverrides: {}
});

const inlineEditing = reactive({
  seriesSlug: "",
  seriesName: "",
  seriesDescription: "",
  episodeId: "",
  episodeName: "",
  characterId: "",
  characterName: "",
  characterBrief: "",
  sceneId: "",
  sceneName: "",
  sceneDescription: "",
  shotId: "",
  shotSceneId: "",
  shotInputMode: "reference_image",
  shotGenerateAudio: true,
  shotAspectRatio: "16:9",
  shotResolution: "1080p",
  shotGenerationCount: 1,
  shotFirstFramePath: "",
  shotLastFramePath: "",
  shotReferenceImagesText: "",
  shotSize: "medium",
  shotMovement: "static",
  shotDuration: 5,
  shotLighting: "",
  shotPalette: "",
  shotCharacterIds: [],
  shotStoryDescription: "",
  shotStoryEmotion: "",
  shotStoryBeat: "",
  shotStoryDialogue: "",
  shotStoryRawExcerpt: "",
  shotAnchorMode: "auto",
  shotAnchorOverrides: {}
});

const parsedShotEditing = reactive({
  sceneIndex: -1,
  shotIndex: -1,
  description: "",
  cameraAngle: "",
  cameraMovement: "",
  cameraShotSize: "",
  charactersText: "",
  dialoguesText: "",
  emotion: "",
  beat: ""
});

const parsedSceneEditing = reactive({
  sceneIndex: -1,
  location: "",
  time: "",
  summary: ""
});

const state = reactive({
  notice: "",
  error: "",
  series: [],
  episodes: [],
  characters: [],
  scenes: [],
  storyboards: [],
  shots: [],
  shotBatches: [],
  snapshots: [],
  jobs: [],
  remoteTasks: [],
  selectedSeriesSlug: "",
  selectedEpisodeId: "",
  selectedStoryboardId: "",
  selectedShotId: "",
  selectedShotIds: [],
  selectedShotBatchId: "",
  selectedCharacterId: "",
  selectedSceneId: "",
  selectedJobId: "",
  selectedSnapshotId: "",
  selectedRemoteTaskId: "",
  selectedCharacterIds: [],
  rawScript: "",
  parsedScriptText: "",
  selectedCharacterBible: null,
  selectedScenePackage: null,
  selectedShotBatch: null,
  selectedJob: null,
  selectedSnapshot: null,
  selectedRemoteTask: null,
  assets: {
    characters: 0,
    scenes: 0,
    storyboards: 0,
    snapshots: 0,
    jobs: 0
  }
});

function defaultParsedScript(title = "") {
  return {
    title,
    acts: [],
    scenes: [],
    extracted_entities: {
      characters: [],
      scenes: [],
      props: []
    }
  };
}

const workspaceLocalHelpers = useWorkspaceLocalHelpers({
  state,
  assetUrl,
  formatShotAnchorOverridesDisplayWithCharacters,
  getAutoReferenceSummaryWithAssets,
  formatSceneLabelWithScenes
});

const {
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
} = workspaceLocalHelpers;

const workspaceDerived = useWorkspaceDerived({
  state,
  loading,
  assetUrl,
  getJobById,
  getRemoteTaskId
});

const {
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
} = workspaceDerived;

function setNotice(message) {
  state.notice = message;
  state.error = "";
  if (message) {
    ElMessage({
      type: "success",
      message,
      grouping: true,
      duration: 2200
    });
  }
}

function setError(error) {
  const message = error instanceof Error ? error.message : String(error);
  state.error = message;
  if (message) {
    ElMessage({
      type: "error",
      message,
      grouping: true,
      showClose: true,
      duration: 3800
    });
  }
}

function assetUrl(relativePath) {
  if (!relativePath || !state.selectedSeriesSlug) {
    return "";
  }
  return `/output/${state.selectedSeriesSlug}/${relativePath}`;
}

function singlePreviewList(relativePath) {
  const url = assetUrl(relativePath);
  return url ? [url] : [];
}

async function confirmDanger(message, title = "确认操作") {
  try {
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      type: "warning"
    });
    return true;
  } catch {
    return false;
  }
}

const workspaceEditing = useWorkspaceEditing({
  state,
  inlineEditing,
  normalizeShotInputMode,
  serializeMediaPaths,
  serializeDialogueEntries,
  normalizeShotAnchorMode,
  normalizeShotAnchorOverrides
});

const {
  isEditingSeries,
  isEditingEpisode,
  isEditingCharacter,
  isEditingScene,
  isEditingShot,
  startSeriesEdit,
  cancelSeriesEdit,
  startEpisodeEdit,
  cancelEpisodeEdit,
  startCharacterEdit,
  cancelCharacterEdit,
  startSceneEdit,
  cancelSceneEdit,
  startShotEdit,
  cancelShotEdit,
  syncAssetCounts
} = workspaceEditing;

function getSceneDirectSceneId() {
  const formSceneId = String(forms.shotSceneId || "").trim();
  if (formSceneId) {
    return formSceneId;
  }

  const selectedSceneId = String(state.selectedSceneId || "").trim();
  if (selectedSceneId) {
    return selectedSceneId;
  }

  return String(state.scenes[0]?.id || "").trim();
}

function buildSceneDirectPayload() {
  const sceneId = getSceneDirectSceneId();
  const visual = {
    aspect_ratio: forms.shotAspectRatio,
    style: "cinematic realism",
    resolution: forms.shotResolution,
    generation_count: normalizeShotGenerationCount(forms.shotGenerationCount),
    shot_size: forms.shotSize,
    camera_angle: "eye_level",
    camera_movement: forms.shotMovement,
    lens: "50mm",
    depth_of_field: "medium",
    lighting: String(forms.shotLighting || "").trim(),
    palette: String(forms.shotPalette || "").trim(),
    duration_seconds: normalizeShotDuration(forms.shotDuration)
  };

  return {
    episode_id: String(selectedEpisode.value?.id || state.selectedEpisodeId || "").trim(),
    scene_id: sceneId,
    characters: [...state.selectedCharacterIds],
    media: buildShotMediaPayload(forms),
    visual
  };
}

async function handleShotMediaUpload(source, target, event) {
  const files = event?.target?.files ? Array.from(event.target.files) : [];
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择分镜板");
    if (event?.target) {
      event.target.value = "";
    }
    return;
  }
  if (!files.length) {
    return;
  }

  loading.shotMediaUpload = true;
  try {
    const shotId = source === inlineEditing ? inlineEditing.shotId || "" : "";
    const payload = await uploadShotMediaImages(
      state.selectedSeriesSlug,
      state.selectedStoryboardId,
      target,
      files,
      shotId
    );
    const uploadedPaths = (payload.items || []).map((item) => String(item.path || "").trim()).filter(Boolean);
    if (!uploadedPaths.length) {
      throw new Error("上传后未返回有效图片路径");
    }

    if (target === "first_frame") {
      source.shotFirstFramePath = uploadedPaths[0];
    } else if (target === "last_frame") {
      source.shotLastFramePath = uploadedPaths[0];
    } else if (target === "reference_images") {
      source.shotReferenceImagesText = appendMediaPaths(source.shotReferenceImagesText, uploadedPaths);
    }

    setNotice("镜头图片已上传");
  } catch (error) {
    setError(error);
  } finally {
    loading.shotMediaUpload = false;
    if (event?.target) {
      event.target.value = "";
    }
  }
}
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

async function loadProductionData(seriesSlug) {
  const requestId = ++productionRequestSeed;
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

    if (requestId !== productionRequestSeed || seriesSlug !== state.selectedSeriesSlug) {
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
    if (requestId !== productionRequestSeed || seriesSlug !== state.selectedSeriesSlug) {
      return;
    }
    setError(error);
  } finally {
    if (requestId === productionRequestSeed) {
      loading.production = false;
    }
  }
}

async function loadShotsForStoryboard(seriesSlug, storyboardId, preferredShotId = "") {
  const requestId = ++shotsRequestSeed;
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
      requestId !== shotsRequestSeed ||
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
      requestId !== shotsRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      storyboardId !== state.selectedStoryboardId
    ) {
      return;
    }
    setError(error);
  } finally {
    if (requestId === shotsRequestSeed) {
      loading.shots = false;
    }
  }
}

const parsedScriptEditor = useParsedScriptEditor({
  state,
  forms,
  loading,
  parsedShotEditing,
  parsedSceneEditing,
  parsedScriptObject,
  selectedStoryboard,
  createShot,
  loadProductionData,
  loadShotsForStoryboard,
  setNotice,
  setError
});

const {
  isEditingParsedShot,
  isEditingParsedScene,
  startParsedSceneEdit,
  cancelParsedSceneEdit,
  saveParsedSceneEdit,
  startParsedShotEdit,
  cancelParsedShotEdit,
  saveParsedShotEdit,
  buildParsedShotStoryPayload,
  handleCopyReadableShot,
  getShotStoryValue,
  getShotStoryDisplay,
  resolveParsedSceneId,
  resolveParsedCharacterIds,
  mapParsedShotSize,
  mapParsedShotMovement,
  mapParsedCameraAngle,
  buildImportedShotMedia,
  handleImportReadableShot,
  handleImportAllReadableShots
} = parsedScriptEditor;

async function loadShotBatchesForStoryboard(seriesSlug, storyboardId, preferredBatchId = "") {
  const requestId = ++shotBatchRequestSeed;
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
      requestId !== shotBatchRequestSeed ||
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
      requestId !== shotBatchRequestSeed ||
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
    if (requestId === shotBatchRequestSeed) {
      loading.shotBatches = false;
    }
  }
}

async function loadEpisodeScripts(seriesSlug, episodeId) {
  const requestId = ++episodeScriptsRequestSeed;
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
      requestId !== episodeScriptsRequestSeed ||
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
      requestId !== episodeScriptsRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      episodeId !== state.selectedEpisodeId
    ) {
      return;
    }
    setError(error);
  } finally {
    if (requestId === episodeScriptsRequestSeed) {
      loading.scripts = false;
    }
  }
}

async function loadCharacterBible(seriesSlug, characterId) {
  const requestId = ++characterBibleRequestSeed;
  if (!seriesSlug || !characterId) {
    state.selectedCharacterBible = null;
    return;
  }

  loading.characterBible = true;
  state.selectedCharacterBible = null;
  try {
    const response = await getCharacterBible(seriesSlug, characterId);
    if (
      requestId !== characterBibleRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      characterId !== state.selectedCharacterId
    ) {
      return;
    }
    state.selectedCharacterBible = response.item || null;
  } catch (error) {
    if (
      requestId !== characterBibleRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      characterId !== state.selectedCharacterId
    ) {
      return;
    }
    state.selectedCharacterBible = null;
    setError(error);
  } finally {
    if (requestId === characterBibleRequestSeed) {
      loading.characterBible = false;
    }
  }
}

async function loadScenePackage(seriesSlug, sceneId) {
  const requestId = ++scenePackageRequestSeed;
  if (!seriesSlug || !sceneId) {
    state.selectedScenePackage = null;
    return;
  }

  loading.scenePackage = true;
  state.selectedScenePackage = null;
  try {
    const response = await getScenePromptPackage(seriesSlug, sceneId);
    if (
      requestId !== scenePackageRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      sceneId !== state.selectedSceneId
    ) {
      return;
    }
    state.selectedScenePackage = response.item || null;
  } catch (error) {
    if (
      requestId !== scenePackageRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      sceneId !== state.selectedSceneId
    ) {
      return;
    }
    state.selectedScenePackage = null;
    setError(error);
  } finally {
    if (requestId === scenePackageRequestSeed) {
      loading.scenePackage = false;
    }
  }
}

async function loadJobDetail(seriesSlug, jobId) {
  const requestId = ++jobDetailRequestSeed;
  if (!seriesSlug || !jobId) {
    state.selectedJob = null;
    return;
  }

  loading.jobDetail = true;
  state.selectedJob = null;
  try {
    const response = await getJob(seriesSlug, jobId);
    if (
      requestId !== jobDetailRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      jobId !== state.selectedJobId
    ) {
      return;
    }
    state.selectedJob = response.item || null;
  } catch (error) {
    if (
      requestId !== jobDetailRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      jobId !== state.selectedJobId
    ) {
      return;
    }
    state.selectedJob = null;
    setError(error);
  } finally {
    if (requestId === jobDetailRequestSeed) {
      loading.jobDetail = false;
    }
  }
}

async function loadSnapshotDetail(seriesSlug, snapshotId) {
  const requestId = ++snapshotDetailRequestSeed;
  if (!seriesSlug || !snapshotId) {
    state.selectedSnapshotId = "";
    state.selectedSnapshot = null;
    return;
  }

  loading.snapshotDetail = true;
  state.selectedSnapshot = null;
  try {
    const response = await getSnapshot(seriesSlug, snapshotId);
    if (requestId !== snapshotDetailRequestSeed || seriesSlug !== state.selectedSeriesSlug) {
      return;
    }
    state.selectedSnapshot = response.item || null;
  } catch (error) {
    if (requestId !== snapshotDetailRequestSeed || seriesSlug !== state.selectedSeriesSlug) {
      return;
    }
    state.selectedSnapshot = null;
    setError(error);
  } finally {
    if (requestId === snapshotDetailRequestSeed) {
      loading.snapshotDetail = false;
    }
  }
}

async function loadShotBatchDetail(seriesSlug, storyboardId, batchId) {
  const requestId = ++shotBatchDetailRequestSeed;
  if (!seriesSlug || !storyboardId || !batchId) {
    state.selectedShotBatch = null;
    return;
  }

  loading.shotBatches = true;
  state.selectedShotBatch = null;
  try {
    const response = await getShotBatch(seriesSlug, storyboardId, batchId);
    if (
      requestId !== shotBatchDetailRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      storyboardId !== state.selectedStoryboardId ||
      batchId !== state.selectedShotBatchId
    ) {
      return;
    }
    state.selectedShotBatch = response.item || null;
  } catch (error) {
    if (
      requestId !== shotBatchDetailRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      storyboardId !== state.selectedStoryboardId ||
      batchId !== state.selectedShotBatchId
    ) {
      return;
    }
    state.selectedShotBatch = null;
    setError(error);
  } finally {
    if (requestId === shotBatchDetailRequestSeed) {
      loading.shotBatches = false;
    }
  }
}

async function loadRemoteTasks(seriesSlug, preferredTaskId = "") {
  const requestId = ++remoteTaskRequestSeed;
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
    if (requestId !== remoteTaskRequestSeed || seriesSlug !== state.selectedSeriesSlug) {
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
    if (requestId !== remoteTaskRequestSeed || seriesSlug !== state.selectedSeriesSlug) {
      return;
    }
    state.remoteTasks = [];
    state.selectedRemoteTaskId = "";
    state.selectedRemoteTask = null;
    setError(error);
  } finally {
    if (requestId === remoteTaskRequestSeed) {
      loading.remoteTasks = false;
    }
  }
}

async function loadRemoteTaskDetail(seriesSlug, taskId) {
  const requestId = ++remoteTaskDetailRequestSeed;
  if (!seriesSlug || !taskId) {
    state.selectedRemoteTask = null;
    return;
  }

  loading.remoteTaskDetail = true;
  state.selectedRemoteTask = null;
  try {
    const response = await getRemoteVideoTask(seriesSlug, taskId);
    if (
      requestId !== remoteTaskDetailRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      taskId !== state.selectedRemoteTaskId
    ) {
      return;
    }
    state.selectedRemoteTask = response || null;
  } catch (error) {
    if (
      requestId !== remoteTaskDetailRequestSeed ||
      seriesSlug !== state.selectedSeriesSlug ||
      taskId !== state.selectedRemoteTaskId
    ) {
      return;
    }
    state.selectedRemoteTask = null;
    setError(error);
  } finally {
    if (requestId === remoteTaskDetailRequestSeed) {
      loading.remoteTaskDetail = false;
    }
  }
}

async function boot() {
  await loadHealth();
  await loadSeries();
  loading.boot = false;
}

async function handleCreateSeries() {
  if (!forms.seriesName.trim()) {
    setError("请输入系列名称");
    return;
  }

  loading.createSeries = true;
  try {
    const response = await createSeries({
      name: forms.seriesName.trim(),
      description: forms.seriesDescription.trim()
    });
    forms.seriesName = "";
    forms.seriesDescription = "";
    await loadSeries();
    state.selectedSeriesSlug = response.item.slug;
    setNotice(`已创建系列：${response.item.name}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createSeries = false;
  }
}

async function handleUpdateSeries(item = selectedSeries.value) {
  const targetSlug = item?.slug || state.selectedSeriesSlug;
  const name = (isEditingSeries(targetSlug) ? inlineEditing.seriesName : forms.seriesName).trim();
  const description = isEditingSeries(targetSlug) ? inlineEditing.seriesDescription.trim() : forms.seriesDescription.trim();

  if (!targetSlug) {
    setError("请先选择一个系列");
    return;
  }
  if (!name) {
    setError("请输入系列名称");
    return;
  }

  loading.updateSeries = true;
  try {
    await updateSeries(targetSlug, {
      name,
      description
    });
    await loadSeries();
    state.selectedSeriesSlug = targetSlug;
    if (isEditingSeries(targetSlug)) {
      cancelSeriesEdit();
    }
    setNotice("系列信息已更新");
  } catch (error) {
    setError(error);
  } finally {
    loading.updateSeries = false;
  }
}

async function handleDeleteSeries(item = selectedSeries.value) {
  const targetSeries = item || selectedSeries.value;
  const targetSlug = targetSeries?.slug || "";

  if (!targetSlug || !targetSeries) {
    setError("请先选择一个系列");
    return;
  }
  const confirmed = await confirmDanger(`确定删除系列“${targetSeries.name}”吗？这会删除该系列下的全部本地数据。`, "删除系列");
  if (!confirmed) {
    return;
  }

  loading.deleteSeries = true;
  try {
    await deleteSeries(targetSlug);
    if (state.selectedSeriesSlug === targetSlug) {
      state.selectedSeriesSlug = "";
    }
    if (isEditingSeries(targetSlug)) {
      cancelSeriesEdit();
    }
    await loadSeries();
    setNotice("系列已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteSeries = false;
  }
}

async function handleCreateEpisode() {
  if (!state.selectedSeriesSlug) {
    setError("请先选择一个系列");
    return;
  }

  loading.createEpisode = true;
  try {
    const response = await createEpisode({
      series_slug: state.selectedSeriesSlug,
      name: forms.episodeName.trim()
    });
    forms.episodeName = "";
    await loadEpisodes(state.selectedSeriesSlug);
    state.selectedEpisodeId = response.item.id;
    setNotice(`已创建剧集：${response.item.name}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createEpisode = false;
  }
}

async function handleUpdateEpisode(item = selectedEpisode.value) {
  const targetEpisodeId = item?.id || state.selectedEpisodeId;
  const name = (isEditingEpisode(targetEpisodeId) ? inlineEditing.episodeName : forms.episodeName).trim();

  if (!state.selectedSeriesSlug || !targetEpisodeId) {
    setError("请先选择一个剧集");
    return;
  }
  if (!name) {
    setError("请输入剧集名称");
    return;
  }

  loading.updateEpisode = true;
  try {
    await updateEpisode(state.selectedSeriesSlug, targetEpisodeId, {
      name
    });
    await loadEpisodes(state.selectedSeriesSlug);
    state.selectedEpisodeId = targetEpisodeId;
    if (isEditingEpisode(targetEpisodeId)) {
      cancelEpisodeEdit();
    }
    setNotice("剧集信息已更新");
  } catch (error) {
    setError(error);
  } finally {
    loading.updateEpisode = false;
  }
}

async function handleDeleteEpisode(item = selectedEpisode.value) {
  const targetEpisode = item || selectedEpisode.value;
  const targetEpisodeId = targetEpisode?.id || "";

  if (!state.selectedSeriesSlug || !targetEpisodeId || !targetEpisode) {
    setError("请先选择一个剧集");
    return;
  }
  const confirmed = await confirmDanger(`确定删除剧集“${targetEpisode.name}”吗？`, "删除剧集");
  if (!confirmed) {
    return;
  }

  loading.deleteEpisode = true;
  try {
    await deleteEpisode(state.selectedSeriesSlug, targetEpisodeId);
    if (state.selectedEpisodeId === targetEpisodeId) {
      state.selectedEpisodeId = "";
    }
    if (isEditingEpisode(targetEpisodeId)) {
      cancelEpisodeEdit();
    }
    await loadEpisodes(state.selectedSeriesSlug);
    setNotice("剧集已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteEpisode = false;
  }
}

async function handleSaveRawScript() {
  if (!state.selectedSeriesSlug || !state.selectedEpisodeId) {
    setError("请先选择一个剧集");
    return;
  }

  loading.saveRaw = true;
  try {
    await saveRawScript(state.selectedSeriesSlug, state.selectedEpisodeId, state.rawScript);
    setNotice("剧本原文已保存");
  } catch (error) {
    setError(error);
  } finally {
    loading.saveRaw = false;
  }
}

async function handleSaveParsedScript() {
  if (!state.selectedSeriesSlug || !state.selectedEpisodeId) {
    setError("请先选择一个剧集");
    return;
  }

  loading.saveParsed = true;
  try {
    const parsed = JSON.parse(state.parsedScriptText);
    await saveParsedScript(state.selectedSeriesSlug, state.selectedEpisodeId, parsed);
    setNotice("结构化 JSON 已保存");
  } catch (error) {
    setError(error);
  } finally {
    loading.saveParsed = false;
  }
}

async function handleAnalyzeScript() {
  if (!state.selectedSeriesSlug || !state.selectedEpisodeId) {
    setError("请先选择一个剧集");
    return;
  }

  loading.analyzeScript = true;
  try {
    const response = await analyzeEpisodeScript(state.selectedSeriesSlug, state.selectedEpisodeId);
    state.parsedScriptText = JSON.stringify(response.parsed_script, null, 2);
    setNotice("剧本拆解完成");
  } catch (error) {
    setError(error);
  } finally {
    loading.analyzeScript = false;
  }
}

async function handleCreateCharacter() {
  if (!state.selectedSeriesSlug) {
    setError("请先选择一个系列");
    return;
  }
  if (!forms.characterName.trim()) {
    setError("请输入角色名称");
    return;
  }

  loading.createCharacter = true;
  try {
    const response = await createCharacter({
      series_slug: state.selectedSeriesSlug,
      name: forms.characterName.trim(),
      brief: forms.characterBrief.trim()
    });
    forms.characterName = "";
    forms.characterBrief = "";
    await loadProductionData(state.selectedSeriesSlug);
    state.selectedCharacterId = response.item.id;
    setNotice(`已创建角色：${response.item.name}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createCharacter = false;
  }
}

async function handleUpdateCharacter(item = selectedCharacter.value) {
  const targetCharacterId = item?.id || state.selectedCharacterId;
  const name = (isEditingCharacter(targetCharacterId) ? inlineEditing.characterName : forms.characterName).trim();
  const brief = isEditingCharacter(targetCharacterId) ? inlineEditing.characterBrief.trim() : forms.characterBrief.trim();

  if (!state.selectedSeriesSlug || !targetCharacterId) {
    setError("请先选择一个角色");
    return;
  }
  if (!name) {
    setError("请输入角色名称");
    return;
  }

  loading.updateCharacter = true;
  try {
    await updateCharacter(state.selectedSeriesSlug, targetCharacterId, {
      name,
      brief
    });
    await loadProductionData(state.selectedSeriesSlug);
    state.selectedCharacterId = targetCharacterId;
    if (isEditingCharacter(targetCharacterId)) {
      cancelCharacterEdit();
    }
    setNotice("角色信息已更新");
  } catch (error) {
    setError(error);
  } finally {
    loading.updateCharacter = false;
  }
}

async function handleDeleteCharacter(item = selectedCharacter.value) {
  const targetCharacter = item || selectedCharacter.value;
  const targetCharacterId = targetCharacter?.id || "";

  if (!state.selectedSeriesSlug || !targetCharacterId || !targetCharacter) {
    setError("请先选择一个角色");
    return;
  }
  const confirmed = await confirmDanger(`确定删除角色“${targetCharacter.name}”吗？`, "删除角色");
  if (!confirmed) {
    return;
  }

  loading.deleteCharacter = true;
  try {
    await deleteCharacter(state.selectedSeriesSlug, targetCharacterId);
    if (state.selectedCharacterId === targetCharacterId) {
      state.selectedCharacterId = "";
    }
    if (isEditingCharacter(targetCharacterId)) {
      cancelCharacterEdit();
    }
    await loadProductionData(state.selectedSeriesSlug);
    setNotice("角色已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteCharacter = false;
  }
}

function handleCharacterSourceFileChange(event) {
  const files = event?.target?.files;
  characterSourceFiles.value = files ? Array.from(files) : [];
}

async function handleUploadCharacterSourceImages() {
  if (!state.selectedSeriesSlug || !state.selectedCharacterId) {
    setError("请先选择一个角色");
    return;
  }
  if (!characterSourceFiles.value.length) {
    setError("请先选择要上传的角色参考图");
    return;
  }

  loading.characterUpload = true;
  try {
    await uploadCharacterSourceImages(
      state.selectedSeriesSlug,
      state.selectedCharacterId,
      characterSourceFiles.value
    );
    characterSourceFiles.value = [];
    if (characterSourceInput.value) {
      characterSourceInput.value.value = "";
    }
    await loadProductionData(state.selectedSeriesSlug);
    await loadCharacterBible(state.selectedSeriesSlug, state.selectedCharacterId);
    setNotice("角色参考图已上传，后续生成会优先参考上传图片");
  } catch (error) {
    setError(error);
  } finally {
    loading.characterUpload = false;
  }
}

async function handleDeleteCharacterSourceImage(imagePath) {
  if (!state.selectedSeriesSlug || !state.selectedCharacterId || !imagePath) {
    setError("请先选择角色参考图");
    return;
  }
  const confirmed = await confirmDanger("确定删除这张角色参考图吗？", "删除参考图");
  if (!confirmed) {
    return;
  }

  loading.deleteCharacterSourceImage = true;
  try {
    await deleteCharacterSourceImage(state.selectedSeriesSlug, state.selectedCharacterId, imagePath);
    await loadProductionData(state.selectedSeriesSlug);
    await loadCharacterBible(state.selectedSeriesSlug, state.selectedCharacterId);
    setNotice("角色参考图已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteCharacterSourceImage = false;
  }
}

async function handleGenerateCharacterAssets(generationMode = "reference_plus_text") {
  if (!state.selectedSeriesSlug || !state.selectedCharacterId) {
    setError("请先选择一个角色");
    return;
  }
  if (generationMode === "reference_subject_only" && !hasUploadedCharacterSourceImages.value) {
    setError("请先上传至少一张角色参考图，再使用“仅按参考图生成”");
    return;
  }

  loading.characterAssets = true;
  try {
    await generateCharacterAssets(
      state.selectedSeriesSlug,
      state.selectedCharacterId,
      state.selectedEpisodeId ? [state.selectedEpisodeId] : [],
      generationMode
    );
    await loadProductionData(state.selectedSeriesSlug);
    await loadCharacterBible(state.selectedSeriesSlug, state.selectedCharacterId);
    setNotice(
      generationMode === "reference_subject_only"
        ? "已按上传参考图主体生成三视图与特征分解拼图"
        : "已按文字设定与参考图联合生成角色圣经拼图"
    );
  } catch (error) {
    setError(error);
  } finally {
    loading.characterAssets = false;
  }
}

async function handleCreateScene() {
  if (!state.selectedSeriesSlug) {
    setError("请先选择一个系列");
    return;
  }
  if (!forms.sceneName.trim()) {
    setError("请输入场景名称");
    return;
  }

  loading.createScene = true;
  try {
    const response = await createScene({
      series_slug: state.selectedSeriesSlug,
      name: forms.sceneName.trim(),
      description: forms.sceneDescription.trim(),
      episode_id: state.selectedEpisodeId
    });
    forms.sceneName = "";
    forms.sceneDescription = "";
    await loadProductionData(state.selectedSeriesSlug);
    state.selectedSceneId = response.item.id;
    setNotice(`已创建场景：${response.item.name}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createScene = false;
  }
}

async function handleUpdateScene(item = selectedScene.value) {
  const targetSceneId = item?.id || state.selectedSceneId;
  const name = (isEditingScene(targetSceneId) ? inlineEditing.sceneName : forms.sceneName).trim();
  const description = isEditingScene(targetSceneId) ? inlineEditing.sceneDescription.trim() : forms.sceneDescription.trim();
  const episodeId = item?.episode_id ?? selectedScene.value?.episode_id ?? state.selectedEpisodeId ?? "";

  if (!state.selectedSeriesSlug || !targetSceneId) {
    setError("请先选择一个场景");
    return;
  }
  if (!name) {
    setError("请输入场景名称");
    return;
  }

  loading.updateScene = true;
  try {
    await updateScene(state.selectedSeriesSlug, targetSceneId, {
      name,
      description,
      episode_id: episodeId
    });
    await loadProductionData(state.selectedSeriesSlug);
    state.selectedSceneId = targetSceneId;
    if (isEditingScene(targetSceneId)) {
      cancelSceneEdit();
    }
    setNotice("场景信息已更新");
  } catch (error) {
    setError(error);
  } finally {
    loading.updateScene = false;
  }
}

async function handleDeleteScene(item = selectedScene.value) {
  const targetScene = item || selectedScene.value;
  const targetSceneId = targetScene?.id || "";

  if (!state.selectedSeriesSlug || !targetSceneId || !targetScene) {
    setError("请先选择一个场景");
    return;
  }
  const confirmed = await confirmDanger(`确定删除场景“${targetScene.name}”吗？`, "删除场景");
  if (!confirmed) {
    return;
  }

  loading.deleteScene = true;
  try {
    await deleteScene(state.selectedSeriesSlug, targetSceneId);
    if (state.selectedSceneId === targetSceneId) {
      state.selectedSceneId = "";
    }
    if (isEditingScene(targetSceneId)) {
      cancelSceneEdit();
    }
    await loadProductionData(state.selectedSeriesSlug);
    setNotice("场景已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteScene = false;
  }
}

async function handleGenerateSceneAssets() {
  if (!state.selectedSeriesSlug || !state.selectedSceneId) {
    setError("请先选择一个场景");
    return;
  }

  loading.sceneAssets = true;
  try {
    await generateSceneAssets(
      state.selectedSeriesSlug,
      state.selectedSceneId,
      state.selectedEpisodeId ? [state.selectedEpisodeId] : []
    );
    await loadProductionData(state.selectedSeriesSlug);
    await loadScenePackage(state.selectedSeriesSlug, state.selectedSceneId);
    setNotice("场景包与单张场景参考拼图已生成");
  } catch (error) {
    setError(error);
  } finally {
    loading.sceneAssets = false;
  }
}

async function handleCreateStoryboard() {
  if (!state.selectedSeriesSlug || !state.selectedEpisodeId) {
    setError("请先选择系列和剧集");
    return;
  }

  loading.createStoryboard = true;
  try {
    const response = await createStoryboard({
      series_slug: state.selectedSeriesSlug,
      episode_id: state.selectedEpisodeId,
      production_mode: "shot_pipeline"
    });
    await loadProductionData(state.selectedSeriesSlug);
    state.selectedStoryboardId = response.item.id;
    setNotice(`已创建分镜板：${response.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createStoryboard = false;
  }
}

async function handleChangeStoryboardProductionMode(mode) {
  if (!state.selectedSeriesSlug || !selectedStoryboard.value) {
    setError("请先选择一个分镜板");
    return;
  }

  const normalizedMode = normalizeStoryboardProductionMode(mode);
  if (normalizedMode === normalizeStoryboardProductionMode(selectedStoryboard.value.production_mode)) {
    return;
  }

  loading.updateStoryboard = true;
  try {
    await updateStoryboard(state.selectedSeriesSlug, selectedStoryboard.value.id, {
      production_mode: normalizedMode
    });
    await loadProductionData(state.selectedSeriesSlug);
    if (normalizedMode === "scene_direct") {
      state.selectedShotId = "";
      cancelShotEdit();
    }
    setNotice(`分镜板已切换为${formatStoryboardProductionMode(normalizedMode)}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.updateStoryboard = false;
  }
}

async function handleDeleteStoryboard(item = selectedStoryboard.value) {
  const targetStoryboard = item || selectedStoryboard.value;
  const targetStoryboardId = targetStoryboard?.id || "";

  if (!state.selectedSeriesSlug || !targetStoryboardId || !targetStoryboard) {
    setError("请先选择一个分镜板");
    return;
  }
  const confirmed = await confirmDanger(`确定删除分镜板“${targetStoryboardId}”吗？`, "删除分镜板");
  if (!confirmed) {
    return;
  }

  loading.deleteStoryboard = true;
  try {
    await deleteStoryboard(state.selectedSeriesSlug, targetStoryboardId);
    if (state.selectedStoryboardId === targetStoryboardId) {
      state.selectedStoryboardId = "";
      state.selectedShotId = "";
      cancelShotEdit();
    }
    await loadProductionData(state.selectedSeriesSlug);
    setNotice("分镜板已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteStoryboard = false;
  }
}

async function handleCreateShot() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先创建或选择一个分镜板");
    return;
  }
  if (selectedStoryboardProductionMode.value !== "shot_pipeline") {
    setError("当前分镜板处于场景直出模式，不创建单镜头卡");
    return;
  }
  if (!forms.shotSceneId) {
    setError("请先选择一个场景");
    return;
  }

  loading.createShot = true;
  try {
    applyShotModeRules(forms);
    validateShotSource(forms);
    const response = await createShot(state.selectedSeriesSlug, state.selectedStoryboardId, {
      scene_id: forms.shotSceneId,
      shot_payload: {
        characters: state.selectedCharacterIds,
        anchor_strategy: buildShotAnchorStrategyPayload(forms, state.selectedCharacterIds),
        story: buildShotStoryPayload(forms),
        dialogue: buildShotDialoguePayload(forms),
        media: buildShotMediaPayload(forms),
        visual: {
          aspect_ratio: forms.shotAspectRatio,
          style: "cinematic realism",
          resolution: forms.shotResolution,
          generation_count: normalizeShotGenerationCount(forms.shotGenerationCount),
          shot_size: forms.shotSize,
          camera_angle: "eye_level",
          camera_movement: forms.shotMovement,
          lens: "50mm",
          depth_of_field: "medium",
          lighting: forms.shotLighting.trim(),
          palette: forms.shotPalette.trim(),
          duration_seconds: normalizeShotDuration(forms.shotDuration)
        }
      }
    });
    await loadProductionData(state.selectedSeriesSlug);
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, state.selectedShotBatchId);
    state.selectedShotId = response.item.id;
    setNotice(`已创建镜头：${response.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createShot = false;
  }
}

async function handleUpdateShot(item = selectedShot.value) {
  const targetShot = item || selectedShot.value;
  const targetShotId = targetShot?.id || "";

  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !targetShotId) {
    setError("请先选择一个镜头");
    return;
  }
  if (!inlineEditing.shotSceneId) {
    setError("请先选择关联场景");
    return;
  }

  loading.updateShot = true;
  try {
    applyShotModeRules(inlineEditing);
    validateShotSource(inlineEditing);
    await updateShot(state.selectedSeriesSlug, state.selectedStoryboardId, targetShotId, {
      scene_id: inlineEditing.shotSceneId,
      characters: [...inlineEditing.shotCharacterIds],
      anchor_strategy: buildShotAnchorStrategyPayload(inlineEditing, inlineEditing.shotCharacterIds),
      story: buildShotStoryPayload(inlineEditing),
      dialogue: buildShotDialoguePayload(inlineEditing),
      media: buildShotMediaPayload(inlineEditing),
      visual: {
        ...(targetShot.visual || {}),
        aspect_ratio: inlineEditing.shotAspectRatio,
        resolution: inlineEditing.shotResolution,
        generation_count: normalizeShotGenerationCount(inlineEditing.shotGenerationCount),
        shot_size: inlineEditing.shotSize,
        camera_movement: inlineEditing.shotMovement,
        duration_seconds: normalizeShotDuration(inlineEditing.shotDuration),
        lighting: inlineEditing.shotLighting.trim(),
        palette: inlineEditing.shotPalette.trim()
      }
    });
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, state.selectedShotBatchId);
    state.selectedShotId = targetShotId;
    cancelShotEdit();
    setNotice("镜头已更新");
  } catch (error) {
    setError(error);
  } finally {
    loading.updateShot = false;
  }
}

async function handleDeleteShot(item = selectedShot.value) {
  const targetShot = item || selectedShot.value;
  const targetShotId = targetShot?.id || "";

  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !targetShotId) {
    setError("请先选择一个镜头");
    return;
  }
  const confirmed = await confirmDanger(`确定删除镜头“${targetShotId}”吗？`, "删除镜头");
  if (!confirmed) {
    return;
  }

  loading.deleteShot = true;
  try {
    await deleteShot(state.selectedSeriesSlug, state.selectedStoryboardId, targetShotId);
    if (state.selectedShotId === targetShotId) {
      state.selectedShotId = "";
      cancelShotEdit();
    }
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, state.selectedShotBatchId);
    await loadProductionData(state.selectedSeriesSlug);
    setNotice("镜头已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteShot = false;
  }
}

async function handleCreateRenderTask() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !state.selectedShotId) {
    setError("请先选择一个镜头");
    return;
  }
  if (selectedStoryboardProductionMode.value !== "shot_pipeline") {
    setError("场景直出模式不走单镜头任务草稿，请改用场景级直出流程");
    return;
  }
  if (!selectedShotPromptPackage.value?.positive) {
    setError("请先生成镜头包");
    return;
  }

  loading.createRender = true;
  try {
    const shotId = state.selectedShotId;

    const snapshotResponse = await createSnapshot({
      series_slug: state.selectedSeriesSlug,
      storyboard_id: state.selectedStoryboardId,
      shot_id: shotId,
      provider_payload: {
        source: "frontend-workbench",
        note: "seedance-2.0-ready"
      }
    });

    const jobResponse = await createVideoJobFromSnapshot({
      series_slug: state.selectedSeriesSlug,
      snapshot_id: snapshotResponse.item.id,
      type: "video_generation",
      provider: {
        name: "doubao-seedance-2-0",
        submit_mode: "generic_http",
        model: "doubao-seedance-2-0-260128"
      },
      auto_submit: false
    });

    await loadProductionData(state.selectedSeriesSlug);
    state.selectedJobId = jobResponse.item.id;
    await loadJobDetail(state.selectedSeriesSlug, jobResponse.item.id);
    setNotice(`已生成快照 ${snapshotResponse.item.id}，并创建任务草稿 ${jobResponse.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createRender = false;
  }
}

async function handleCreateShotBatch(scope = "selected") {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择一个分镜板");
    return;
  }
  if (selectedStoryboardProductionMode.value !== "shot_pipeline") {
    setError("场景直出模式不生成镜头批次");
    return;
  }

  const shotIds =
    scope === "all"
      ? state.shots.map((item) => item.id).filter(Boolean)
      : state.selectedShotIds.filter(Boolean);
  if (!shotIds.length) {
    setError(scope === "all" ? "当前分镜板还没有镜头卡" : "请先勾选至少一个镜头卡");
    return;
  }

  loading.createShotBatch = true;
  try {
    const response = await createShotBatch(state.selectedSeriesSlug, state.selectedStoryboardId, {
      shot_ids: shotIds,
      auto_assemble_if_missing: true
    });
    await loadProductionData(state.selectedSeriesSlug);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, response.item.id);
    state.selectedShotBatchId = response.item.id;
    setNotice(`已创建批次：${response.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createShotBatch = false;
  }
}

async function handleSubmitShotBatch(batch = selectedShotBatchComputed.value) {
  const batchId = String(batch?.id || "").trim();
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !batchId) {
    setError("请先选择一个批次");
    return;
  }

  loading.submitShotBatch = true;
  try {
    const response = await submitShotBatch(state.selectedSeriesSlug, state.selectedStoryboardId, batchId);
    await loadProductionData(state.selectedSeriesSlug);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, response.item.id);
    state.selectedShotBatchId = response.item.id;
    await loadRemoteTasks(state.selectedSeriesSlug);
    setNotice(`批次已提交：${response.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.submitShotBatch = false;
  }
}

async function handleRefreshShotBatch(batch = selectedShotBatchComputed.value) {
  const batchId = String(batch?.id || "").trim();
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !batchId) {
    setError("请先选择一个批次");
    return;
  }

  loading.refreshShotBatch = true;
  try {
    const response = await refreshShotBatch(state.selectedSeriesSlug, state.selectedStoryboardId, batchId);
    await loadProductionData(state.selectedSeriesSlug);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, response.item.id);
    state.selectedShotBatchId = response.item.id;
    await loadRemoteTasks(state.selectedSeriesSlug);
    setNotice(`批次已刷新：${response.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.refreshShotBatch = false;
  }
}

async function handleRetryFailedShotBatch(batch = selectedShotBatchComputed.value) {
  const batchId = String(batch?.id || "").trim();
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !batchId) {
    setError("请先选择一个批次");
    return;
  }

  loading.retryShotBatch = true;
  try {
    const response = await retryFailedShotBatch(state.selectedSeriesSlug, state.selectedStoryboardId, batchId);
    await loadProductionData(state.selectedSeriesSlug);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, response.item.id);
    state.selectedShotBatchId = response.item.id;
    setNotice(`批次失败项已重试：${response.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.retryShotBatch = false;
  }
}

async function handleDeleteShotBatch(batch = selectedShotBatchComputed.value) {
  const batchId = String(batch?.id || "").trim();
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !batchId) {
    setError("请先选择一个批次");
    return;
  }

  const confirmed = await confirmDanger(`确定删除批次“${batchId}”吗？`, "删除批次");
  if (!confirmed) {
    return;
  }

  loading.deleteShotBatch = true;
  try {
    await deleteShotBatch(state.selectedSeriesSlug, state.selectedStoryboardId, batchId);
    if (state.selectedShotBatchId === batchId) {
      state.selectedShotBatchId = "";
      state.selectedShotBatch = null;
    }
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    setNotice(`批次已删除：${batchId}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteShotBatch = false;
  }
}

async function handleClearShotBatches() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择一个分镜板");
    return;
  }
  if (!state.shotBatches.length) {
    setError("当前没有可清空的批次");
    return;
  }

  const confirmed = await confirmDanger("确定清空当前分镜板下的全部批次吗？", "清空批次");
  if (!confirmed) {
    return;
  }

  loading.clearShotBatches = true;
  try {
    await clearShotBatches(state.selectedSeriesSlug, state.selectedStoryboardId);
    state.selectedShotBatchId = "";
    state.selectedShotBatch = null;
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    setNotice("批次已清空");
  } catch (error) {
    setError(error);
  } finally {
    loading.clearShotBatches = false;
  }
}

async function handleClearShots() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择一个分镜板");
    return;
  }
  if (!state.shots.length) {
    setError("当前没有可清空的镜头卡");
    return;
  }

  const confirmed = await confirmDanger("确定清空当前分镜板下的全部镜头卡吗？", "清空镜头卡");
  if (!confirmed) {
    return;
  }

  loading.clearShots = true;
  try {
    await clearShots(state.selectedSeriesSlug, state.selectedStoryboardId);
    state.selectedShotId = "";
    state.selectedShotIds = [];
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    await loadShotBatchesForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    setNotice("镜头卡已清空");
  } catch (error) {
    setError(error);
  } finally {
    loading.clearShots = false;
  }
}

async function handleRefreshRemoteTasks() {
  if (!state.selectedSeriesSlug) {
    setError("请先选择一个系列");
    return;
  }

  await loadRemoteTasks(state.selectedSeriesSlug, state.selectedRemoteTaskId);
  if (state.selectedRemoteTaskId) {
    await loadRemoteTaskDetail(state.selectedSeriesSlug, state.selectedRemoteTaskId);
  }
  setNotice("远程任务列表已刷新");
}

async function handleOpenRemoteTaskJob(task = selectedRemoteTaskComputed.value) {
  const linkedJob = getRemoteTaskLinkedJob(task);
  if (!linkedJob) {
    setError("当前远程任务没有关联本地草稿");
    return;
  }
  state.selectedJobId = linkedJob.id;
}

async function handleDeleteRemoteTask(task = selectedRemoteTaskComputed.value) {
  const taskId = getRemoteTaskId(task);
  if (!state.selectedSeriesSlug || !taskId) {
    setError("请先选择一个远程任务");
    return;
  }

  const confirmed = await confirmDanger(`确定取消或删除远程任务“${taskId}”吗？`, "删除远程任务");
  if (!confirmed) {
    return;
  }

  loading.deleteRemoteTask = true;
  try {
    const linkedJob = getRemoteTaskLinkedJob(task);
    await deleteRemoteVideoTask(state.selectedSeriesSlug, taskId, {
      job_id: linkedJob?.id || ""
    });
    if (state.selectedRemoteTaskId === taskId) {
      state.selectedRemoteTaskId = "";
      state.selectedRemoteTask = null;
    }
    await loadProductionData(state.selectedSeriesSlug);
    await loadRemoteTasks(state.selectedSeriesSlug);
    setNotice(`远程任务已删除：${taskId}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteRemoteTask = false;
  }
}

async function handleSelectShotPromptVariant(variant) {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !state.selectedShotId) {
    setError("请先选择一个镜头");
    return;
  }

  const normalizedVariant = variant === "ai_refined" ? "ai_refined" : "fallback_template";
  const promptPackage = selectedShotPromptPackage.value;
  if (!promptPackage) {
    setError("当前镜头还没有镜头包");
    return;
  }

  const promptVariants = {
    ai_refined: String(selectedShotPromptVariants.value.ai_refined || "").trim(),
    fallback_template: String(selectedShotPromptVariants.value.fallback_template || "").trim()
  };
  const nextPrompt = promptVariants[normalizedVariant];
  if (!nextPrompt) {
    setError(`${formatPromptVariantLabel(normalizedVariant)}当前不可用`);
    return;
  }
  if (selectedShotPromptVariant.value === normalizedVariant && promptPackage.positive === nextPrompt) {
    return;
  }

  loading.updateShot = true;
  try {
    await updateShot(state.selectedSeriesSlug, state.selectedStoryboardId, state.selectedShotId, {
      prompt_package: {
        ...promptPackage,
        positive: nextPrompt,
        prompt_variants: promptVariants,
        selected_prompt_variant: normalizedVariant,
        video_payload: {
          ...(promptPackage.video_payload || {}),
          prompt: nextPrompt
        }
      }
    });
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, state.selectedShotId);
    setNotice(`已切换为${formatPromptVariantLabel(normalizedVariant)}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.updateShot = false;
  }
}

async function handleSubmitJob() {
  if (!state.selectedSeriesSlug || !state.selectedJobId) {
    setError("请先选择一个任务");
    return;
  }

  loading.submitJob = true;
  try {
    const response = await submitJob(state.selectedSeriesSlug, state.selectedJobId);
    await loadProductionData(state.selectedSeriesSlug);
    await loadRemoteTasks(state.selectedSeriesSlug, getRemoteTaskIdByJob(response.item));
    state.selectedJobId = response.item.id;
    await loadJobDetail(state.selectedSeriesSlug, response.item.id);
    setNotice(`任务 ${response.item.id} 当前状态：${formatStatus(response.item.status)}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.submitJob = false;
  }
}

async function handleRefreshJob() {
  if (!state.selectedSeriesSlug || !state.selectedJobId) {
    setError("请先选择一个任务");
    return;
  }

  loading.refreshJob = true;
  try {
    const response = await refreshJob(state.selectedSeriesSlug, state.selectedJobId);
    await loadProductionData(state.selectedSeriesSlug);
    await loadRemoteTasks(state.selectedSeriesSlug, getRemoteTaskIdByJob(response.item));
    state.selectedJobId = response.item.id;
    await loadJobDetail(state.selectedSeriesSlug, response.item.id);
    setNotice(`任务 ${response.item.id} 已刷新：${formatStatus(response.item.status)}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.refreshJob = false;
  }
}

async function handleOpenJobSnapshot(item = selectedJobComputed.value) {
  const targetJob = item || selectedJobComputed.value;
  const snapshotId = targetJob?.snapshot_id || "";
  if (!state.selectedSeriesSlug || !snapshotId) {
    setError("当前任务没有关联快照");
    return;
  }

  if (targetJob?.id && targetJob.id !== state.selectedJobId) {
    state.selectedJobId = targetJob.id;
    return;
  }
  state.selectedSnapshotId = snapshotId;
  await loadSnapshotDetail(state.selectedSeriesSlug, snapshotId);
}

async function handleOpenSnapshot(item = state.selectedSnapshot) {
  const targetSnapshot = item || state.selectedSnapshot;
  const snapshotId = targetSnapshot?.id || "";
  if (!state.selectedSeriesSlug || !snapshotId) {
    setError("请先选择一个快照");
    return;
  }

  state.selectedSnapshotId = snapshotId;
  await loadSnapshotDetail(state.selectedSeriesSlug, snapshotId);
}

async function handleDeleteJob(item = selectedJobComputed.value) {
  const targetJob = item || selectedJobComputed.value;
  const targetJobId = targetJob?.id || "";
  if (!state.selectedSeriesSlug || !targetJobId) {
    setError("请先选择一个任务");
    return;
  }

  const confirmed = await confirmDanger(`确定删除任务“${targetJobId}”吗？`, "删除任务");
  if (!confirmed) {
    return;
  }

  loading.deleteJob = true;
  try {
    await deleteJob(state.selectedSeriesSlug, targetJobId);
    if (state.selectedJobId === targetJobId) {
      state.selectedJobId = "";
      state.selectedJob = null;
      state.selectedSnapshot = null;
    }
    await loadProductionData(state.selectedSeriesSlug);
    setNotice("任务已删除");
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteJob = false;
  }
}

async function handleDeleteSnapshot(item = state.selectedSnapshot) {
  const targetSnapshot = item || state.selectedSnapshot;
  const snapshotId = targetSnapshot?.id || "";
  if (!state.selectedSeriesSlug || !snapshotId) {
    setError("请先选择一个快照");
    return;
  }

  const confirmed = await confirmDanger(`确定删除快照“${snapshotId}”吗？`, "删除快照");
  if (!confirmed) {
    return;
  }

  loading.deleteSnapshot = true;
  try {
    await deleteSnapshot(state.selectedSeriesSlug, snapshotId);
    if (state.selectedSnapshotId === snapshotId) {
      state.selectedSnapshotId = "";
      state.selectedSnapshot = null;
    }
    await loadProductionData(state.selectedSeriesSlug);
    setNotice(`快照已删除：${snapshotId}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.deleteSnapshot = false;
  }
}

async function handleClearJobs() {
  if (!state.selectedSeriesSlug) {
    setError("请先选择一个系列");
    return;
  }
  if (!state.jobs.length) {
    setError("当前没有可清空的任务草稿");
    return;
  }

  const confirmed = await confirmDanger("确定清空当前系列下可删除的全部任务草稿吗？", "清空任务草稿");
  if (!confirmed) {
    return;
  }

  loading.clearJobs = true;
  try {
    const targetJobs = [...state.jobs];
    let deletedCount = 0;
    const failedNotes = [];

    for (const item of targetJobs) {
      const jobId = String(item?.id || "").trim();
      if (!jobId) {
        continue;
      }
      try {
        await deleteJob(state.selectedSeriesSlug, jobId);
        deletedCount += 1;
      } catch (error) {
        failedNotes.push(`${jobId}：${error instanceof Error ? error.message : String(error)}`);
      }
    }

    if (state.selectedJobId && !targetJobs.some((item) => item.id === state.selectedJobId)) {
      state.selectedJobId = "";
      state.selectedJob = null;
    }
    await loadProductionData(state.selectedSeriesSlug);
    await loadRemoteTasks(state.selectedSeriesSlug);

    if (!deletedCount && failedNotes.length) {
      throw new Error(failedNotes.join("；"));
    }

    setNotice(`已清空 ${deletedCount} 条任务草稿${failedNotes.length ? `，失败 ${failedNotes.length} 条` : ""}`);
    state.error = failedNotes.join("\n");
  } catch (error) {
    setError(error);
  } finally {
    loading.clearJobs = false;
  }
}

async function handleClearSnapshots() {
  if (!state.selectedSeriesSlug) {
    setError("请先选择一个系列");
    return;
  }
  if (!state.snapshots.length) {
    setError("当前没有可清空的快照");
    return;
  }

  const confirmed = await confirmDanger("确定清空当前系列下可删除的全部快照吗？", "清空快照");
  if (!confirmed) {
    return;
  }

  loading.clearSnapshots = true;
  try {
    const targetSnapshots = [...state.snapshots];
    let deletedCount = 0;
    const failedNotes = [];

    for (const item of targetSnapshots) {
      const snapshotId = String(item?.id || "").trim();
      if (!snapshotId) {
        continue;
      }
      try {
        await deleteSnapshot(state.selectedSeriesSlug, snapshotId);
        deletedCount += 1;
      } catch (error) {
        failedNotes.push(`${snapshotId}：${error instanceof Error ? error.message : String(error)}`);
      }
    }

    await loadProductionData(state.selectedSeriesSlug);

    if (!deletedCount && failedNotes.length) {
      throw new Error(failedNotes.join("；"));
    }

    setNotice(`已清空 ${deletedCount} 个快照${failedNotes.length ? `，失败 ${failedNotes.length} 个` : ""}`);
    state.error = failedNotes.join("\n");
  } catch (error) {
    setError(error);
  } finally {
    loading.clearSnapshots = false;
  }
}

async function handleAssembleShotPackage() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !state.selectedShotId) {
    setError("请先选择一个镜头");
    return;
  }
  if (selectedStoryboardProductionMode.value !== "shot_pipeline") {
    setError("场景直出模式不组装单镜头包，请改用场景级组包流程");
    return;
  }

  loading.shotPackage = true;
  try {
    const shotId = state.selectedShotId;
    await assembleShotPackage(state.selectedSeriesSlug, state.selectedStoryboardId, shotId);
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, shotId);
    setNotice(`镜头包已组装：${shotId}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.shotPackage = false;
  }
}

async function handleAssembleSceneDirectPackage() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择一个分镜板");
    return;
  }
  if (selectedStoryboardProductionMode.value !== "scene_direct") {
    setError("当前分镜板不是场景直出模式");
    return;
  }

  const sceneId = getSceneDirectSceneId();
  if (!sceneId) {
    setError("请先选择一个场景");
    return;
  }

  loading.sceneDirectPackage = true;
  try {
    applyShotModeRules(forms);
    validateShotSource(forms);
    await assembleScenePackage(state.selectedSeriesSlug, state.selectedStoryboardId, sceneId, buildSceneDirectPayload());
    await loadProductionData(state.selectedSeriesSlug);
    state.selectedSceneId = sceneId;
    setNotice(`场景直出包已组装：${sceneId}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.sceneDirectPackage = false;
  }
}

async function handleCreateSceneDirectTask() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择一个分镜板");
    return;
  }
  if (selectedStoryboardProductionMode.value !== "scene_direct") {
    setError("当前分镜板不是场景直出模式");
    return;
  }

  const sceneId = getSceneDirectSceneId();
  if (!sceneId) {
    setError("请先选择一个场景");
    return;
  }

  loading.createSceneDirectTask = true;
  try {
    applyShotModeRules(forms);
    validateShotSource(forms);
    await assembleScenePackage(state.selectedSeriesSlug, state.selectedStoryboardId, sceneId, buildSceneDirectPayload());
    const snapshotResponse = await createSceneDirectSnapshot({
      series_slug: state.selectedSeriesSlug,
      storyboard_id: state.selectedStoryboardId,
      provider_payload: {
        source: "frontend-scene-direct",
        note: "seedance-scene-direct"
      }
    });
    const jobResponse = await createVideoJobFromSnapshot({
      series_slug: state.selectedSeriesSlug,
      snapshot_id: snapshotResponse.item.id,
      type: "video_generation",
      provider: {
        name: "doubao-seedance-2-0",
        submit_mode: "generic_http",
        model: "doubao-seedance-2-0-260128"
      },
      auto_submit: false
    });
    await loadProductionData(state.selectedSeriesSlug);
    state.selectedSceneId = sceneId;
    state.selectedSnapshotId = snapshotResponse.item.id;
    state.selectedJobId = jobResponse.item.id;
    await loadJobDetail(state.selectedSeriesSlug, jobResponse.item.id);
    setNotice(`已生成场景快照 ${snapshotResponse.item.id}，并创建任务草稿 ${jobResponse.item.id}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.createSceneDirectTask = false;
  }
}

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

provideWorkspaceContext({
  health,
  characterSourceFiles,
  characterSourceInput,
  parsedScriptViewMode,
  loadingSpinnerViewBox,
  loadingSpinnerSvg,
  loading,
  forms,
  inlineEditing,
  parsedShotEditing,
  parsedSceneEditing,
  state,
  ...workspaceDerived,
  shotAnchorModeOptions,
  shotAspectRatioOptions,
  shotGenerationCountOptions,
  shotInputModeOptions,
  shotMovementOptions,
  shotResolutionOptions,
  shotSizeOptions,
  storyboardProductionModeOptions,
  setNotice,
  setError,
  assetUrl,
  singlePreviewList,
  ...workspaceEditing,
  ...workspaceLocalHelpers,
  formatShotBatchCounts,
  formatShotBatchProgress,
  formatHealth,
  formatStatus,
  formatAnchorKey,
  formatShotSize,
  formatShotMovement,
  formatShotInputMode,
  normalizeShotAnchorMode,
  formatShotAnchorMode,
  normalizeShotAnchorOverrides,
  buildShotAnchorStrategyPayload,
  getShotAnchorOverrideValue,
  setShotAnchorOverrideValue,
  countShotAnchorOverrides,
  normalizeStoryboardProductionMode,
  formatStoryboardProductionMode,
  formatSnapshotSource,
  formatShotAspectRatio,
  formatShotResolution,
  parseMediaPaths,
  serializeMediaPaths,
  normalizeShotInputMode,
  isReferenceMode,
  isFirstLastFrameMode,
  isTextOnlyMode,
  normalizeShotDuration,
  normalizeShotGenerationCount,
  applyShotModeRules,
  validateShotSource,
  getShotMediaEntries,
  removeShotMediaEntry,
  handleShotMediaUpload,
  buildShotMediaPayload,
  formatShotKeyword,
  formatPromptGenerationMode,
  formatPromptVariantLabel,
  formatProviderName,
  formatJobApiKind,
  inferSeedanceModeFromContent,
  formatSeedanceMode,
  normalizeSeedanceRequestBodyForDisplay,
  buildSeedanceRequestSummary,
  getJobSeedanceSummary,
  formatJobOutputSummary,
  formatJobReferenceSummary,
  formatReadableField,
  getReadableSceneInfo,
  getReadableShotInfo,
  normalizeDialogueEntries,
  formatDialogueEntries,
  serializeDialogueEntries,
  parseDialogueText,
  buildShotStoryPayload,
  buildShotDialoguePayload,
  formatLegacyCameraSummary,
  normalizeMatchText,
  firstNonEmptyText,
  getParsedShotDialogueEntries,
  buildParsedShotDescription,
  serializeCharacterEntries,
  parseCharacterText,
  buildParsedCameraSummary,
  ...parsedScriptEditor,
  getSceneDirectSceneId,
  buildSceneDirectPayload,
  handleCreateSeries,
  handleUpdateSeries,
  handleDeleteSeries,
  handleCreateEpisode,
  handleUpdateEpisode,
  handleDeleteEpisode,
  handleSaveRawScript,
  handleSaveParsedScript,
  handleAnalyzeScript,
  handleCreateCharacter,
  handleUpdateCharacter,
  handleDeleteCharacter,
  handleCharacterSourceFileChange,
  handleUploadCharacterSourceImages,
  handleDeleteCharacterSourceImage,
  handleGenerateCharacterAssets,
  handleCreateScene,
  handleUpdateScene,
  handleDeleteScene,
  handleGenerateSceneAssets,
  handleCreateStoryboard,
  handleChangeStoryboardProductionMode,
  handleDeleteStoryboard,
  handleCreateShot,
  handleUpdateShot,
  handleDeleteShot,
  handleCreateRenderTask,
  handleCreateShotBatch,
  handleSubmitShotBatch,
  handleRefreshShotBatch,
  handleRetryFailedShotBatch,
  handleDeleteShotBatch,
  handleClearShotBatches,
  handleClearShots,
  handleRefreshRemoteTasks,
  handleOpenRemoteTaskJob,
  handleDeleteRemoteTask,
  handleSelectShotPromptVariant,
  handleSubmitJob,
  handleRefreshJob,
  handleOpenJobSnapshot,
  handleOpenSnapshot,
  handleDeleteJob,
  handleDeleteSnapshot,
  handleClearJobs,
  handleClearSnapshots,
  handleAssembleShotPackage,
  handleAssembleSceneDirectPackage,
  handleCreateSceneDirectTask
});

onMounted(boot);
</script>

<template>
  <main class="shell">
    <WorkspaceHero />
    <section class="workspace">
      <WorkspaceSidebarLeft />
      <WorkspaceMainPanel />
      <WorkspaceStoryboardPanel />
      <WorkspaceExecutionPanel />
    </section>
  </main>
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  --ui-accent: #74ff52;
  --ui-accent-strong: #5cf43d;
  --ui-accent-cyan: #a8ff8e;
  --ui-accent-soft: rgba(116, 255, 82, 0.14);
  --ui-accent-border: rgba(116, 255, 82, 0.28);
  --ui-panel: rgba(7, 12, 19, 0.68);
  --ui-panel-strong: rgba(7, 12, 19, 0.8);
  --ui-card: rgba(255, 255, 255, 0.028);
  --ui-card-strong: rgba(255, 255, 255, 0.045);
  --ui-line: rgba(255, 255, 255, 0.07);
  --ui-gap: 12px;
  --ui-panel-pad: 16px;
  --ui-card-pad: 12px;
  margin: 0;
  min-height: 100vh;
  font-family: "SF Pro Display", "PingFang SC", "Segoe UI", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at 14% 12%, rgba(116, 255, 82, 0.2), transparent 10%),
    radial-gradient(circle at 82% 0%, rgba(168, 255, 142, 0.08), transparent 12%),
    radial-gradient(circle at 50% 100%, rgba(64, 128, 78, 0.12), transparent 16%),
    linear-gradient(152deg, #010102 0%, #09111a 36%, #010201 72%, #010102 100%);
  color: #edf2f7;
  letter-spacing: 0.01em;
}

button,
input,
select,
textarea {
  font: inherit;
}

.el-message {
  --el-message-bg-color: rgba(12, 20, 34, 0.94);
  --el-message-border-color: rgba(255, 255, 255, 0.14);
  --el-message-text-color: #edf2f7;
  backdrop-filter: blur(18px);
}

.shell .el-loading-mask {
  backdrop-filter: blur(10px);
  border-radius: 18px;
}

.shell .el-loading-spinner {
  margin-top: calc(0px - 28px);
  display: grid;
  justify-items: center;
  gap: 12px;
}

.shell .el-loading-spinner .circular {
  width: 62px;
  height: 62px;
}

.shell .el-loading-spinner .el-loading-text {
  margin: 0;
  padding: 8px 14px;
  border-radius: 999px;
  color: #efffed;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  background: rgba(6, 10, 14, 0.56);
  border: 1px solid rgba(116, 255, 82, 0.18);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 12px 30px rgba(0, 0, 0, 0.22);
}

.el-message--success {
  --el-message-bg-color: rgba(11, 46, 34, 0.92);
  --el-message-border-color: rgba(52, 211, 153, 0.36);
}

.el-message--error {
  --el-message-bg-color: rgba(61, 18, 28, 0.94);
  --el-message-border-color: rgba(251, 113, 133, 0.38);
}

.el-select__popper,
.el-popper.is-light {
  --el-bg-color-overlay: #111a2b;
  --el-fill-color-light: rgba(255, 255, 255, 0.05);
  --el-border-color-light: rgba(255, 255, 255, 0.12);
  --el-text-color-regular: #edf2f7;
  --el-text-color-primary: #edf2f7;
  --el-text-color-placeholder: rgba(237, 242, 247, 0.52);
}

.el-select-dropdown__item {
  color: #edf2f7;
}

.el-select-dropdown__item.is-hovering,
.el-select-dropdown__item.hover {
  background: rgba(116, 255, 82, 0.16);
}

.el-select-dropdown__item.selected {
  color: var(--ui-accent-cyan);
  font-weight: 700;
}

.shell {
  width: min(2360px, calc(100% - 20px));
  margin: 0 auto;
  padding: 20px 0 34px;
}

.masthead {
  display: grid;
  grid-template-columns: 1.5fr minmax(380px,
      480px);
  gap: var(--ui-gap);
  margin-bottom: var(--ui-gap);
  align-items: stretch;
}

.masthead> :first-child {
  padding: 8px 4px 4px;
}

.eyebrow,
.panel-kicker {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 10px;
  color: var(--ui-accent);
}

h1 {
  margin: 0 0 10px;
  font-size: clamp(30px, 4.8vw, 48px);
  line-height: 1.02;
  letter-spacing: -0.04em;
}

h2,
h3 {
  margin: 0;
}

h2 {
  font-size: 20px;
}

h3 {
  font-size: 14px;
}

.lead,
.status-copy,
.inline-note,
.upload-copy {
  margin: 0;
  line-height: 1.6;
  font-size: 12.5px;
  color: rgba(237, 242, 247, 0.7);
}

.lead {
  max-width: 760px;
}

.view-switch {
  flex-shrink: 0;
}

.storyboard-mode-switch {
  flex-shrink: 0;
}

.readable-script-view {
  display: grid;
  gap: 12px;
}

.status-panel,
.panel {
  border: 1px solid var(--ui-line);
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)),
    var(--ui-panel);
  backdrop-filter: blur(18px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 14px 36px rgba(2, 6, 16, 0.28),
    0 1px 0 rgba(10, 18, 32, 0.2);
}

.status-panel {
  padding: var(--ui-panel-pad);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.014)),
    rgba(8, 14, 22, 0.54);
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 7px 11px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(116, 255, 82, 0.14), rgba(168, 255, 142, 0.1));
  border: 1px solid rgba(116, 255, 82, 0.16);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-dot.ok {
  background: var(--ui-accent-cyan);
  box-shadow: 0 0 14px rgba(102, 224, 255, 0.55);
}

.status-dot.offline {
  background: #fb7185;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(250px, 300px) minmax(0, 1fr) minmax(380px, 480px) minmax(380px, 480px);
  gap: var(--ui-gap);
  align-items: start;
}

.column {
  display: grid;
  gap: var(--ui-gap);
  min-width: 0;
}

.panel {
  padding: var(--ui-panel-pad);
  min-width: 0;
  overflow: hidden;
}

.panel-accent {
  background:
    linear-gradient(165deg, rgba(116, 255, 82, 0.16), rgba(255, 255, 255, 0.035)),
    var(--ui-panel-strong);
}

.hero-panel {
  background:
    radial-gradient(circle at 88% 18%, rgba(168, 255, 142, 0.13), transparent 24%),
    radial-gradient(circle at 16% 88%, rgba(116, 255, 82, 0.1), transparent 22%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.032), rgba(255, 255, 255, 0.01)),
    rgba(6, 11, 18, 0.78);
  border-color: rgba(116, 255, 82, 0.18);
  overflow: hidden;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(240px, 300px);
  gap: 14px;
  align-items: stretch;
}

.hero-copy {
  display: grid;
  gap: 12px;
}

.hero-header {
  margin-bottom: 0;
}

.hero-lead {
  margin: 0;
  max-width: 720px;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(237, 242, 247, 0.76);
}

.hero-poster {
  position: relative;
  display: grid;
  align-content: end;
  gap: 10px;
  min-height: 188px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(116, 255, 82, 0.16);
  background:
    radial-gradient(circle at 82% 18%, rgba(168, 255, 142, 0.22), transparent 22%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)),
    linear-gradient(145deg, rgba(10, 18, 14, 0.94), rgba(6, 11, 18, 0.96));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 16px 36px rgba(0, 0, 0, 0.28);
}

.hero-poster::before {
  content: "";
  position: absolute;
  inset: 10px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  pointer-events: none;
}

.hero-poster-tag {
  display: inline-flex;
  width: fit-content;
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(116, 255, 82, 0.14);
  border: 1px solid rgba(116, 255, 82, 0.18);
  color: rgba(226, 255, 216, 0.96);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-poster strong {
  position: relative;
  z-index: 1;
  font-size: 26px;
  line-height: 1.05;
  letter-spacing: -0.04em;
}

.hero-poster small {
  position: relative;
  z-index: 1;
  color: rgba(237, 242, 247, 0.66);
}

.hero-poster-meta {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hero-poster-meta span {
  padding: 5px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(237, 242, 247, 0.76);
  font-size: 11px;
}

.hero-poster-glow {
  position: absolute;
  right: -24px;
  top: -20px;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(116, 255, 82, 0.28), rgba(116, 255, 82, 0));
  filter: blur(6px);
}

.panel-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 0;
  flex-wrap: wrap;
}

.sub-panel-header {
  margin-top: 14px;
}

.execution-flow {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.flow-card {
  position: relative;
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background:
    radial-gradient(circle at top right, rgba(116, 255, 82, 0.06), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.042), rgba(255, 255, 255, 0.018)),
    rgba(255, 255, 255, 0.024);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 10px 22px rgba(0, 0, 0, 0.14);
}

.flow-card.active {
  border-color: rgba(116, 255, 82, 0.28);
  background:
    radial-gradient(circle at top right, rgba(116, 255, 82, 0.14), transparent 26%),
    linear-gradient(145deg, rgba(116, 255, 82, 0.08), rgba(255, 255, 255, 0.04)),
    rgba(255, 255, 255, 0.03);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    inset 0 0 0 1px rgba(116, 255, 82, 0.1),
    0 12px 26px rgba(0, 0, 0, 0.16);
}

.flow-step {
  display: inline-flex;
  width: fit-content;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(116, 255, 82, 0.12);
  color: rgba(205, 255, 190, 0.84);
  font-size: 11px;
  letter-spacing: 0.08em;
}

.flow-card strong {
  font-size: 15px;
  letter-spacing: -0.02em;
}

.flow-card small {
  color: rgba(237, 242, 247, 0.62);
  line-height: 1.55;
}

.flow-card em {
  color: rgba(215, 255, 203, 0.84);
  font-style: normal;
  font-size: 11px;
}

.execution-stage {
  display: grid;
  gap: 10px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.execution-stage:first-of-type {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.execution-stage-header {
  margin-top: 0;
}

.subsection-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.nested-mini-list {
  gap: 10px;
}

.panel-header>div {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.panel-header h2,
.panel-header h3 {
  font-weight: 650;
  letter-spacing: -0.02em;
}

.pill,
.series-slug {
  padding: 5px 9px;
  border-radius: 999px;
  background:
    linear-gradient(135deg, rgba(116, 255, 82, 0.08), rgba(255, 255, 255, 0.04)),
    rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(116, 255, 82, 0.12);
  color: rgba(237, 242, 247, 0.74);
  font-size: 11px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.form-stack,
.list-stack,
.meta-list,
.mini-list,
.lab-stack {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.field {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.085);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.038);
  color: #edf2f7;
  outline: none;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 2px 10px rgba(0, 0, 0, 0.08);
}

.field::placeholder {
  color: rgba(237, 242, 247, 0.34);
}

.field:focus {
  border-color: var(--ui-accent-strong);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 0 0 3px rgba(116, 255, 82, 0.11);
}

.hidden-file-input {
  display: none;
}

.upload-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: space-between;
}

.upload-count {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(116, 255, 82, 0.1);
  color: rgba(237, 242, 247, 0.68);
  font-size: 11px;
}

.file-input {
  padding-block: 10px;
  cursor: pointer;
}

.file-input::file-selector-button {
  margin-right: 12px;
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(168, 255, 142, 0.98), rgba(116, 255, 82, 0.94));
  color: #081109;
  font-weight: 700;
  cursor: pointer;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.34),
    0 6px 14px rgba(116, 255, 82, 0.24);
}

.shot-media-panel {
  position: relative;
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(116, 255, 82, 0.14);
  background:
    radial-gradient(circle at top right, rgba(168, 255, 142, 0.1), transparent 24%),
    radial-gradient(circle at left top, rgba(116, 255, 82, 0.08), transparent 20%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.016)),
    rgba(255, 255, 255, 0.025);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 12px 28px rgba(0, 0, 0, 0.16);
}

.inline-shot-media-panel {
  padding: 12px;
}

.story-binding-panel {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(116, 255, 82, 0.12);
  background:
    radial-gradient(circle at top right, rgba(116, 255, 82, 0.08), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.042), rgba(255, 255, 255, 0.018)),
    rgba(255, 255, 255, 0.024);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 10px 24px rgba(0, 0, 0, 0.14);
}

.story-binding-header {
  display: grid;
  gap: 4px;
}

.story-binding-header strong {
  font-size: 13px;
  letter-spacing: -0.01em;
}

.story-binding-header small {
  color: rgba(237, 242, 247, 0.68);
  line-height: 1.55;
}

.compact-stack {
  gap: 8px;
}

.inline-label {
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.035);
  color: rgba(237, 242, 247, 0.82);
  font-size: 12px;
}

.shot-media-header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}

.shot-media-header strong {
  display: block;
  margin-bottom: 3px;
  font-size: 13px;
  letter-spacing: -0.01em;
}

.shot-media-header small {
  color: rgba(237, 242, 247, 0.72);
  white-space: nowrap;
  font-size: 11px;
  padding: 5px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(116, 255, 82, 0.1);
}

.shot-media-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.shot-upload-tile,
.shot-disabled-tile {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.016)),
    rgba(255, 255, 255, 0.028);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 8px 18px rgba(0, 0, 0, 0.1);
}

.shot-upload-tile {
  cursor: pointer;
  transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
}

.shot-upload-tile:hover {
  transform: translateY(-1px);
  border-color: var(--ui-accent-border);
  background:
    linear-gradient(145deg, rgba(116, 255, 82, 0.09), rgba(255, 255, 255, 0.04)),
    rgba(255, 255, 255, 0.03);
}

.shot-upload-tile-wide {
  grid-column: span 2;
}

.shot-upload-chip {
  display: inline-flex;
  width: fit-content;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(116, 255, 82, 0.16);
  color: rgba(229, 255, 220, 0.94);
  font-size: 11px;
  line-height: 1;
}

.shot-upload-chip.muted {
  background: rgba(148, 163, 184, 0.14);
  color: rgba(203, 213, 225, 0.82);
}

.shot-upload-input {
  display: none;
}

.shot-disabled-tile {
  opacity: 0.82;
  border-style: dashed;
}

.shot-media-preview-grid {
  gap: 12px;
}

.shot-media-card {
  gap: 10px;
}

.field-select {
  width: 100%;
  min-width: 0;
}

.field-select .el-select__wrapper {
  min-height: 40px;
  border-radius: 12px;
  padding: 0 12px;
  box-shadow: none;
  background: rgba(255, 255, 255, 0.038);
  border: 1px solid rgba(255, 255, 255, 0.085);
}

.field-select .el-select__wrapper.is-focused {
  border-color: var(--ui-accent-strong);
  box-shadow: 0 0 0 3px rgba(116, 255, 82, 0.1);
}

.field-select .el-select__placeholder,
.field-select .el-select__selected-item,
.field-select .el-select__input-wrapper,
.field-select .el-select__caret {
  color: #edf2f7;
}

.field-textarea {
  min-height: 88px;
}

.field-textarea.compact {
  min-height: 76px;
}

.editor-textarea {
  min-height: 360px;
}

.editor-textarea .el-textarea__inner {
  min-height: 360px;
  font-size: 14px;
  line-height: 1.6;
}

.code-textarea {
  font-family: "Consolas", "SFMono-Regular", monospace;
}

.code-textarea .el-textarea__inner {
  font-family: "Consolas", "SFMono-Regular", monospace;
}

.job-code {
  min-height: 180px;
}

.field-textarea .el-textarea__inner {
  min-height: inherit;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.085);
  background: rgba(255, 255, 255, 0.038);
  color: #edf2f7;
  box-shadow: none;
}

.field-textarea .el-textarea__inner::placeholder {
  color: rgba(237, 242, 247, 0.34);
}

.field-textarea .el-textarea__inner:focus {
  border-color: var(--ui-accent-strong);
  box-shadow: 0 0 0 3px rgba(116, 255, 82, 0.1);
}

.field-number {
  width: 100%;
}

.field-number .el-input__wrapper {
  min-height: 40px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.038);
  border: 1px solid rgba(255, 255, 255, 0.085);
  box-shadow: none;
}

.field-number .el-input__inner {
  color: #edf2f7;
}

.field-number .el-input-number__decrease,
.field-number .el-input-number__increase {
  background: rgba(255, 255, 255, 0.08);
  color: #edf2f7;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
}

.action-button,
.action-button.el-button {
  --el-button-border-color: transparent;
  --el-button-bg-color: transparent;
  --el-button-text-color: inherit;
  --el-button-hover-text-color: inherit;
  --el-button-hover-border-color: transparent;
  --el-button-hover-bg-color: transparent;
  --el-button-active-border-color: transparent;
  --el-button-active-bg-color: transparent;
  --el-button-active-text-color: inherit;
  --el-button-disabled-border-color: transparent;
  --el-button-disabled-bg-color: transparent;
  --el-button-disabled-text-color: inherit;
  min-height: 38px;
  border: none;
  border-radius: 12px;
  padding: 9px 12px;
  color: #0f172a;
  cursor: pointer;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.01em;
  background-image: none;
  transition: transform 160ms ease, opacity 160ms ease, box-shadow 160ms ease;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    0 7px 16px rgba(0, 0, 0, 0.14);
}

.action-button.el-button>span {
  display: inline-flex;
  align-items: center;
}

.action-button.el-button+.action-button.el-button {
  margin-left: 0;
}

.action-button:hover:not(:disabled),
.action-button.el-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 10px 22px rgba(0, 0, 0, 0.2);
}

.action-button:disabled,
.action-button.el-button.is-disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-button.warm {
  background: linear-gradient(135deg, #b5ff9b 0%, #74ff52 100%);
  color: #081109;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    0 10px 24px rgba(72, 178, 44, 0.24);
}

.action-button.dark {
  background: linear-gradient(135deg, rgba(245, 249, 244, 0.9), rgba(193, 235, 183, 0.86));
  color: #0b130d;
}

.action-button.ghost {
  color: #edf2f7;
  background: linear-gradient(135deg, rgba(116, 255, 82, 0.09), rgba(168, 255, 142, 0.07));
  border: 1px solid rgba(116, 255, 82, 0.16);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 6px 14px rgba(0, 0, 0, 0.12);
}

.action-button.danger {
  color: #ffe4e6;
  background: linear-gradient(135deg, rgba(190, 24, 93, 0.22), rgba(244, 63, 94, 0.24));
  border: 1px solid rgba(251, 113, 133, 0.3);
}

.action-button.primary-action {
  min-height: 42px;
  font-size: 12.5px;
  letter-spacing: 0.02em;
}

.action-button.selected-variant {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    0 10px 24px rgba(72, 178, 44, 0.24);
}

.action-button.full-width {
  width: 100%;
  margin-bottom: 10px;
}

.compact-button {
  padding: 7px 9px;
  font-size: 11px;
}

.compact-button.el-button {
  min-height: 30px;
}

.list-card,
.episode-chip,
.mini-card.selectable {
  position: relative;
  width: 100%;
  border: 1px solid var(--ui-line);
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  text-align: left;
  cursor: default;
  transition:
    transform 160ms ease,
    border-color 160ms ease,
    background 160ms ease,
    box-shadow 160ms ease;
}

.list-card,
.mini-card,
.focus-card,
.anchor-card,
.reference-card,
.meta-panel,
.upload-panel {
  display: grid;
  gap: 5px;
  padding: var(--ui-card-pad);
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.018)),
    rgba(255, 255, 255, 0.026);
  border: 1px solid var(--ui-line);
  min-width: 0;
  overflow: hidden;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 8px 22px rgba(0, 0, 0, 0.12);
}

.focus-card,
.meta-panel,
.reference-card,
.upload-panel {
  position: relative;
  border-color: rgba(255, 255, 255, 0.07);
  background:
    radial-gradient(circle at top right, rgba(116, 255, 82, 0.07), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.016)),
    rgba(255, 255, 255, 0.026);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 12px 24px rgba(0, 0, 0, 0.14);
}

.focus-card::before,
.meta-panel::before,
.reference-card::before,
.upload-panel::before,
.shot-media-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0));
  opacity: 0.8;
}

.debug-disclosure {
  display: grid;
  gap: 8px;
}

.debug-disclosure summary {
  cursor: pointer;
  color: rgba(237, 242, 247, 0.72);
  font-size: 12px;
  user-select: none;
  list-style: none;
}

.debug-disclosure summary::-webkit-details-marker {
  display: none;
}

.debug-disclosure summary::before {
  content: "▸";
  display: inline-block;
  margin-right: 6px;
  transition: transform 160ms ease;
}

.debug-disclosure[open] summary::before {
  transform: rotate(90deg);
}

.debug-panel {
  margin-top: 2px;
}

.storyboard-detail-section {
  min-width: 0;
}

.detail-skeleton-stack {
  display: grid;
  gap: 12px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.skeleton-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background:
    radial-gradient(circle at top right, rgba(116, 255, 82, 0.06), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.042), rgba(255, 255, 255, 0.018)),
    rgba(255, 255, 255, 0.024);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 10px 24px rgba(0, 0, 0, 0.14);
}

.skeleton-header-card {
  gap: 12px;
}

.skeleton-chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.skeleton-kicker {
  width: 96px;
}

.skeleton-title {
  width: min(260px, 70%);
}

.skeleton-line {
  width: 100%;
}

.skeleton-line-mid {
  width: 72%;
}

.skeleton-line-wide {
  width: 88%;
}

.skeleton-chip {
  width: 96px;
  height: 32px;
}

.skeleton-button {
  width: 156px;
  height: 40px;
}

.skeleton-button-strong {
  width: 180px;
}

.skeleton-media {
  width: 100%;
  height: 180px;
  border-radius: 14px;
}

.detail-skeleton-stack .el-skeleton__item {
  --el-skeleton-color: rgba(255, 255, 255, 0.08);
  --el-skeleton-to-color: rgba(116, 255, 82, 0.14);
  border-radius: 12px;
}

.list-card::before,
.mini-card.selectable::before,
.episode-chip::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  opacity: 0;
  transition: opacity 160ms ease;
}

.list-card:not(.active):hover,
.mini-card.selectable:not(.active):hover,
.episode-chip:not(.active):hover {
  transform: translateY(-1px);
  border-color: rgba(116, 255, 82, 0.18);
  background:
    linear-gradient(145deg, rgba(116, 255, 82, 0.08), rgba(255, 255, 255, 0.04)),
    rgba(255, 255, 255, 0.028);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 12px 24px rgba(0, 0, 0, 0.16);
}

.list-card:not(.active):hover::before,
.mini-card.selectable:not(.active):hover::before,
.episode-chip:not(.active):hover::before {
  opacity: 1;
  background:
    linear-gradient(180deg, rgba(190, 255, 176, 0.12), rgba(255, 255, 255, 0)),
    radial-gradient(circle at 100% 0%, rgba(116, 255, 82, 0.1), transparent 24%);
}

.list-card.active,
.mini-card.selectable.active,
.episode-chip.active {
  border-color: rgba(116, 255, 82, 0.38);
  background:
    linear-gradient(140deg, rgba(116, 255, 82, 0.14), rgba(255, 255, 255, 0.045)),
    rgba(255, 255, 255, 0.028);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 0 0 1px rgba(116, 255, 82, 0.12),
    0 10px 24px rgba(0, 0, 0, 0.16);
}

.list-card.active::before,
.mini-card.selectable.active::before,
.episode-chip.active::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg, rgba(178, 255, 161, 0.86), rgba(116, 255, 82, 0.26));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.list-card.active::after,
.mini-card.selectable.active::after,
.episode-chip.active::after {
  content: "";
  position: absolute;
  left: 14px;
  right: 14px;
  top: -1px;
  height: 1px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0), rgba(184, 255, 168, 0.9), rgba(255, 255, 255, 0));
  opacity: 0.92;
  pointer-events: none;
}

.item-body {
  display: grid;
  gap: 3px;
  min-width: 0;
  cursor: pointer;
  flex: 1;
}

.script-shot-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.script-shot-actions .action-button.el-button {
  min-height: 30px;
}

.script-scene-editor {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.script-scene-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.script-scene-actions .action-button.el-button {
  min-height: 30px;
}

.direct-beat-list {
  margin-top: 8px;
}

.mode-placeholder-card {
  margin-top: 12px;
}

.list-card strong,
.mini-card strong,
.episode-chip strong,
.focus-card strong {
  letter-spacing: -0.02em;
}

.item-editor {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.script-shot-editor {
  display: grid;
  gap: 8px;
  min-width: 0;
  padding: 2px 0;
}

.item-actions {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 2px;
  flex-shrink: 0;
  opacity: 0.84;
  transition: opacity 160ms ease;
}

.list-card:hover .item-actions,
.mini-card.selectable:hover .item-actions,
.episode-chip:hover .item-actions {
  opacity: 1;
}

.item-inline-field {
  min-width: 180px;
}

.list-card span,
.list-card small,
.mini-card span,
.mini-card small,
.focus-card span,
.focus-card small,
.reference-header small,
.anchor-card span,
.meta-row span {
  color: rgba(237, 242, 247, 0.6);
  font-size: 14px;
}

.list-card span,
.mini-card span,
.episode-chip span {
  color: rgba(205, 255, 190, 0.78);
}

.episode-chip {
  overflow: hidden;
}

.summary-grid,
.studio-grid,
.lab-grid,
.editor-grid,
.reference-grid,
.anchor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ui-gap);
  min-width: 0;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.summary-card {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)),
    rgba(255, 255, 255, 0.026);
  border: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 0;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 10px 18px rgba(0, 0, 0, 0.14);
}

.summary-card span {
  display: block;
  margin-bottom: 2px;
  color: rgba(237, 242, 247, 0.62);
  font-size: 11px;
}

.summary-card strong {
  font-size: 22px;
  letter-spacing: -0.03em;
}

.code-label {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(237, 242, 247, 0.62);
}

.inline-actions {
  display: flex !important;
  gap: 6px;
  align-items: center;
  min-width: 0;
  flex-wrap: nowrap;
}

.compact-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.prompt-variant-actions {
  width: 100%;
}

.inline-field {
  min-width: 180px;
}

.episode-strip {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.episode-chip {
  display: flex;
  gap: 16px;
  padding: 10px 12px;
  border-radius: 14px;
  min-width: 210px;
}

.subsection {
  display: grid;
  gap: 8px;
  margin: 12px 0;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.split-grid,
.check-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  min-width: 0;
}

.check-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-right: 0;
  min-width: 0;
}

.check-card .el-checkbox__input {
  margin-right: 2px;
}

.check-card .el-checkbox__label {
  color: #edf2f7;
  padding-left: 0;
  overflow-wrap: anywhere;
}

.check-card.is-checked {
  border-color: rgba(116, 255, 82, 0.42);
  background: linear-gradient(140deg, rgba(116, 255, 82, 0.18), rgba(168, 255, 142, 0.06));
}

.preview-image {
  width: 100%;
  aspect-ratio: 3 / 2;
  display: block;
}

.preview-image .el-image__inner {
  width: 100%;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}

.preview-image-large {
  aspect-ratio: auto;
  max-height: 760px;
}

.preview-image-large .el-image__inner {
  object-fit: contain;
  background: rgba(255, 255, 255, 0.02);
}

.video-preview {
  width: 100%;
  aspect-ratio: 3 / 2;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}

.reference-empty {
  display: grid;
  place-items: center;
  min-height: 220px;
  border-radius: 14px;
  border: 1px dashed rgba(116, 255, 82, 0.16);
  background:
    radial-gradient(circle at 50% 24%, rgba(116, 255, 82, 0.08), transparent 30%),
    rgba(255, 255, 255, 0.02);
  color: rgba(237, 242, 247, 0.5);
}

.reference-card {
  gap: 12px;
  transition:
    transform 160ms ease,
    border-color 160ms ease,
    box-shadow 160ms ease;
}

.reference-card:hover {
  transform: translateY(-1px);
  border-color: rgba(116, 255, 82, 0.16);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 14px 28px rgba(0, 0, 0, 0.16);
}

.reference-header {
  display: grid;
  gap: 4px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.reference-header strong {
  font-size: 13px;
  letter-spacing: -0.01em;
}

.reference-header small {
  line-height: 1.5;
}

.upload-panel {
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
}

.upload-panel>div:first-child {
  display: grid;
  gap: 8px;
}

.upload-panel strong {
  font-size: 13px;
  letter-spacing: -0.01em;
}

.focus-card {
  gap: 6px;
  padding: 14px;
  border-radius: 16px;
}

.focus-card span {
  color: rgba(200, 255, 184, 0.78);
  font-size: 11px;
}

.focus-card strong {
  font-size: 18px;
}

.focus-card small {
  color: rgba(237, 242, 247, 0.58);
}

.meta-panel,
.meta-list {
  gap: 10px;
}

.meta-panel {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  padding: 14px;
  border-radius: 16px;
}

.meta-row,
.meta-list>div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.meta-row {
  padding: 10px 12px;
  border-radius: 12px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.015)),
    rgba(255, 255, 255, 0.022);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.meta-row-wide {
  grid-column: 1 / -1;
}

.meta-row strong {
  line-height: 1.55;
}

.prompt-preview {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.6;
  font-size: 14px;
}

.subsection>h3,
.mini-list>h3 {
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(201, 255, 190, 0.72);
}

.list-card strong,
.list-card span,
.list-card small,
.mini-card strong,
.mini-card span,
.mini-card small,
.focus-card strong,
.focus-card small,
.anchor-card strong,
.reference-header strong,
.reference-header small,
.meta-row strong,
.meta-list strong,
.summary-card span,
.summary-card strong,
.upload-copy,
.inline-note,
.lead,
.status-copy,
.message,
.empty-state {
  overflow-wrap: anywhere;
}

.job-code,
.code-textarea {
  max-width: 100%;
  overflow-x: auto;
}

.message {
  margin: 0 0 12px;
  padding: 12px 14px;
  border-radius: 14px;
  line-height: 1.6;
}

.message.success {
  background: rgba(52, 211, 153, 0.14);
  border: 1px solid rgba(52, 211, 153, 0.28);
}

.message.error {
  background: rgba(251, 113, 133, 0.12);
  border: 1px solid rgba(251, 113, 133, 0.26);
}

.message.muted {
  background:
    linear-gradient(135deg, rgba(116, 255, 82, 0.06), rgba(255, 255, 255, 0.03)),
    rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(116, 255, 82, 0.1);
  color: rgba(237, 242, 247, 0.7);
}

.empty-state {
  position: relative;
  display: grid;
  place-items: center;
  gap: 8px;
  min-height: 110px;
  padding: 16px;
  border-radius: 16px;
  border: 1px dashed rgba(116, 255, 82, 0.18);
  background:
    radial-gradient(circle at top right, rgba(116, 255, 82, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.014)),
    rgba(255, 255, 255, 0.02);
  color: rgba(237, 242, 247, 0.6);
  text-align: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.empty-state::before {
  content: "";
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background:
    radial-gradient(circle at 35% 35%, rgba(220, 255, 212, 0.92), rgba(116, 255, 82, 0.2) 42%, rgba(116, 255, 82, 0) 72%);
  box-shadow: 0 0 22px rgba(116, 255, 82, 0.18);
}

@media (max-width: 1420px) {
  .workspace {
    grid-template-columns: 280px 1fr;
  }

  .column-right,
  .column-execution {
    grid-column: 1 / -1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .hero-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 1080px) {

  .masthead,
  .hero-grid,
  .workspace,
  .editor-grid,
  .studio-grid,
  .lab-grid,
  .summary-grid,
  .execution-flow,
  .column-right,
  .column-execution,
  .split-grid,
  .check-grid,
  .reference-grid,
  .anchor-grid {
    grid-template-columns: 1fr;
  }

  .inline-actions {
    width: 100%;
    flex-direction: column;
  }

  .item-actions {
    width: 100%;
  }

  .inline-field {
    min-width: 0;
  }

  .item-inline-field {
    min-width: 0;
  }

  .shot-media-header {
    flex-direction: column;
  }

  .shot-media-header small {
    white-space: normal;
  }

  .shot-media-grid {
    grid-template-columns: 1fr;
  }

  .shot-upload-tile-wide {
    grid-column: span 1;
  }

  .hero-poster {
    min-height: 160px;
  }
}

@media (max-width: 640px) {
  .shell {
    width: min(100% - 24px, 1600px);
    padding-top: 20px;
  }

  .panel,
  .status-panel {
    padding: 16px;
    border-radius: 18px;
  }

  h1 {
    font-size: 42px;
  }

  .hero-poster {
    padding: 14px;
    min-height: 148px;
  }
}

.el-input {
  background: rgba(255, 255, 255, 0.05)
}

.el-input__wrapper {
  background: transparent;
  border: none;
  box-shadow: none;

}

.el-input__inner {
  color: #fff;
}
</style>

