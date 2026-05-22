<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
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

const shotSizeOptions = [
  { value: "wide", label: "远景" },
  { value: "medium", label: "中景" },
  { value: "closeup", label: "近景" },
  { value: "extreme_closeup", label: "特写" }
];

const shotMovementOptions = [
  { value: "static", label: "固定机位" },
  { value: "push_in", label: "推进" },
  { value: "pull_out", label: "拉远" },
  { value: "pan", label: "摇镜" },
  { value: "tracking", label: "跟拍" }
];

const shotInputModeOptions = [
  { value: "reference_image", label: "参考生成" },
  { value: "first_last_frame", label: "首尾帧生成" },
  { value: "text_only", label: "纯文本" }
];

const supportedShotInputModes = new Set(shotInputModeOptions.map((item) => item.value));

const shotAnchorModeOptions = [
  { value: "auto", label: "自动" },
  { value: "face_priority", label: "面部优先" },
  { value: "costume_priority", label: "服装优先" },
  { value: "aura_priority", label: "气质优先" },
  { value: "first_appearance", label: "首次出场" },
  { value: "minimal", label: "最简" }
];

const supportedShotAnchorModes = new Set(shotAnchorModeOptions.map((item) => item.value));

const shotAspectRatioOptions = [
  { value: "21:9", label: "21:9" },
  { value: "1:1", label: "1:1" },
  { value: "16:9", label: "16:9" },
  { value: "3:4", label: "3:4" },
  { value: "4:3", label: "4:3" },
  { value: "9:16", label: "9:16" },
  { value: "adaptive", label: "智能比例" }
];

const shotResolutionOptions = [
  { value: "480p", label: "480p" },
  { value: "720p", label: "720p" },
  { value: "1080p", label: "1080p" }
];

const shotGenerationCountOptions = [
  { value: 1, label: "1 条" },
  { value: 2, label: "2 条" },
  { value: 3, label: "3 条" },
  { value: 4, label: "4 条" }
];

const storyboardProductionModeOptions = [
  { value: "shot_pipeline", label: "分镜生产" },
  { value: "scene_direct", label: "场景直出" }
];

const healthTextMap = {
  checking: "检测中",
  ok: "正常",
  offline: "离线",
  unknown: "未知"
};

const entityStatusTextMap = {
  draft: "草稿",
  pending: "待处理",
  package_ready: "已组装",
  prepared: "已准备",
  submitting: "提交中",
  submitted: "已提交",
  completed: "已完成",
  failed: "失败",
  active: "启用中",
  reference_ready: "参考图已生成"
};

const anchorLabelMap = {
  face: "五官锚点",
  hair: "发型锚点",
  costume: "服装锚点",
  aura: "气质锚点"
};

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
  () => loading.boot || loading.production || loading.episodes || loading.createEpisode || loading.updateEpisode || loading.deleteEpisode
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
const selectedRemoteTaskText = computed(() =>
  JSON.stringify(selectedRemoteTaskComputed.value || {}, null, 2)
);
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
  return [
    { key: "sheet", label: "角色圣经拼图", path: images.sheet || "" }
  ];
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
  Object.entries(selectedCharacter.value?.anchors || {})
    .filter(([key]) => ["face", "hair", "costume", "aura"].includes(key))
);

const selectedSceneImageEntries = computed(() => {
  const images = selectedScene.value?.reference_images || {};
  return [
    { key: "sheet", label: "场景参考拼图", path: images.sheet || "" }
  ];
});

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

function isEditingSeries(seriesSlug) {
  return inlineEditing.seriesSlug === seriesSlug;
}

function isEditingEpisode(episodeId) {
  return inlineEditing.episodeId === episodeId;
}

function isEditingCharacter(characterId) {
  return inlineEditing.characterId === characterId;
}

function isEditingScene(sceneId) {
  return inlineEditing.sceneId === sceneId;
}

function isEditingShot(shotId) {
  return inlineEditing.shotId === shotId;
}

function startSeriesEdit(item) {
  inlineEditing.seriesSlug = item.slug;
  inlineEditing.seriesName = item.name || "";
  inlineEditing.seriesDescription = item.description || "";
  state.selectedSeriesSlug = item.slug;
}

function cancelSeriesEdit() {
  inlineEditing.seriesSlug = "";
  inlineEditing.seriesName = "";
  inlineEditing.seriesDescription = "";
}

function startEpisodeEdit(item) {
  inlineEditing.episodeId = item.id;
  inlineEditing.episodeName = item.name || "";
  state.selectedEpisodeId = item.id;
}

function cancelEpisodeEdit() {
  inlineEditing.episodeId = "";
  inlineEditing.episodeName = "";
}

function startCharacterEdit(item) {
  inlineEditing.characterId = item.id;
  inlineEditing.characterName = item.name || "";
  inlineEditing.characterBrief = item.brief || "";
  state.selectedCharacterId = item.id;
}

function cancelCharacterEdit() {
  inlineEditing.characterId = "";
  inlineEditing.characterName = "";
  inlineEditing.characterBrief = "";
}

function startSceneEdit(item) {
  inlineEditing.sceneId = item.id;
  inlineEditing.sceneName = item.name || "";
  inlineEditing.sceneDescription = item.description || "";
  state.selectedSceneId = item.id;
}

function cancelSceneEdit() {
  inlineEditing.sceneId = "";
  inlineEditing.sceneName = "";
  inlineEditing.sceneDescription = "";
}

function startShotEdit(item) {
  const media = item.media || {};
  const visual = item.visual || {};
  const story = item.story || {};
  const anchorStrategy = item.anchor_strategy || {};
  inlineEditing.shotId = item.id;
  inlineEditing.shotSceneId = item.scene_id || "";
  inlineEditing.shotInputMode = normalizeShotInputMode(media.mode);
  inlineEditing.shotGenerateAudio = Boolean(media.generate_audio);
  inlineEditing.shotAspectRatio = visual.aspect_ratio || "16:9";
  inlineEditing.shotResolution = visual.resolution || "1080p";
  inlineEditing.shotGenerationCount = Number(visual.generation_count) || 1;
  inlineEditing.shotFirstFramePath = media.first_frame_path || "";
  inlineEditing.shotLastFramePath = media.last_frame_path || "";
  inlineEditing.shotReferenceImagesText = serializeMediaPaths(media.reference_image_paths);
  inlineEditing.shotSize = item.visual?.shot_size || "medium";
  inlineEditing.shotMovement = item.visual?.camera_movement || "static";
  inlineEditing.shotDuration = item.visual?.duration_seconds || 5;
  inlineEditing.shotLighting = item.visual?.lighting || "";
  inlineEditing.shotPalette = item.visual?.palette || "";
  inlineEditing.shotCharacterIds = [...(item.characters || [])];
  inlineEditing.shotStoryDescription = story.description || "";
  inlineEditing.shotStoryEmotion = story.emotion || "";
  inlineEditing.shotStoryBeat = story.beat || "";
  inlineEditing.shotStoryDialogue = serializeDialogueEntries(item.dialogue || []);
  inlineEditing.shotStoryRawExcerpt = story.raw_script_excerpt || "";
  inlineEditing.shotAnchorMode = normalizeShotAnchorMode(anchorStrategy.mode);
  inlineEditing.shotAnchorOverrides = normalizeShotAnchorOverrides(
    anchorStrategy.per_character,
    item.characters || []
  );
  state.selectedShotId = item.id;
}

function cancelShotEdit() {
  inlineEditing.shotId = "";
  inlineEditing.shotSceneId = "";
  inlineEditing.shotInputMode = "reference_image";
  inlineEditing.shotGenerateAudio = true;
  inlineEditing.shotAspectRatio = "16:9";
  inlineEditing.shotResolution = "1080p";
  inlineEditing.shotGenerationCount = 1;
  inlineEditing.shotFirstFramePath = "";
  inlineEditing.shotLastFramePath = "";
  inlineEditing.shotReferenceImagesText = "";
  inlineEditing.shotSize = "medium";
  inlineEditing.shotMovement = "static";
  inlineEditing.shotDuration = 5;
  inlineEditing.shotLighting = "";
  inlineEditing.shotPalette = "";
  inlineEditing.shotCharacterIds = [];
  inlineEditing.shotStoryDescription = "";
  inlineEditing.shotStoryEmotion = "";
  inlineEditing.shotStoryBeat = "";
  inlineEditing.shotStoryDialogue = "";
  inlineEditing.shotStoryRawExcerpt = "";
  inlineEditing.shotAnchorMode = "auto";
  inlineEditing.shotAnchorOverrides = {};
}

function syncAssetCounts() {
  state.assets = {
    characters: state.characters.length,
    scenes: state.scenes.length,
    storyboards: state.storyboards.length,
    snapshots: state.snapshots.length,
    jobs: state.jobs.length
  };
}

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

function formatShotBatchCounts(batch) {
  const item = batch || {};
  const totalCount = Number(item.total_count || 0) || 0;
  const successCount = Number(item.success_count || 0) || 0;
  const failedCount = Number(item.failed_count || 0) || 0;
  const pendingCount = Number(item.pending_count || 0) || 0;
  const processingCount = Number(item.processing_count || 0) || 0;
  return `${successCount}/${totalCount} 成功 · ${failedCount} 失败 · ${pendingCount + processingCount} 待处理`;
}

