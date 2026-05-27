export const shotSizeOptions = [
  { value: "wide", label: "远景" },
  { value: "medium", label: "中景" },
  { value: "closeup", label: "近景" },
  { value: "extreme_closeup", label: "特写" }
];

export const shotMovementOptions = [
  { value: "static", label: "固定机位" },
  { value: "push_in", label: "推进" },
  { value: "pull_out", label: "拉远" },
  { value: "pan", label: "摇镜" },
  { value: "tracking", label: "跟拍" }
];

export const shotInputModeOptions = [
  { value: "reference_image", label: "参考生成" },
  { value: "first_last_frame", label: "首尾帧生成" },
  { value: "text_only", label: "纯文本" }
];

export const supportedShotInputModes = new Set(shotInputModeOptions.map((item) => item.value));

export const shotAnchorModeOptions = [
  { value: "auto", label: "自动" },
  { value: "face_priority", label: "面部优先" },
  { value: "costume_priority", label: "服装优先" },
  { value: "aura_priority", label: "气质优先" },
  { value: "first_appearance", label: "首次出场" },
  { value: "minimal", label: "最简" }
];

export const supportedShotAnchorModes = new Set(shotAnchorModeOptions.map((item) => item.value));

export const shotAspectRatioOptions = [
  { value: "21:9", label: "21:9" },
  { value: "1:1", label: "1:1" },
  { value: "16:9", label: "16:9" },
  { value: "3:4", label: "3:4" },
  { value: "4:3", label: "4:3" },
  { value: "9:16", label: "9:16" },
  { value: "adaptive", label: "智能比例" }
];

export const shotResolutionOptions = [
  { value: "480p", label: "480p" },
  { value: "720p", label: "720p" },
  { value: "1080p", label: "1080p" }
];

export const shotGenerationCountOptions = [
  { value: 1, label: "1 条" },
  { value: 2, label: "2 条" },
  { value: 3, label: "3 条" },
  { value: 4, label: "4 条" }
];

export const storyboardProductionModeOptions = [
  { value: "shot_pipeline", label: "分镜生产" },
  { value: "scene_direct", label: "场景直出" }
];
