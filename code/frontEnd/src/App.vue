<script setup>
import { computed, reactive, ref } from "vue";
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
import { useWorkspaceActions } from "./composables/useWorkspaceActions";
import { useWorkspaceReadActions } from "./composables/useWorkspaceReadActions";
import { useWorkspaceWatchers } from "./composables/useWorkspaceWatchers";
import { useParsedScriptEditor } from "./composables/useParsedScriptEditor";
import { buildWorkspaceContextValue } from "./composables/buildWorkspaceContextValue";
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
import { createShot } from "./services/api";

const workspaceStep = ref("script");
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

const workspaceReadActions = useWorkspaceReadActions({
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
});

const {
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
} = workspaceReadActions;

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

const workspaceActions = useWorkspaceActions({
  characterSourceFiles,
  characterSourceInput,
  state,
  forms,
  inlineEditing,
  loading,
  selectedSeries,
  selectedEpisode,
  selectedCharacter,
  selectedScene,
  selectedStoryboard,
  selectedShot,
  selectedShotBatchComputed,
  selectedRemoteTaskComputed,
  selectedJobComputed,
  selectedShotPromptPackage,
  selectedShotPromptVariants,
  selectedShotPromptVariant,
  selectedStoryboardProductionMode,
  hasUploadedCharacterSourceImages,
  loadSeries,
  loadEpisodes,
  loadProductionData,
  loadShotsForStoryboard,
  loadShotBatchesForStoryboard,
  loadCharacterBible,
  loadScenePackage,
  loadJobDetail,
  loadSnapshotDetail,
  loadRemoteTasks,
  loadRemoteTaskDetail,
  setNotice,
  setError,
  confirmDanger,
  isEditingSeries,
  isEditingEpisode,
  isEditingCharacter,
  isEditingScene,
  cancelSeriesEdit,
  cancelEpisodeEdit,
  cancelCharacterEdit,
  cancelSceneEdit,
  cancelShotEdit,
  getRemoteTaskId,
  getRemoteTaskIdByJob,
  getRemoteTaskLinkedJob,
  formatStatus,
  formatPromptVariantLabel,
  formatStoryboardProductionMode,
  normalizeStoryboardProductionMode,
  buildShotAnchorStrategyPayload,
  buildShotStoryPayload,
  buildShotDialoguePayload,
  buildShotMediaPayload,
  normalizeShotGenerationCount,
  normalizeShotDuration,
  applyShotModeRules,
  validateShotSource,
  appendMediaPaths,
  buildSceneDirectPayload,
  getSceneDirectSceneId
});
useWorkspaceWatchers({
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
});

provideWorkspaceContext(
  buildWorkspaceContextValue({
    core: {
      workspaceStep,
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
      state
    },
    derived: workspaceDerived,
    options: {
      shotAnchorModeOptions,
      shotAspectRatioOptions,
      shotGenerationCountOptions,
      shotInputModeOptions,
      shotMovementOptions,
      shotResolutionOptions,
      shotSizeOptions,
      storyboardProductionModeOptions
    },
    helpers: {
      setNotice,
      setError,
      assetUrl,
      singlePreviewList
    },
    editing: workspaceEditing,
    localHelpers: workspaceLocalHelpers,
    formatters: {
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
      buildParsedCameraSummary
    },
    parsedScriptEditor,
    sceneDirect: {
      getSceneDirectSceneId,
      buildSceneDirectPayload
    },
    actions: workspaceActions
  })
);

</script>

<template>
  <main class="shell">
    <WorkspaceHero />
    <section class="workspace-flow">
      <WorkspaceSidebarLeft />

      <div class="workspace-flow-stage">
        <div class="workspace-flow-nav">
          <el-button-group class="segmented-button-group workspace-step-group">
            <el-button color="var(--ui-accent-solid)" :plain="workspaceStep !== 'script'" dark
              @click="workspaceStep = 'script'">
              1. 剧本
            </el-button>
            <el-button color="var(--ui-accent-solid)" :plain="workspaceStep !== 'assets'" dark
              @click="workspaceStep = 'assets'">
              2. 角色&场景
            </el-button>
            <el-button color="var(--ui-accent-solid)" :plain="workspaceStep !== 'storyboard'" dark
              @click="workspaceStep = 'storyboard'">
              3. 分镜
            </el-button>
            <el-button color="var(--ui-accent-solid)" :plain="workspaceStep !== 'execution'" dark
              @click="workspaceStep = 'execution'">
              4. 执行
            </el-button>
          </el-button-group>
        </div>

        <section v-show="workspaceStep === 'script' || workspaceStep === 'assets'" class="workspace-step">
          <WorkspaceMainPanel />
        </section>

        <section v-show="workspaceStep === 'storyboard'" class="workspace-step">
          <WorkspaceStoryboardPanel />
        </section>

        <section v-show="workspaceStep === 'execution'" class="workspace-step">
          <WorkspaceExecutionPanel />
        </section>
      </div>
    </section>
  </main>
</template>
