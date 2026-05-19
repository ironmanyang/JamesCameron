# 本地文件存储规范

本文档以当前代码实现为准，描述项目实际使用的本地存储结构、命名规则和各类实体的落盘方式。

适用范围：

- 后端：`code/backEnd/app/storage/*`
- 前端：只通过后端 API 读取这些本地文件

## 1. 设计原则

本项目采用纯本地文件存储：

- 不使用数据库
- 不以浏览器缓存作为真实数据源
- 所有业务状态都必须能从磁盘恢复
- 所有 JSON 中的路径都以“当前系列根目录相对路径”保存

核心约束：

1. `output/` 是唯一业务数据根目录
2. 一个系列就是一个独立工作区
3. 每个实体都以 manifest JSON 为主记录
4. 图片、音频、视频等二进制文件只保存到磁盘，并在 JSON 中记录相对路径
5. 可重生成内容允许覆盖当前引用文件，但版本快照必须保留

## 2. 根目录结构

```text
output/
├── _system/
│   └── storage_manifest.json
└── {series_slug}/
    ├── series.json
    ├── episodes/
    ├── characters/
    ├── scenes/
    ├── props/
    ├── storyboards/
    ├── snapshots/
    ├── jobs/
    ├── outputs/
    │   ├── images/
    │   ├── videos/
    │   ├── audio/
    │   └── exports/
    └── trash/
```

说明：

- `_system/`：系统级存储元信息
- `{series_slug}/`：某个系列的根目录
- `props/`：当前已预留，尚未形成完整业务链路
- `outputs/`：视频生成等最终产出目录

## 3. 系统级文件

### 3.1 `output/_system/storage_manifest.json`

由后端启动时自动创建。

当前结构：

```json
{
  "storage_version": "1.0.0",
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z",
  "series_root": "output",
  "notes": "Local file storage manifest for AI video workflow"
}
```

用途：

- 标记当前存储版本
- 记录存储根目录

## 4. 命名规则

命名逻辑由 `code/backEnd/app/storage/naming.py` 负责。

### 4.1 系列 `slug`

- 来自系列名的 slug 化结果
- 优先使用英文、数字和 `-`
- 如果名字无法转为 ASCII，会生成哈希型兜底值，例如 `s-xxxxxxxx`
- 若已存在同名目录，则自动追加 `-2`、`-3`

示例：

- `My Story` -> `my-story`
- 中文名可能兜底为 `s-668372f3`

### 4.2 系列 `id`

格式：

```text
series_{slug中-替换为_}
```

示例：

```text
series_my_story
series_s_668372f3
```

### 4.3 实体 ID

当前已实现实体前缀：

- 剧集：`ep_001`
- 角色：`char_xxx`
- 场景：`scene_xxx`
- 分镜板：`sb_{episode_id}_v001`
- 镜头：`shot_001`
- 快照：`snap_{shot_id}_v001`
- 任务：`job_YYYYMMDD_HHMMSS_0001`

规则：

- `ep_001` 这类纯数字序号按递增生成
- `char_` / `scene_` 优先根据名称生成，可冲突时自动追加 `_2`、`_3`
- 分镜板以剧集为作用域递增版本号
- 快照以镜头为作用域递增版本号

## 5. 系列目录

### 5.1 路径

```text
output/{series_slug}/
```

### 5.2 清单文件

```text
output/{series_slug}/series.json
```

### 5.3 当前结构

```json
{
  "id": "series_s_668372f3",
  "slug": "s-668372f3",
  "name": "示例系列",
  "description": "",
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z",
  "status": "active",
  "defaults": {
    "aspect_ratio": "16:9",
    "style": "cinematic realism",
    "resolution": "1080p",
    "language": "zh-CN"
  },
  "providers": {
    "script_llm": "deepseek",
    "image_model": "gpt-image",
    "video_model": ""
  },
  "pointers": {
    "current_episode_id": "",
    "current_storyboard_id": ""
  }
}
```