function formatShotBatchProgress(batch) {
  const item = batch || {};
  const totalCount = Number(item.total_count || 0) || 0;
  const successCount = Number(item.success_count || 0) || 0;
  if (!totalCount) {
    return "0%";
  }
  return `${Math.round((successCount / totalCount) * 100)}%`;
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

function formatHealth(value) {
  return healthTextMap[value] || value || "未知";
}

function formatStatus(value) {
  return entityStatusTextMap[value] || value || "未设置";
}

function formatAnchorKey(value) {
  return anchorLabelMap[value] || value;
}

function formatShotSize(value) {
  return shotSizeOptions.find((item) => item.value === value)?.label || value || "未设置";
}

function formatShotMovement(value) {
  return shotMovementOptions.find((item) => item.value === value)?.label || value || "未设置";
}

function formatShotInputMode(value) {
  return shotInputModeOptions.find((item) => item.value === value)?.label || value || "未设置";
}

function normalizeShotAnchorMode(value) {
  return supportedShotAnchorModes.has(value) ? value : "auto";
}

function formatShotAnchorMode(value) {
  return shotAnchorModeOptions.find((item) => item.value === normalizeShotAnchorMode(value))?.label || "自动";
}

function normalizeShotAnchorOverrides(raw, characterIds = []) {
  const source = raw && typeof raw === "object" ? raw : {};
  const allowedIds = new Set((characterIds || []).filter(Boolean));
  const normalized = {};

  for (const characterId of allowedIds) {
    const mode = normalizeShotAnchorMode(source[characterId]);
    if (mode !== "auto") {
      normalized[characterId] = mode;
    }
  }

  return normalized;
}

function buildShotAnchorStrategyPayload(source, characterIds = []) {
  return {
    mode: normalizeShotAnchorMode(source.shotAnchorMode),
    per_character: normalizeShotAnchorOverrides(source.shotAnchorOverrides, characterIds)
  };
}

function getShotAnchorOverrideValue(source, characterId) {
  if (!characterId) {
    return "auto";
  }
  return normalizeShotAnchorMode(source.shotAnchorOverrides?.[characterId]);
}

function setShotAnchorOverrideValue(source, characterId, value) {
  if (!characterId) {
    return;
  }
  if (!source.shotAnchorOverrides || typeof source.shotAnchorOverrides !== "object") {
    source.shotAnchorOverrides = {};
  }
  const normalized = normalizeShotAnchorMode(value);
  if (normalized === "auto") {
    delete source.shotAnchorOverrides[characterId];
    return;
  }
  source.shotAnchorOverrides[characterId] = normalized;
}

function countShotAnchorOverrides(raw, characterIds = []) {
  return Object.keys(normalizeShotAnchorOverrides(raw, characterIds)).length;
}

function formatShotAnchorOverridesDisplay(anchorStrategy, characterIds = []) {
  const overrides = normalizeShotAnchorOverrides(anchorStrategy?.per_character, characterIds);
  return (characterIds || [])
    .filter((characterId) => overrides[characterId])
    .map((characterId) => {
      const name = state.characters.find((item) => item.id === characterId)?.name || characterId;
      return `${name}：${formatShotAnchorMode(overrides[characterId])}`;
    })
    .join("；");
}

function normalizeStoryboardProductionMode(value) {
  return storyboardProductionModeOptions.some((item) => item.value === value) ? value : "shot_pipeline";
}

function formatStoryboardProductionMode(value) {
  return (
    storyboardProductionModeOptions.find((item) => item.value === normalizeStoryboardProductionMode(value))?.label ||
    "分镜生产"
  );
}

function formatSnapshotSource(snapshot) {
  const source = snapshot || {};
  if (source.scene_id && !source.shot_id) {
    return `${source.storyboard_id || "未绑定分镜板"} · ${source.scene_id}`;
  }
  return `${source.storyboard_id || "未绑定分镜板"} · ${source.shot_id || "scene_direct"}`;
}

function formatShotAspectRatio(value) {
  return shotAspectRatioOptions.find((item) => item.value === value)?.label || value || "未设置";
}

function formatShotResolution(value) {
  return shotResolutionOptions.find((item) => item.value === value)?.label || value || "未设置";
}

function parseMediaPaths(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function serializeMediaPaths(values) {
  return Array.isArray(values) ? values.filter(Boolean).join("\n") : "";
}

function normalizeShotInputMode(value) {
  return supportedShotInputModes.has(value) ? value : "reference_image";
}

function isReferenceMode(value) {
  return normalizeShotInputMode(value) === "reference_image";
}

function isFirstLastFrameMode(value) {
  return normalizeShotInputMode(value) === "first_last_frame";
}

function isTextOnlyMode(value) {
  return normalizeShotInputMode(value) === "text_only";
}

function normalizeShotDuration(value) {
  return Math.max(1, Math.min(15, Number(value) || 5));
}

function normalizeShotGenerationCount(value) {
  return Math.max(1, Math.min(4, Number(value) || 1));
}

function getAutoReferenceSummary(characterIds, sceneId) {
  const normalizedCharacterIds = (characterIds || []).filter(Boolean);
  const characterCount = normalizedCharacterIds.length;
  const sceneCount = sceneId ? 1 : 0;
  const totalCount = characterCount + sceneCount;
  const characterNames = normalizedCharacterIds
    .map((characterId) => state.characters.find((item) => item.id === characterId)?.name || characterId)
    .filter(Boolean);
  const sceneName = state.scenes.find((item) => item.id === sceneId)?.name || sceneId || "";

  return {
    totalCount,
    characterCount,
    sceneCount,
    characterNames,
    sceneName
  };
}

function applyShotModeRules(source) {
  const mode = normalizeShotInputMode(source.shotInputMode);
  source.shotInputMode = mode;
  if (mode !== "first_last_frame") {
    source.shotFirstFramePath = "";
    source.shotLastFramePath = "";
  }
  source.shotReferenceImagesText = "";
}

function validateShotSource(source) {
  const mode = normalizeShotInputMode(source.shotInputMode);
  if (mode === "first_last_frame" && !String(source.shotFirstFramePath || "").trim()) {
    throw new Error("首尾帧生成模式下必须上传首帧图");
  }
}

function appendMediaPaths(currentValue, nextPaths) {
  return serializeMediaPaths([...new Set([...parseMediaPaths(currentValue), ...nextPaths.filter(Boolean)])]);
}

function getShotMediaEntries(source) {
  const entries = [];
  const firstFramePath = String(source.shotFirstFramePath || "").trim();
  const lastFramePath = String(source.shotLastFramePath || "").trim();
  const referenceImagePaths = parseMediaPaths(source.shotReferenceImagesText);

  if (firstFramePath) {
    entries.push({ key: `first-${firstFramePath}`, kind: "first_frame", label: "首帧", path: firstFramePath });
  }
  if (lastFramePath) {
    entries.push({ key: `last-${lastFramePath}`, kind: "last_frame", label: "尾帧", path: lastFramePath });
  }
  referenceImagePaths.forEach((path, index) => {
    entries.push({ key: `ref-${path}-${index}`, kind: "reference_image", label: `参考图 ${index + 1}`, path });
  });

  return entries;
}

function removeShotMediaEntry(source, kind, path = "") {
  if (kind === "first_frame") {
    source.shotFirstFramePath = "";
    return;
  }
  if (kind === "last_frame") {
    source.shotLastFramePath = "";
    return;
  }
  if (kind === "reference_image") {
    source.shotReferenceImagesText = serializeMediaPaths(
      parseMediaPaths(source.shotReferenceImagesText).filter((item) => item !== path)
    );
  }
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

function buildShotMediaPayload(source) {
  const mode = normalizeShotInputMode(source.shotInputMode);
  const generateAudio = Boolean(source.shotGenerateAudio);
  if (mode === "text_only" || mode === "reference_image") {
    return {
      mode,
      generate_audio: generateAudio,
      first_frame_path: "",
      last_frame_path: "",
      reference_image_paths: []
    };
  }
  return {
    mode,
    generate_audio: generateAudio,
    first_frame_path: String(source.shotFirstFramePath || "").trim(),
    last_frame_path: String(source.shotLastFramePath || "").trim(),
    reference_image_paths: []
  };
}

function formatSceneLabel(sceneId) {
  const scene = state.scenes.find((item) => item.id === sceneId);
  if (!scene) {
    return sceneId || "未关联场景";
  }
  return `${scene.name} · ${scene.id}`;
}

function formatShotKeyword(value, fallback = "未设置") {
  const normalized = String(value || "").trim();
  return normalized || fallback;
}

function formatPromptGenerationMode(value) {
  if (value === "ai_refined") {
    return "AI 润色";
  }
  if (value === "fallback_template") {
    return "模板回退";
  }
  return value || "未知";
}

function formatPromptVariantLabel(value) {
  if (value === "ai_refined") {
    return "AI 润色版";
  }
  if (value === "fallback_template") {
    return "本地模板版";
  }
  return value || "未知版本";
}

function formatProviderName(value) {
  if (!value || value === "manual") {
    return "手动占位";
  }
  if (value === "doubao-seedance-2-0") {
    return "Doubao Seedance 2.0";
  }
  return value;
}

function formatJobApiKind(provider) {
  const apiKind = String(provider?.api_kind || "").trim();
  if (apiKind === "ark_content_generation_tasks") {
    return "Seedance Tasks API";
  }
  const submitMode = String(provider?.submit_mode || "").trim();
  if (submitMode === "generic_http") {
    return "Seedance Tasks API";
  }
  if (!apiKind && !submitMode) {
    return "未设置";
  }
  return apiKind || submitMode;
}

function inferSeedanceModeFromContent(content) {
  const items = Array.isArray(content) ? content : [];
  const imageItems = items.filter((item) => item?.type === "image_url");
  if (!imageItems.length) {
    return "text_only";
  }
  if (imageItems.some((item) => item?.role === "first_frame" || item?.role === "last_frame")) {
    return "first_last_frame";
  }
  return "reference_image";
}

function formatSeedanceMode(value) {
  if (value === "reference_image") {
    return "参考生成";
  }
  if (value === "first_last_frame" || value === "first_frame") {
    return "首尾帧生成";
  }
  if (value === "text_only") {
    return "纯文字生成";
  }
  return value || "未识别";
}

function normalizeSeedanceRequestBodyForDisplay(job) {
  const provider = job?.provider || {};
  const submittedRequestBody =
    provider.submitted_request_body &&
      typeof provider.submitted_request_body === "object" &&
      Object.keys(provider.submitted_request_body).length
      ? provider.submitted_request_body
      : null;
  const requestBody = submittedRequestBody || provider.request_body || {};
  const rawContent = Array.isArray(requestBody.content) ? requestBody.content : [];

  const textItem =
    rawContent.find((item) => item?.type === "text" && String(item?.text || "").trim()) || null;
  const imageItemsFromContent = rawContent
    .filter((item) => item?.type === "image_url" && String(item?.image_url?.url || "").trim())
    .map((item) => ({
      type: "image_url",
      image_url: {
        url: item.image_url.url
      },
      ...(item.role ? { role: item.role } : {})
    }));

  const legacyImagePaths = Array.isArray(requestBody.reference_images)
    ? requestBody.reference_images.filter((item) => String(item || "").trim())
    : [];
  const legacyMediaItems = Array.isArray(requestBody.media_references)
    ? requestBody.media_references
      .filter((item) => item?.type === "image" && String(item?.path || "").trim())
      .map((item) => ({
        type: "image_url",
        image_url: {
          url: item.path
        },
        ...(item.role ? { role: item.role } : {})
      }))
    : [];
  const fallbackImageItems = (imageItemsFromContent.length ? imageItemsFromContent : legacyMediaItems.length ? legacyMediaItems : legacyImagePaths.map((path) => ({
    type: "image_url",
    image_url: {
      url: path
    }
  })));

  const normalizedContent = [];
  if (textItem) {
    normalizedContent.push({
      type: "text",
      text: textItem.text
    });
  } else if (String(requestBody.prompt || "").trim()) {
    normalizedContent.push({
      type: "text",
      text: requestBody.prompt
    });
  }
  normalizedContent.push(...fallbackImageItems);

  const normalized = {
    model: String(provider.model || requestBody.model || "doubao-seedance-2-0-260128").trim(),
    content: normalizedContent,
    ratio: String(requestBody.ratio || requestBody.aspect_ratio || "").trim(),
    resolution: String(requestBody.resolution || "").trim(),
    duration: Number(requestBody.duration ?? requestBody.duration_seconds ?? 0) || undefined,
    count: Number(requestBody.count ?? requestBody.generation_count ?? 1) || 1,
    generate_audio: Boolean(requestBody.generate_audio),
    watermark: Boolean(requestBody.watermark)
  };

  if (requestBody.return_last_frame || inferSeedanceModeFromContent(normalizedContent) === "first_last_frame") {
    normalized.return_last_frame = Boolean(requestBody.return_last_frame ?? true);
  }

  if (!normalized.ratio) {
    delete normalized.ratio;
  }
  if (!normalized.resolution) {
    delete normalized.resolution;
  }
  if (!normalized.duration) {
    delete normalized.duration;
  }

  return normalized;
}

function buildSeedanceRequestSummary(requestBody) {
  const content = Array.isArray(requestBody?.content) ? requestBody.content : [];
  const imageItems = content.filter((item) => item?.type === "image_url");
  const mode = inferSeedanceModeFromContent(content);
  return {
    mode,
    modeLabel: formatSeedanceMode(mode),
    imageCount: imageItems.length,
    hasAudio: Boolean(requestBody?.generate_audio),
    ratio: String(requestBody?.ratio || "").trim() || "未设置",
    resolution: String(requestBody?.resolution || "").trim() || "未设置",
    duration: Number(requestBody?.duration || 0) || 0,
    count: Number(requestBody?.count || 1) || 1,
    returnLastFrame: Boolean(requestBody?.return_last_frame)
  };
}

function getJobSeedanceSummary(job) {
  return buildSeedanceRequestSummary(normalizeSeedanceRequestBodyForDisplay(job));
}

function formatJobOutputSummary(job) {
  const summary = getJobSeedanceSummary(job);
  const durationText = summary.duration ? `${summary.duration} 秒` : "未设时长";
  return `${durationText} · ${summary.count} 条 · ${summary.hasAudio ? "有声" : "无声"}`;
}

function formatJobReferenceSummary(job) {
  const summary = getJobSeedanceSummary(job);
  if (summary.mode === "reference_image") {
    return `${summary.imageCount} 张参考图`;
  }
  if (summary.mode === "first_last_frame") {
    return `${summary.imageCount} 张首尾帧`;
  }
  return "无图像参考";
}

function formatReadableField(value, fallback = "暂无") {
  const normalized = String(value || "").trim();
  return normalized || fallback;
}

function getReadableSceneInfo(scene) {
  return scene?.readable || {};
}

function getReadableShotInfo(shot) {
  return shot?.readable || {};
}

function normalizeDialogueEntries(dialogues) {
  const items = Array.isArray(dialogues) ? dialogues : [];
  return items
    .map((item) => {
      if (typeof item === "string") {
        const raw = item.trim();
        if (!raw) {
          return null;
        }
        const parts = raw.split(/[:：]/, 2).map((part) => part.trim());
        if (parts.length === 2) {
          return { character: parts[0], text: parts[1] };
        }
        return { character: "", text: raw };
      }
      const character = String(item?.character || "").trim();
      const text = String(item?.text || "").trim();
      if (!character && !text) {
        return null;
      }
      return { character, text };
    })
    .filter(Boolean);
}

function formatDialogueEntries(dialogues) {
  return normalizeDialogueEntries(dialogues)
    .map((item) => {
      const character = String(item.character || "").trim();
      const text = String(item.text || "").trim();
      if (character && text) {
        return `${character}: ${text}`;
      }
      return text;
    })
    .filter(Boolean)
    .join(" / ");
}

function serializeDialogueEntries(dialogues) {
  return normalizeDialogueEntries(dialogues)
    .map((item) => {
      if (item.character && item.text) {
        return `${item.character}: ${item.text}`;
      }
      return item.text;
    })
    .filter(Boolean)
    .join("\n");
}

function parseDialogueText(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(/[:：]/, 2).map((part) => part.trim());
      if (parts.length === 2) {
        return { character: parts[0], text: parts[1] };
      }
      return { character: "", text: line };
    })
    .filter((item) => item.character || item.text);
}

function buildShotStoryPayload(source) {
  return {
    description: String(source.shotStoryDescription || "").trim(),
    emotion: String(source.shotStoryEmotion || "").trim(),
    beat: String(source.shotStoryBeat || "").trim(),
    raw_script_excerpt: String(source.shotStoryRawExcerpt || "").trim()
  };
}

function buildShotDialoguePayload(source) {
  return parseDialogueText(source.shotStoryDialogue);
}

function formatLegacyCameraSummary(camera) {
  const source = camera || {};
  const parts = [
    source.angle ? `机位角度：${source.angle}` : "",
    source.movement ? `运镜方式：${source.movement}` : "",
    source.shot_size ? `景别：${source.shot_size}` : ""
  ].filter(Boolean);
  return parts.join("；");
}

function normalizeMatchText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[.,/#!$%^&*;:{}=\-_`~()"'?<>[\]\\|，。！？；：、“”‘’（）【】《》·]/g, "");
}

function firstNonEmptyText(...values) {
  for (const value of values) {
    const text = String(value || "").trim();
    if (text) {
      return text;
    }
  }
  return "";
}

function getParsedShotDialogueEntries(shot) {
  return Array.isArray(shot?.dialogues)
    ? shot.dialogues
      .map((item) => ({
        character: String(item?.character || "").trim(),
        text: String(item?.text || "").trim()
      }))
      .filter((item) => item.character || item.text)
    : [];
}

function buildParsedShotDescription(scene, shot, sceneIndex, shotIndex) {
  const readableScene = getReadableSceneInfo(scene);
  const readableShot = getReadableShotInfo(shot);
  const sceneLocation = firstNonEmptyText(readableScene["场景地点"], scene?.location);
  const sceneTime = firstNonEmptyText(readableScene["时间"], scene?.time);
  const description = firstNonEmptyText(readableShot["画面描述"], shot?.description);
  const cameraSummary = firstNonEmptyText(
    readableShot["镜头信息"],
    shot?.camera?.summary,
    formatLegacyCameraSummary(shot?.camera)
  );
  const characterText = firstNonEmptyText(readableShot["出场角色"], (shot?.characters || []).join("、"));
  const dialogueText = formatDialogueEntries(getParsedShotDialogueEntries(shot));
  const emotionText = firstNonEmptyText(readableShot["情绪"], shot?.emotion);
  const beatText = firstNonEmptyText(readableShot["剧情节拍"], shot?.beat);
  const lines = [`场景 ${sceneIndex + 1} / 镜头 ${shotIndex + 1}`];

  if (sceneLocation || sceneTime) {
    lines.push(`场景：${[sceneLocation, sceneTime].filter(Boolean).join(" / ")}`);
  }
  if (description) {
    lines.push(`画面：${description}`);
  }
  if (cameraSummary) {
    lines.push(`镜头：${cameraSummary}`);
  }
  if (characterText) {
    lines.push(`角色：${characterText}`);
  }
  if (dialogueText) {
    lines.push(`对白：${dialogueText}`);
  }
  if (emotionText) {
    lines.push(`情绪：${emotionText}`);
  }
  if (beatText) {
    lines.push(`节拍：${beatText}`);
  }

  return lines.join("\n");
}

function serializeCharacterEntries(characters) {
  return Array.isArray(characters)
    ? characters
      .map((item) => String(item || "").trim())
      .filter(Boolean)
      .join("、")
    : "";
}

function parseCharacterText(value) {
  return String(value || "")
    .split(/\r?\n|[，,、]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildParsedCameraSummary(camera) {
  const source = camera || {};
  const parts = [
    source.angle ? `机位角度：${source.angle}` : "",
    source.movement ? `运镜方式：${source.movement}` : "",
    source.shot_size ? `景别：${source.shot_size}` : ""
  ].filter(Boolean);
  return parts.join("；");
}

function isEditingParsedShot(sceneIndex, shotIndex) {
  return parsedShotEditing.sceneIndex === sceneIndex && parsedShotEditing.shotIndex === shotIndex;
}

function isEditingParsedScene(sceneIndex) {
  return parsedSceneEditing.sceneIndex === sceneIndex;
}

function startParsedSceneEdit(scene, sceneIndex) {
  parsedSceneEditing.sceneIndex = sceneIndex;
  parsedSceneEditing.location = String(scene?.location || "").trim();
  parsedSceneEditing.time = String(scene?.time || "").trim();
  parsedSceneEditing.summary = String(scene?.summary || "").trim();
}

function cancelParsedSceneEdit() {
  parsedSceneEditing.sceneIndex = -1;
  parsedSceneEditing.location = "";
  parsedSceneEditing.time = "";
  parsedSceneEditing.summary = "";
}

function saveParsedSceneEdit(sceneIndex) {
  if (!parsedScriptObject.value) {
    setError("当前解析 JSON 无法编辑，请先修复结构。");
    return;
  }

  try {
    const parsed = JSON.parse(state.parsedScriptText || "{}");
    const targetScene = Array.isArray(parsed?.scenes) ? parsed.scenes[sceneIndex] : null;
    if (!targetScene) {
      throw new Error("未找到要修改的场景。");
    }

    targetScene.location = String(parsedSceneEditing.location || "").trim();
    targetScene.time = String(parsedSceneEditing.time || "").trim();
    targetScene.summary = String(parsedSceneEditing.summary || "").trim();

    const readable = {
      ...((targetScene.readable && typeof targetScene.readable === "object") ? targetScene.readable : {})
    };
    readable["场景地点"] = targetScene.location;
    readable["时间"] = targetScene.time;
    readable["场景摘要"] = targetScene.summary;
    readable["镜头数"] = Array.isArray(targetScene.shots) ? targetScene.shots.length : 0;
    targetScene.readable = readable;

    if (parsed.extracted_entities && Array.isArray(parsed.extracted_entities.scenes)) {
      parsed.extracted_entities.scenes = [...new Set(
        (parsed.scenes || [])
          .map((scene) => String(scene?.location || "").trim())
          .filter(Boolean)
      )];
    }

    state.parsedScriptText = JSON.stringify(parsed, null, 2);
    cancelParsedSceneEdit();
    setNotice(`场景 ${sceneIndex + 1} 已更新到解析 JSON，请记得点击“保存 JSON”。`);
  } catch (error) {
    setError(error);
  }
}

function startParsedShotEdit(scene, shot, sceneIndex, shotIndex) {
  parsedShotEditing.sceneIndex = sceneIndex;
  parsedShotEditing.shotIndex = shotIndex;
  parsedShotEditing.description = String(shot?.description || "").trim();
  parsedShotEditing.cameraAngle = String(shot?.camera?.angle || "").trim();
  parsedShotEditing.cameraMovement = String(shot?.camera?.movement || "").trim();
  parsedShotEditing.cameraShotSize = String(shot?.camera?.shot_size || "").trim();
  parsedShotEditing.charactersText = serializeCharacterEntries(shot?.characters || []);
  parsedShotEditing.dialoguesText = serializeDialogueEntries(getParsedShotDialogueEntries(shot));
  parsedShotEditing.emotion = String(shot?.emotion || "").trim();
  parsedShotEditing.beat = String(shot?.beat || "").trim();
}

function cancelParsedShotEdit() {
  parsedShotEditing.sceneIndex = -1;
  parsedShotEditing.shotIndex = -1;
  parsedShotEditing.description = "";
  parsedShotEditing.cameraAngle = "";
  parsedShotEditing.cameraMovement = "";
  parsedShotEditing.cameraShotSize = "";
  parsedShotEditing.charactersText = "";
  parsedShotEditing.dialoguesText = "";
  parsedShotEditing.emotion = "";
  parsedShotEditing.beat = "";
}

function saveParsedShotEdit(sceneIndex, shotIndex) {
  if (!parsedScriptObject.value) {
    setError("当前解析 JSON 无法编辑，请先修复结构。");
    return;
  }

  try {
    const parsed = JSON.parse(state.parsedScriptText || "{}");
    const targetScene = Array.isArray(parsed?.scenes) ? parsed.scenes[sceneIndex] : null;
    const targetShot = Array.isArray(targetScene?.shots) ? targetScene.shots[shotIndex] : null;
    if (!targetScene || !targetShot) {
      throw new Error("未找到要修改的分镜。");
    }

    const nextDialogues = parseDialogueText(parsedShotEditing.dialoguesText);
    const nextCharacters = parseCharacterText(parsedShotEditing.charactersText);
    const nextCamera = {
      ...(targetShot.camera || {}),
      angle: String(parsedShotEditing.cameraAngle || "").trim(),
      movement: String(parsedShotEditing.cameraMovement || "").trim(),
      shot_size: String(parsedShotEditing.cameraShotSize || "").trim(),
      summary: ""
    };

    targetShot.description = String(parsedShotEditing.description || "").trim();
    targetShot.camera = nextCamera;
    targetShot.dialogues = nextDialogues;
    targetShot.characters = nextCharacters;
    targetShot.emotion = String(parsedShotEditing.emotion || "").trim();
    targetShot.beat = String(parsedShotEditing.beat || "").trim();

    const readable = {
      ...((targetShot.readable && typeof targetShot.readable === "object") ? targetShot.readable : {})
    };
    readable["画面描述"] = targetShot.description;
    readable["镜头信息"] = buildParsedCameraSummary(nextCamera);
    readable["出场角色"] = serializeCharacterEntries(nextCharacters);
    readable["对白"] = formatDialogueEntries(nextDialogues);
    readable["情绪"] = targetShot.emotion;
    readable["剧情节拍"] = targetShot.beat;
    targetShot.readable = readable;

    targetShot.camera.summary = buildParsedCameraSummary(nextCamera);

    state.parsedScriptText = JSON.stringify(parsed, null, 2);
    cancelParsedShotEdit();
    setNotice(`镜头 ${shotIndex + 1} 已更新到解析 JSON，请记得点击“保存 JSON”。`);
  } catch (error) {
    setError(error);
  }
}

function buildParsedShotStoryPayload(shot) {
  const readableShot = getReadableShotInfo(shot);
  const description = firstNonEmptyText(readableShot["画面描述"], shot?.description);
  const emotion = firstNonEmptyText(readableShot["情绪"], shot?.emotion);
  const beat = firstNonEmptyText(readableShot["剧情节拍"], shot?.beat);
  const dialogueLines = normalizeDialogueEntries(getParsedShotDialogueEntries(shot))
    .map((item) => (item.character && item.text ? `${item.character}: ${item.text}` : item.text))
    .filter(Boolean);
  const rawScriptExcerpt = [description, ...dialogueLines].filter(Boolean).join("\n");

  return {
    description,
    emotion,
    beat,
    raw_script_excerpt: rawScriptExcerpt
  };
}

function getShotStoryValue(shot, fieldName) {
  return String(shot?.story?.[fieldName] || "").trim();
}

function getShotStoryDisplay(shot, fieldName, fallback = "暂无") {
  const storyValue = getShotStoryValue(shot, fieldName);
  if (storyValue) {
    return storyValue;
  }
  const scriptContext = shot?.prompt_package?.script_context || {};
  const scriptFieldMap = {
    description: "shot_description",
    emotion: "shot_emotion",
    beat: "shot_beat",
    raw_script_excerpt: "raw_script_excerpt"
  };
  const scriptValue = String(scriptContext[scriptFieldMap[fieldName]] || "").trim();
  return scriptValue || fallback;
}

async function copyTextToClipboard(text) {
  const content = String(text || "").trim();
  if (!content) {
    throw new Error("没有可复制的内容");
  }
  if (navigator?.clipboard?.writeText) {
    await navigator.clipboard.writeText(content);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = content;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

async function handleCopyReadableShot(scene, shot, sceneIndex, shotIndex) {
  try {
    await copyTextToClipboard(buildParsedShotDescription(scene, shot, sceneIndex, shotIndex));
    setNotice(`镜头 ${shotIndex + 1} 的分镜描述已复制`);
  } catch (error) {
    setError(error);
  }
}

function resolveParsedSceneId(scene) {
  const readableScene = getReadableSceneInfo(scene);
  const candidates = [
    readableScene["场景地点"],
    scene?.location,
    readableScene["场景摘要"],
    scene?.summary
  ]
    .map((item) => String(item || "").trim())
    .filter(Boolean);
  const normalizedCandidates = candidates.map((item) => normalizeMatchText(item)).filter(Boolean);

  if (!normalizedCandidates.length) {
    return state.selectedSceneId || state.scenes[0]?.id || "";
  }

  const exactMatch = state.scenes.find((item) => {
    const normalizedName = normalizeMatchText(item?.name);
    return normalizedName && normalizedCandidates.includes(normalizedName);
  });
  if (exactMatch) {
    return exactMatch.id;
  }

  const partialMatch = state.scenes.find((item) => {
    const normalizedName = normalizeMatchText(item?.name);
    return (
      normalizedName &&
      normalizedCandidates.some((candidate) => candidate.includes(normalizedName) || normalizedName.includes(candidate))
    );
  });
  if (partialMatch) {
    return partialMatch.id;
  }

  return state.selectedSceneId || (state.scenes.length === 1 ? state.scenes[0].id : "");
}

function resolveParsedCharacterIds(shot) {
  const sourceNames = [
    ...(Array.isArray(shot?.characters) ? shot.characters : []),
    ...getParsedShotDialogueEntries(shot).map((item) => item.character)
  ]
    .map((item) => String(item || "").trim())
    .filter(Boolean);
  const uniqueNames = [...new Set(sourceNames)];
  const matchedIds = [];
  const unmatchedNames = [];

  uniqueNames.forEach((name) => {
    const normalizedName = normalizeMatchText(name);
    const matchedCharacter = state.characters.find((item) => normalizeMatchText(item?.name) === normalizedName);
    if (matchedCharacter) {
      matchedIds.push(matchedCharacter.id);
    } else {
      unmatchedNames.push(name);
    }
  });

  return {
    matchedIds: [...new Set(matchedIds)],
    unmatchedNames
  };
}

function mapParsedShotSize(value) {
  const text = String(value || "").trim();
  if (!text) {
    return forms.shotSize;
  }
  if (text.includes("特写")) {
    return "extreme_closeup";
  }
  if (text.includes("近景")) {
    return "closeup";
  }
  if (text.includes("中")) {
    return "medium";
  }
  if (text.includes("全景") || text.includes("远景")) {
    return "wide";
  }
  return forms.shotSize;
}

function mapParsedShotMovement(value) {
  const text = String(value || "").trim();
  if (!text) {
    return forms.shotMovement;
  }
  if (text.includes("推")) {
    return "push_in";
  }
  if (text.includes("拉")) {
    return "pull_out";
  }
  if (text.includes("摇")) {
    return "pan";
  }
  if (text.includes("跟")) {
    return "tracking";
  }
  if (text.includes("固定") || text.includes("静")) {
    return "static";
  }
  return forms.shotMovement;
}

function mapParsedCameraAngle(value) {
  const text = String(value || "").trim();
  if (!text) {
    return "eye_level";
  }
  if (text.includes("顶")) {
    return "top_down";
  }
  if (text.includes("俯")) {
    return "high_angle";
  }
  if (text.includes("仰")) {
    return "low_angle";
  }
  return "eye_level";
}

function buildImportedShotMedia() {
  return {
    mode: normalizeShotInputMode(forms.shotInputMode),
    generate_audio: Boolean(forms.shotGenerateAudio),
    first_frame_path: "",
    last_frame_path: "",
    reference_image_paths: []
  };
}

function getSceneDirectSceneId() {
  return String(forms.shotSceneId || state.selectedSceneId || "").trim();
}

function buildSceneDirectPayload() {
  return {
    characters: [...state.selectedCharacterIds],
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
  };
}

async function handleImportReadableShot(scene, shot, sceneIndex, shotIndex) {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择一个分镜板，再导入镜头卡草稿");
    return;
  }

  loading.importParsedShot = true;
  try {
    const result = await importReadableShotDraft(scene, shot, sceneIndex, shotIndex);
    await loadProductionData(state.selectedSeriesSlug);
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId, result.item.id);
    state.selectedSceneId = result.sceneId;
    state.selectedShotId = result.item.id;
    setNotice(
      `已导入镜头卡草稿：${result.item.id}${result.unmatchedNames.length ? `，未匹配角色：${result.unmatchedNames.join("、")}` : ""}`
    );
  } catch (error) {
    setError(error);
  } finally {
    loading.importParsedShot = false;
  }
}

async function importReadableShotDraft(scene, shot, sceneIndex, shotIndex) {
  const sceneId = resolveParsedSceneId(scene);
  if (!sceneId) {
    throw new Error("未匹配到可用场景，请先创建或选择对应场景");
  }

  const { matchedIds, unmatchedNames } = resolveParsedCharacterIds(shot);
  const dialogues = getParsedShotDialogueEntries(shot);
  const story = buildParsedShotStoryPayload(shot);
  const shotCamera = shot?.camera || {};
  const episodeId = String(
    parsedScriptObject.value?.episode_id || selectedStoryboard.value?.episode_id || state.selectedEpisodeId || ""
  ).trim();

  const response = await createShot(state.selectedSeriesSlug, state.selectedStoryboardId, {
    scene_id: sceneId,
    shot_payload: {
      characters: matchedIds,
      script_source: {
        episode_id: episodeId,
        scene_index: sceneIndex + 1,
        shot_index: shotIndex + 1
      },
      story,
      dialogue: dialogues,
      media: buildImportedShotMedia(),
      visual: {
        aspect_ratio: forms.shotAspectRatio,
        style: "cinematic realism",
        resolution: forms.shotResolution,
        generation_count: normalizeShotGenerationCount(forms.shotGenerationCount),
        shot_size: mapParsedShotSize(shotCamera.shot_size),
        camera_angle: mapParsedCameraAngle(shotCamera.angle),
        camera_movement: mapParsedShotMovement(shotCamera.movement),
        lens: "50mm",
        depth_of_field: "medium",
        lighting: forms.shotLighting.trim(),
        palette: forms.shotPalette.trim(),
        duration_seconds: normalizeShotDuration(forms.shotDuration)
      },
      status: "draft"
    }
  });

  return {
    item: response.item,
    sceneId,
    unmatchedNames
  };
}

async function handleImportAllReadableShots() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
    setError("请先选择一个分镜板，再导入镜头卡草稿");
    return;
  }

  const shotEntries = [];
  for (const [sceneIndex, scene] of (parsedScriptReadableScenes.value || []).entries()) {
    for (const [shotIndex, shot] of (scene?.shots || []).entries()) {
      shotEntries.push({ scene, shot, sceneIndex, shotIndex });
    }
  }

  if (!shotEntries.length) {
    setError("当前可读视图里没有可导入的镜头");
    return;
  }

  loading.importParsedShot = true;
  try {
    const importedIds = [];
    const unmatchedNotes = [];
    const failedNotes = [];
    let lastSceneId = "";

    for (const entry of shotEntries) {
      try {
        const result = await importReadableShotDraft(entry.scene, entry.shot, entry.sceneIndex, entry.shotIndex);
        importedIds.push(result.item.id);
        lastSceneId = result.sceneId || lastSceneId;
        if (result.unmatchedNames.length) {
          unmatchedNotes.push(`镜头${entry.shotIndex + 1} 未匹配角色：${result.unmatchedNames.join("、")}`);
        }
      } catch (error) {
        failedNotes.push(
          `场景${entry.sceneIndex + 1}/镜头${entry.shotIndex + 1}：${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    if (!importedIds.length) {
      throw new Error(failedNotes.join("；") || "全部导入失败");
    }

    await loadProductionData(state.selectedSeriesSlug);
    await loadShotsForStoryboard(
      state.selectedSeriesSlug,
      state.selectedStoryboardId,
      importedIds[importedIds.length - 1]
    );
    if (lastSceneId) {
      state.selectedSceneId = lastSceneId;
    }
    state.selectedShotId = importedIds[importedIds.length - 1];

    const noticeParts = [`已批量导入 ${importedIds.length} 个镜头卡草稿`];
    if (failedNotes.length) {
      noticeParts.push(`失败 ${failedNotes.length} 个`);
    }
    if (unmatchedNotes.length) {
      noticeParts.push(unmatchedNotes.slice(0, 2).join("；"));
    }
    setNotice(noticeParts.join("，"));
    state.error = failedNotes.join("\n");
  } catch (error) {
    setError(error);
  } finally {
    loading.importParsedShot = false;
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

onMounted(boot);
</script>

<template>
  <main class="shell">
    <section class="masthead">
      <div>
        <p class="eyebrow">AI 视频工作流</p>
        <h1>本地生产工作台</h1>
        <p class="lead">
          全链路只使用本地文件，不依赖数据库。剧本、角色、场景、分镜、快照和任务数据都直接保存在
          `output/` 目录。
        </p>
      </div>

      <div class="status-panel ">
        <div class="status-chip">
          <span class="status-dot" :class="health"></span>
          <strong>后端服务</strong>
          <span>{{ formatHealth(health) }}</span>
        </div>
        <p class="status-copy">
          角色和场景参考图会直接写入本地目录，前端回显也读取同一份本地数据源。
        </p>
      </div>
    </section>

    <section class="workspace">
      <aside class="column column-left">
        <section v-loading="seriesListPanelLoading" element-loading-text="系列列表加载中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.2)" class="panel ">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">工作区</p>
              <h2>选择系列</h2>
            </div>
          </div>

          <div class="list-stack">
            <div v-for="item in state.series" :key="item.slug" class="list-card"
              :class="{ active: item.slug === state.selectedSeriesSlug }">
              <div class="item-body" @click="state.selectedSeriesSlug = item.slug">
                <template v-if="isEditingSeries(item.slug)">
                  <div class="item-editor">
                    <el-input v-model="inlineEditing.seriesName" class="field" type="text" placeholder="输入系列名称" />
                    <el-input v-model="inlineEditing.seriesDescription" class="field-textarea compact" type="textarea"
                      resize="vertical" placeholder="输入系列简介" />
                  </div>
                </template>
                <template v-else>
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.slug }}</span>
                  <small>{{ item.description || "暂无简介" }}</small>
                </template>
              </div>
              <div class="item-actions">
                <el-button v-if="isEditingSeries(item.slug)" class="action-button dark compact-button"
                  :disabled="loading.updateSeries" @click.stop="handleUpdateSeries(item)">
                  {{ loading.updateSeries ? "保存中..." : "保存" }}
                </el-button>
                <el-button v-else class="action-button ghost compact-button" @click.stop="startSeriesEdit(item)">
                  编辑
                </el-button>
                <el-button v-if="isEditingSeries(item.slug)" class="action-button ghost compact-button"
                  @click.stop="cancelSeriesEdit">
                  取消
                </el-button>
                <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteSeries"
                  @click.stop="handleDeleteSeries(item)">
                  {{ loading.deleteSeries ? "删除中..." : "删除" }}
                </el-button>
              </div>
            </div>

            <div v-if="!state.series.length && !loading.series" class="empty-state">
              还没有系列，先创建一个吧。
            </div>
          </div>
        </section>
        <section v-loading="seriesCreatePanelLoading" element-loading-text="系列创建中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.16)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">系列</p>
              <h2>系列库</h2>
            </div>
            <span class="pill">共：{{ state.series.length }}</span>
          </div>

          <div class="form-stack">
            <el-input v-model="forms.seriesName" class="field" type="text" placeholder="输入系列名称" />
            <el-input v-model="forms.seriesDescription" class="field-textarea compact" type="textarea" resize="vertical"
              placeholder="输入系列简介" />
            <el-button class="action-button warm" :disabled="loading.createSeries" @click="handleCreateSeries">
              {{ loading.createSeries ? "创建中..." : "新建系列" }}
            </el-button>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">反馈</p>
              <h2>状态面板</h2>
            </div>
          </div>

          <p v-if="state.notice" class="message success">{{ state.notice }}</p>
          <p v-else class="message muted">操作结果和流程提醒会显示在这里。</p>
          <p v-if="state.error" class="message error">{{ state.error }}</p>

          <div class="meta-list">
            <div>
              <span>系列</span>
              <strong>{{ selectedSeries?.name || "暂无" }}</strong>
            </div>
            <div>
              <span>剧集</span>
              <strong>{{ selectedEpisode?.name || "暂无" }}</strong>
            </div>
            <div>
              <span>分镜板</span>
              <strong>{{ selectedStoryboard?.id || "暂无" }}</strong>
            </div>
            <div>
              <span>生产模式</span>
              <strong>{{ formatStoryboardProductionMode(selectedStoryboardProductionMode) }}</strong>
            </div>
            <div>
              <span>输出根目录</span>
              <strong>output/</strong>
            </div>
          </div>
        </section>
      </aside>

      <section class="column column-main">
        <section class="panel hero-panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">当前系列</p>
              <h2>{{ selectedSeries?.name || "尚未选择系列" }}</h2>
            </div>
            <span v-if="selectedSeries" class="series-slug">{{ selectedSeries.slug }}</span>
          </div>

          <div class="summary-grid">
            <article class="summary-card">
              <span>角色</span>
              <strong>{{ state.assets.characters }}</strong>
            </article>
            <article class="summary-card">
              <span>场景</span>
              <strong>{{ state.assets.scenes }}</strong>
            </article>
            <article class="summary-card">
              <span>分镜板</span>
              <strong>{{ state.assets.storyboards }}</strong>
            </article>
            <article class="summary-card">
              <span>任务</span>
              <strong>{{ state.assets.jobs }}</strong>
            </article>
          </div>
        </section>

        <section v-loading="episodesPanelLoading" element-loading-text="剧集面板加载中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">剧集</p>
              <h2>剧本与结构化拆解</h2>
            </div>
            <div class="inline-actions" style="flex-shrink: 0;display: flex;gap: 12px;">
              <el-input v-model="forms.episodeName" class="field inline-field" type="text" placeholder="输入剧集名称" />
              <el-button class="action-button dark" style="flex-shrink: 0;" :disabled="loading.createEpisode"
                @click="handleCreateEpisode">
                {{ loading.createEpisode ? "创建中..." : "新建剧集" }}
              </el-button>
            </div>
          </div>

          <div class="episode-strip">
            <div v-for="item in state.episodes" :key="item.id" class="episode-chip"
              :class="{ active: item.id === state.selectedEpisodeId }">
              <div class="item-body" style="flex: 1;" @click="state.selectedEpisodeId = item.id">
                <template v-if="isEditingEpisode(item.id)">
                  <el-input v-model="inlineEditing.episodeName" class="field item-inline-field" type="text"
                    placeholder="输入剧集名称" />
                </template>
                <template v-else>
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.id }}</span>
                </template>
              </div>
              <div class="item-actions">
                <el-button v-if="isEditingEpisode(item.id)" class="action-button dark compact-button"
                  :disabled="loading.updateEpisode" @click.stop="handleUpdateEpisode(item)">
                  {{ loading.updateEpisode ? "保存中..." : "保存" }}
                </el-button>
                <el-button v-else class="action-button ghost compact-button" @click.stop="startEpisodeEdit(item)">
                  编辑
                </el-button>
                <el-button v-if="isEditingEpisode(item.id)" class="action-button ghost compact-button"
                  @click.stop="cancelEpisodeEdit">
                  取消
                </el-button>
                <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteEpisode"
                  @click.stop="handleDeleteEpisode(item)">
                  {{ loading.deleteEpisode ? "删除中..." : "删除" }}
                </el-button>
              </div>
            </div>
          </div>
        </section>

        <section class="editor-grid">
          <article v-loading="rawScriptPanelLoading" element-loading-text="剧本处理中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.18)" class="panel editor-panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">原始剧本</p>
                <h2>剧本输入区</h2>
              </div>
              <div class="inline-actions compact-actions" style="flex-shrink: 0;display: flex;gap: 12px;">
                <el-button class="action-button ghost" :disabled="loading.analyzeScript" @click="handleAnalyzeScript">
                  {{ loading.analyzeScript ? "分析中..." : "AI 拆解剧本" }}
                </el-button>
                <el-button class="action-button dark" :disabled="loading.saveRaw" @click="handleSaveRawScript">
                  {{ loading.saveRaw ? "保存中..." : "保存原稿" }}
                </el-button>
              </div>
            </div>
            <el-input v-model="state.rawScript" class="field-textarea editor-textarea" type="textarea"
              :autosize="{ minRows: 22, maxRows: 30 }" resize="auto" placeholder="在这里粘贴或编写原始剧本内容。" />
          </article>

          <article v-loading="parsedScriptPanelLoading" element-loading-text="解析结果处理中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.18)" class="panel editor-panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">结构化结果</p>
                <h2>解析 JSON</h2>
              </div>
              <div class="inline-actions compact-actions" style="flex-shrink: 0;display: flex;gap: 12px;">
                <el-radio-group v-model="parsedScriptViewMode" text-color="#fff" fill="var(--ui-accent-soft)"
                  class="view-switch">
                  <el-radio-button label="raw">原生结构</el-radio-button>
                  <el-radio-button label="readable">可读视图</el-radio-button>
                </el-radio-group>
                <el-button class="action-button dark" :disabled="loading.saveParsed" @click="handleSaveParsedScript">
                  {{ loading.saveParsed ? "保存中..." : "保存 JSON" }}
                </el-button>
              </div>
            </div>
            <template v-if="parsedScriptViewMode === 'raw'">
              <el-input v-model="state.parsedScriptText" class="field-textarea editor-textarea code-textarea"
                type="textarea" :autosize="{ minRows: 22, maxRows: 30 }" resize="auto" placeholder="" />
            </template>
            <template v-else>
              <div v-if="parsedScriptObject" class="readable-script-view">
                <div v-if="parsedScriptReadableOutline" class="meta-panel">
                  <div class="meta-row">
                    <span>剧集标题</span>
                    <strong>{{ formatReadableField(parsedScriptReadableOutline["剧集标题"]) }}</strong>
                  </div>
                  <div class="meta-row">
                    <span>场景总数</span>
                    <strong>{{ parsedScriptReadableOutline["场景总数"] ?? 0 }}</strong>
                  </div>
                  <div class="meta-row meta-row-wide">
                    <span>角色总览</span>
                    <strong>{{ (parsedScriptReadableOutline["角色总览"] || []).join("、") || "暂无" }}</strong>
                  </div>
                </div>


                <div v-if="parsedScriptReadableScenes.length" class="form-stack">
                  <div v-for="(scene, sceneIndex) in parsedScriptReadableScenes"
                    :key="scene.scene_id || scene.readable?.['场景编号']" class="meta-panel">
                    <template v-if="isEditingParsedScene(sceneIndex)">
                      <div class="script-scene-editor" style="grid-column: 1 / -1; ">
                        <div class="meta-row">
                          <span>场景编号</span>
                          <strong>{{ getReadableSceneInfo(scene)["场景编号"] ?? scene.scene_id ?? "暂无" }}</strong>
                        </div>
                        <div class="split-grid">
                          <el-input v-model="parsedSceneEditing.location" class="field" type="text"
                            placeholder="场景地点" />
                          <el-input v-model="parsedSceneEditing.time" class="field" type="text" placeholder="时间" />
                        </div>
                        <div class="meta-row">
                          <span>镜头数</span>
                          <strong>{{ getReadableSceneInfo(scene)["镜头数"] ?? (scene.shots || []).length }}</strong>
                        </div>
                        <el-input v-model="parsedSceneEditing.summary" class="field-textarea compact" type="textarea"
                          :autosize="{ minRows: 2, maxRows: 4 }" placeholder="场景摘要" />
                        <div class="script-scene-actions">
                          <el-button class="action-button dark compact-button"
                            @click.stop="saveParsedSceneEdit(sceneIndex)">
                            保存场景
                          </el-button>
                          <el-button class="action-button ghost compact-button" @click.stop="cancelParsedSceneEdit">
                            取消
                          </el-button>
                        </div>
                      </div>
                    </template>
                    <template v-else>
                      <div class="meta-row">
                        <span>场景编号</span>
                        <strong>{{ getReadableSceneInfo(scene)["场景编号"] ?? scene.scene_id ?? "暂无" }}</strong>
                      </div>
                      <div class="meta-row">
                        <span>场景地点</span>
                        <strong>{{ formatReadableField(getReadableSceneInfo(scene)["场景地点"] || scene.location) }}</strong>
                      </div>
                      <div class="meta-row">
                        <span>时间</span>
                        <strong>{{ formatReadableField(getReadableSceneInfo(scene)["时间"] || scene.time) }}</strong>
                      </div>
                      <div class="meta-row">
                        <span>镜头数</span>
                        <strong>{{ getReadableSceneInfo(scene)["镜头数"] ?? (scene.shots || []).length }}</strong>
                      </div>
                      <div class="meta-row meta-row-wide">
                        <span>场景摘要</span>
                        <strong>{{ formatReadableField(getReadableSceneInfo(scene)["场景摘要"] || scene.summary) }}</strong>
                      </div>
                      <div class="script-scene-actions">
                        <el-button class="action-button ghost compact-button"
                          @click.stop="startParsedSceneEdit(scene, sceneIndex)">
                          修改场景
                        </el-button>
                      </div>
                    </template>

                    <div v-if="(scene.shots || []).length" class="mini-list" style="grid-column: 1 / -1; ">
                      <div v-for="(shot, shotIndex) in scene.shots || []"
                        :key="`${scene.scene_id || 'scene'}-${shot.shot_id || getReadableShotInfo(shot)['镜头编号']}`"
                        class="mini-card">
                        <div class="item-body">
                          <template v-if="isEditingParsedShot(sceneIndex, shotIndex)">
                            <div class="script-shot-editor">
                              <strong>镜头 {{ getReadableShotInfo(shot)["镜头编号"] ?? shot.shot_id ?? "?" }}</strong>
                              <el-input v-model="parsedShotEditing.description" class="field-textarea compact"
                                type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="画面描述" />
                              <div class="split-grid">
                                <el-input v-model="parsedShotEditing.cameraAngle" class="field" type="text"
                                  placeholder="机位角度" />
                                <el-input v-model="parsedShotEditing.cameraMovement" class="field" type="text"
                                  placeholder="运镜方式" />
                              </div>
                              <el-input v-model="parsedShotEditing.cameraShotSize" class="field" type="text"
                                placeholder="景别" />
                              <el-input v-model="parsedShotEditing.charactersText" class="field" type="text"
                                placeholder="角色，多个角色用 顿号 / 逗号 分隔" />
                              <el-input v-model="parsedShotEditing.dialoguesText" class="field-textarea compact"
                                type="textarea" :autosize="{ minRows: 2, maxRows: 5 }"
                                placeholder="对白，一行一句，例如：乌萨奇: 小八小八，别睡啦！" />
                              <div class="split-grid">
                                <el-input v-model="parsedShotEditing.emotion" class="field" type="text"
                                  placeholder="情绪" />
                                <el-input v-model="parsedShotEditing.beat" class="field" type="text"
                                  placeholder="剧情节拍" />
                              </div>
                              <div class="script-shot-actions">
                                <el-button class="action-button dark compact-button"
                                  @click.stop="saveParsedShotEdit(sceneIndex, shotIndex)">
                                  保存修改
                                </el-button>
                                <el-button class="action-button ghost compact-button"
                                  @click.stop="cancelParsedShotEdit">
                                  取消
                                </el-button>
                                <el-button class="action-button dark compact-button"
                                  :disabled="loading.importParsedShot || !state.selectedStoryboardId"
                                  @click.stop="handleImportReadableShot(scene, shot, sceneIndex, shotIndex)">
                                  {{ loading.importParsedShot ? "导入中..." : "导入为镜头卡草稿" }}
                                </el-button>
                              </div>
                            </div>
                          </template>
                          <template v-else>
                            <strong>镜头 {{ getReadableShotInfo(shot)["镜头编号"] ?? shot.shot_id ?? "?" }}</strong>
                            <small>{{ formatReadableField(getReadableShotInfo(shot)["画面描述"] || shot.description) }}</small>
                            <small>{{ formatReadableField(getReadableShotInfo(shot)["镜头信息"] || shot.camera?.summary || formatLegacyCameraSummary(shot.camera)) }}</small>
                            <small>角色：{{ formatReadableField(getReadableShotInfo(shot)["出场角色"] || (shot.characters ||
                              []).join("、")) }}</small>
                            <small>对白：{{ formatReadableField(getReadableShotInfo(shot)["对白"] ||
                              formatDialogueEntries(shot.dialogues)) }}</small>
                            <small>情绪 / 节拍：{{ formatReadableField(getReadableShotInfo(shot)["情绪"] || shot.emotion) }} ·
                              {{ formatReadableField(getReadableShotInfo(shot)["剧情节拍"] || shot.beat) }}</small>
                            <div class="script-shot-actions">
                              <el-button class="action-button ghost compact-button"
                                @click.stop="startParsedShotEdit(scene, shot, sceneIndex, shotIndex)">
                                修改分镜
                              </el-button>
                              <el-button class="action-button dark compact-button"
                                :disabled="loading.importParsedShot || !state.selectedStoryboardId"
                                @click.stop="handleImportReadableShot(scene, shot, sceneIndex, shotIndex)">
                                {{ loading.importParsedShot ? "导入中..." : "导入为镜头卡草稿" }}
                              </el-button>
                            </div>
                          </template>
                        </div>
                      </div>
                    </div>

                    <div style="grid-column: 1 / -1; ">


                      <el-button class="action-button warm" style="width: 100%;"
                        :disabled="loading.importParsedShot || !state.selectedStoryboardId || !parsedScriptReadableScenes.length"
                        @click="handleImportAllReadableShots">
                        {{ loading.importParsedShot ? "导入中..." : "全部导入为镜头卡草稿" }}
                      </el-button>
                    </div>

                  </div>
                </div>

                <div v-else class="empty-state">当前解析结果还没有场景内容。</div>
              </div>
              <div v-else class="empty-state">当前 JSON 不是合法格式，无法切换到可读视图。</div>
            </template>
          </article>
        </section>

        <section class="studio-grid">
          <article v-loading="characterCreatePanelLoading" element-loading-text="角色列表处理中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">角色</p>
                <h2>角色创建</h2>
              </div>
            </div>

            <div class="form-stack">
              <el-input v-model="forms.characterName" class="field" type="text" placeholder="输入角色名称" />
              <el-input v-model="forms.characterBrief" class="field-textarea compact" type="textarea" resize="vertical"
                placeholder="输入角色简介、身份、性格等描述" />
              <p class="inline-note">
                支持两种入口：先用文字描述创建角色；如果是固定角色，也可以在创建后上传官图或参考图，再进行生成。
              </p>
              <el-button class="action-button warm" :disabled="loading.createCharacter" @click="handleCreateCharacter"
                style="margin-bottom: 12px;">
                {{ loading.createCharacter ? "创建中..." : "新建角色" }}
              </el-button>
            </div>

            <div class="mini-list">
              <div v-for="item in state.characters" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedCharacterId }">
                <div class="item-body" @click="state.selectedCharacterId = item.id">
                  <template v-if="isEditingCharacter(item.id)">
                    <div class="item-editor">
                      <el-input v-model="inlineEditing.characterName" class="field" type="text" placeholder="输入角色名称" />
                      <el-input v-model="inlineEditing.characterBrief" class="field-textarea compact" type="textarea"
                        :autosize="{ minRows: 5, maxRows: 15 }" resize="vertical" placeholder="输入角色简介、身份、性格等描述" />
                    </div>
                  </template>
                  <template v-else>
                    <strong>{{ item.name }}</strong>
                    <span>{{ item.id }}</span>
                    <small>{{ formatStatus(item.status) }}</small>
                    <small>{{ item.brief || "暂无角色简介" }}</small>
                  </template>
                </div>
                <div class="item-actions">
                  <el-button v-if="isEditingCharacter(item.id)" class="action-button dark compact-button"
                    :disabled="loading.updateCharacter" @click.stop="handleUpdateCharacter(item)">
                    {{ loading.updateCharacter ? "保存中..." : "保存" }}
                  </el-button>
                  <el-button v-else class="action-button ghost compact-button" @click.stop="startCharacterEdit(item)">
                    编辑
                  </el-button>
                  <el-button v-if="isEditingCharacter(item.id)" class="action-button ghost compact-button"
                    @click.stop="cancelCharacterEdit">
                    取消
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteCharacter"
                    @click.stop="handleDeleteCharacter(item)">
                    {{ loading.deleteCharacter ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
            </div>
          </article>

          <article v-loading="sceneCreatePanelLoading" element-loading-text="场景列表处理中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">场景</p>
                <h2>场景创建</h2>
              </div>
            </div>

            <div class="form-stack">
              <el-input v-model="forms.sceneName" class="field" type="text" placeholder="输入场景名称" />
              <el-input v-model="forms.sceneDescription" class="field-textarea compact" type="textarea"
                resize="vertical" placeholder="输入场景环境、氛围、时代、空间信息" />

              <el-button class="action-button warm" :disabled="loading.createScene" @click="handleCreateScene"
                style="margin-bottom: 12px;">
                {{ loading.createScene ? "创建中..." : "新建场景" }}
              </el-button>
            </div>

            <div class="mini-list">
              <div v-for="item in state.scenes" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedSceneId }">
                <div class="item-body" @click="state.selectedSceneId = item.id">
                  <template v-if="isEditingScene(item.id)">
                    <div class="item-editor">
                      <el-input v-model="inlineEditing.sceneName" class="field" type="text" placeholder="输入场景名称" />
                      <el-input v-model="inlineEditing.sceneDescription" class="field-textarea compact" type="textarea"
                        resize="vertical" placeholder="输入场景环境、氛围、时代、空间信息" />
                    </div>
                  </template>
                  <template v-else>
                    <strong>{{ item.name }}</strong>
                    <span>{{ item.id }}</span>
                    <small>{{ formatStatus(item.status) }}</small>
                    <small>{{ item.description || "暂无场景描述" }}</small>
                  </template>
                </div>
                <div class="item-actions">
                  <el-button v-if="isEditingScene(item.id)" class="action-button dark compact-button"
                    :disabled="loading.updateScene" @click.stop="handleUpdateScene(item)">
                    {{ loading.updateScene ? "保存中..." : "保存" }}
                  </el-button>
                  <el-button v-else class="action-button ghost compact-button" @click.stop="startSceneEdit(item)">
                    编辑
                  </el-button>
                  <el-button v-if="isEditingScene(item.id)" class="action-button ghost compact-button"
                    @click.stop="cancelSceneEdit">
                    取消
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteScene"
                    @click.stop="handleDeleteScene(item)">
                    {{ loading.deleteScene ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section class="lab-grid">
          <article v-loading="characterLabPanelLoading" element-loading-text="角色素材处理中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">角色工坊</p>
                <h2>角色圣经</h2>
              </div>
              <div class="inline-actions" style="flex-shrink: 0;display: flex;gap: 12px;">
                <el-button class="action-button warm" :disabled="loading.characterAssets || !selectedCharacter"
                  @click="handleGenerateCharacterAssets('reference_plus_text')">
                  {{ loading.characterAssets ? "生成中..." : (hasUploadedCharacterSourceImages ? "参考图+文字生成" : "按文字生成角色圣经") }}
                </el-button>
                <el-button v-if="hasUploadedCharacterSourceImages" class="action-button dark"
                  :disabled="loading.characterAssets || !selectedCharacter"
                  @click="handleGenerateCharacterAssets('reference_subject_only')">
                  {{ loading.characterAssets ? "生成中..." : "仅按参考图生成拼图" }}
                </el-button>
              </div>
            </div>

            <div v-if="selectedCharacter" class="lab-stack">
              <div class="focus-card">
                <span>当前角色</span>
                <strong>{{ selectedCharacter.name }}</strong>
                <small>{{ selectedCharacter.id }} · {{ formatStatus(selectedCharacter.status) }}</small>
              </div>

              <div class="upload-panel">
                <div>
                  <strong>上传角色参考图</strong>
                  <p class="upload-copy">
                    适用于固定角色。上传后，角色生成会优先参考你提供的图片，而不是只靠文字描述。
                  </p>
                  <p class="upload-copy">
                    你可以选择两种生成方式：`参考图+文字生成` 会结合当前角色描述；`仅按参考图生成拼图` 会把上传图作为唯一主体来源，只生成三视图和特征分解拼图。
                  </p>
                </div>
                <input ref="characterSourceInput" class="hidden-file-input" type="file" accept="image/*" multiple
                  @change="handleCharacterSourceFileChange" />
                <div class="upload-actions">
                  <el-button class="action-button ghost" @click="characterSourceInput?.click()">
                    选择参考图
                  </el-button>
                  <span
                    class="upload-count">{{ characterSourceFiles.length ? `已选 ${characterSourceFiles.length} 张` : "未选择文件" }}</span>
                </div>
                <el-button class="action-button dark"
                  :disabled="loading.characterUpload || !characterSourceFiles.length"
                  @click="handleUploadCharacterSourceImages">
                  {{ loading.characterUpload ? "上传中..." : "上传参考图" }}
                </el-button>
              </div>

              <div v-if="selectedCharacterSourceEntries.length" class="reference-grid">
                <div v-for="image in selectedCharacterSourceEntries" :key="image.key" class="reference-card">
                  <div class="reference-header">
                    <strong>上传参考</strong>
                    <small>{{ image.label }}</small>
                  </div>
                  <el-button class="action-button ghost danger compact-button"
                    :disabled="loading.deleteCharacterSourceImage"
                    @click="handleDeleteCharacterSourceImage(image.path)">
                    {{ loading.deleteCharacterSourceImage ? "删除中..." : "删除参考图" }}
                  </el-button>
                  <el-image class="preview-image" :src="assetUrl(image.path)"
                    :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                    preview-teleported />
                </div>
              </div>

              <div class="anchor-grid">
                <article v-for="([key, value]) in selectedCharacterAnchorEntries" :key="key" class="anchor-card">
                  <span>{{ formatAnchorKey(key) }}</span>
                  <strong>{{ value || "待生成" }}</strong>
                </article>
              </div>

              <div class="reference-grid">
                <div v-for="image in selectedCharacterImageEntries" :key="image.key"
                  class="reference-card reference-card-large" style="grid-column: span 2;">
                  <div class="reference-header">
                    <strong>{{ image.label }}</strong>
                    <small>{{ image.path || "尚未生成" }}</small>
                  </div>
                  <el-image v-if="image.path" class="preview-image preview-image-large" :src="assetUrl(image.path)"
                    :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="contain"
                    preview-teleported />
                  <div v-else class="reference-empty">待生成</div>
                </div>
              </div>

              <div v-if="state.selectedCharacterBible" class="meta-panel">
                <div class="meta-row">
                  <span>角色概述</span>
                  <strong>{{ state.selectedCharacterBible.summary || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>核心身份</span>
                  <strong>{{ state.selectedCharacterBible.bible?.core_identity || "暂无" }}</strong>
                </div>
              </div>
            </div>

            <div v-else class="empty-state">选择一个角色后，可上传角色参考图并生成单张角色圣经拼图。</div>
          </article>

          <article v-loading="sceneLabPanelLoading" element-loading-text="场景素材处理中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">场景工坊</p>
                <h2>场景包</h2>
              </div>
              <el-button class="action-button warm" :disabled="loading.sceneAssets || !selectedScene"
                @click="handleGenerateSceneAssets">
                {{ loading.sceneAssets ? "生成中..." : "生成场景参考拼图" }}
              </el-button>
            </div>

            <div v-if="selectedScene" class="lab-stack">
              <div class="focus-card">
                <span>当前场景</span>
                <strong>{{ selectedScene.name }}</strong>
                <small>{{ selectedScene.id }} · {{ formatStatus(selectedScene.status) }}</small>
              </div>

              <div class="reference-grid">
                <div v-for="image in selectedSceneImageEntries" :key="image.key" class="reference-card">
                  <div class="reference-header">
                    <strong>{{ image.label }}</strong>
                    <small>{{ image.path || "尚未生成" }}</small>
                  </div>
                  <el-image v-if="image.path" class="preview-image" :src="assetUrl(image.path)"
                    :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                    preview-teleported />
                  <div v-else class="reference-empty">待生成</div>
                </div>
              </div>

              <div v-if="state.selectedScenePackage" class="meta-panel">
                <div class="meta-row">
                  <span>场景概述</span>
                  <strong>{{ state.selectedScenePackage.summary || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>光线</span>
                  <strong>{{ state.selectedScenePackage.visual_profile?.lighting || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>色调</span>
                  <strong>{{ state.selectedScenePackage.visual_profile?.palette || "暂无" }}</strong>
                </div>
              </div>
            </div>

            <div v-else class="empty-state">选择一个场景后可查看场景包和单张场景参考拼图。</div>
          </article>
        </section>
      </section>

      <aside class="column column-right">
        <section v-loading="storyboardConfigPanelLoading" element-loading-text="分镜配置处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">分镜</p>
              <h2>镜头配置</h2>
            </div>
            <el-button class="action-button dark" :disabled="loading.createStoryboard" @click="handleCreateStoryboard">
              {{ loading.createStoryboard ? "创建中..." : "新建分镜板" }}
            </el-button>
          </div>

          <div class="mini-list">
            <div v-for="item in filteredStoryboards" :key="item.id" class="mini-card selectable" style="display: flex;"
              :class="{ active: item.id === state.selectedStoryboardId }">
              <div class="item-body" @click="state.selectedStoryboardId = item.id">
                <strong>{{ item.id }}</strong>
                <span>{{ item.episode_id }}</span>
                <small>{{ formatStoryboardProductionMode(item.production_mode) }}</small>
                <small>{{ item.shot_ids.length }} 个镜头</small>
              </div>
              <div class="item-actions">
                <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteStoryboard"
                  @click.stop="handleDeleteStoryboard(item)">
                  {{ loading.deleteStoryboard ? "删除中..." : "删除" }}
                </el-button>
              </div>
            </div>
          </div>

          <div v-if="selectedStoryboard" v-loading="storyboardDetailLoading" element-loading-text="分镜板详情加载中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.16)" class="subsection storyboard-detail-section">
            <div class="panel-header sub-panel-header">
              <div>
                <p class="panel-kicker">生产模式</p>
                <h3>{{ formatStoryboardProductionMode(selectedStoryboardProductionMode) }}</h3>
              </div>
              <el-radio-group :model-value="selectedStoryboardProductionMode" class="view-switch storyboard-mode-switch"
                @update:model-value="handleChangeStoryboardProductionMode" text-color="#fff"
                fill="var(--ui-accent-soft)" style="display: flex;">
                <el-radio-button v-for="item in storyboardProductionModeOptions" :key="item.value" :label="item.value">
                  {{ item.label }}
                </el-radio-button>
              </el-radio-group>
            </div>
            <p class="inline-note">
              {{ selectedStoryboardProductionMode === "shot_pipeline"
                ? "分镜生产模式以单镜头为最小生成单元：一张镜头卡对应一份镜头包与一条 Seedance 任务草稿，适合稳定生产与后期拼接。"
                : "场景直出模式以整段场景为最小生成单元：不创建单镜头卡，后续会围绕场景摘要、节拍与参考设定一次生成整段视频。" }}
            </p>
          </div>

          <template v-if="selectedStoryboardProductionMode === 'shot_pipeline'">
            <div class="subsection">
              <h3>新建镜头</h3>
              <div class="form-stack">
                <el-select v-model="forms.shotSceneId" class="field-select" placeholder="选择关联场景" clearable>
                  <el-option v-for="item in state.scenes" :key="item.id" :label="`${item.name} · ${item.id}`"
                    :value="item.id" />
                </el-select>

                <el-select v-model="forms.shotInputMode" class="field-select" placeholder="选择 Seedance 输入模式">
                  <el-option v-for="item in shotInputModeOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>

                <div class="split-grid">
                  <el-select v-model="forms.shotAspectRatio" class="field-select" placeholder="视频比例">
                    <el-option v-for="item in shotAspectRatioOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                  <el-select v-model="forms.shotResolution" class="field-select" placeholder="分辨率">
                    <el-option v-for="item in shotResolutionOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                </div>

                <div class="split-grid">
                  <el-input-number v-model="forms.shotDuration" class="field-number" :min="1" :max="15" :step="1">
                    <template #suffix>
                      <span>秒</span>
                    </template>
                  </el-input-number>
                  <el-select v-model="forms.shotGenerationCount" class="field-select" placeholder="生成数量">
                    <el-option v-for="item in shotGenerationCountOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                </div>
                <div class="split-grid">
                  <el-checkbox v-model="forms.shotGenerateAudio">需要声音</el-checkbox>
                </div>
                <div v-if="isReferenceMode(forms.shotInputMode)" class="shot-media-panel">
                  <div class="shot-media-header">
                    <div>
                      <strong>参考生成</strong>
                      <p class="upload-copy">将自动注入角色圣经拼图与场景参考拼图，不需要上传首尾帧。</p>
                    </div>
                    <small>{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).totalCount }}
                      张系统参考</small>
                  </div>
                  <div class="meta-list compact-meta-list">
                    <div>
                      <span>角色圣经拼图</span>
                      <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).characterCount }}</strong>
                    </div>
                    <div>
                      <span>场景参考拼图</span>
                      <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).sceneCount }}</strong>
                    </div>
                    <div>
                      <span>角色匹配</span>
                      <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).characterNames.join("、") || "未选角色" }}</strong>
                    </div>
                    <div>
                      <span>场景匹配</span>
                      <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).sceneName || "未选场景" }}</strong>
                    </div>
                  </div>
                </div>

                <div v-else-if="isFirstLastFrameMode(forms.shotInputMode)" class="shot-media-panel">
                  <div class="shot-media-header">
                    <div>
                      <strong>首尾帧生成</strong>
                      <p class="upload-copy">首帧必传，尾帧可选。本模式不会注入角色圣经拼图和场景参考拼图。</p>
                    </div>
                    <small>{{ getShotMediaEntries(forms).length }} 张图片</small>
                  </div>

                  <div class="shot-media-grid">
                    <label class="shot-upload-tile">
                      <span class="shot-upload-chip">首帧</span>
                      <strong>上传首帧图</strong>
                      <small>必传，用于确定开场画面</small>
                      <input class="shot-upload-input" type="file" accept="image/*"
                        @change="handleShotMediaUpload(forms, 'first_frame', $event)" />
                    </label>

                    <label class="shot-upload-tile">
                      <span class="shot-upload-chip">尾帧</span>
                      <strong>上传尾帧图</strong>
                      <small>可选，用于约束结尾状态</small>
                      <input class="shot-upload-input" type="file" accept="image/*"
                        @change="handleShotMediaUpload(forms, 'last_frame', $event)" />
                    </label>
                  </div>

                  <div v-if="getShotMediaEntries(forms).length" class="reference-grid shot-media-preview-grid">
                    <div v-for="image in getShotMediaEntries(forms)" :key="image.key"
                      class="reference-card shot-media-card">
                      <div class="reference-header">
                        <strong>{{ image.label }}</strong>
                        <small>{{ image.path }}</small>
                      </div>
                      <el-button class="action-button ghost danger compact-button" :disabled="loading.shotMediaUpload"
                        @click="removeShotMediaEntry(forms, image.kind, image.path)">
                        移除
                      </el-button>
                      <el-image class="preview-image" :src="assetUrl(image.path)"
                        :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                        preview-teleported />
                    </div>
                  </div>
                </div>

                <div class="split-grid">
                  <el-select v-model="forms.shotSize" class="field-select" placeholder="镜头景别">
                    <el-option v-for="item in shotSizeOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>

                  <el-select v-model="forms.shotMovement" class="field-select" placeholder="运镜方式">
                    <el-option v-for="item in shotMovementOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                </div>

                <div class="split-grid">
                  <el-input v-model="forms.shotLighting" class="field" type="text" placeholder="输入光线关键词" />
                  <el-input v-model="forms.shotPalette" class="field" type="text" placeholder="输入色调关键词" />
                </div>

                <div class="story-binding-panel">
                  <div class="story-binding-header">
                    <strong>剧情绑定</strong>
                    <small>镜头卡自身保存剧情描述、对白与原文摘录，镜头包组装优先使用这里。</small>
                  </div>
                  <el-input v-model="forms.shotStoryDescription" class="field-textarea compact" type="textarea"
                    :autosize="{ minRows: 2, maxRows: 4 }" placeholder="剧情描述：这个镜头里具体拍什么" />
                  <div class="split-grid">
                    <el-input v-model="forms.shotStoryEmotion" class="field" type="text" placeholder="情绪基调" />
                    <el-input v-model="forms.shotStoryBeat" class="field" type="text" placeholder="剧情节拍 / 动作节点" />
                  </div>
                  <el-input v-model="forms.shotStoryDialogue" class="field-textarea compact" type="textarea"
                    :autosize="{ minRows: 2, maxRows: 5 }" placeholder="对白，一行一句，例如：乌萨奇: 小八小八，别睡啦！" />
                  <el-input v-model="forms.shotStoryRawExcerpt" class="field-textarea compact" type="textarea"
                    :autosize="{ minRows: 2, maxRows: 6 }" placeholder="剧本原文摘录，可直接粘贴当前镜头对应的原始剧本片段" />
                </div>

                <div class="story-binding-panel">
                  <div class="story-binding-header">
                    <strong>角色锚点策略</strong>
                    <small>默认自动按景别抽取角色锚点；如有必要，可对当前镜头里的单个角色单独覆盖。</small>
                  </div>
                  <el-select v-model="forms.shotAnchorMode" class="field-select" placeholder="选择默认锚点策略">
                    <el-option v-for="option in shotAnchorModeOptions" :key="option.value" :label="option.label"
                      :value="option.value" />
                  </el-select>
                  <div v-if="state.selectedCharacterIds.length" class="form-stack compact-stack">
                    <div v-for="characterId in state.selectedCharacterIds" :key="`create-anchor-${characterId}`"
                      class="split-grid">
                      <div class="inline-label">
                        {{state.characters.find((item) => item.id === characterId)?.name || characterId}}
                      </div>
                      <el-select :model-value="getShotAnchorOverrideValue(forms, characterId)" class="field-select"
                        placeholder="跟随默认策略"
                        @update:model-value="setShotAnchorOverrideValue(forms, characterId, $event)">
                        <el-option v-for="option in shotAnchorModeOptions" :key="option.value" :label="option.label"
                          :value="option.value" />
                      </el-select>
                    </div>
                  </div>
                </div>

                <el-checkbox-group v-model="state.selectedCharacterIds" class="check-grid">
                  <el-checkbox v-for="item in state.characters" :key="item.id" :value="item.id" class="check-card">
                    {{ item.name }}
                  </el-checkbox>
                </el-checkbox-group>

                <el-button class="action-button warm primary-action" :disabled="loading.createShot"
                  @click="handleCreateShot">
                  {{ loading.createShot ? "创建中..." : "生成镜头卡" }}
                </el-button>
              </div>
            </div>

            <div class="mini-list">
              <h3>导入的静头卡最好编辑一下，因为时间之类的都是默认的</h3>
              <div class="subsection-header">
                <div class="inline-actions compact-actions">
                  <el-button class="action-button ghost compact-button" @click="selectAllShotsForBatch">
                    全选批次
                  </el-button>
                  <el-button class="action-button ghost compact-button" @click="clearShotSelection">
                    清空勾选
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.clearShots"
                    @click="handleClearShots">
                    {{ loading.clearShots ? "清空中..." : "清空镜头卡" }}
                  </el-button>
                </div>
              </div>
              <div v-for="item in state.shots" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedShotId }">
                <div class="item-body" @click="state.selectedShotId = item.id">
                  <template v-if="isEditingShot(item.id)">
                    <div class="item-editor">
                      <el-select v-model="inlineEditing.shotSceneId" class="field-select" placeholder="选择关联场景">
                        <el-option v-for="scene in state.scenes" :key="scene.id" :label="`${scene.name} · ${scene.id}`"
                          :value="scene.id" />
                      </el-select>
                      <el-select v-model="inlineEditing.shotInputMode" class="field-select"
                        placeholder="选择 Seedance 输入模式">
                        <el-option v-for="option in shotInputModeOptions" :key="option.value" :label="option.label"
                          :value="option.value" />
                      </el-select>
                      <div class="split-grid">
                        <el-select v-model="inlineEditing.shotAspectRatio" class="field-select" placeholder="视频比例">
                          <el-option v-for="option in shotAspectRatioOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                        <el-select v-model="inlineEditing.shotResolution" class="field-select" placeholder="分辨率">
                          <el-option v-for="option in shotResolutionOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                      </div>
                      <div class="split-grid">
                        <el-input-number v-model="inlineEditing.shotDuration" class="field-number" :min="1" :max="15"
                          :step="1">
                          <template #suffix>
                            <span>秒</span>
                          </template>
                        </el-input-number>
                        <el-select v-model="inlineEditing.shotGenerationCount" class="field-select" placeholder="生成数量">
                          <el-option v-for="option in shotGenerationCountOptions" :key="option.value"
                            :label="option.label" :value="option.value" />
                        </el-select>
                      </div>
                      <el-checkbox v-model="inlineEditing.shotGenerateAudio">需要声音</el-checkbox>
                      <div v-if="isReferenceMode(inlineEditing.shotInputMode)"
                        class="shot-media-panel inline-shot-media-panel">
                        <div class="shot-media-header">
                          <div>
                            <strong>参考生成</strong>
                            <p class="upload-copy">将自动注入角色圣经拼图与场景参考拼图，不展示首尾帧上传。</p>
                          </div>
                          <small>{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).totalCount }}
                            张系统参考</small>
                        </div>
                        <div class="meta-list compact-meta-list">
                          <div>
                            <span>角色圣经拼图</span>
                            <strong>{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).characterCount }}</strong>
                          </div>
                          <div>
                            <span>场景参考拼图</span>
                            <strong>{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).sceneCount }}</strong>
                          </div>
                          <div>
                            <span>角色匹配</span>
                            <strong>{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).characterNames.join("、") || "未选角色" }}</strong>
                          </div>
                          <div>
                            <span>场景匹配</span>
                            <strong>{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).sceneName || "未选场景" }}</strong>
                          </div>
                        </div>
                      </div>
                      <div v-else-if="isFirstLastFrameMode(inlineEditing.shotInputMode)"
                        class="shot-media-panel inline-shot-media-panel">
                        <div class="shot-media-header">
                          <div>
                            <strong>首尾帧生成</strong>
                            <p class="upload-copy">首帧必传，尾帧可选。本模式不会注入角色圣经拼图和场景参考拼图。</p>
                          </div>
                          <small>{{ getShotMediaEntries(inlineEditing).length }} 张图片</small>
                        </div>

                        <div class="shot-media-grid">
                          <label class="shot-upload-tile">
                            <span class="shot-upload-chip">首帧</span>
                            <strong>替换首帧图</strong>
                            <small>必传，用于确定开场画面</small>
                            <input class="shot-upload-input" type="file" accept="image/*"
                              @change="handleShotMediaUpload(inlineEditing, 'first_frame', $event)" />
                          </label>

                          <label class="shot-upload-tile">
                            <span class="shot-upload-chip">尾帧</span>
                            <strong>替换尾帧图</strong>
                            <small>可选，用于约束结尾状态</small>
                            <input class="shot-upload-input" type="file" accept="image/*"
                              @change="handleShotMediaUpload(inlineEditing, 'last_frame', $event)" />
                          </label>
                        </div>

                        <div v-if="getShotMediaEntries(inlineEditing).length"
                          class="reference-grid shot-media-preview-grid">
                          <div v-for="image in getShotMediaEntries(inlineEditing)" :key="image.key"
                            class="reference-card shot-media-card">
                            <div class="reference-header">
                              <strong>{{ image.label }}</strong>
                              <small>{{ image.path }}</small>
                            </div>
                            <el-button class="action-button ghost danger compact-button"
                              :disabled="loading.shotMediaUpload"
                              @click="removeShotMediaEntry(inlineEditing, image.kind, image.path)">
                              移除
                            </el-button>
                            <el-image class="preview-image" :src="assetUrl(image.path)"
                              :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                              preview-teleported />
                          </div>
                        </div>
                      </div>
                      <div class="split-grid">
                        <el-select v-model="inlineEditing.shotSize" class="field-select" placeholder="镜头景别">
                          <el-option v-for="option in shotSizeOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                        <el-select v-model="inlineEditing.shotMovement" class="field-select" placeholder="运镜方式">
                          <el-option v-for="option in shotMovementOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                      </div>
                      <div class="split-grid">
                        <el-input v-model="inlineEditing.shotLighting" class="field" type="text"
                          placeholder="输入光线关键词" />
                        <el-input v-model="inlineEditing.shotPalette" class="field" type="text" placeholder="输入色调关键词" />
                      </div>
                      <div class="story-binding-panel">
                        <div class="story-binding-header">
                          <strong>剧情绑定</strong>
                          <small>这里的描述、对白、摘录会直接参与镜头包组装。</small>
                        </div>
                        <el-input v-model="inlineEditing.shotStoryDescription" class="field-textarea compact"
                          type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="剧情描述：这个镜头里具体拍什么" />
                        <div class="split-grid">
                          <el-input v-model="inlineEditing.shotStoryEmotion" class="field" type="text"
                            placeholder="情绪基调" />
                          <el-input v-model="inlineEditing.shotStoryBeat" class="field" type="text"
                            placeholder="剧情节拍 / 动作节点" />
                        </div>
                        <el-input v-model="inlineEditing.shotStoryDialogue" class="field-textarea compact"
                          type="textarea" :autosize="{ minRows: 2, maxRows: 5 }"
                          placeholder="对白，一行一句，例如：乌萨奇: 小八小八，别睡啦！" />
                        <el-input v-model="inlineEditing.shotStoryRawExcerpt" class="field-textarea compact"
                          type="textarea" :autosize="{ minRows: 2, maxRows: 6 }"
                          placeholder="剧本原文摘录，可直接粘贴当前镜头对应的原始剧本片段" />
                      </div>
                      <div class="story-binding-panel">
                        <div class="story-binding-header">
                          <strong>角色锚点策略</strong>
                          <small>先用全局策略控制当前镜头，再按角色做局部覆盖。</small>
                        </div>
                        <el-select v-model="inlineEditing.shotAnchorMode" class="field-select" placeholder="选择默认锚点策略">
                          <el-option v-for="option in shotAnchorModeOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                        <div v-if="inlineEditing.shotCharacterIds.length" class="form-stack compact-stack">
                          <div v-for="characterId in inlineEditing.shotCharacterIds" :key="`edit-anchor-${characterId}`"
                            class="split-grid">
                            <div class="inline-label">
                              {{state.characters.find((item) => item.id === characterId)?.name || characterId}}
                            </div>
                            <el-select :model-value="getShotAnchorOverrideValue(inlineEditing, characterId)"
                              class="field-select" placeholder="跟随默认策略"
                              @update:model-value="setShotAnchorOverrideValue(inlineEditing, characterId, $event)">
                              <el-option v-for="option in shotAnchorModeOptions" :key="option.value"
                                :label="option.label" :value="option.value" />
                            </el-select>
                          </div>
                        </div>
                      </div>
                      <el-checkbox-group v-model="inlineEditing.shotCharacterIds" class="check-grid">
                        <el-checkbox v-for="character in state.characters" :key="character.id" :value="character.id"
                          class="check-card">
                          {{ character.name }}
                        </el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </template>
                  <template v-else>
                    <strong>{{ item.id }}</strong>
                    <small>{{ getShotStoryDisplay(item, "description") }}</small>
                    <small>对白：{{ formatDialogueEntries(item.dialogue) || "暂无" }}</small>
                    <small>情绪 / 节拍：{{ getShotStoryDisplay(item, "emotion") }} ·
                      {{ getShotStoryDisplay(item, "beat") }}</small>
                    <span>{{ formatShotInputMode(item.media?.mode) }}</span>
                    <small>锚点：{{ formatShotAnchorMode(item.anchor_strategy?.mode) }}<template
                        v-if="countShotAnchorOverrides(item.anchor_strategy?.per_character, item.characters)"> · {{
                          countShotAnchorOverrides(item.anchor_strategy?.per_character, item.characters) }}
                        个角色覆盖</template></small>
                    <span>{{ formatShotAspectRatio(item.visual.aspect_ratio) }} ·
                      {{ formatShotResolution(item.visual.resolution) }}</span>
                    <span>{{ formatShotSize(item.visual.shot_size) }} ·
                      {{ formatShotMovement(item.visual.camera_movement) }}</span>
                    <small>场景：{{ formatSceneLabel(item.scene_id) }}</small>
                    <small>输出：{{ item.visual.duration_seconds }} 秒 · {{ item.visual.generation_count || 1 }} 条 ·
                      {{ item.media?.generate_audio ? "有声" : "无声" }}</small>
                    <small>光线：{{ formatShotKeyword(item.visual.lighting) }} · 色调：{{
                      formatShotKeyword(item.visual.palette)
                    }}</small>
                    <small>参考：{{ isReferenceMode(item.media?.mode) ? "角色圣经拼图 + 场景参考拼图" :
                      isFirstLastFrameMode(item.media?.mode) ? "首帧/尾帧" : "纯文字" }}</small>
                    <small>{{ (item.characters || []).length }} 个角色</small>
                  </template>
                </div>
                <div class="item-actions">
                  <el-button v-if="!isEditingShot(item.id)" class="action-button compact-button"
                    :class="isShotSelectedForBatch(item.id) ? 'warm' : 'ghost'"
                    @click.stop="toggleShotSelection(item.id)">
                    {{ isShotSelectedForBatch(item.id) ? "已选入批次" : "选入批次" }}
                  </el-button>
                  <el-button v-if="isEditingShot(item.id)" class="action-button dark compact-button"
                    :disabled="loading.updateShot" @click.stop="handleUpdateShot(item)">
                    {{ loading.updateShot ? "保存中..." : "保存" }}
                  </el-button>
                  <el-button v-else class="action-button ghost compact-button" @click.stop="startShotEdit(item)">
                    编辑
                  </el-button>
                  <el-button v-if="isEditingShot(item.id)" class="action-button ghost compact-button"
                    @click.stop="cancelShotEdit">
                    取消
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteShot"
                    @click.stop="handleDeleteShot(item)">
                    {{ loading.deleteShot ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
            </div>
          </template>

          <div v-else class="subsection">
            <h3>场景直出配置</h3>
            <div class="form-stack">
              <el-select v-model="forms.shotSceneId" class="field-select" placeholder="选择要直出的场景" clearable>
                <el-option v-for="item in state.scenes" :key="item.id" :label="`${item.name} · ${item.id}`"
                  :value="item.id" />
              </el-select>

              <el-select v-model="forms.shotInputMode" class="field-select" placeholder="选择 Seedance 输入模式">
                <el-option v-for="item in shotInputModeOptions" :key="item.value" :label="item.label"
                  :value="item.value" />
              </el-select>

              <div class="split-grid">
                <el-select v-model="forms.shotAspectRatio" class="field-select" placeholder="视频比例">
                  <el-option v-for="item in shotAspectRatioOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
                <el-select v-model="forms.shotResolution" class="field-select" placeholder="分辨率">
                  <el-option v-for="item in shotResolutionOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
              </div>

              <div class="split-grid">
                <el-input-number v-model="forms.shotDuration" class="field-number" :min="1" :max="15" :step="1">
                  <template #suffix>
                    <span>秒</span>
                  </template>
                </el-input-number>
                <el-select v-model="forms.shotGenerationCount" class="field-select" placeholder="生成数量">
                  <el-option v-for="item in shotGenerationCountOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
              </div>

              <el-checkbox v-model="forms.shotGenerateAudio">需要声音</el-checkbox>

              <div v-if="isReferenceMode(forms.shotInputMode)" class="shot-media-panel">
                <div class="shot-media-header">
                  <div>
                    <strong>参考生成</strong>
                    <p class="upload-copy">自动注入角色圣经拼图与场景参考拼图，用于整段场景视频的角色和空间稳定。</p>
                  </div>
                  <small>{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).totalCount }}
                    张系统参考</small>
                </div>
                <div class="meta-list compact-meta-list">
                  <div>
                    <span>角色圣经拼图</span>
                    <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).characterCount }}</strong>
                  </div>
                  <div>
                    <span>场景参考拼图</span>
                    <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).sceneCount }}</strong>
                  </div>
                  <div>
                    <span>角色匹配</span>
                    <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).characterNames.join("、") || "未选角色" }}</strong>
                  </div>
                  <div>
                    <span>场景匹配</span>
                    <strong>{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).sceneName || "未选场景" }}</strong>
                  </div>
                </div>
              </div>

              <div v-else-if="isFirstLastFrameMode(forms.shotInputMode)" class="shot-media-panel">
                <div class="shot-media-header">
                  <div>
                    <strong>首尾帧生成</strong>
                    <p class="upload-copy">首帧必传，尾帧可选。场景直出时会围绕首尾帧完成整段剧情过程。</p>
                  </div>
                  <small>{{ getShotMediaEntries(forms).length }} 张图片</small>
                </div>

                <div class="shot-media-grid">
                  <label class="shot-upload-tile">
                    <span class="shot-upload-chip">首帧</span>
                    <strong>上传首帧图</strong>
                    <small>必传，用于定义开场画面</small>
                    <input class="shot-upload-input" type="file" accept="image/*"
                      @change="handleShotMediaUpload(forms, 'first_frame', $event)" />
                  </label>

                  <label class="shot-upload-tile">
                    <span class="shot-upload-chip">尾帧</span>
                    <strong>上传尾帧图</strong>
                    <small>可选，用于约束结尾状态</small>
                    <input class="shot-upload-input" type="file" accept="image/*"
                      @change="handleShotMediaUpload(forms, 'last_frame', $event)" />
                  </label>
                </div>

                <div v-if="getShotMediaEntries(forms).length" class="reference-grid shot-media-preview-grid">
                  <div v-for="image in getShotMediaEntries(forms)" :key="image.key"
                    class="reference-card shot-media-card">
                    <div class="reference-header">
                      <strong>{{ image.label }}</strong>
                      <small>{{ image.path }}</small>
                    </div>
                    <el-button class="action-button ghost danger compact-button" :disabled="loading.shotMediaUpload"
                      @click="removeShotMediaEntry(forms, image.kind, image.path)">
                      移除
                    </el-button>
                    <el-image class="preview-image" :src="assetUrl(image.path)"
                      :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                      preview-teleported />
                  </div>
                </div>
              </div>

              <div class="split-grid">
                <el-select v-model="forms.shotSize" class="field-select" placeholder="主镜头景别">
                  <el-option v-for="item in shotSizeOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>

                <el-select v-model="forms.shotMovement" class="field-select" placeholder="主运镜方式">
                  <el-option v-for="item in shotMovementOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
              </div>

              <div class="split-grid">
                <el-input v-model="forms.shotLighting" class="field" type="text" placeholder="输入光线关键词" />
                <el-input v-model="forms.shotPalette" class="field" type="text" placeholder="输入色调关键词" />
              </div>

              <el-checkbox-group v-model="state.selectedCharacterIds" class="check-grid">
                <el-checkbox v-for="item in state.characters" :key="item.id" :value="item.id" class="check-card">
                  {{ item.name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
        </section>

      </aside>

      <aside class="column column-execution">
        <section v-loading="executionPanelLoading" element-loading-text="执行区处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">执行区</p>
              <h2>快照与任务</h2>
            </div>
          </div>

          <p class="message muted">
            {{ selectedStoryboardProductionMode === "shot_pipeline"
              ? "已接入 Doubao Seedance 2.0 任务草稿生成。当前可先完成镜头包组装、快照落盘和 Seedance 请求体预览，再按配置提交远端任务。"
              : "当前处于场景直出模式。这里会承接后续的场景级组包、快照与任务提交，不再以单镜头为单位推进。" }}
          </p>

          <div class="execution-flow">
            <div class="flow-card"
              :class="{ active: selectedStoryboardProductionMode === 'shot_pipeline' ? !!selectedShotPromptPackage?.positive : !!selectedSceneDirectPackage?.positive }">
              <span class="flow-step">01</span>
              <strong>{{ selectedStoryboardProductionMode === "shot_pipeline" ? "镜头包" : "场景包" }}</strong>
              <small>
                {{ selectedStoryboardProductionMode === "shot_pipeline"
                  ? "先把镜头卡、剧情、参考素材和参数组装成可生成包。"
                  : "先把场景摘要、节拍、参考素材和参数组装成场景级生成包。" }}
              </small>
              <em>{{ (selectedStoryboardProductionMode === "shot_pipeline" ? selectedShotPromptPackage?.positive : selectedSceneDirectPackage?.positive) ? "已生成" : "待生成" }}</em>
            </div>

            <div class="flow-card" :class="{ active: !!state.selectedSnapshotId || !!state.snapshots.length }">
              <span class="flow-step">02</span>
              <strong>快照</strong>
              <small>把当前组装结果和已解析素材固化成一次可追踪的本地快照。</small>
              <em>{{ state.snapshots.length ? `${state.snapshots.length} 个快照` : "待生成" }}</em>
            </div>

            <div class="flow-card" :class="{ active: !!state.selectedJobId || !!state.jobs.length }">
              <span class="flow-step">03</span>
              <strong>提交草稿</strong>
              <small>基于快照生成最终要发给 Seedance 的 request_body 和任务记录。</small>
              <em>{{ state.jobs.length ? `${state.jobs.length} 个草稿` : "待生成" }}</em>
            </div>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div>
                <p class="panel-kicker">Step 1</p>
                <h3>{{ selectedStoryboardProductionMode === "shot_pipeline" ? "镜头包" : "场景包" }}</h3>
              </div>
              <span class="pill">
                {{ (selectedStoryboardProductionMode === "shot_pipeline" ? selectedShotPromptPackage?.positive : selectedSceneDirectPackage?.positive) ? "已生成" : "待生成" }}
              </span>
            </div>

            <template v-if="selectedStoryboardProductionMode === 'shot_pipeline'">
              <el-button class="action-button dark full-width" :disabled="loading.shotPackage"
                @click="handleAssembleShotPackage">
                {{ loading.shotPackage ? "生成中..." : "生成当前镜头包" }}
              </el-button>

              <div class="meta-panel">
                <div class="meta-row">
                  <span>当前镜头卡</span>
                  <strong>{{ state.shots.length }}</strong>
                </div>
                <div class="meta-row">
                  <span>已勾选批次</span>
                  <strong>{{ state.selectedShotIds.length }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>批次草稿</span>
                  <div class="inline-actions compact-actions">
                    <el-button class="action-button ghost compact-button"
                      :disabled="loading.createShotBatch || !state.selectedShotIds.length"
                      @click="handleCreateShotBatch('selected')">
                      {{ loading.createShotBatch ? "处理中..." : "生成选中批次" }}
                    </el-button>
                    <el-button class="action-button warm compact-button"
                      :disabled="loading.createShotBatch || !state.shots.length" @click="handleCreateShotBatch('all')">
                      {{ loading.createShotBatch ? "处理中..." : "批量生成草稿批次" }}
                    </el-button>
                  </div>
                </div>
              </div>

              <div v-if="selectedShot" class="focus-card">
                <span>当前镜头</span>
                <strong>{{ selectedShot.id }}</strong>
                <small>{{ formatShotInputMode(selectedShot.media?.mode) }} · {{ selectedShot.scene_id }} ·
                  {{ selectedShot.visual.duration_seconds }} 秒</small>
              </div>

              <div v-if="selectedShot" class="meta-panel">
                <div class="meta-row meta-row-wide">
                  <span>镜头卡剧情描述</span>
                  <strong>{{ getShotStoryDisplay(selectedShot, "description") }}</strong>
                </div>
                <div class="meta-row">
                  <span>镜头卡情绪</span>
                  <strong>{{ getShotStoryDisplay(selectedShot, "emotion") }}</strong>
                </div>
                <div class="meta-row">
                  <span>镜头卡节拍</span>
                  <strong>{{ getShotStoryDisplay(selectedShot, "beat") }}</strong>
                </div>
                <div class="meta-row">
                  <span>锚点策略</span>
                  <strong>{{ formatShotAnchorMode(selectedShot.anchor_strategy?.mode) }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>镜头卡对白</span>
                  <strong class="prompt-preview">{{ formatDialogueEntries(selectedShot.dialogue) || "暂无" }}</strong>
                </div>
                <div
                  v-if="countShotAnchorOverrides(selectedShot.anchor_strategy?.per_character, selectedShot.characters)"
                  class="meta-row meta-row-wide">
                  <span>角色覆盖</span>
                  <strong class="prompt-preview">{{ formatShotAnchorOverridesDisplay(selectedShot.anchor_strategy,
                    selectedShot.characters) || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>镜头卡原文摘录</span>
                  <strong class="prompt-preview">{{ getShotStoryDisplay(selectedShot, "raw_script_excerpt") }}</strong>
                </div>
              </div>

              <div v-if="selectedShotPromptPackage?.positive" class="meta-panel">
                <div class="meta-row">
                  <span>参考素材数量</span>
                  <strong>{{ selectedShotPromptPackage.media_references?.length || selectedShotPromptPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span>参考图片</span>
                  <strong>{{ selectedShotPromptPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span>当前版本</span>
                  <strong>{{ formatPromptVariantLabel(selectedShotPromptVariant) }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>提示词版本切换</span>
                  <div class="inline-actions compact-actions prompt-variant-actions">
                    <el-button class="action-button compact-button"
                      :class="selectedShotPromptVariant === 'ai_refined' ? 'warm selected-variant' : 'ghost'"
                      :disabled="loading.updateShot || !selectedShotPromptVariants.ai_refined"
                      @click="handleSelectShotPromptVariant('ai_refined')">
                      {{ loading.updateShot && selectedShotPromptVariant !== 'ai_refined' ? "切换中..." : "使用 AI 润色版" }}
                    </el-button>
                    <el-button class="action-button compact-button"
                      :class="selectedShotPromptVariant === 'fallback_template' ? 'warm selected-variant' : 'ghost'"
                      :disabled="loading.updateShot || !selectedShotPromptVariants.fallback_template"
                      @click="handleSelectShotPromptVariant('fallback_template')">
                      {{ loading.updateShot && selectedShotPromptVariant !== 'fallback_template' ? "切换中..." : "使用 本地模板版" }}
                    </el-button>
                  </div>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>Seedance 提示词预览</span>
                  <strong class="prompt-preview">{{ selectedShotPromptPreview }}</strong>
                </div>
              </div>

              <div v-if="selectedShotPromptPackage?.prompt_generation" class="meta-panel">
                <div class="meta-row">
                  <span>生成方式</span>
                  <strong>{{ formatPromptGenerationMode(selectedShotPromptPackage.prompt_generation.mode) }}</strong>
                </div>
                <div class="meta-row">
                  <span>模型</span>
                  <strong>{{ selectedShotPromptPackage.prompt_generation.model || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>Fallback</span>
                  <strong>{{ selectedShotPromptPackage.prompt_generation.fallback_used ? "是" : "否" }}</strong>
                </div>
                <div v-if="selectedShotPromptPackage.prompt_generation.error" class="meta-row meta-row-wide">
                  <span>回退原因</span>
                  <strong class="prompt-preview">{{ selectedShotPromptPackage.prompt_generation.error }}</strong>
                </div>
              </div>

              <div v-if="selectedShotPromptPackage?.script_context" class="meta-panel">
                <div class="meta-row">
                  <span>剧集标题</span>
                  <strong>{{ selectedShotPromptPackage.script_context.episode_title || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>场景位置</span>
                  <strong>{{ selectedShotPromptPackage.script_context.scene_location || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>场景时间</span>
                  <strong>{{ selectedShotPromptPackage.script_context.scene_time || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>镜头动作</span>
                  <strong>{{ selectedShotPromptPackage.script_context.shot_description || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>情绪基调</span>
                  <strong>{{ selectedShotPromptPackage.script_context.shot_emotion || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>剧情节点</span>
                  <strong>{{ selectedShotPromptPackage.script_context.shot_beat || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>当前镜头台词片段</span>
                  <strong
                    class="prompt-preview">{{ selectedShotPromptPackage.script_context.dialogue_excerpt || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>剧本原文摘录</span>
                  <strong
                    class="prompt-preview">{{ selectedShotPromptPackage.script_context.raw_script_excerpt || "暂无" }}</strong>
                </div>
              </div>
              <el-button class="action-button warm full-width primary-action" :disabled="loading.createRender"
                @click="handleCreateRenderTask">
                {{ loading.createRender ? "生成中..." : "生成提交草稿" }}
              </el-button>

              <div class="subsection">
                <div class="subsection-header">
                  <h3>批次列表</h3>
                  <div class="inline-actions compact-actions">
                    <el-button class="action-button ghost compact-button"
                      :disabled="loading.deleteShotBatch || !selectedShotBatchComputed"
                      @click="handleDeleteShotBatch()">
                      {{ loading.deleteShotBatch ? "删除中..." : "删除当前批次" }}
                    </el-button>
                    <el-button class="action-button ghost danger compact-button"
                      :disabled="loading.clearShotBatches || !state.shotBatches.length" @click="handleClearShotBatches">
                      {{ loading.clearShotBatches ? "清空中..." : "清空批次" }}
                    </el-button>
                  </div>
                </div>

                <div v-loading="shotBatchesListLoading" element-loading-text="批次列表加载中..."
                  :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
                  element-loading-background="rgba(7, 10, 14, 0.18)" class="mini-list nested-mini-list">
                  <div v-for="batch in state.shotBatches" :key="batch.id" class="mini-card selectable"
                    :class="{ active: batch.id === state.selectedShotBatchId }">
                    <div class="item-body" @click="state.selectedShotBatchId = batch.id">
                      <strong>{{ batch.name || batch.id }}</strong>
                      <span>{{ batch.id }} · {{ formatStatus(batch.status) }}</span>
                      <small>{{ formatShotBatchCounts(batch) }}</small>
                      <small>进度：{{ formatShotBatchProgress(batch) }} · 可提交
                        {{ getShotBatchSubmittableCount(batch) }}</small>
                    </div>
                    <div class="item-actions">
                      <el-button class="action-button ghost compact-button"
                        :disabled="loading.submitShotBatch || !getShotBatchSubmittableCount(batch)"
                        @click.stop="handleSubmitShotBatch(batch)">
                        {{ loading.submitShotBatch ? "提交中..." : "未提交/失败-镜头提交" }}
                      </el-button>
                      <el-button class="action-button ghost compact-button" :disabled="loading.refreshShotBatch"
                        @click.stop="handleRefreshShotBatch(batch)">
                        {{ loading.refreshShotBatch ? "刷新中..." : "刷新批次" }}
                      </el-button>
                      <el-button class="action-button ghost compact-button"
                        :disabled="loading.retryShotBatch || !batch.failed_count"
                        @click.stop="handleRetryFailedShotBatch(batch)">
                        {{ loading.retryShotBatch ? "重试中..." : "重试失败项" }}
                      </el-button>
                    </div>
                  </div>
                  <div v-if="!state.shotBatches.length" class="empty-state">当前还没有镜头批次。</div>
                </div>

                <div v-if="selectedShotBatchComputed" class="meta-panel">
                  <div class="meta-row">
                    <span>当前批次</span>
                    <strong>{{ selectedShotBatchComputed.id }}</strong>
                  </div>
                  <div class="meta-row">
                    <span>批次状态</span>
                    <strong>{{ formatStatus(selectedShotBatchComputed.status) }}</strong>
                  </div>
                  <div class="meta-row">
                    <span>镜头数量</span>
                    <strong>{{ selectedShotBatchComputed.total_count || 0 }}</strong>
                  </div>
                  <div class="meta-row">
                    <span>批次成功率</span>
                    <strong>{{ formatShotBatchProgress(selectedShotBatchComputed) }}</strong>
                  </div>
                  <div class="meta-row meta-row-wide">
                    <span>明细</span>
                    <strong class="prompt-preview">{{ formatShotBatchCounts(selectedShotBatchComputed) }}</strong>
                  </div>
                </div>

                <div v-if="selectedShotBatchComputed?.items?.length" class="mini-list nested-mini-list">
                  <div v-for="batchItem in selectedShotBatchComputed.items"
                    :key="`${selectedShotBatchComputed.id}-${batchItem.shot_id}`" class="mini-card">
                    <div class="item-body">
                      <strong>{{ batchItem.shot_id }}</strong>
                      <span>{{ formatStatus(batchItem.status) }}</span>
                      <small>快照：{{ batchItem.snapshot_id || "暂无" }} · 草稿：{{ batchItem.job_id || "暂无" }}</small>
                      <small>{{ batchItem.error || "无错误" }}</small>
                    </div>
                    <div class="item-actions">
                      <el-button v-if="batchItem.job_id" class="action-button ghost compact-button"
                        @click.stop="state.selectedJobId = batchItem.job_id">
                        打开草稿
                      </el-button>
                    </div>
                  </div>
                </div>

                <div v-if="getBatchCompletedItems(selectedShotBatchComputed).length" class="reference-grid">
                  <div v-for="item in getBatchCompletedItems(selectedShotBatchComputed)"
                    :key="`batch-result-${item.job_id}`" class="reference-card">
                    <div class="reference-header">
                      <strong>{{ item.shot_id }}</strong>
                      <small>{{ item.job_id }}</small>
                    </div>
                    <video v-if="getBatchJobVideoUrl(item.job_id)" class="video-preview"
                      :src="getBatchJobVideoUrl(item.job_id)" controls preload="metadata" />
                    <el-image v-else-if="getBatchJobCoverUrl(item.job_id)" class="preview-image"
                      :src="getBatchJobCoverUrl(item.job_id)"
                      :preview-src-list="getBatchJobCoverUrl(item.job_id) ? [getBatchJobCoverUrl(item.job_id)] : []"
                      :initial-index="0" fit="cover" preview-teleported />
                    <div v-else class="reference-empty">暂无结果预览</div>
                  </div>
                </div>
              </div>
            </template>

            <template v-else>
              <el-button class="action-button dark full-width" :disabled="loading.sceneDirectPackage"
                @click="handleAssembleSceneDirectPackage">
                {{ loading.sceneDirectPackage ? "组装中..." : "组装场景包" }}
              </el-button>


              <div class="focus-card" style="margin-bottom: 12px;">
                <span>当前场景</span>
                <strong>{{state.scenes.find((item) => item.id === getSceneDirectSceneId())?.name || "请先选择场景"}}</strong>
                <small>{{ getSceneDirectSceneId() || "未指定场景" }} · {{ formatShotInputMode(forms.shotInputMode) }} ·
                  {{ normalizeShotDuration(forms.shotDuration) }} 秒</small>
              </div>

              <div v-if="selectedSceneDirectPackage?.positive" class="meta-panel" style="margin-bottom: 12px;">
                <div class="meta-row">
                  <span>参考素材数量</span>
                  <strong>{{ selectedSceneDirectPackage.media_references?.length || selectedSceneDirectPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span>参考图片</span>
                  <strong>{{ selectedSceneDirectPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>场景级提示词预览</span>
                  <strong class="prompt-preview">{{ selectedSceneDirectPackage.positive }}</strong>
                </div>
              </div>

              <div v-if="selectedSceneDirectPackage?.script_context" class="meta-panel" style="margin-bottom: 12px;">
                <div class="meta-row">
                  <span>剧集标题</span>
                  <strong>{{ selectedSceneDirectPackage.script_context.episode_title || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>场景位置</span>
                  <strong>{{ selectedSceneDirectPackage.script_context.scene_location || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>场景时间</span>
                  <strong>{{ selectedSceneDirectPackage.script_context.scene_time || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>场景摘要</span>
                  <strong>{{ selectedSceneDirectPackage.script_context.scene_summary || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>节拍大纲</span>
                  <strong
                    class="prompt-preview">{{ (selectedSceneDirectPackage.script_context.beat_outline || []).join("\n") || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>剧本原文摘录</span>
                  <strong
                    class="prompt-preview">{{ selectedSceneDirectPackage.script_context.raw_script_excerpt || "暂无" }}</strong>
                </div>
              </div>

              <div v-if="selectedSceneDirectPackage?.prompt_generation" class="meta-panel" style="margin-bottom: 12px;">
                <div class="meta-row">
                  <span>生成方式</span>
                  <strong>{{ formatPromptGenerationMode(selectedSceneDirectPackage.prompt_generation.mode) }}</strong>
                </div>
                <div class="meta-row">
                  <span>模型</span>
                  <strong>{{ selectedSceneDirectPackage.prompt_generation.model || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span>Fallback</span>
                  <strong>{{ selectedSceneDirectPackage.prompt_generation.fallback_used ? "是" : "否" }}</strong>
                </div>
                <div v-if="selectedSceneDirectPackage.prompt_generation.error" class="meta-row meta-row-wide">
                  <span>回退原因</span>
                  <strong class="prompt-preview">{{ selectedSceneDirectPackage.prompt_generation.error }}</strong>
                </div>
              </div>

              <div v-if="selectedSceneDirectPackage?.prompt_input" class="meta-panel" style="margin-bottom: 12px;">
                <div class="meta-row meta-row-wide">
                  <span>Prompt 骨架：参考绑定</span>
                  <strong class="prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.reference_binding || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>Prompt 骨架：场景目标</span>
                  <strong
                    class="prompt-preview">{{ selectedSceneDirectPackage.prompt_input.scene_goal || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>Prompt 骨架：剧情阶段</span>
                  <strong class="prompt-preview">{{
                    (selectedSceneDirectPackage.prompt_input.condensed_beats || []).join("\n") || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>Prompt 骨架：场景视觉</span>
                  <strong class="prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.scene_visual || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>Prompt 骨架：镜头原则</span>
                  <strong class="prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.camera_direction || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>Prompt 骨架：输出规格</span>
                  <strong class="prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.output_spec || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span>Prompt 骨架：约束</span>
                  <strong class="prompt-preview">{{
                    (selectedSceneDirectPackage.prompt_input.constraints || []).join("，") || "暂无"
                  }}</strong>
                </div>
                <div v-if="(selectedSceneDirectPackage.prompt_input.warnings || []).length"
                  class="meta-row meta-row-wide">
                  <span>Prompt 骨架：备注</span>
                  <strong class="prompt-preview">{{
                    (selectedSceneDirectPackage.prompt_input.warnings || []).join("；")
                  }}</strong>
                </div>
              </div>

              <details v-if="selectedSceneDirectPackage?.prompt_input?.raw_script_excerpt" class="debug-disclosure"
                style="margin-bottom: 12px;">
                <summary>调试查看：原始剧本摘录</summary>
                <div class="meta-panel debug-panel">
                  <div class="meta-row meta-row-wide">
                    <span>Prompt 骨架：原文摘录</span>
                    <strong class="prompt-preview">{{
                      selectedSceneDirectPackage.prompt_input.raw_script_excerpt
                    }}</strong>
                  </div>
                </div>
              </details>

              <div v-if="(selectedSceneDirectPackage?.script_context?.shot_outlines || []).length"
                class="mini-list direct-beat-list" style="margin-bottom: 12px;">
                <div v-for="item in selectedSceneDirectPackage.script_context.shot_outlines"
                  :key="`scene-beat-${item.index}`" class="mini-card">
                  <div class="item-body">
                    <strong>节拍 {{ item.index }}</strong>
                    <small>{{ formatReadableField(item.description) }}</small>
                    <small>镜头建议：{{ formatReadableField(item.camera_summary) }}</small>
                    <small>情绪：{{ formatReadableField(item.emotion) }}</small>
                    <small>剧情节拍：{{ formatReadableField(item.beat) }}</small>
                    <small>对白：{{ formatReadableField(item.dialogue_excerpt) }}</small>
                  </div>
                </div>
              </div>
              <el-button class="action-button warm full-width primary-action" :disabled="loading.createSceneDirectTask"
                @click="handleCreateSceneDirectTask">
                {{ loading.createSceneDirectTask ? "生成中..." : "生成场景任务草稿" }}
              </el-button>
            </template>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div>
                <p class="panel-kicker">Step 2</p>
                <h3>快照</h3>
              </div>
              <div class="inline-actions compact-actions">
                <el-button class="action-button ghost danger compact-button"
                  :disabled="loading.clearSnapshots || !state.snapshots.length" @click="handleClearSnapshots">
                  {{ loading.clearSnapshots ? "清空中..." : "清空快照" }}
                </el-button>
                <span class="pill">{{ state.snapshots.length ? `${state.snapshots.length} 个` : "0 个" }}</span>
              </div>
            </div>

            <div v-loading="snapshotsListLoading" element-loading-text="快照列表加载中..."
              :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
              element-loading-background="rgba(7, 10, 14, 0.2)" class="mini-list">
              <div v-for="item in state.snapshots" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedSnapshotId }">
                <div class="item-body" @click="handleOpenSnapshot(item)">
                  <strong>{{ item.id }}</strong>
                  <span>{{ item.storyboard_id }} · {{ item.shot_id }}</span>
                  <small>{{ formatSnapshotSource(item) }}</small>
                  <small>图片 {{ item.resolved_assets?.images?.length || 0 }}</small>
                </div>
                <div class="item-actions">
                  <el-button class="action-button ghost compact-button" @click.stop="handleOpenSnapshot(item)">
                    查看
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteSnapshot"
                    @click.stop="handleDeleteSnapshot(item)">
                    {{ loading.deleteSnapshot ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
              <div v-if="!state.snapshots.length" class="empty-state">当前还没有本地快照。</div>
            </div>

            <el-skeleton v-if="snapshotDetailSectionLoading" animated>
              <template #template>
                <div class="detail-skeleton-stack">
                  <div class="skeleton-grid">
                    <div class="skeleton-card" v-for="item in 4" :key="`snapshot-detail-skeleton-${item}`">
                      <el-skeleton-item variant="text" class="skeleton-line" />
                      <el-skeleton-item variant="h3" class="skeleton-line skeleton-line-mid" />
                    </div>
                  </div>
                </div>
              </template>
            </el-skeleton>
            <div v-else-if="state.selectedSnapshot" class="meta-panel">
              <div class="meta-row">
                <span>当前快照</span>
                <strong>{{ state.selectedSnapshot.id }}</strong>
              </div>
              <div class="meta-row">
                <span>所属分镜板 / 镜头</span>
                <strong>{{ formatSnapshotSource(state.selectedSnapshot) }}</strong>
              </div>
              <div class="meta-row">
                <span>引用图片数量</span>
                <strong>{{ selectedSnapshotImageCount }}</strong>
              </div>
              <div class="meta-row">
                <span>卡片路径</span>
                <strong>{{ state.selectedSnapshot.inputs?.shot_card_path || state.selectedSnapshot.inputs?.scene_card_path || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>角色文件数量</span>
                <strong>{{ state.selectedSnapshot.inputs?.character_paths?.length || 0 }}</strong>
              </div>
              <div class="meta-row">
                <span>场景文件数量</span>
                <strong>{{ state.selectedSnapshot.inputs?.scene_paths?.length || 0 }}</strong>
              </div>
            </div>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div>
                <p class="panel-kicker">Step 3</p>
                <h3>提交草稿</h3>
              </div>
              <div class="inline-actions compact-actions">
                <el-button class="action-button ghost danger compact-button"
                  :disabled="loading.clearJobs || !state.jobs.length" @click="handleClearJobs">
                  {{ loading.clearJobs ? "清空中..." : "清空草稿" }}
                </el-button>
                <span class="pill">{{ state.jobs.length ? `${state.jobs.length} 个` : "0 个" }}</span>
              </div>
            </div>

            <div v-loading="jobsListLoading" element-loading-text="任务列表加载中..." :element-loading-svg="loadingSpinnerSvg"
              :element-loading-svg-view-box="loadingSpinnerViewBox" element-loading-background="rgba(7, 10, 14, 0.2)"
              class="mini-list">
              <div v-for="item in state.jobs" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedJobId }">
                <div class="item-body" @click="state.selectedJobId = item.id">
                  <strong>{{ item.id }}</strong>
                  <span>{{ formatStatus(item.status) }}</span>
                  <small>{{ formatSeedanceMode(getJobSeedanceSummary(item).mode) }} ·
                    {{ item.provider?.model || "doubao-seedance-2-0-260128" }}</small>
                  <small>输出：{{ getJobSeedanceSummary(item).ratio }} · {{ getJobSeedanceSummary(item).resolution }} ·
                    {{ formatJobOutputSummary(item) }}</small>
                  <small>素材：{{ formatJobReferenceSummary(item) }} ·
                    {{ getJobSeedanceSummary(item).returnLastFrame ? "回传尾帧" : "不回传尾帧" }}</small>
                  <small>关联快照：{{ item.snapshot_id || "暂无" }}</small>
                </div>
                <div class="item-actions">
                  <el-button class="action-button ghost compact-button" @click.stop="handleOpenJobSnapshot(item)">
                    查看快照
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteJob"
                    @click.stop="handleDeleteJob(item)">
                    {{ loading.deleteJob ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
              <div v-if="!state.jobs.length" class="empty-state">当前还没有任务草稿。</div>
            </div>

            <div v-if="selectedJobComputed" class="subsection">
              <el-skeleton :loading="jobDetailSectionLoading" animated>
                <template #template>
                  <div class="detail-skeleton-stack">
                    <div class="skeleton-card skeleton-header-card">
                      <el-skeleton-item variant="text" class="skeleton-kicker" />
                      <el-skeleton-item variant="h3" class="skeleton-title" />
                      <div class="skeleton-chip-row">
                        <el-skeleton-item variant="button" class="skeleton-chip" />
                        <el-skeleton-item variant="button" class="skeleton-chip" />
                        <el-skeleton-item variant="button" class="skeleton-chip" />
                      </div>
                    </div>
                    <div class="skeleton-grid">
                      <div class="skeleton-card" v-for="item in 6" :key="`job-detail-skeleton-${item}`">
                        <el-skeleton-item variant="text" class="skeleton-line" />
                        <el-skeleton-item variant="h3" class="skeleton-line skeleton-line-mid" />
                      </div>
                    </div>
                    <div class="skeleton-card">
                      <el-skeleton-item variant="image" class="skeleton-media" />
                    </div>
                    <div class="skeleton-card">
                      <el-skeleton-item variant="text" class="skeleton-line" />
                      <el-skeleton-item variant="text" class="skeleton-line skeleton-line-wide" />
                      <el-skeleton-item variant="text" class="skeleton-line skeleton-line-wide" />
                    </div>
                  </div>
                </template>
                <template #default>
                  <div class="panel-header">
                    <div>
                      <p class="panel-kicker">当前任务</p>
                      <h3>{{ selectedJobComputed.id }}</h3>
                    </div>
                    <div class="inline-actions compact-actions" style="flex-shrink: 0;display: flex;gap: 12px;">

                      <el-button class="action-button ghost"
                        :disabled="loading.snapshotDetail || !selectedJobComputed.snapshot_id"
                        @click="handleOpenJobSnapshot()">
                        {{ loading.snapshotDetail ? "加载中..." : "查看快照" }}
                      </el-button>
                      <el-button class="action-button ghost"
                        :disabled="loading.submitJob || loading.jobDetail || selectedJobComputed.status === 'submitting'"
                        @click="handleSubmitJob">
                        {{ loading.submitJob ? "提交中..." : "提交任务" }}
                      </el-button>
                      <el-button class="action-button dark"
                        :disabled="loading.refreshJob || loading.jobDetail || !selectedJobComputed.remote?.task_id"
                        @click="handleRefreshJob">
                        {{ loading.refreshJob ? "刷新中..." : "刷新状态" }}
                      </el-button>
                      <el-button class="action-button ghost danger"
                        :disabled="loading.deleteRemoteTask || !selectedJobComputed.remote?.task_id"
                        @click="handleDeleteRemoteTask({ id: selectedJobComputed.remote?.task_id })">
                        {{ loading.deleteRemoteTask ? "删除中..." : "删除远程任务" }}
                      </el-button>
                    </div>
                  </div>

                  <div class="meta-panel">
                    <div class="meta-row">
                      <span>状态</span>
                      <strong>{{ formatStatus(selectedJobComputed.status) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>供应商</span>
                      <strong>{{ formatProviderName(selectedJobComputed.provider?.name) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>模型</span>
                      <strong>{{ selectedJobComputed.provider?.model || "暂未配置" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>任务接口</span>
                      <strong>{{ formatJobApiKind(selectedJobComputed.provider) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>输入模式</span>
                      <strong>{{ selectedJobRequestSummary.modeLabel }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>图像引用</span>
                      <strong>{{ selectedJobRequestSummary.imageCount }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>输出规格</span>
                      <strong>{{ selectedJobRequestSummary.ratio }} ·
                        {{ selectedJobRequestSummary.resolution }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>时长 / 数量</span>
                      <strong>{{ selectedJobRequestSummary.duration || "未设置" }} 秒 ·
                        {{ selectedJobRequestSummary.count }}
                        条</strong>
                    </div>
                    <div class="meta-row">
                      <span>音频 / 尾帧</span>
                      <strong>{{ selectedJobRequestSummary.hasAudio ? "有声" : "无声" }} ·
                        {{ selectedJobRequestSummary.returnLastFrame ? "回传尾帧" : "不回传尾帧" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>远端任务 ID</span>
                      <strong>{{ selectedJobComputed.remote?.task_id || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>任务响应快照</span>
                      <strong>{{ selectedJobComputed.remote?.raw_response_path || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>结果视频</span>
                      <strong>{{ selectedJobComputed.result?.video_path || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>结果封面</span>
                      <strong>{{ selectedJobComputed.result?.cover_path || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>错误信息</span>
                      <strong>{{ selectedJobComputed.error?.message || "无" }}</strong>
                    </div>
                  </div>

                  <div v-if="selectedJobCoverUrl || selectedJobVideoUrl" class="reference-grid">
                    <div v-if="selectedJobCoverUrl" class="reference-card">
                      <div class="reference-header">
                        <strong>封面</strong>
                        <small>{{ selectedJobComputed.result?.cover_path }}</small>
                      </div>
                      <el-image class="preview-image" :src="selectedJobCoverUrl"
                        :preview-src-list="selectedJobCoverUrl ? [selectedJobCoverUrl] : []" :initial-index="0"
                        fit="cover" preview-teleported />
                    </div>

                    <div v-if="selectedJobVideoUrl" class="reference-card">
                      <div class="reference-header">
                        <strong>视频</strong>
                        <small>{{ selectedJobComputed.result?.video_path }}</small>
                      </div>
                      <video class="video-preview" :src="selectedJobVideoUrl" controls preload="metadata" />
                    </div>
                  </div>

                  <div class="form-stack">
                    <label
                      class="code-label">{{ selectedJobHasSubmittedRequest ? "Seedance 最终提交体" : "Seedance 提交草稿" }}</label>
                    <el-input :model-value="selectedJobRequestText" class="field-textarea code-textarea job-code"
                      type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
                  </div>

                  <div
                    v-if="selectedJobComputed.remote?.raw_response_path || Object.keys(selectedJobComputed.remote?.raw_response || {}).length"
                    class="form-stack">
                    <label class="code-label">Seedance Response</label>
                    <el-input :model-value="selectedJobResponseText" class="field-textarea code-textarea job-code"
                      type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
                  </div>
                </template>
              </el-skeleton>
            </div>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div>
                <p class="panel-kicker">Remote</p>
                <h3>远程任务</h3>
              </div>
              <div class="inline-actions compact-actions">
                <el-button class="action-button ghost compact-button"
                  :disabled="remoteTasksListLoading || !state.remoteTasks.length" @click="handleRefreshRemoteTasks">
                  {{ remoteTasksListLoading ? "刷新中..." : "刷新远程任务" }}
                </el-button>
                <span class="pill">{{ state.remoteTasks.length }} 项</span>
              </div>
            </div>

            <div v-loading="remoteTasksListLoading" element-loading-text="远程任务加载中..."
              :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
              element-loading-background="rgba(7, 10, 14, 0.18)" class="mini-list">
              <div v-for="task in state.remoteTasks" :key="getRemoteTaskId(task)" class="mini-card selectable"
                :class="{ active: getRemoteTaskId(task) === state.selectedRemoteTaskId }">
                <div class="item-body" @click="state.selectedRemoteTaskId = getRemoteTaskId(task)">
                  <strong>{{ getRemoteTaskId(task) }}</strong>
                  <span>{{ getRemoteTaskStatus(task) }}</span>
                  <small>关联草稿：{{ getRemoteTaskLinkedJob(task)?.id || "暂无" }}</small>
                </div>
                <div class="item-actions">
                  <el-button class="action-button ghost compact-button" :disabled="!getRemoteTaskLinkedJob(task)"
                    @click.stop="handleOpenRemoteTaskJob(task)">
                    打开草稿
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteRemoteTask"
                    @click.stop="handleDeleteRemoteTask(task)">
                    {{ loading.deleteRemoteTask ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
              <div v-if="!state.remoteTasks.length" class="empty-state">当前系列还没有关联的远程任务。</div>
            </div>

            <div v-if="selectedRemoteTaskComputed" class="meta-panel">
              <div class="meta-row">
                <span>远程任务 ID</span>
                <strong>{{ getRemoteTaskId(selectedRemoteTaskComputed) }}</strong>
              </div>
              <div class="meta-row">
                <span>远程状态</span>
                <strong>{{ getRemoteTaskStatus(selectedRemoteTaskComputed) }}</strong>
              </div>
              <div class="meta-row">
                <span>关联草稿</span>
                <strong>{{ getRemoteTaskLinkedJob(selectedRemoteTaskComputed)?.id || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>结果视频</span>
                <strong>{{ selectedRemoteTaskVideoUrl || "暂无" }}</strong>
              </div>
            </div>

            <div v-if="selectedRemoteTaskCoverUrl || selectedRemoteTaskVideoUrl" class="reference-grid">
              <div v-if="selectedRemoteTaskCoverUrl" class="reference-card">
                <div class="reference-header">
                  <strong>远程封面</strong>
                  <small>{{ selectedRemoteTaskCoverUrl }}</small>
                </div>
                <el-image class="preview-image" :src="selectedRemoteTaskCoverUrl"
                  :preview-src-list="[selectedRemoteTaskCoverUrl]" :initial-index="0" fit="cover" preview-teleported />
              </div>
              <div v-if="selectedRemoteTaskVideoUrl" class="reference-card">
                <div class="reference-header">
                  <strong>远程视频</strong>
                  <small>{{ selectedRemoteTaskVideoUrl }}</small>
                </div>
                <video class="video-preview" :src="selectedRemoteTaskVideoUrl" controls preload="metadata" />
              </div>
            </div>

            <div v-if="selectedRemoteTaskComputed" class="form-stack">
              <label class="code-label">Remote Task Payload</label>
              <el-input :model-value="selectedRemoteTaskText" class="field-textarea code-textarea job-code"
                type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
            </div>
          </div>
        </section>
      </aside>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
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

:global(button),
:global(input),
:global(select),
:global(textarea) {
  font: inherit;
}

:global(.el-message) {
  --el-message-bg-color: rgba(12, 20, 34, 0.94);
  --el-message-border-color: rgba(255, 255, 255, 0.14);
  --el-message-text-color: #edf2f7;
  backdrop-filter: blur(18px);
}

.shell :deep(.el-loading-mask) {
  backdrop-filter: blur(10px);
  border-radius: 18px;
}

.shell :deep(.el-loading-spinner) {
  margin-top: calc(0px - 28px);
  display: grid;
  justify-items: center;
  gap: 12px;
}

.shell :deep(.el-loading-spinner .circular) {
  width: 62px;
  height: 62px;
}

.shell :deep(.el-loading-spinner .el-loading-text) {
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

:global(.el-message--success) {
  --el-message-bg-color: rgba(11, 46, 34, 0.92);
  --el-message-border-color: rgba(52, 211, 153, 0.36);
}

:global(.el-message--error) {
  --el-message-bg-color: rgba(61, 18, 28, 0.94);
  --el-message-border-color: rgba(251, 113, 133, 0.38);
}

:global(.el-select__popper),
:global(.el-popper.is-light) {
  --el-bg-color-overlay: #111a2b;
  --el-fill-color-light: rgba(255, 255, 255, 0.05);
  --el-border-color-light: rgba(255, 255, 255, 0.12);
  --el-text-color-regular: #edf2f7;
  --el-text-color-primary: #edf2f7;
  --el-text-color-placeholder: rgba(237, 242, 247, 0.52);
}

:global(.el-select-dropdown__item) {
  color: #edf2f7;
}

:global(.el-select-dropdown__item.is-hovering),
:global(.el-select-dropdown__item.hover) {
  background: rgba(116, 255, 82, 0.16);
}

:global(.el-select-dropdown__item.selected) {
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

.field-select :deep(.el-select__wrapper) {
  min-height: 40px;
  border-radius: 12px;
  padding: 0 12px;
  box-shadow: none;
  background: rgba(255, 255, 255, 0.038);
  border: 1px solid rgba(255, 255, 255, 0.085);
}

.field-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--ui-accent-strong);
  box-shadow: 0 0 0 3px rgba(116, 255, 82, 0.1);
}

.field-select :deep(.el-select__placeholder),
.field-select :deep(.el-select__selected-item),
.field-select :deep(.el-select__input-wrapper),
.field-select :deep(.el-select__caret) {
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

.editor-textarea :deep(.el-textarea__inner) {
  min-height: 360px;
  font-size: 14px;
  line-height: 1.6;
}

.code-textarea {
  font-family: "Consolas", "SFMono-Regular", monospace;
}

.code-textarea :deep(.el-textarea__inner) {
  font-family: "Consolas", "SFMono-Regular", monospace;
}

.job-code {
  min-height: 180px;
}

.field-textarea :deep(.el-textarea__inner) {
  min-height: inherit;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.085);
  background: rgba(255, 255, 255, 0.038);
  color: #edf2f7;
  box-shadow: none;
}

.field-textarea :deep(.el-textarea__inner::placeholder) {
  color: rgba(237, 242, 247, 0.34);
}

.field-textarea :deep(.el-textarea__inner:focus) {
  border-color: var(--ui-accent-strong);
  box-shadow: 0 0 0 3px rgba(116, 255, 82, 0.1);
}

.field-number {
  width: 100%;
}

.field-number :deep(.el-input__wrapper) {
  min-height: 40px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.038);
  border: 1px solid rgba(255, 255, 255, 0.085);
  box-shadow: none;
}

.field-number :deep(.el-input__inner) {
  color: #edf2f7;
}

.field-number :deep(.el-input-number__decrease),
.field-number :deep(.el-input-number__increase) {
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

.detail-skeleton-stack :deep(.el-skeleton__item) {
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

.check-card :deep(.el-checkbox__input) {
  margin-right: 2px;
}

.check-card :deep(.el-checkbox__label) {
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

.preview-image :deep(.el-image__inner) {
  width: 100%;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}

.preview-image-large {
  aspect-ratio: auto;
  max-height: 760px;
}

.preview-image-large :deep(.el-image__inner) {
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

:deep(.el-input) {
  background: rgba(255, 255, 255, 0.05)
}

:deep(.el-input__wrapper) {
  background: transparent;
  border: none;
  box-shadow: none;

}

:deep(.el-input__inner) {
  color: #fff;
}
</style>
