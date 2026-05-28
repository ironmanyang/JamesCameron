import {
  buildParsedCameraSummary,
  buildParsedShotDescription,
  buildShotMediaPayload,
  firstNonEmptyText,
  formatDialogueEntries,
  getParsedShotDialogueEntries,
  getReadableSceneInfo,
  getReadableShotInfo,
  normalizeDialogueEntries,
  normalizeMatchText,
  normalizeShotDuration,
  normalizeShotGenerationCount,
  normalizeShotInputMode,
  parseCharacterText,
  parseDialogueText,
  serializeCharacterEntries,
  serializeDialogueEntries
} from "../utils/formatters";

export function useParsedScriptEditor({
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
}) {
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
        parsed.extracted_entities.scenes = [
          ...new Set(
            (parsed.scenes || [])
              .map((sceneItem) => String(sceneItem?.location || "").trim())
              .filter(Boolean)
          )
        ];
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

  function copyTextToClipboard(text) {
    const content = String(text || "").trim();
    if (!content) {
      throw new Error("没有可复制的内容");
    }
    if (navigator?.clipboard?.writeText) {
      return navigator.clipboard.writeText(content);
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
    return Promise.resolve();
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

  async function importReadableShotDraft(scene, shot, sceneIndex, shotIndex) {
    const sceneId = resolveParsedSceneId(scene);
    if (!sceneId) {
      throw new Error("未匹配到可用场景，请先创建或选择对应场景");
    }

    const { matchedIds, unmatchedNames } = resolveParsedCharacterIds(shot);
    const dialogues = getParsedShotDialogueEntries(shot);
    const story = buildParsedShotStoryPayload(shot);
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
          shot_size: mapParsedShotSize(shot?.camera?.shot_size),
          camera_angle: mapParsedCameraAngle(shot?.camera?.angle),
          camera_movement: mapParsedShotMovement(shot?.camera?.movement),
          lens: "50mm",
          depth_of_field: "medium",
          lighting: forms.shotLighting.trim(),
          palette: forms.shotPalette.trim(),
          duration_seconds: normalizeShotDuration(forms.shotDuration)
        }
      }
    });

    return {
      item: response,
      sceneId,
      unmatchedNames
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

  async function handleImportAllReadableShots() {
    if (!state.selectedSeriesSlug || !state.selectedStoryboardId) {
      setError("请先选择一个分镜板，再导入镜头卡草稿");
      return;
    }
    if (!parsedScriptObject.value?.scenes?.length) {
      setError("当前没有可导入的解析分镜");
      return;
    }

    loading.importParsedShot = true;
    try {
      const importedIds = [];
      const unmatchedNames = new Set();
      let lastSceneId = "";

      for (let sceneIndex = 0; sceneIndex < parsedScriptObject.value.scenes.length; sceneIndex += 1) {
        const scene = parsedScriptObject.value.scenes[sceneIndex];
        const shots = Array.isArray(scene?.shots) ? scene.shots : [];
        for (let shotIndex = 0; shotIndex < shots.length; shotIndex += 1) {
          const result = await importReadableShotDraft(scene, shots[shotIndex], sceneIndex, shotIndex);
          importedIds.push(result.item.id);
          lastSceneId = result.sceneId;
          result.unmatchedNames.forEach((name) => unmatchedNames.add(name));
        }
      }

      await loadProductionData(state.selectedSeriesSlug);
      await loadShotsForStoryboard(
        state.selectedSeriesSlug,
        state.selectedStoryboardId,
        importedIds[importedIds.length - 1] || ""
      );

      if (lastSceneId) {
        state.selectedSceneId = lastSceneId;
      }
      if (importedIds.length) {
        state.selectedShotId = importedIds[importedIds.length - 1];
      }

      setNotice(
        `已导入 ${importedIds.length} 个镜头卡草稿${unmatchedNames.size ? `，未匹配角色：${[...unmatchedNames].join("、")}` : ""}`
      );
    } catch (error) {
      setError(error);
    } finally {
      loading.importParsedShot = false;
    }
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

  return {
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
  };
}
