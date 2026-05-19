<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  analyzeEpisodeScript,
  assembleShotPackage,
  createCharacter,
  createEpisode,
  createScene,
  createSeries,
  createShot,
  createSnapshot,
  createStoryboard,
  createVideoJobFromSnapshot,
  deleteCharacter,
  deleteCharacterSourceImage,
  deleteEpisode,
  deleteJob,
  deleteScene,
  deleteSeries,
  deleteShot,
  deleteStoryboard,
  generateCharacterAssets,
  generateSceneAssets,
  getCharacterBible,
  getHealth,
  getJob,
  getSnapshot,
  getParsedScript,
  getRawScript,
  getScenePromptPackage,
  listCharacters,
  listEpisodes,
  listJobs,
  listScenes,
  listSeries,
  listShots,
  listStoryboards,
  refreshJob,
  saveParsedScript,
  saveRawScript,
  submitJob,
  updateCharacter,
  updateEpisode,
  updateScene,
  updateShot,
  updateSeries,
  uploadCharacterSourceImages
} from "./services/api";

const health = ref("checking");
const characterSourceFiles = ref([]);
const characterSourceInput = ref(null);
let episodeScriptsRequestSeed = 0;
let productionRequestSeed = 0;
let shotsRequestSeed = 0;
let characterBibleRequestSeed = 0;
let scenePackageRequestSeed = 0;
let jobDetailRequestSeed = 0;
let snapshotDetailRequestSeed = 0;

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
  createShot: false,
  updateShot: false,
  deleteShot: false,
  deleteStoryboard: false,
  createRender: false,
  characterAssets: false,
  characterUpload: false,
  deleteCharacterSourceImage: false,
  characterBible: false,
  sceneAssets: false,
  scenePackage: false,
  shotPackage: false,
  jobDetail: false,
  snapshotDetail: false,
  deleteJob: false,
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
  shotSize: "medium",
  shotMovement: "static",
  shotDuration: 5,
  shotPalette: "",
  shotLighting: ""
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
  shotSize: "medium",
  shotMovement: "static",
  shotDuration: 5,
  shotLighting: "",
  shotPalette: "",
  shotCharacterIds: []
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
  biology: "生理锚点",
  face: "五官锚点",
  hair: "发型锚点",
  costume: "服装锚点",
  palette: "色彩锚点",
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
  jobs: [],
  selectedSeriesSlug: "",
  selectedEpisodeId: "",
  selectedStoryboardId: "",
  selectedShotId: "",
  selectedCharacterId: "",
  selectedSceneId: "",
  selectedJobId: "",
  selectedCharacterIds: [],
  rawScript: "",
  parsedScriptText: "",
  selectedCharacterBible: null,
  selectedScenePackage: null,
  selectedJob: null,
  selectedSnapshot: null,
  assets: {
    characters: 0,
    scenes: 0,
    storyboards: 0,
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
const selectedShot = computed(() => state.shots.find((item) => item.id === state.selectedShotId) || null);
const selectedJobComputed = computed(() => {
  if (state.selectedJob && state.selectedJob.id === state.selectedJobId) {
    return state.selectedJob;
  }
  return state.jobs.find((item) => item.id === state.selectedJobId) || null;
});
const selectedShotPromptPackage = computed(() => selectedShot.value?.prompt_package || null);
const selectedJobRequestText = computed(() =>
  JSON.stringify(selectedJobComputed.value?.provider?.request_body || {}, null, 2)
);
const selectedJobResponseText = computed(() =>
  JSON.stringify(selectedJobComputed.value?.remote?.raw_response || {}, null, 2)
);
const selectedJobVideoUrl = computed(() => assetUrl(selectedJobComputed.value?.result?.video_path || ""));
const selectedJobCoverUrl = computed(() => assetUrl(selectedJobComputed.value?.result?.cover_path || ""));
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
  inlineEditing.shotId = item.id;
  inlineEditing.shotSceneId = item.scene_id || "";
  inlineEditing.shotSize = item.visual?.shot_size || "medium";
  inlineEditing.shotMovement = item.visual?.camera_movement || "static";
  inlineEditing.shotDuration = item.visual?.duration_seconds || 5;
  inlineEditing.shotLighting = item.visual?.lighting || "";
  inlineEditing.shotPalette = item.visual?.palette || "";
  inlineEditing.shotCharacterIds = [...(item.characters || [])];
  state.selectedShotId = item.id;
}

function cancelShotEdit() {
  inlineEditing.shotId = "";
  inlineEditing.shotSceneId = "";
  inlineEditing.shotSize = "medium";
  inlineEditing.shotMovement = "static";
  inlineEditing.shotDuration = 5;
  inlineEditing.shotLighting = "";
  inlineEditing.shotPalette = "";
  inlineEditing.shotCharacterIds = [];
}