### 5.4 子目录

创建系列时会自动创建这些子目录：

```text
episodes/
characters/
scenes/
props/
storyboards/
snapshots/
jobs/
outputs/images/
outputs/videos/
outputs/audio/
outputs/exports/
trash/
```

### 5.5 编辑与删除规则

- 系列允许直接修改 `name` 和 `description`
- 修改系列信息时，不会改动既有 `slug`，也不会重命名系列目录
- 删除系列时，会直接删除 `output/{series_slug}/` 整个目录

## 6. 剧集存储

### 6.1 路径

```text
output/{series_slug}/episodes/{episode_id}/
```

### 6.2 目录结构

```text
episodes/{episode_id}/
├── episode.json
├── script.raw.txt
├── script.parsed.json
└── script.versions/
    ├── raw_v001.txt
    └── parsed_v001.json
```

### 6.3 `episode.json`

当前结构：

```json
{
  "id": "ep_001",
  "series_id": "series_s_668372f3",
  "episode_number": 1,
  "name": "第1集",
  "status": "draft",
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z",
  "script": {
    "raw_text_path": "episodes/ep_001/script.raw.txt",
    "parsed_path": "episodes/ep_001/script.parsed.json",
    "latest_version": 1
  }
}
```

### 6.4 文件说明

- `script.raw.txt`：原始剧本文本
- `script.parsed.json`：结构化剧本
- `script.versions/`：按版本保存历史剧本

### 6.5 编辑与删除规则

- 剧集允许直接修改 `episode.json.name`
- 删除剧集前，后端会检查：
  - 是否仍有场景的 `episode_id` 指向该剧集
  - 是否仍有分镜板的 `episode_id` 指向该剧集
- 只要存在引用，删除就会被拒绝

## 7. 角色存储

### 7.1 路径

```text
output/{series_slug}/characters/{character_id}/
```

### 7.2 目录结构

```text
characters/{character_id}/
├── character.json
├── bible.json
├── refs/
│   └── character_bible_sheet.jpg
├── source_uploads/
├── generated/
│   └── v003/
│       ├── character_bible_sheet.jpg
│       └── prompt_package.json
└── versions/
    └── bible_v003.json
```

### 7.3 `character.json`

当前结构：

```json
{
  "id": "char_275a060f",
  "name": "小八",
  "aliases": [],
  "series_id": "series_s_668372f3",
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z",
  "status": "reference_ready",
  "anchors": {
    "biology": "",
    "face": "",
    "hair": "",
    "costume": "",
    "palette": "",
    "aura": ""
  },
  "brief": "",
  "bible_path": "characters/char_275a060f/bible.json",
  "reference_images": {
    "sheet": "characters/char_275a060f/refs/character_bible_sheet.jpg"
  },
  "component_images": {
    "front": "",
    "side": "",
    "back": "",
    "features": ""
  },
  "source_images": [],
  "latest_version": 3
}
```

说明：

- 当前角色主参考图只有 `reference_images.sheet`
- `component_images` 字段仍保留，但当前单图模式下通常为空

### 7.4 `bible.json`

保存角色圣经的当前版本，包含：

- `summary`
- `anchors`
- `bible`
- `visual_prompts`
- `negative_prompt`
- `generated_from`
- `generation`
- `reference_images`
- `source_images`

### 7.5 目录说明

- `refs/`：当前前端直接回显的角色参考拼图
- `source_uploads/`：用户上传的原始角色参考图
- `generated/vNNN/`：某次生成的产物快照
- `versions/`：角色圣经 JSON 历史版本

### 7.6 当前角色出图模式

当前角色参考图已实现为单张拼图：

- `character_bible_sheet.jpg`

内容包括：

- 三视图
- 特征分解拼图

### 7.7 编辑与删除规则

- 角色允许直接修改：
  - `character.json.name`
  - `character.json.brief`
