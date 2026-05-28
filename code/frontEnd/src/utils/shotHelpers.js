import {
  formatShotAnchorMode,
  normalizeShotAnchorOverrides,
  normalizeShotInputMode,
  parseMediaPaths,
  serializeMediaPaths
} from "./formatters";

export function formatShotAnchorOverridesDisplay(anchorStrategy, characterIds = [], characters = []) {
  const overrides = normalizeShotAnchorOverrides(anchorStrategy?.per_character, characterIds);
  return (characterIds || [])
    .filter((characterId) => overrides[characterId])
    .map((characterId) => {
      const name = characters.find((item) => item.id === characterId)?.name || characterId;
      return `${name}：${formatShotAnchorMode(overrides[characterId])}`;
    })
    .join("；");
}

export function getAutoReferenceSummary(characterIds, sceneId, characters = [], scenes = []) {
  const normalizedCharacterIds = (characterIds || []).filter(Boolean);
  const characterCount = normalizedCharacterIds.length;
  const sceneCount = sceneId ? 1 : 0;
  const totalCount = characterCount + sceneCount;
  const characterNames = normalizedCharacterIds
    .map((characterId) => characters.find((item) => item.id === characterId)?.name || characterId)
    .filter(Boolean);
  const sceneName = scenes.find((item) => item.id === sceneId)?.name || sceneId || "";

  return {
    totalCount,
    characterCount,
    sceneCount,
    characterNames,
    sceneName
  };
}

export function applyShotModeRules(source) {
  const mode = normalizeShotInputMode(source.shotInputMode);
  source.shotInputMode = mode;
  if (mode !== "first_last_frame") {
    source.shotFirstFramePath = "";
    source.shotLastFramePath = "";
  }
  source.shotReferenceImagesText = "";
}

export function validateShotSource(source) {
  const mode = normalizeShotInputMode(source.shotInputMode);
  if (mode === "first_last_frame" && !String(source.shotFirstFramePath || "").trim()) {
    throw new Error("首尾帧生成模式下必须上传首帧图");
  }
}

export function appendMediaPaths(currentValue, nextPaths) {
  return serializeMediaPaths([...new Set([...parseMediaPaths(currentValue), ...nextPaths.filter(Boolean)])]);
}

export function getShotMediaEntries(source) {
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

export function removeShotMediaEntry(source, kind, path = "") {
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

export function formatSceneLabel(sceneId, scenes = []) {
  const scene = scenes.find((item) => item.id === sceneId);
  if (!scene) {
    return sceneId || "未关联场景";
  }
  return `${scene.name} · ${scene.id}`;
}
