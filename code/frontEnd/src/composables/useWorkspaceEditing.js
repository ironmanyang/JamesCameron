export function useWorkspaceEditing({
  state,
  inlineEditing,
  normalizeShotInputMode,
  serializeMediaPaths,
  serializeDialogueEntries,
  normalizeShotAnchorMode,
  normalizeShotAnchorOverrides
}) {
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

  return {
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
  };
}