- 修改 `brief` 时，会同步更新 `bible.json.brief`
- 删除角色前，后端会遍历全部镜头，检查 `characters` 数组是否仍引用该角色
- 只要仍被镜头引用，删除就会被拒绝

### 7.8 角色参考图删除规则

- 删除单张参考图时，会同步处理三处数据：
  - 删除 `source_uploads/` 下对应原图文件
  - 更新 `character.json.source_images`
  - 更新 `bible.json.source_images`
- 删除参考图不会删除角色本体，也不会主动删除已生成的角色圣经拼图

## 8. 场景存储

### 8.1 路径

```text
output/{series_slug}/scenes/{scene_id}/
```

### 8.2 目录结构

```text
scenes/{scene_id}/
├── scene.json
├── prompt_package.json
├── refs/
│   └── scene_reference_sheet.jpg
├── generated/
│   └── v002/
│       ├── scene_reference_sheet.jpg
│       └── prompt_package.json
└── versions/
    └── scene_v002.json
```

### 8.3 `scene.json`

当前结构：

```json
{
  "id": "scene_05e25ff9",
  "name": "阳光草地",
  "series_id": "series_s_668372f3",
  "episode_id": "ep_001",
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z",
  "status": "reference_ready",
  "description": "",
  "visual_profile": {
    "time": "",
    "weather": "",
    "lighting": "",
    "palette": "",
    "style": "",
    "architecture": "",
    "atmosphere": "",
    "key_props": []
  },
  "prompt_package_path": "scenes/scene_05e25ff9/prompt_package.json",
  "reference_images": {
    "sheet": "scenes/scene_05e25ff9/refs/scene_reference_sheet.jpg"
  },
  "latest_version": 2
}
```

### 8.4 `prompt_package.json`

保存场景结构化包的当前版本，包含：

- `summary`
- `visual_profile`
- `view_prompts`
- `negative_prompt`
- `generated_from`
- `generation`
- `reference_images`

说明：

- `view_prompts` 仍然保留四个视角提示词
- 但当前实际出图已经改为单张拼图 `reference_images.sheet`

### 8.5 当前场景出图模式

当前场景参考图已实现为单张拼图：

- `scene_reference_sheet.jpg`

通常包含：

- 定场大景
- 氛围近景
- 高角度空间关系
- 局部细节或关键道具区域

### 8.6 编辑与删除规则

- 场景允许直接修改：
  - `scene.json.name`
  - `scene.json.description`
  - `scene.json.episode_id`
- 删除场景前，后端会遍历全部镜头，检查 `scene_id` 是否仍引用该场景
- 只要仍被镜头引用，删除就会被拒绝

## 9. 分镜板与镜头存储

### 9.1 分镜板路径

```text
output/{series_slug}/storyboards/{storyboard_id}/
```

### 9.2 目录结构

```text
storyboards/{storyboard_id}/
├── storyboard.json
└── shots/
    ├── shot_001.json
    ├── shot_002.json
    └── ...
```

### 9.3 `storyboard.json`

当前结构：

```json
{
  "id": "sb_ep_001_v001",
  "series_id": "series_s_668372f3",
  "episode_id": "ep_001",
  "version": 1,
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z",
  "status": "draft",
  "shot_ids": ["shot_001", "shot_002"]
}
```

### 9.4 `shots/{shot_id}.json`

镜头文件当前包含这些核心块：

- `scene_id`
- `characters`
- `props`
- `script_source`
- `dialogue`
- `visual`
- `prompt_package`

### 9.5 编辑与删除规则

- 分镜板当前支持删除，但不支持修改其 `id` 或切换所属剧集
- 删除分镜板前，会检查是否仍被快照引用
- 镜头当前支持修改以下核心字段：
  - `scene_id`
  - `characters`
  - `visual.shot_size`
  - `visual.camera_movement`
  - `visual.duration_seconds`
  - `visual.lighting`
  - `visual.palette`
