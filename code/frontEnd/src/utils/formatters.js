import {
  shotAnchorModeOptions,
  shotAspectRatioOptions,
  shotInputModeOptions,
  shotMovementOptions,
  shotResolutionOptions,
  shotSizeOptions,
  storyboardProductionModeOptions,
  supportedShotAnchorModes,
  supportedShotInputModes
} from "../constants/options";

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

export function formatShotBatchCounts(batch) {
  const item = batch || {};
  const totalCount = Number(item.total_count || 0) || 0;
  const successCount = Number(item.success_count || 0) || 0;
  const failedCount = Number(item.failed_count || 0) || 0;
  const pendingCount = Number(item.pending_count || 0) || 0;
  const processingCount = Number(item.processing_count || 0) || 0;
  return `${successCount}/${totalCount} 成功 · ${failedCount} 失败 · ${pendingCount + processingCount} 待处理`;
}

export function formatShotBatchProgress(batch) {
  const item = batch || {};
  const totalCount = Number(item.total_count || 0) || 0;
  const successCount = Number(item.success_count || 0) || 0;
  if (!totalCount) {
    return "0%";
  }
  return `${Math.round((successCount / totalCount) * 100)}%`;
}

export function formatHealth(value) {
  return healthTextMap[value] || value || "未知";
}

export function formatStatus(value) {
  return entityStatusTextMap[value] || value || "未设置";
}

export function formatAnchorKey(value) {
  return anchorLabelMap[value] || value;
}

export function formatShotSize(value) {
  return shotSizeOptions.find((item) => item.value === value)?.label || value || "未设置";
}

export function formatShotMovement(value) {
  return shotMovementOptions.find((item) => item.value === value)?.label || value || "未设置";
}

export function formatShotInputMode(value) {
  return shotInputModeOptions.find((item) => item.value === value)?.label || value || "未设置";
}

export function normalizeShotAnchorMode(value) {
  return supportedShotAnchorModes.has(value) ? value : "auto";
}

export function formatShotAnchorMode(value) {
  return shotAnchorModeOptions.find((item) => item.value === normalizeShotAnchorMode(value))?.label || "自动";
}

