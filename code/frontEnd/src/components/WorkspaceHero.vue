<template>
  <section class="masthead">
    <div class="masthead-copy">
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
        <strong class="status-chip-title">后端服务</strong>
        <span class="status-chip-value">{{ formatHealth(health) }}</span>
      </div>
      <p class="status-copy">
        角色和场景参考图会直接写入本地目录，前端回显也读取同一份本地数据源。
      </p>
    </div>
  </section>
</template>

<script>
import { useWorkspaceContext } from "./workspaceContext";

export default {
  name: "WorkspaceHero",
  setup() {
    return useWorkspaceContext();
  }
};
</script>