- 删除镜头前，会检查是否仍被快照或任务引用
- `status`

其中：

- `visual` 保存前端配置的景别、运镜、镜头时长等
- `prompt_package` 保存镜头组装后的正负提示词、参考图、上下文信息

## 10. 快照存储

### 10.1 路径

```text
output/{series_slug}/snapshots/{snapshot_id}/
```

### 10.2 目录结构

```text
snapshots/{snapshot_id}/
├── snapshot.json
└── bundle/
```

说明：

- `bundle/` 当前已创建，但尚未把素材实体拷贝进去
- 当前更多是通过 `snapshot.json` 固定记录一次提交所依赖的资源路径

### 10.3 `snapshot.json`

当前结构包含：

- `storyboard_id`
- `shot_id`
- `inputs`
- `resolved_assets`
- `provider_payload`

`resolved_assets.images` 会收集：

- 角色参考拼图
- 角色上传原图
- 场景参考拼图

## 11. 任务存储

### 11.1 路径

```text
output/{series_slug}/jobs/
```

### 11.2 目录结构

```text
jobs/
├── job_20260519_023403_0001.json
└── _responses/
    └── job_20260519_023403_0001.response.json
```

### 11.3 任务文件

每个任务是一个独立 JSON 文件。

当前包含：

- `id`
- `snapshot_id`
- `type`
- `status`
- `provider`
- `remote`
- `result`
- `error`

### 11.4 远端响应

当任务提交到外部视频服务后，原始返回会单独保存到：

```text
jobs/_responses/{job_id}.response.json
```

### 11.5 删除规则

- 任务支持删除本地草稿
- 如果任务已经生成远端 `task_id`，则不能直接删除
- 如果任务状态已经进入 `submitting`、`submitted`、`completed`，则不能直接删除
- 删除任务时，会同时尝试清理 `jobs/_responses/{job_id}.response.json`

## 12. 最终产出目录

每个系列下预留：

```text
outputs/
├── images/
├── videos/
├── audio/
└── exports/
```

当前用途：

- `images/`：部分图像类最终产出
- `videos/`：视频下载结果
- `audio/`：音频结果或预留
- `exports/`：导出结果或预留

## 13. 路径保存规则

所有业务 JSON 中的路径都保存为“相对当前系列根目录”的路径。

例如系列根目录为：

```text
output/s-668372f3/
```

那么角色参考图保存为：

```json
{
  "sheet": "characters/char_275a060f/refs/character_bible_sheet.jpg"
}
```

而不是绝对路径。

## 14. 原子写入规则

当前后端所有核心写入都使用原子写入：

- `write_json_atomic`
- `write_text_atomic`
- `write_bytes_atomic`

流程：

1. 先写入同目录临时文件
2. 再用替换方式覆盖正式文件

目的：

- 降低写入中断导致的半文件风险

## 15. 前端读取规则

前端不能直接把浏览器内存当成最终数据源。

当前规则：

1. 前端发请求到后端 API
2. 后端从本地文件读取 manifest
3. 前端只渲染 API 返回结果
4. 图片与视频通过后端挂载的 `/output/...` 静态路径访问

这保证了：

- 刷新页面后数据仍一致
- 本地文件才是唯一真实状态

## 16. 当前版本与过期说明

以下内容属于当前实现：

- 角色参考图：单张拼图
- 场景参考图：单张拼图
- 角色支持上传参考图
- 角色支持两种生成模式
- 分镜镜头包会汇总角色与场景参考资源

以下内容目前仍是预留或未完全打通：

- `props/` 完整业务链路
- 视频正式模型稳定接入
- 快照 `bundle/` 真实素材复制

## 17. 推荐维护方式

后续如果存储结构变更，建议同步更新：

1. `docs/local-storage-spec.md`
2. `docs/operation-guide.md`
3. 对应 `app/storage/*.py`
4. 前端任何依赖路径字段的回显逻辑
