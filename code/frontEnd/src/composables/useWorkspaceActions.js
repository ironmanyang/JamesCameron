import {
  analyzeEpisodeScript,
  assembleScenePackage,
  assembleShotPackage,
  clearShotBatches,
  clearShots,
  createCharacter,
  createEpisode,
  createScene,
  createSceneDirectSnapshot,
  createShot,
  createShotBatch,
  createSnapshot,
  createSeries,
  createStoryboard,
  createVideoJobFromSnapshot,
  deleteCharacter,
  deleteCharacterSourceImage,
  deleteEpisode,
  deleteJob,
  deleteRemoteVideoTask,
  deleteScene,
  deleteSeries,
  deleteShot,
  deleteShotBatch,
  deleteSnapshot,
  deleteStoryboard,
  generateCharacterAssets,
  generateSceneAssets,
  refreshJob,
  refreshShotBatch,
  retryFailedShotBatch,
  saveParsedScript,
  saveRawScript,
  submitJob,
  submitShotBatch,
  updateCharacter,
  updateEpisode,
  updateScene,
  updateSeries,
  updateShot,
  updateStoryboard,
  uploadCharacterSourceImages,
  uploadShotMediaImages
} from "../services/api";

const SEEDANCE_PROVIDER = {
  name: "doubao-seedance-2-0",
  submit_mode: "generic_http",
  model: "doubao-seedance-2-0-260128"
};

export function useWorkspaceActions({
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
}) {
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
    const confirmed = await confirmDanger(
      `确定删除系列“${targetSeries.name}”吗？这会删除该系列下的全部本地数据。`,
      "删除系列"
    );
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
          ? "已按上传参考图主体生成三视图与特征拆解拼图"
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
      setNotice(`分镜板已切换为 ${formatStoryboardProductionMode(normalizedMode)}`);
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
          ...SEEDANCE_PROVIDER
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
      setNotice(`已切换为 ${formatPromptVariantLabel(normalizedVariant)}`);
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
          failedNotes.push(`${jobId}: ${error instanceof Error ? error.message : String(error)}`);
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
          failedNotes.push(`${snapshotId}: ${error instanceof Error ? error.message : String(error)}`);
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
          ...SEEDANCE_PROVIDER
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

  return {
    handleShotMediaUpload,
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
  };
}