export function normalizeShotAnchorOverrides(raw, characterIds = []) {
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

export function buildShotAnchorStrategyPayload(source, characterIds = []) {
  return {
    mode: normalizeShotAnchorMode(source.shotAnchorMode),
    per_character: normalizeShotAnchorOverrides(source.shotAnchorOverrides, characterIds)
  };
}

export function getShotAnchorOverrideValue(source, characterId) {
  if (!characterId) {
    return "auto";
  }
  return normalizeShotAnchorMode(source.shotAnchorOverrides?.[characterId]);
}

export function setShotAnchorOverrideValue(source, characterId, value) {
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

export function countShotAnchorOverrides(raw, characterIds = []) {
  return Object.keys(normalizeShotAnchorOverrides(raw, characterIds)).length;
}

export function normalizeStoryboardProductionMode(value) {
  return storyboardProductionModeOptions.some((item) => item.value === value) ? value : "shot_pipeline";
}

export function formatStoryboardProductionMode(value) {
  return (
    storyboardProductionModeOptions.find((item) => item.value === normalizeStoryboardProductionMode(value))?.label ||
    "分镜生产"
  );
}

export function formatSnapshotSource(snapshot) {
  const source = snapshot || {};
  if (source.scene_id && !source.shot_id) {
    return `${source.storyboard_id || "未绑定分镜板"} · ${source.scene_id}`;
  }
  return `${source.storyboard_id || "未绑定分镜板"} · ${source.shot_id || "scene_direct"}`;
}

export function formatShotAspectRatio(value) {
  return shotAspectRatioOptions.find((item) => item.value === value)?.label || value || "未设置";
}

export function formatShotResolution(value) {
  return shotResolutionOptions.find((item) => item.value === value)?.label || value || "未设置";
}

export function parseMediaPaths(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function serializeMediaPaths(values) {
  return Array.isArray(values) ? values.filter(Boolean).join("\n") : "";
}

export function normalizeShotInputMode(value) {
  return supportedShotInputModes.has(value) ? value : "reference_image";
}

export function isReferenceMode(value) {
  return normalizeShotInputMode(value) === "reference_image";
}

export function isFirstLastFrameMode(value) {
  return normalizeShotInputMode(value) === "first_last_frame";
}

export function isTextOnlyMode(value) {
  return normalizeShotInputMode(value) === "text_only";
}

export function normalizeShotDuration(value) {
  return Math.max(1, Math.min(15, Number(value) || 5));
}

export function normalizeShotGenerationCount(value) {
  return Math.max(1, Math.min(4, Number(value) || 1));
}

export function buildShotMediaPayload(source) {
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

export function formatShotKeyword(value, fallback = "未设置") {
  const normalized = String(value || "").trim();
  return normalized || fallback;
}

export function formatPromptGenerationMode(value) {
  if (value === "ai_refined") {
    return "AI 润色";
  }
  if (value === "fallback_template") {
    return "模板回退";
  }
  return value || "未知";
}

export function formatPromptVariantLabel(value) {
  if (value === "ai_refined") {
    return "AI 润色版";
  }
  if (value === "fallback_template") {
    return "本地模板版";
  }
  return value || "未知版本";
}

export function formatProviderName(value) {
  if (!value || value === "manual") {
    return "手动占位";
  }
  if (value === "doubao-seedance-2-0") {
    return "Doubao Seedance 2.0";
  }
  return value;
}

export function formatJobApiKind(provider) {
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

export function inferSeedanceModeFromContent(content) {
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

export function formatSeedanceMode(value) {
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

export function normalizeSeedanceRequestBodyForDisplay(job) {
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
  const fallbackImageItems = (
    imageItemsFromContent.length
      ? imageItemsFromContent
      : legacyMediaItems.length
        ? legacyMediaItems
        : legacyImagePaths.map((path) => ({
            type: "image_url",
            image_url: {
              url: path
            }
          }))
  );

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

export function buildSeedanceRequestSummary(requestBody) {
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

export function getJobSeedanceSummary(job) {
  return buildSeedanceRequestSummary(normalizeSeedanceRequestBodyForDisplay(job));
}

export function formatJobOutputSummary(job) {
  const summary = getJobSeedanceSummary(job);
  const durationText = summary.duration ? `${summary.duration} 秒` : "未设时长";
  return `${durationText} · ${summary.count} 条 · ${summary.hasAudio ? "有声" : "无声"}`;
}

export function formatJobReferenceSummary(job) {
  const summary = getJobSeedanceSummary(job);
  if (summary.mode === "reference_image") {
    return `${summary.imageCount} 张参考图`;
  }
  if (summary.mode === "first_last_frame") {
    return `${summary.imageCount} 张首尾帧`;
  }
  return "无图像参考";
}

export function formatReadableField(value, fallback = "暂无") {
  const normalized = String(value || "").trim();
  return normalized || fallback;
}

export function getReadableSceneInfo(scene) {
  return scene?.readable || {};
}

export function getReadableShotInfo(shot) {
  return shot?.readable || {};
}

export function normalizeDialogueEntries(dialogues) {
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

export function formatDialogueEntries(dialogues) {
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

export function serializeDialogueEntries(dialogues) {
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

export function parseDialogueText(value) {
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

export function buildShotStoryPayload(source) {
  return {
    description: String(source.shotStoryDescription || "").trim(),
    emotion: String(source.shotStoryEmotion || "").trim(),
    beat: String(source.shotStoryBeat || "").trim(),
    raw_script_excerpt: String(source.shotStoryRawExcerpt || "").trim()
  };
}

export function buildShotDialoguePayload(source) {
  return parseDialogueText(source.shotStoryDialogue);
}

export function formatLegacyCameraSummary(camera) {
  const source = camera || {};
  const parts = [
    source.angle ? `机位角度：${source.angle}` : "",
    source.movement ? `运镜方式：${source.movement}` : "",
    source.shot_size ? `景别：${source.shot_size}` : ""
  ].filter(Boolean);
  return parts.join("；");
}

export function normalizeMatchText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[.,/#!$%^&*;:{}=\-_`~()"'?<>[\]\\|，。！？；：、“”‘’（）【】《》·]/g, "");
}

export function firstNonEmptyText(...values) {
  for (const value of values) {
    const text = String(value || "").trim();
    if (text) {
      return text;
    }
  }
  return "";
}

export function getParsedShotDialogueEntries(shot) {
  return Array.isArray(shot?.dialogues)
    ? shot.dialogues
        .map((item) => ({
          character: String(item?.character || "").trim(),
          text: String(item?.text || "").trim()
        }))
        .filter((item) => item.character || item.text)
    : [];
}

export function buildParsedShotDescription(scene, shot, sceneIndex, shotIndex) {
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

export function serializeCharacterEntries(characters) {
  return Array.isArray(characters)
    ? characters
        .map((item) => String(item || "").trim())
        .filter(Boolean)
        .join("、")
    : "";
}

export function parseCharacterText(value) {
  return String(value || "")
    .split(/\r?\n|[，,、]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function buildParsedCameraSummary(camera) {
  const source = camera || {};
  const parts = [
    source.angle ? `机位角度：${source.angle}` : "",
    source.movement ? `运镜方式：${source.movement}` : "",
    source.shot_size ? `景别：${source.shot_size}` : ""
  ].filter(Boolean);
  return parts.join("；");
}
