<template>
  <aside class="column column-left">
    <section
      v-loading="seriesListPanelLoading"
      element-loading-text="系列列表加载中..."
      :element-loading-svg="loadingSpinnerSvg"
      :element-loading-svg-view-box="loadingSpinnerViewBox"
      element-loading-background="rgba(7, 10, 14, 0.2)"
      class="panel "
    >
      <div class="panel-header">
        <div>
          <p class="panel-kicker">工作区</p>
          <h2>选择系列</h2>
        </div>
      </div>

      <div class="list-stack">
        <div
          v-for="item in state.series"
          :key="item.slug"
          class="list-card"
          :class="{ active: item.slug === state.selectedSeriesSlug }"
        >
          <div class="item-body" @click="state.selectedSeriesSlug = item.slug">
            <template v-if="isEditingSeries(item.slug)">
              <div class="item-editor">
                <el-input v-model="inlineEditing.seriesName" class="field" type="text" placeholder="输入系列名称" />
                <el-input
                  v-model="inlineEditing.seriesDescription"
                  class="field-textarea compact"
                  type="textarea"
                  resize="vertical"
                  placeholder="输入系列简介"
                />
              </div>
            </template>
            <template v-else>
              <strong>{{ item.name }}</strong>
              <span>{{ item.slug }}</span>
              <small>{{ item.description || "暂无简介" }}</small>
            </template>
          </div>
          <div class="item-actions">
            <el-button
              v-if="isEditingSeries(item.slug)"
              class="action-button dark compact-button"
              :disabled="loading.updateSeries"
              @click.stop="handleUpdateSeries(item)"
            >
              {{ loading.updateSeries ? "保存中..." : "保存" }}
            </el-button>
            <el-button v-else class="action-button ghost compact-button" @click.stop="startSeriesEdit(item)">
              编辑
            </el-button>
            <el-button
              v-if="isEditingSeries(item.slug)"
              class="action-button ghost compact-button"
              @click.stop="cancelSeriesEdit"
            >
              取消
            </el-button>
            <el-button
              class="action-button ghost danger compact-button"
              :disabled="loading.deleteSeries"
              @click.stop="handleDeleteSeries(item)"
            >
              {{ loading.deleteSeries ? "删除中..." : "删除" }}
            </el-button>
          </div>
        </div>

        <div v-if="!state.series.length && !loading.series" class="empty-state">
          还没有系列，先创建一个吧。
        </div>
      </div>
    </section>

    <section
      v-loading="seriesCreatePanelLoading"
      element-loading-text="系列创建中..."
      :element-loading-svg="loadingSpinnerSvg"
      :element-loading-svg-view-box="loadingSpinnerViewBox"
      element-loading-background="rgba(7, 10, 14, 0.16)"
      class="panel"
    >
      <div class="panel-header">
        <div>
          <p class="panel-kicker">系列</p>
          <h2>系列库</h2>
        </div>
        <span class="pill">共：{{ state.series.length }}</span>
      </div>

      <div class="form-stack">
        <el-input v-model="forms.seriesName" class="field" type="text" placeholder="输入系列名称" />
        <el-input
          v-model="forms.seriesDescription"
          class="field-textarea compact"
          type="textarea"
          resize="vertical"
          placeholder="输入系列简介"
        />
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
</template>

<script>
import { useWorkspaceContext } from "./workspaceContext";

export default {
  name: "WorkspaceSidebarLeft",
  setup() {
    return useWorkspaceContext();
  }
};
</script>