function syncAssetCounts() {
  state.assets = {
    characters: state.characters.length,
    scenes: state.scenes.length,
    storyboards: state.storyboards.length,
    jobs: state.jobs.length
  };
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

function formatProviderName(value) {
  if (!value || value === "manual") {
    return "手动占位";
  }
  return value;
}

function formatSubmitMode(value) {
  if (!value || value === "manual") {
    return "手动";
  }
  if (value === "generic_http") {
    return "通用 HTTP";
  }
  return value;
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
    state.jobs = [];
    state.shots = [];
    state.selectedCharacterId = "";
    state.selectedSceneId = "";
    state.selectedStoryboardId = "";
    state.selectedShotId = "";
    state.selectedJobId = "";
    state.selectedCharacterBible = null;
    state.selectedScenePackage = null;
    state.selectedJob = null;
    syncAssetCounts();
    return;
  }

  loading.production = true;
  try {
    const [characters, scenes, storyboards, jobs] = await Promise.all([
      listCharacters(seriesSlug),
      listScenes(seriesSlug),
      listStoryboards(seriesSlug),
      listJobs(seriesSlug)
    ]);

    if (requestId !== productionRequestSeed || seriesSlug !== state.selectedSeriesSlug) {
      return;
    }

    state.characters = characters.items || [];
    state.scenes = scenes.items || [];
    state.storyboards = storyboards.items || [];
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

async function loadShotsForStoryboard(seriesSlug, storyboardId) {
  const requestId = ++shotsRequestSeed;
  if (!seriesSlug || !storyboardId) {
    state.shots = [];
    state.selectedShotId = "";
    return;
  }

  loading.shots = true;
  state.shots = [];
  state.selectedShotId = "";
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
    if (!state.shots.some((item) => item.id === state.selectedShotId)) {
      state.selectedShotId = state.shots[0]?.id || "";
    }
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
      episode_id: state.selectedEpisodeId
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
  if (!forms.shotSceneId) {
    setError("请先选择一个场景");
    return;
  }

  loading.createShot = true;
  try {
    const response = await createShot(state.selectedSeriesSlug, state.selectedStoryboardId, {
      scene_id: forms.shotSceneId,
      shot_payload: {
        characters: state.selectedCharacterIds,
        visual: {
          aspect_ratio: "16:9",
          style: "cinematic realism",
          resolution: "1080p",
          shot_size: forms.shotSize,
          camera_angle: "eye_level",
          camera_movement: forms.shotMovement,
          lens: "50mm",
          depth_of_field: "medium",
          lighting: forms.shotLighting.trim(),
          palette: forms.shotPalette.trim(),
          duration_seconds: Number(forms.shotDuration) || 5
        }
      }
    });
    await loadProductionData(state.selectedSeriesSlug);
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
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
    await updateShot(state.selectedSeriesSlug, state.selectedStoryboardId, targetShotId, {
      scene_id: inlineEditing.shotSceneId,
      characters: [...inlineEditing.shotCharacterIds],
      visual: {
        ...(targetShot.visual || {}),
        shot_size: inlineEditing.shotSize,
        camera_movement: inlineEditing.shotMovement,
        duration_seconds: Number(inlineEditing.shotDuration) || 5,
        lighting: inlineEditing.shotLighting.trim(),
        palette: inlineEditing.shotPalette.trim()
      }
    });
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
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

  loading.createRender = true;
  try {
    await assembleShotPackage(state.selectedSeriesSlug, state.selectedStoryboardId, state.selectedShotId);
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);

    const snapshotResponse = await createSnapshot({
      series_slug: state.selectedSeriesSlug,
      storyboard_id: state.selectedStoryboardId,
      shot_id: state.selectedShotId,
      provider_payload: {
        source: "frontend-workbench",
        note: "video-provider-pending"
      }
    });

    const jobResponse = await createVideoJobFromSnapshot({
      series_slug: state.selectedSeriesSlug,
      snapshot_id: snapshotResponse.item.id,
      type: "video_generation",
      provider: {
        name: "manual"
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

async function handleSubmitJob() {
  if (!state.selectedSeriesSlug || !state.selectedJobId) {
    setError("请先选择一个任务");
    return;
  }

  loading.submitJob = true;
  try {
    const response = await submitJob(state.selectedSeriesSlug, state.selectedJobId);
    await loadProductionData(state.selectedSeriesSlug);
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

async function handleAssembleShotPackage() {
  if (!state.selectedSeriesSlug || !state.selectedStoryboardId || !state.selectedShotId) {
    setError("请先选择一个镜头");
    return;
  }

  loading.shotPackage = true;
  try {
    await assembleShotPackage(state.selectedSeriesSlug, state.selectedStoryboardId, state.selectedShotId);
    await loadShotsForStoryboard(state.selectedSeriesSlug, state.selectedStoryboardId);
    setNotice(`镜头包已组装：${state.selectedShotId}`);
  } catch (error) {
    setError(error);
  } finally {
    loading.shotPackage = false;
  }
}

watch(
  () => state.selectedSeriesSlug,
  async (seriesSlug, previousSeriesSlug) => {
    if (seriesSlug !== previousSeriesSlug) {
      state.selectedEpisodeId = "";
      state.selectedStoryboardId = "";
      state.selectedShotId = "";
      state.selectedCharacterId = "";
      state.selectedSceneId = "";
      state.selectedJobId = "";
      state.characters = [];
      state.scenes = [];
      state.storyboards = [];
      state.shots = [];
      state.jobs = [];
      state.selectedCharacterIds = [];
      state.selectedCharacterBible = null;
      state.selectedScenePackage = null;
      state.selectedJob = null;
      state.selectedSnapshot = null;
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
        <section class="panel ">
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
                <button v-if="isEditingSeries(item.slug)" class="action-button dark compact-button"
                  :disabled="loading.updateSeries" @click.stop="handleUpdateSeries(item)">
                  {{ loading.updateSeries ? "保存中..." : "保存" }}
                </button>
                <button v-else class="action-button ghost compact-button" @click.stop="startSeriesEdit(item)">
                  编辑
                </button>
                <button v-if="isEditingSeries(item.slug)" class="action-button ghost compact-button"
                  @click.stop="cancelSeriesEdit">
                  取消
                </button>
                <button class="action-button ghost danger compact-button" :disabled="loading.deleteSeries"
                  @click.stop="handleDeleteSeries(item)">
                  {{ loading.deleteSeries ? "删除中..." : "删除" }}
                </button>
              </div>
            </div>

            <div v-if="!state.series.length && !loading.series" class="empty-state">
              还没有系列，先创建一个吧。
            </div>
          </div>
        </section>
        <section class="panel">
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
            <div class="inline-actions">
              <button class="action-button warm" :disabled="loading.createSeries" @click="handleCreateSeries">
                {{ loading.createSeries ? "创建中..." : "新建系列" }}
              </button>
            </div>
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

        <section class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">剧集</p>
              <h2>剧本与结构化拆解</h2>
            </div>
            <div class="inline-actions">
              <el-input v-model="forms.episodeName" class="field inline-field" type="text" placeholder="输入剧集名称" />
              <button class="action-button dark" style="flex-shrink: 0;" :disabled="loading.createEpisode"
                @click="handleCreateEpisode">
                {{ loading.createEpisode ? "创建中..." : "新建剧集" }}
              </button>
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
                <button v-if="isEditingEpisode(item.id)" class="action-button dark compact-button"
                  :disabled="loading.updateEpisode" @click.stop="handleUpdateEpisode(item)">
                  {{ loading.updateEpisode ? "保存中..." : "保存" }}
                </button>
                <button v-else class="action-button ghost compact-button" @click.stop="startEpisodeEdit(item)">
                  编辑
                </button>
                <button v-if="isEditingEpisode(item.id)" class="action-button ghost compact-button"
                  @click.stop="cancelEpisodeEdit">
                  取消
                </button>
                <button class="action-button ghost danger compact-button" :disabled="loading.deleteEpisode"
                  @click.stop="handleDeleteEpisode(item)">
                  {{ loading.deleteEpisode ? "删除中..." : "删除" }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <section class="editor-grid">
          <article class="panel editor-panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">原始剧本</p>
                <h2>剧本输入区</h2>
              </div>
              <div class="inline-actions compact-actions">
                <button class="action-button ghost" :disabled="loading.analyzeScript" @click="handleAnalyzeScript">
                  {{ loading.analyzeScript ? "分析中..." : "AI 拆解剧本" }}
                </button>
                <button class="action-button dark" :disabled="loading.saveRaw" @click="handleSaveRawScript">
                  {{ loading.saveRaw ? "保存中..." : "保存原稿" }}
                </button>
              </div>
            </div>
            <el-input v-model="state.rawScript" class="field-textarea editor-textarea" type="textarea"
              :autosize="{ minRows: 22, maxRows: 30 }" resize="auto" placeholder="在这里粘贴或编写原始剧本内容。" />
          </article>

          <article class="panel editor-panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">结构化结果</p>
                <h2>解析 JSON</h2>
              </div>
              <button class="action-button dark" :disabled="loading.saveParsed" @click="handleSaveParsedScript">
                {{ loading.saveParsed ? "保存中..." : "保存 JSON" }}
              </button>
            </div>
            <el-input v-model="state.parsedScriptText" class="field-textarea editor-textarea code-textarea"
              type="textarea" :autosize="{ minRows: 22, maxRows: 30 }" resize="auto" placeholder="" />
          </article>
        </section>

        <section class="studio-grid">
          <article class="panel">
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
              <div class="inline-actions" style="margin-bottom: 12px;">
                <button class="action-button warm" :disabled="loading.createCharacter" @click="handleCreateCharacter">
                  {{ loading.createCharacter ? "创建中..." : "新建角色" }}
                </button>
              </div>
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
                  <button v-if="isEditingCharacter(item.id)" class="action-button dark compact-button"
                    :disabled="loading.updateCharacter" @click.stop="handleUpdateCharacter(item)">
                    {{ loading.updateCharacter ? "保存中..." : "保存" }}
                  </button>
                  <button v-else class="action-button ghost compact-button" @click.stop="startCharacterEdit(item)">
                    编辑
                  </button>
                  <button v-if="isEditingCharacter(item.id)" class="action-button ghost compact-button"
                    @click.stop="cancelCharacterEdit">
                    取消
                  </button>
                  <button class="action-button ghost danger compact-button" :disabled="loading.deleteCharacter"
                    @click.stop="handleDeleteCharacter(item)">
                    {{ loading.deleteCharacter ? "删除中..." : "删除" }}
                  </button>
                </div>
              </div>
            </div>
          </article>

          <article class="panel">
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
              <div class="inline-actions" style="margin-bottom: 12px;">
                <button class="action-button warm" :disabled="loading.createScene" @click="handleCreateScene">
                  {{ loading.createScene ? "创建中..." : "新建场景" }}
                </button>
              </div>
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
                  <button v-if="isEditingScene(item.id)" class="action-button dark compact-button"
                    :disabled="loading.updateScene" @click.stop="handleUpdateScene(item)">
                    {{ loading.updateScene ? "保存中..." : "保存" }}
                  </button>
                  <button v-else class="action-button ghost compact-button" @click.stop="startSceneEdit(item)">
                    编辑
                  </button>
                  <button v-if="isEditingScene(item.id)" class="action-button ghost compact-button"
                    @click.stop="cancelSceneEdit">
                    取消
                  </button>
                  <button class="action-button ghost danger compact-button" :disabled="loading.deleteScene"
                    @click.stop="handleDeleteScene(item)">
                    {{ loading.deleteScene ? "删除中..." : "删除" }}
                  </button>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section class="lab-grid">
          <article class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">角色工坊</p>
                <h2>角色圣经</h2>
              </div>
              <div class="inline-actions">
                <button class="action-button warm" :disabled="loading.characterAssets || !selectedCharacter"
                  @click="handleGenerateCharacterAssets('reference_plus_text')">
                  {{ loading.characterAssets ? "生成中..." : (hasUploadedCharacterSourceImages ? "参考图+文字生成" : "按文字生成角色圣经") }}
                </button>
                <button v-if="hasUploadedCharacterSourceImages" class="action-button dark"
                  :disabled="loading.characterAssets || !selectedCharacter"
                  @click="handleGenerateCharacterAssets('reference_subject_only')">
                  {{ loading.characterAssets ? "生成中..." : "仅按参考图生成拼图" }}
                </button>
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
                <input ref="characterSourceInput" class="field file-input" type="file" accept="image/*" multiple
                  @change="handleCharacterSourceFileChange" />
                <button class="action-button dark" :disabled="loading.characterUpload || !characterSourceFiles.length"
                  @click="handleUploadCharacterSourceImages">
                  {{ loading.characterUpload ? "上传中..." : "上传参考图" }}
                </button>
              </div>

              <div v-if="selectedCharacterSourceEntries.length" class="reference-grid">
                <div v-for="image in selectedCharacterSourceEntries" :key="image.key" class="reference-card">
                  <div class="reference-header">
                    <strong>上传参考</strong>
                    <small>{{ image.label }}</small>
                  </div>
                  <button class="action-button ghost danger compact-button"
                    :disabled="loading.deleteCharacterSourceImage"
                    @click="handleDeleteCharacterSourceImage(image.path)">
                    {{ loading.deleteCharacterSourceImage ? "删除中..." : "删除参考图" }}
                  </button>
                  <el-image class="preview-image" :src="assetUrl(image.path)"
                    :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                    preview-teleported />
                </div>
              </div>

              <div class="anchor-grid">
                <article v-for="(value, key) in selectedCharacter.anchors" :key="key" class="anchor-card">
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

          <article class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">场景工坊</p>
                <h2>场景包</h2>
              </div>
              <button class="action-button warm" :disabled="loading.sceneAssets || !selectedScene"
                @click="handleGenerateSceneAssets">
                {{ loading.sceneAssets ? "生成中..." : "生成场景参考拼图" }}
              </button>
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
        <section class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">分镜</p>
              <h2>镜头配置</h2>
            </div>
            <button class="action-button dark" :disabled="loading.createStoryboard" @click="handleCreateStoryboard">
              {{ loading.createStoryboard ? "创建中..." : "新建分镜板" }}
            </button>
          </div>

          <div class="mini-list">
            <div v-for="item in filteredStoryboards" :key="item.id" class="mini-card selectable" style="display: flex;"
              :class="{ active: item.id === state.selectedStoryboardId }">
              <div class="item-body" @click="state.selectedStoryboardId = item.id">
                <strong>{{ item.id }}</strong>
                <span>{{ item.episode_id }}</span>
                <small>{{ item.shot_ids.length }} 个镜头</small>
              </div>
              <div class="item-actions">
                <button class="action-button ghost danger compact-button" :disabled="loading.deleteStoryboard"
                  @click.stop="handleDeleteStoryboard(item)">
                  {{ loading.deleteStoryboard ? "删除中..." : "删除" }}
                </button>
              </div>
            </div>
          </div>

          <div class="subsection">
            <h3>新建镜头</h3>
            <div class="form-stack">
              <el-select v-model="forms.shotSceneId" class="field-select" placeholder="选择关联场景" clearable>
                <el-option v-for="item in state.scenes" :key="item.id" :label="`${item.name} · ${item.id}`"
                  :value="item.id" />
              </el-select>

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

              <el-input-number v-model="forms.shotDuration" class="field-number" :min="1" :max="30" :step="1"
                placeholder="输入镜头时长">
                <template #suffix>
                  <span>镜头时长</span>
                </template>
              </el-input-number>

              <el-checkbox-group v-model="state.selectedCharacterIds" class="check-grid">
                <el-checkbox v-for="item in state.characters" :key="item.id" :value="item.id" class="check-card">
                  {{ item.name }}
                </el-checkbox>
              </el-checkbox-group>

              <button class="action-button warm" :disabled="loading.createShot" @click="handleCreateShot">
                {{ loading.createShot ? "创建中..." : "生成镜头卡" }}
              </button>
            </div>
          </div>

          <div class="mini-list">
            <div v-for="item in state.shots" :key="item.id" class="mini-card selectable"
              :class="{ active: item.id === state.selectedShotId }">
              <div class="item-body" @click="state.selectedShotId = item.id">
                <template v-if="isEditingShot(item.id)">
                  <div class="item-editor">
                    <el-select v-model="inlineEditing.shotSceneId" class="field-select" placeholder="选择关联场景">
                      <el-option v-for="scene in state.scenes" :key="scene.id" :label="`${scene.name} · ${scene.id}`"
                        :value="scene.id" />
                    </el-select>
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
                      <el-input v-model="inlineEditing.shotLighting" class="field" type="text" placeholder="输入光线关键词" />
                      <el-input v-model="inlineEditing.shotPalette" class="field" type="text" placeholder="输入色调关键词" />
                    </div>
                    <el-input-number v-model="inlineEditing.shotDuration" class="field-number" :min="1" :max="30"
                      :step="1" />
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
                  <span>{{ formatShotSize(item.visual.shot_size) }} ·
                    {{ formatShotMovement(item.visual.camera_movement) }}</span>
                  <small>场景：{{ formatSceneLabel(item.scene_id) }}</small>
                  <small>光线：{{ formatShotKeyword(item.visual.lighting) }}</small>
                  <small>色调：{{ formatShotKeyword(item.visual.palette) }}</small>
                  <small>{{ item.visual.duration_seconds }} 秒 · {{ (item.characters || []).length }} 个角色</small>
                </template>
              </div>
              <div class="item-actions">
                <button v-if="isEditingShot(item.id)" class="action-button dark compact-button"
                  :disabled="loading.updateShot" @click.stop="handleUpdateShot(item)">
                  {{ loading.updateShot ? "保存中..." : "保存" }}
                </button>
                <button v-else class="action-button ghost compact-button" @click.stop="startShotEdit(item)">
                  编辑
                </button>
                <button v-if="isEditingShot(item.id)" class="action-button ghost compact-button"
                  @click.stop="cancelShotEdit">
                  取消
                </button>
                <button class="action-button ghost danger compact-button" :disabled="loading.deleteShot"
                  @click.stop="handleDeleteShot(item)">
                  {{ loading.deleteShot ? "删除中..." : "删除" }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">执行区</p>
              <h2>快照与任务</h2>
            </div>
          </div>

          <p class="message muted">
            视频模型暂未接入。当前可以先完整测试剧本拆解、角色生成、场景生成、镜头包组装，以及任务草稿落盘。
          </p>

          <button class="action-button dark full-width" :disabled="loading.shotPackage"
            @click="handleAssembleShotPackage">
            {{ loading.shotPackage ? "组装中..." : "组装镜头包" }}
          </button>

          <button class="action-button warm full-width" :disabled="loading.createRender"
            @click="handleCreateRenderTask">
            {{ loading.createRender ? "生成中..." : "生成任务草稿" }}
          </button>

          <div v-if="selectedShot" class="focus-card">
            <span>当前镜头</span>
            <strong>{{ selectedShot.id }}</strong>
            <small>{{ selectedShot.scene_id }} · {{ selectedShot.visual.duration_seconds }} 秒</small>
          </div>

          <div v-if="selectedShotPromptPackage?.positive" class="meta-panel">
            <div class="meta-row">
              <span>参考图数量</span>
              <strong>{{ selectedShotPromptPackage.reference_images?.length || 0 }}</strong>
            </div>
            <div class="meta-row">
              <span>提示词预览</span>
              <strong class="prompt-preview">{{ selectedShotPromptPackage.positive }}</strong>
            </div>
          </div>

          <div class="mini-list">
            <div v-for="item in state.jobs" :key="item.id" class="mini-card selectable"
              :class="{ active: item.id === state.selectedJobId }">
              <div class="item-body" @click="state.selectedJobId = item.id">
                <strong>{{ item.id }}</strong>
                <span>{{ formatStatus(item.status) }}</span>
                <small>关联快照：{{ item.snapshot_id || "暂无" }}</small>
              </div>
              <div class="item-actions">
                <button class="action-button ghost compact-button" @click.stop="handleOpenJobSnapshot(item)">
                  查看快照
                </button>
                <button class="action-button ghost danger compact-button" :disabled="loading.deleteJob"
                  @click.stop="handleDeleteJob(item)">
                  {{ loading.deleteJob ? "删除中..." : "删除" }}
                </button>
              </div>
            </div>
            <div v-if="!state.jobs.length" class="empty-state">当前还没有任务草稿。</div>
          </div>

          <div v-if="selectedJobComputed" class="subsection">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">当前任务</p>
                <h3>{{ selectedJobComputed.id }}</h3>
              </div>
              <div class="inline-actions compact-actions">
                <button class="action-button ghost"
                  :disabled="loading.snapshotDetail || !selectedJobComputed.snapshot_id"
                  @click="handleOpenJobSnapshot()">
                  {{ loading.snapshotDetail ? "加载中..." : "查看快照" }}
                </button>
                <button class="action-button ghost"
                  :disabled="loading.submitJob || loading.jobDetail || selectedJobComputed.status === 'submitting'"
                  @click="handleSubmitJob">
                  {{ loading.submitJob ? "提交中..." : "提交任务" }}
                </button>
                <button class="action-button dark"
                  :disabled="loading.refreshJob || loading.jobDetail || !selectedJobComputed.remote?.task_id"
                  @click="handleRefreshJob">
                  {{ loading.refreshJob ? "刷新中..." : "刷新状态" }}
                </button>
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
                <span>提交方式</span>
                <strong>{{ formatSubmitMode(selectedJobComputed.provider?.submit_mode) }}</strong>
              </div>
              <div class="meta-row">
                <span>远端任务 ID</span>
                <strong>{{ selectedJobComputed.remote?.task_id || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>远端响应文件</span>
                <strong>{{ selectedJobComputed.remote?.raw_response_path || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>视频文件</span>
                <strong>{{ selectedJobComputed.result?.video_path || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>封面文件</span>
                <strong>{{ selectedJobComputed.result?.cover_path || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>错误信息</span>
                <strong>{{ selectedJobComputed.error?.message || "无" }}</strong>
              </div>
            </div>

            <div v-if="state.selectedSnapshot" class="meta-panel">
              <div class="meta-row">
                <span>关联快照</span>
                <strong>{{ state.selectedSnapshot.id }}</strong>
              </div>
              <div class="meta-row">
                <span>所属分镜板 / 镜头</span>
                <strong>{{ state.selectedSnapshot.storyboard_id }} · {{ state.selectedSnapshot.shot_id }}</strong>
              </div>
              <div class="meta-row">
                <span>引用图片数量</span>
                <strong>{{ selectedSnapshotImageCount }}</strong>
              </div>
              <div class="meta-row">
                <span>镜头卡路径</span>
                <strong>{{ state.selectedSnapshot.inputs?.shot_card_path || "暂无" }}</strong>
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

            <div v-if="selectedJobCoverUrl || selectedJobVideoUrl" class="reference-grid">
              <div v-if="selectedJobCoverUrl" class="reference-card">
                <div class="reference-header">
                  <strong>封面</strong>
                  <small>{{ selectedJobComputed.result?.cover_path }}</small>
                </div>
                <el-image class="preview-image" :src="selectedJobCoverUrl"
                  :preview-src-list="selectedJobCoverUrl ? [selectedJobCoverUrl] : []" :initial-index="0" fit="cover"
                  preview-teleported />
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
              <label class="code-label">提交请求体</label>
              <el-input :model-value="selectedJobRequestText" class="field-textarea code-textarea job-code"
                type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
            </div>

            <div
              v-if="selectedJobComputed.remote?.raw_response_path || Object.keys(selectedJobComputed.remote?.raw_response || {}).length"
              class="form-stack">
              <label class="code-label">远端返回</label>
              <el-input :model-value="selectedJobResponseText" class="field-textarea code-textarea job-code"
                type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
            </div>
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
              <span>输出根目录</span>
              <strong>output/</strong>
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
  margin: 0;
  min-height: 100vh;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at 15% 20%, rgba(255, 186, 107, 0.16), transparent 25%),
    radial-gradient(circle at 80% 0%, rgba(84, 120, 255, 0.18), transparent 28%),
    linear-gradient(145deg, #0d1426 0%, #101826 38%, #172336 100%);
  color: #edf2f7;
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
  background: rgba(255, 189, 115, 0.16);
}

:global(.el-select-dropdown__item.selected) {
  color: #ffbd73;
  font-weight: 700;
}

.shell {
  width: min(1600px, calc(100% - 40px));
  margin: 0 auto;
  padding: 32px 0 48px;
}

.masthead {
  display: grid;
  grid-template-columns: 1.5fr minmax(320px, 380px);
  gap: 18px;
  margin-bottom: 18px;
}

.eyebrow,
.panel-kicker {
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.24em;
  font-size: 11px;
  color: #ffbd73;
}

h1 {
  margin: 0 0 14px;
  font-size: clamp(42px, 7vw, 64px);
  line-height: 0.95;
  letter-spacing: -0.04em;
}

h2,
h3 {
  margin: 0;
}

h2 {
  font-size: 24px;
}

h3 {
  font-size: 16px;
}

.lead,
.status-copy,
.inline-note,
.upload-copy {
  margin: 0;
  line-height: 1.7;
  color: rgba(237, 242, 247, 0.76);
}

.status-panel,
.panel {
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 26px;
  background: rgba(9, 15, 28, 0.62);
  backdrop-filter: blur(20px);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
}

.status-panel {
  padding: 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  width: fit-content;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-dot.ok {
  background: #34d399;
  box-shadow: 0 0 16px rgba(52, 211, 153, 0.65);
}

.status-dot.offline {
  background: #fb7185;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(260px, 300px) minmax(0, 1fr) minmax(320px, 380px);
  gap: 18px;
  align-items: start;
}

.column {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.panel {
  padding: 22px;
  min-width: 0;
  overflow: hidden;
}

.panel-accent {
  background:
    linear-gradient(165deg, rgba(255, 185, 105, 0.18), rgba(255, 255, 255, 0.04)),
    rgba(9, 15, 28, 0.74);
}

.hero-panel {
  background:
    radial-gradient(circle at right top, rgba(255, 188, 109, 0.12), transparent 30%),
    rgba(9, 15, 28, 0.62);
}

.panel-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  min-width: 0;
  flex-wrap: wrap;
}

.pill,
.series-slug {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(237, 242, 247, 0.82);
  font-size: 12px;
}

.form-stack,
.list-stack,
.meta-list,
.mini-list,
.lab-stack {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.field {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  color: #edf2f7;
  outline: none;
}

.field::placeholder {
  color: rgba(237, 242, 247, 0.34);
}

.field:focus {
  border-color: rgba(255, 189, 115, 0.7);
  box-shadow: 0 0 0 4px rgba(255, 189, 115, 0.12);
}

.file-input {
  padding-block: 12px;
  cursor: pointer;
}

.file-input::file-selector-button {
  margin-right: 12px;
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(255, 204, 136, 0.9), rgba(255, 154, 90, 0.9));
  color: #0f172a;
  font-weight: 700;
  cursor: pointer;
}

.field-select {
  width: 100%;
  min-width: 0;
}

.field-select :deep(.el-select__wrapper) {
  min-height: 50px;
  border-radius: 16px;
  padding: 0 16px;
  box-shadow: none;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.field-select :deep(.el-select__wrapper.is-focused) {
  border-color: rgba(255, 189, 115, 0.7);
  box-shadow: 0 0 0 4px rgba(255, 189, 115, 0.12);
}

.field-select :deep(.el-select__placeholder),
.field-select :deep(.el-select__selected-item),
.field-select :deep(.el-select__input-wrapper),
.field-select :deep(.el-select__caret) {
  color: #edf2f7;
}

.field-textarea {
  min-height: 100px;
}

.field-textarea.compact {
  min-height: 82px;
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
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #edf2f7;
  box-shadow: none;
}

.field-textarea :deep(.el-textarea__inner::placeholder) {
  color: rgba(237, 242, 247, 0.34);
}

.field-textarea :deep(.el-textarea__inner:focus) {
  border-color: rgba(255, 189, 115, 0.7);
  box-shadow: 0 0 0 4px rgba(255, 189, 115, 0.12);
}

.field-number {
  width: 100%;
}

.field-number :deep(.el-input__wrapper) {
  min-height: 50px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
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

.action-button {
  border: none;
  border-radius: 16px;
  padding: 14px 16px;
  color: #0f172a;
  cursor: pointer;
  font-weight: 700;
  transition: transform 160ms ease, opacity 160ms ease;
}

.action-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-button.warm {
  background: linear-gradient(135deg, #ffcc88 0%, #ff9a5a 100%);
}

.action-button.dark {
  background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
}

.action-button.ghost {
  color: #edf2f7;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.18), rgba(16, 185, 129, 0.24));
  border: 1px solid rgba(52, 211, 153, 0.28);
}

.action-button.danger {
  color: #ffe4e6;
  background: linear-gradient(135deg, rgba(190, 24, 93, 0.22), rgba(244, 63, 94, 0.24));
  border: 1px solid rgba(251, 113, 133, 0.3);
}

.action-button.full-width {
  width: 100%;
  margin-bottom: 14px;
}

.compact-button {
  padding: 10px 12px;
  font-size: 12px;
}

.list-card,
.episode-chip,
.mini-card.selectable {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: inherit;
  text-align: left;
  cursor: default;
}

.list-card,
.mini-card,
.focus-card,
.anchor-card,
.reference-card,
.meta-panel,
.upload-panel {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  min-width: 0;
  overflow: hidden;
}

.list-card.active,
.mini-card.selectable.active,
.episode-chip.active {
  border-color: rgba(255, 189, 115, 0.56);
  background: linear-gradient(140deg, rgba(255, 189, 115, 0.18), rgba(255, 255, 255, 0.05));
}

.item-body {
  display: grid;
  gap: 6px;
  min-width: 0;
  cursor: pointer;
  flex: 1;
}

.item-editor {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.item-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 4px;
  flex-shrink: 0;
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
}

.summary-grid,
.studio-grid,
.lab-grid,
.editor-grid,
.reference-grid,
.anchor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  min-width: 0;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.summary-card {
  padding: 8px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  min-width: 0;
}

.summary-card span {
  display: block;
  margin-bottom: 6px;
  color: rgba(237, 242, 247, 0.66);
}

.summary-card strong {
  font-size: 28px;
}

.code-label {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(237, 242, 247, 0.62);
}

.inline-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
  flex-wrap: nowrap;
}

.compact-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.inline-field {
  min-width: 180px;
}

.episode-strip {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.episode-chip {
  display: flex;
  gap: 20px;
  padding: 12px 14px;
  border-radius: 16px;
  min-width: 220px;
}

.subsection {
  display: grid;
  gap: 12px;
  margin: 18px 0;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.split-grid,
.check-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
}

.check-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
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
  border-color: rgba(255, 189, 115, 0.56);
  background: linear-gradient(140deg, rgba(255, 189, 115, 0.18), rgba(255, 255, 255, 0.05));
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
  border: 1px dashed rgba(255, 255, 255, 0.12);
  color: rgba(237, 242, 247, 0.5);
}

.meta-panel,
.meta-list {
  gap: 10px;
}

.meta-row,
.meta-list>div {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.prompt-preview {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.6;
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
  padding: 14px 16px;
  border-radius: 16px;
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
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(237, 242, 247, 0.7);
}

.empty-state {
  padding: 18px;
  border-radius: 18px;
  border: 1px dashed rgba(255, 255, 255, 0.12);
  color: rgba(237, 242, 247, 0.58);
}

@media (max-width: 1420px) {
  .workspace {
    grid-template-columns: 280px 1fr;
  }

  .column-right {
    grid-column: 1 / -1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {

  .masthead,
  .workspace,
  .editor-grid,
  .studio-grid,
  .lab-grid,
  .summary-grid,
  .column-right,
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
}

@media (max-width: 640px) {
  .shell {
    width: min(100% - 24px, 1600px);
    padding-top: 20px;
  }

  .panel,
  .status-panel {
    padding: 18px;
    border-radius: 22px;
  }

  h1 {
    font-size: 42px;
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
