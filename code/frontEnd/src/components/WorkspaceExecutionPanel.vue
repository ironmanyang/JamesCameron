<template>
      <aside class="column column-execution">
        <section v-loading="executionPanelLoading" element-loading-text="执行区处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div class="panel-header-copy">
              <p class="panel-kicker">执行区</p>
              <h2 class="panel-title">快照与任务</h2>
            </div>
          </div>

          <p class="message muted">
            {{ selectedStoryboardProductionMode === "shot_pipeline"
              ? "已接入 Doubao Seedance 2.0 任务草稿生成。当前可先完成镜头包组装、快照落盘和 Seedance 请求体预览，再按配置提交远端任务。"
              : "当前处于场景直出模式。这里会承接后续的场景级组包、快照与任务提交，不再以单镜头为单位推进。" }}
          </p>

          <div class="execution-flow">
            <div class="flow-card"
              :class="{ active: selectedStoryboardProductionMode === 'shot_pipeline' ? !!selectedShotPromptPackage?.positive : !!selectedSceneDirectPackage?.positive }">
              <span class="flow-step">01</span>
              <strong class="flow-card-title">{{ selectedStoryboardProductionMode === "shot_pipeline" ? "镜头包" : "场景包" }}</strong>
              <small class="flow-card-copy">
                {{ selectedStoryboardProductionMode === "shot_pipeline"
                  ? "先把镜头卡、剧情、参考素材和参数组装成可生成包。"
                  : "先把场景摘要、节拍、参考素材和参数组装成场景级生成包。" }}
              </small>
              <em class="flow-card-status">{{ (selectedStoryboardProductionMode === "shot_pipeline" ? selectedShotPromptPackage?.positive : selectedSceneDirectPackage?.positive) ? "已生成" : "待生成" }}</em>
            </div>

            <div class="flow-card" :class="{ active: !!state.selectedSnapshotId || !!state.snapshots.length }">
              <span class="flow-step">02</span>
              <strong class="flow-card-title">快照</strong>
              <small class="flow-card-copy">把当前组装结果和已解析素材固化成一次可追踪的本地快照。</small>
              <em class="flow-card-status">{{ state.snapshots.length ? `${state.snapshots.length} 个快照` : "待生成" }}</em>
            </div>

            <div class="flow-card" :class="{ active: !!state.selectedJobId || !!state.jobs.length }">
              <span class="flow-step">03</span>
              <strong class="flow-card-title">提交草稿</strong>
              <small class="flow-card-copy">基于快照生成最终要发给 Seedance 的 request_body 和任务记录。</small>
              <em class="flow-card-status">{{ state.jobs.length ? `${state.jobs.length} 个草稿` : "待生成" }}</em>
            </div>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div class="panel-header-copy">
                <p class="panel-kicker">Step 1</p>
                <h3 class="panel-title">{{ selectedStoryboardProductionMode === "shot_pipeline" ? "镜头包" : "场景包" }}</h3>
              </div>
              <span class="pill">
                {{ (selectedStoryboardProductionMode === "shot_pipeline" ? selectedShotPromptPackage?.positive : selectedSceneDirectPackage?.positive) ? "已生成" : "待生成" }}
              </span>
            </div>

            <template v-if="selectedStoryboardProductionMode === 'shot_pipeline'">
              <el-button class="action-button dark full-width" :disabled="loading.shotPackage"
                @click="handleAssembleShotPackage">
                {{ loading.shotPackage ? "生成中..." : "生成当前镜头包" }}
              </el-button>
              <p class="inline-note action-hint">{{ loading.shotPackage ? "镜头包正在生成中..." : "先把当前镜头的剧情、对白和参考素材组装成镜头包。" }}</p>

              <div class="meta-panel">
                <div class="meta-row">
                  <span class="meta-label">当前镜头卡</span>
                  <strong class="meta-value">{{ state.shots.length }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">已勾选批次</span>
                  <strong class="meta-value">{{ state.selectedShotIds.length }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">批次草稿</span>
                  <div class="inline-actions compact-actions">
                    <el-button class="action-button ghost compact-button"
                      :disabled="loading.createShotBatch || !state.selectedShotIds.length"
                      @click="handleCreateShotBatch('selected')">
                      {{ loading.createShotBatch ? "处理中..." : "生成选中批次" }}
                    </el-button>
                    <el-button class="action-button warm compact-button"
                      :disabled="loading.createShotBatch || !state.shots.length" @click="handleCreateShotBatch('all')">
                      {{ loading.createShotBatch ? "处理中..." : "批量生成草稿批次" }}
                    </el-button>
                  </div>
                  <p class="inline-note action-hint">{{ loading.createShotBatch ? "批次正在生成中..." : (!state.selectedShotIds.length ? "请先勾选至少一个镜头" : "可按勾选镜头生成一个批次，或直接批量生成全部批次。") }}</p>
                </div>
              </div>

              <div v-if="selectedShot" class="focus-card">
                <span class="focus-label">当前镜头</span>
                <strong class="focus-value">{{ selectedShot.id }}</strong>
                <small class="focus-meta">{{ formatShotInputMode(selectedShot.media?.mode) }} · {{ selectedShot.scene_id }} ·
                  {{ selectedShot.visual.duration_seconds }} 秒</small>
              </div>

              <div v-if="selectedShot" class="meta-panel">
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">镜头卡剧情描述</span>
                  <strong class="meta-value">{{ getShotStoryDisplay(selectedShot, "description") }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">镜头卡情绪</span>
                  <strong class="meta-value">{{ getShotStoryDisplay(selectedShot, "emotion") }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">镜头卡节拍</span>
                  <strong class="meta-value">{{ getShotStoryDisplay(selectedShot, "beat") }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">锚点策略</span>
                  <strong class="meta-value">{{ formatShotAnchorMode(selectedShot.anchor_strategy?.mode) }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">镜头卡对白</span>
                  <strong class="meta-value prompt-preview">{{ formatDialogueEntries(selectedShot.dialogue) || "暂无" }}</strong>
                </div>
                <div
                  v-if="countShotAnchorOverrides(selectedShot.anchor_strategy?.per_character, selectedShot.characters)"
                  class="meta-row meta-row-wide">
                  <span class="meta-label">角色覆盖</span>
                  <strong class="meta-value prompt-preview">{{ formatShotAnchorOverridesDisplay(selectedShot.anchor_strategy,
                    selectedShot.characters) || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">镜头卡原文摘录</span>
                  <strong class="meta-value prompt-preview">{{ getShotStoryDisplay(selectedShot, "raw_script_excerpt") }}</strong>
                </div>
              </div>

              <div v-if="selectedShotPromptPackage?.positive" class="meta-panel">
                <div class="meta-row">
                  <span class="meta-label">参考素材数量</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.media_references?.length || selectedShotPromptPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">参考图片</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">当前版本</span>
                  <strong class="meta-value">{{ formatPromptVariantLabel(selectedShotPromptVariant) }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">提示词版本切换</span>
                  <div class="inline-actions compact-actions prompt-variant-actions">
                    <el-button class="action-button compact-button"
                      :class="selectedShotPromptVariant === 'ai_refined' ? 'warm selected-variant' : 'ghost'"
                      :disabled="loading.updateShot || !selectedShotPromptVariants.ai_refined"
                      @click="handleSelectShotPromptVariant('ai_refined')">
                      {{ loading.updateShot && selectedShotPromptVariant !== 'ai_refined' ? "切换中..." : "使用 AI 润色版" }}
                    </el-button>
                    <el-button class="action-button compact-button"
                      :class="selectedShotPromptVariant === 'fallback_template' ? 'warm selected-variant' : 'ghost'"
                      :disabled="loading.updateShot || !selectedShotPromptVariants.fallback_template"
                      @click="handleSelectShotPromptVariant('fallback_template')">
                      {{ loading.updateShot && selectedShotPromptVariant !== 'fallback_template' ? "切换中..." : "使用 本地模板版" }}
                    </el-button>
                  </div>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Seedance 提示词预览</span>
                  <strong class="meta-value prompt-preview">{{ selectedShotPromptPreview }}</strong>
                </div>
              </div>

              <div v-if="selectedShotPromptPackage?.prompt_generation" class="meta-panel">
                <div class="meta-row">
                  <span class="meta-label">生成方式</span>
                  <strong class="meta-value">{{ formatPromptGenerationMode(selectedShotPromptPackage.prompt_generation.mode) }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">模型</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.prompt_generation.model || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">Fallback</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.prompt_generation.fallback_used ? "是" : "否" }}</strong>
                </div>
                <div v-if="selectedShotPromptPackage.prompt_generation.error" class="meta-row meta-row-wide">
                  <span class="meta-label">回退原因</span>
                  <strong class="meta-value prompt-preview">{{ selectedShotPromptPackage.prompt_generation.error }}</strong>
                </div>
              </div>

              <div v-if="selectedShotPromptPackage?.script_context" class="meta-panel">
                <div class="meta-row">
                  <span class="meta-label">剧集标题</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.script_context.episode_title || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">场景位置</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.script_context.scene_location || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">场景时间</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.script_context.scene_time || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">镜头动作</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.script_context.shot_description || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">情绪基调</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.script_context.shot_emotion || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">剧情节点</span>
                  <strong class="meta-value">{{ selectedShotPromptPackage.script_context.shot_beat || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">当前镜头台词片段</span>
                  <strong class="meta-value prompt-preview">{{ selectedShotPromptPackage.script_context.dialogue_excerpt || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">剧本原文摘录</span>
                  <strong class="meta-value prompt-preview">{{ selectedShotPromptPackage.script_context.raw_script_excerpt || "暂无" }}</strong>
                </div>
              </div>
              <el-button class="action-button warm full-width primary-action" :disabled="loading.createRender"
                @click="handleCreateRenderTask">
                {{ loading.createRender ? "生成中..." : "生成提交草稿" }}
              </el-button>
              <p class="inline-note action-hint">{{ getDisabledHint("createRender") || "先生成快照，再产出最终提交给 Seedance 的 request_body。" }}</p>

              <div class="subsection">
                <div class="subsection-header">
                  <h3 class="section-title">批次列表</h3>
                  <div class="inline-actions compact-actions">
                    <el-button class="action-button ghost compact-button"
                      :disabled="loading.deleteShotBatch || !selectedShotBatchComputed"
                      @click="handleDeleteShotBatch()">
                      {{ loading.deleteShotBatch ? "删除中..." : "删除当前批次" }}
                    </el-button>
                    <el-button class="action-button ghost danger compact-button"
                      :disabled="loading.clearShotBatches || !state.shotBatches.length" @click="handleClearShotBatches">
                      {{ loading.clearShotBatches ? "清空中..." : "清空批次" }}
                    </el-button>
                  </div>
                </div>

                <div v-loading="shotBatchesListLoading" element-loading-text="批次列表加载中..."
                  :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
                  element-loading-background="rgba(7, 10, 14, 0.18)"
                  class="mini-list nested-mini-list compact-card-grid compact-card-grid-2">
                  <div v-for="batch in state.shotBatches" :key="batch.id" class="mini-card selectable"
                    :class="{ active: batch.id === state.selectedShotBatchId }">
                    <div class="item-body compact-card-body" @click="state.selectedShotBatchId = batch.id">
                      <strong class="item-title">{{ batch.name || batch.id }}</strong>
                      <span class="item-meta">{{ batch.id }} · {{ formatStatus(batch.status) }}</span>
                      <small class="item-copy">{{ formatShotBatchCounts(batch) }}</small>
                      <small class="item-copy">进度：{{ formatShotBatchProgress(batch) }} · 可提交
                        {{ getShotBatchSubmittableCount(batch) }}</small>
                    </div>
                    <div class="item-actions item-actions-block">
                      <el-button class="action-button ghost compact-button"
                        :disabled="loading.submitShotBatch || !getShotBatchSubmittableCount(batch)"
                        @click.stop="handleSubmitShotBatch(batch)">
                        {{ loading.submitShotBatch ? "提交中..." : "未提交/失败-镜头提交" }}
                      </el-button>
                      <el-button class="action-button ghost compact-button" :disabled="loading.refreshShotBatch"
                        @click.stop="handleRefreshShotBatch(batch)">
                        {{ loading.refreshShotBatch ? "刷新中..." : "刷新批次" }}
                      </el-button>
                      <el-button class="action-button ghost compact-button"
                        :disabled="loading.retryShotBatch || !batch.failed_count"
                        @click.stop="handleRetryFailedShotBatch(batch)">
                        {{ loading.retryShotBatch ? "重试中..." : "重试失败项" }}
                      </el-button>
                    </div>
                    <p class="inline-note action-hint">
                      {{ getShotBatchActionHint(batch, "submit") || getShotBatchActionHint(batch, "refresh") || getShotBatchActionHint(batch, "retry") }}
                    </p>
                  </div>
                  <div v-if="!state.shotBatches.length" class="empty-state">当前还没有镜头批次。</div>
                </div>

                <div v-if="selectedShotBatchComputed" class="meta-panel">
                  <div class="meta-row">
                    <span class="meta-label">当前批次</span>
                    <strong class="meta-value">{{ selectedShotBatchComputed.id }}</strong>
                  </div>
                  <div class="meta-row">
                    <span class="meta-label">批次状态</span>
                    <strong class="meta-value">{{ formatStatus(selectedShotBatchComputed.status) }}</strong>
                  </div>
                  <div class="meta-row">
                    <span class="meta-label">镜头数量</span>
                    <strong class="meta-value">{{ selectedShotBatchComputed.total_count || 0 }}</strong>
                  </div>
                  <div class="meta-row">
                    <span class="meta-label">批次成功率</span>
                    <strong class="meta-value">{{ formatShotBatchProgress(selectedShotBatchComputed) }}</strong>
                  </div>
                  <div class="meta-row meta-row-wide">
                    <span class="meta-label">明细</span>
                    <strong class="meta-value prompt-preview">{{ formatShotBatchCounts(selectedShotBatchComputed) }}</strong>
                  </div>
                </div>

                <div v-if="selectedShotBatchComputed?.items?.length"
                  class="mini-list nested-mini-list compact-card-grid compact-card-grid-3">
                  <div v-for="batchItem in selectedShotBatchComputed.items"
                    :key="`${selectedShotBatchComputed.id}-${batchItem.shot_id}`" class="mini-card">
                    <div class="item-body compact-card-body">
                      <strong class="item-title">{{ batchItem.shot_id }}</strong>
                      <span class="item-meta">{{ formatStatus(batchItem.status) }}</span>
                      <small class="item-copy">快照：{{ batchItem.snapshot_id || "暂无" }} · 草稿：{{ batchItem.job_id || "暂无" }}</small>
                      <small class="item-copy">{{ batchItem.error || "无错误" }}</small>
                    </div>
                    <div class="item-actions item-actions-block">
                      <el-button v-if="batchItem.job_id" class="action-button ghost compact-button"
                        @click.stop="state.selectedJobId = batchItem.job_id">
                        打开草稿
                      </el-button>
                    </div>
                  </div>
                </div>

                <div v-if="getBatchCompletedItems(selectedShotBatchComputed).length" class="reference-grid">
                  <div v-for="item in getBatchCompletedItems(selectedShotBatchComputed)"
                    :key="`batch-result-${item.job_id}`" class="reference-card">
                    <div class="reference-header">
                      <strong class="reference-title">{{ item.shot_id }}</strong>
                      <small class="reference-meta">{{ item.job_id }}</small>
                    </div>
                    <video v-if="getBatchJobVideoUrl(item.job_id)" class="video-preview"
                      :src="getBatchJobVideoUrl(item.job_id)" controls preload="metadata" />
                    <el-image v-else-if="getBatchJobCoverUrl(item.job_id)" class="preview-image"
                      :src="getBatchJobCoverUrl(item.job_id)"
                      :preview-src-list="getBatchJobCoverUrl(item.job_id) ? [getBatchJobCoverUrl(item.job_id)] : []"
                      :initial-index="0" fit="cover" preview-teleported />
                    <div v-else class="reference-empty">暂无结果预览</div>
                  </div>
                </div>
              </div>
            </template>

            <template v-else>
              <el-button class="action-button dark full-width" :disabled="loading.sceneDirectPackage"
                @click="handleAssembleSceneDirectPackage">
                {{ loading.sceneDirectPackage ? "组装中..." : "组装场景包" }}
              </el-button>
              <p class="inline-note action-hint">{{ loading.sceneDirectPackage ? "场景包正在组装中..." : "把场景摘要、节拍、参考素材和输出参数组装成一个场景级生成包。" }}</p>


              <div class="focus-card stack-block">
                <span class="focus-label">当前场景</span>
                <strong class="focus-value">{{state.scenes.find((item) => item.id === getSceneDirectSceneId())?.name || "请先选择场景"}}</strong>
                <small class="focus-meta">{{ getSceneDirectSceneId() || "未指定场景" }} · {{ formatShotInputMode(forms.shotInputMode) }} ·
                  {{ normalizeShotDuration(forms.shotDuration) }} 秒</small>
              </div>

              <div v-if="selectedSceneDirectPackage?.positive" class="meta-panel stack-block">
                <div class="meta-row">
                  <span class="meta-label">参考素材数量</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.media_references?.length || selectedSceneDirectPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">参考图片</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.reference_images?.length || 0 }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">场景级提示词预览</span>
                  <strong class="meta-value prompt-preview">{{ selectedSceneDirectPackage.positive }}</strong>
                </div>
              </div>

              <div v-if="selectedSceneDirectPackage?.script_context" class="meta-panel stack-block">
                <div class="meta-row">
                  <span class="meta-label">剧集标题</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.script_context.episode_title || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">场景位置</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.script_context.scene_location || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">场景时间</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.script_context.scene_time || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">场景摘要</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.script_context.scene_summary || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">节拍大纲</span>
                  <strong class="meta-value prompt-preview">{{ (selectedSceneDirectPackage.script_context.beat_outline || []).join("\n") || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">剧本原文摘录</span>
                  <strong class="meta-value prompt-preview">{{ selectedSceneDirectPackage.script_context.raw_script_excerpt || "暂无" }}</strong>
                </div>
              </div>

              <div v-if="selectedSceneDirectPackage?.prompt_generation" class="meta-panel stack-block">
                <div class="meta-row">
                  <span class="meta-label">生成方式</span>
                  <strong class="meta-value">{{ formatPromptGenerationMode(selectedSceneDirectPackage.prompt_generation.mode) }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">模型</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.prompt_generation.model || "暂无" }}</strong>
                </div>
                <div class="meta-row">
                  <span class="meta-label">Fallback</span>
                  <strong class="meta-value">{{ selectedSceneDirectPackage.prompt_generation.fallback_used ? "是" : "否" }}</strong>
                </div>
                <div v-if="selectedSceneDirectPackage.prompt_generation.error" class="meta-row meta-row-wide">
                  <span class="meta-label">回退原因</span>
                  <strong class="meta-value prompt-preview">{{ selectedSceneDirectPackage.prompt_generation.error }}</strong>
                </div>
              </div>

              <div v-if="selectedSceneDirectPackage?.prompt_input" class="meta-panel stack-block">
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：参考绑定</span>
                  <strong class="meta-value prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.reference_binding || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：场景目标</span>
                  <strong class="meta-value prompt-preview">{{ selectedSceneDirectPackage.prompt_input.scene_goal || "暂无" }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：剧情阶段</span>
                  <strong class="meta-value prompt-preview">{{
                    (selectedSceneDirectPackage.prompt_input.condensed_beats || []).join("\n") || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：场景视觉</span>
                  <strong class="meta-value prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.scene_visual || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：镜头原则</span>
                  <strong class="meta-value prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.camera_direction || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：输出规格</span>
                  <strong class="meta-value prompt-preview">{{
                    selectedSceneDirectPackage.prompt_input.output_spec || "暂无"
                  }}</strong>
                </div>
                <div class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：约束</span>
                  <strong class="meta-value prompt-preview">{{
                    (selectedSceneDirectPackage.prompt_input.constraints || []).join("，") || "暂无"
                  }}</strong>
                </div>
                <div v-if="(selectedSceneDirectPackage.prompt_input.warnings || []).length"
                  class="meta-row meta-row-wide">
                  <span class="meta-label">Prompt 骨架：备注</span>
                  <strong class="meta-value prompt-preview">{{
                    (selectedSceneDirectPackage.prompt_input.warnings || []).join("；")
                  }}</strong>
                </div>
              </div>

              <details v-if="selectedSceneDirectPackage?.prompt_input?.raw_script_excerpt"
                class="debug-disclosure stack-block">
                <summary class="debug-summary">调试查看：原始剧本摘录</summary>
                <div class="meta-panel debug-panel">
                  <div class="meta-row meta-row-wide">
                    <span class="meta-label">Prompt 骨架：原文摘录</span>
                    <strong class="meta-value prompt-preview">{{
                      selectedSceneDirectPackage.prompt_input.raw_script_excerpt
                    }}</strong>
                  </div>
                </div>
              </details>

              <div v-if="(selectedSceneDirectPackage?.script_context?.shot_outlines || []).length"
                class="mini-list direct-beat-list compact-card-grid compact-card-grid-2 stack-block">
                <div v-for="item in selectedSceneDirectPackage.script_context.shot_outlines"
                  :key="`scene-beat-${item.index}`" class="mini-card">
                  <div class="item-body compact-card-body">
                    <strong class="item-title">节拍 {{ item.index }}</strong>
                    <small class="item-copy">{{ formatReadableField(item.description) }}</small>
                    <small class="item-copy">镜头建议：{{ formatReadableField(item.camera_summary) }}</small>
                    <small class="item-copy">情绪：{{ formatReadableField(item.emotion) }}</small>
                    <small class="item-copy">剧情节拍：{{ formatReadableField(item.beat) }}</small>
                    <small class="item-copy">对白：{{ formatReadableField(item.dialogue_excerpt) }}</small>
                  </div>
                </div>
              </div>
              <el-button class="action-button warm full-width primary-action" :disabled="loading.createSceneDirectTask"
                @click="handleCreateSceneDirectTask">
                {{ loading.createSceneDirectTask ? "生成中..." : "生成场景任务草稿" }}
              </el-button>
              <p class="inline-note action-hint">{{ loading.createSceneDirectTask ? "场景任务草稿正在生成中..." : "基于当前场景包生成一条场景级任务草稿。" }}</p>
            </template>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div class="panel-header-copy">
                <p class="panel-kicker">Step 2</p>
                <h3 class="panel-title">快照</h3>
              </div>
              <div class="inline-actions compact-actions">
                <el-button class="action-button ghost danger compact-button"
                  :disabled="loading.clearSnapshots || !state.snapshots.length" @click="handleClearSnapshots">
                  {{ loading.clearSnapshots ? "清空中..." : "清空快照" }}
                </el-button>
                <span class="pill">{{ state.snapshots.length ? `${state.snapshots.length} 个` : "0 个" }}</span>
              </div>
            </div>

              <div v-loading="snapshotsListLoading" element-loading-text="快照列表加载中..."
              :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
              element-loading-background="rgba(7, 10, 14, 0.2)"
              class="mini-list compact-card-grid compact-card-grid-3">
              <div v-for="item in state.snapshots" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedSnapshotId }">
                <div class="item-body compact-card-body" @click="handleOpenSnapshot(item)">
                  <strong class="item-title">{{ item.id }}</strong>
                  <span class="item-meta">{{ item.storyboard_id }} · {{ item.shot_id }}</span>
                  <small class="item-copy">{{ formatSnapshotSource(item) }}</small>
                  <small class="item-copy">图片 {{ item.resolved_assets?.images?.length || 0 }}</small>
                </div>
                <div class="item-actions item-actions-block">
                  <el-button class="action-button ghost compact-button" @click.stop="handleOpenSnapshot(item)">
                    查看
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteSnapshot"
                    @click.stop="handleDeleteSnapshot(item)">
                    {{ loading.deleteSnapshot ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
              <div v-if="!state.snapshots.length" class="empty-state">当前还没有本地快照。</div>
            </div>

            <el-skeleton v-if="snapshotDetailSectionLoading" animated>
              <template #template>
                <div class="detail-skeleton-stack">
                  <div class="skeleton-grid">
                    <div class="skeleton-card" v-for="item in 4" :key="`snapshot-detail-skeleton-${item}`">
                      <el-skeleton-item variant="text" class="skeleton-line" />
                      <el-skeleton-item variant="h3" class="skeleton-line skeleton-line-mid" />
                    </div>
                  </div>
                </div>
              </template>
            </el-skeleton>
            <div v-else-if="state.selectedSnapshot" class="meta-panel">
              <div class="meta-row">
                <span class="meta-label">当前快照</span>
                <strong class="meta-value">{{ state.selectedSnapshot.id }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">所属分镜板 / 镜头</span>
                <strong class="meta-value">{{ formatSnapshotSource(state.selectedSnapshot) }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">引用图片数量</span>
                <strong class="meta-value">{{ selectedSnapshotImageCount }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">卡片路径</span>
                <strong class="meta-value">{{ state.selectedSnapshot.inputs?.shot_card_path || state.selectedSnapshot.inputs?.scene_card_path || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">角色文件数量</span>
                <strong class="meta-value">{{ state.selectedSnapshot.inputs?.character_paths?.length || 0 }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">场景文件数量</span>
                <strong class="meta-value">{{ state.selectedSnapshot.inputs?.scene_paths?.length || 0 }}</strong>
              </div>
            </div>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div class="panel-header-copy">
                <p class="panel-kicker">Step 3</p>
                <h3 class="panel-title">提交草稿</h3>
              </div>
              <div class="inline-actions compact-actions">
                <el-button class="action-button ghost danger compact-button"
                  :disabled="loading.clearJobs || !state.jobs.length" @click="handleClearJobs">
                  {{ loading.clearJobs ? "清空中..." : "清空草稿" }}
                </el-button>
                <span class="pill">{{ state.jobs.length ? `${state.jobs.length} 个` : "0 个" }}</span>
              </div>
            </div>

            <div v-loading="jobsListLoading" element-loading-text="任务列表加载中..." :element-loading-svg="loadingSpinnerSvg"
              :element-loading-svg-view-box="loadingSpinnerViewBox" element-loading-background="rgba(7, 10, 14, 0.2)"
              class="mini-list compact-card-grid compact-card-grid-2">
              <div v-for="item in state.jobs" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedJobId }">
                <div class="item-body compact-card-body" @click="state.selectedJobId = item.id">
                  <strong class="item-title">{{ item.id }}</strong>
                  <span class="item-meta">{{ formatStatus(item.status) }}</span>
                  <small class="item-copy">{{ formatSeedanceMode(getJobSeedanceSummary(item).mode) }} ·
                    {{ item.provider?.model || "doubao-seedance-2-0-260128" }}</small>
                  <small class="item-copy">输出：{{ getJobSeedanceSummary(item).ratio }} · {{ getJobSeedanceSummary(item).resolution }} ·
                    {{ formatJobOutputSummary(item) }}</small>
                  <small class="item-copy">素材：{{ formatJobReferenceSummary(item) }} ·
                    {{ getJobSeedanceSummary(item).returnLastFrame ? "回传尾帧" : "不回传尾帧" }}</small>
                  <small class="item-copy">关联快照：{{ item.snapshot_id || "暂无" }}</small>
                </div>
                <div class="item-actions item-actions-block">
                  <el-button class="action-button ghost compact-button" @click.stop="handleOpenJobSnapshot(item)">
                    查看快照
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteJob"
                    @click.stop="handleDeleteJob(item)">
                    {{ loading.deleteJob ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
              <div v-if="!state.jobs.length" class="empty-state">当前还没有任务草稿。</div>
            </div>

            <div v-if="selectedJobComputed" class="subsection">
              <el-skeleton :loading="jobDetailSectionLoading" animated>
                <template #template>
                  <div class="detail-skeleton-stack">
                    <div class="skeleton-card skeleton-header-card">
                      <el-skeleton-item variant="text" class="skeleton-kicker" />
                      <el-skeleton-item variant="h3" class="skeleton-title" />
                      <div class="skeleton-chip-row">
                        <el-skeleton-item variant="button" class="skeleton-chip" />
                        <el-skeleton-item variant="button" class="skeleton-chip" />
                        <el-skeleton-item variant="button" class="skeleton-chip" />
                      </div>
                    </div>
                    <div class="skeleton-grid">
                      <div class="skeleton-card" v-for="item in 6" :key="`job-detail-skeleton-${item}`">
                        <el-skeleton-item variant="text" class="skeleton-line" />
                        <el-skeleton-item variant="h3" class="skeleton-line skeleton-line-mid" />
                      </div>
                    </div>
                    <div class="skeleton-card">
                      <el-skeleton-item variant="image" class="skeleton-media" />
                    </div>
                    <div class="skeleton-card">
                      <el-skeleton-item variant="text" class="skeleton-line" />
                      <el-skeleton-item variant="text" class="skeleton-line skeleton-line-wide" />
                      <el-skeleton-item variant="text" class="skeleton-line skeleton-line-wide" />
                    </div>
                  </div>
                </template>
                <template #default>
                  <div class="panel-header">
                    <div class="panel-header-copy">
                      <p class="panel-kicker">当前任务</p>
                      <h3 class="panel-title">{{ selectedJobComputed.id }}</h3>
                    </div>
                    <div class="inline-actions compact-actions panel-header-actions">

                      <el-button class="action-button ghost"
                        :disabled="loading.snapshotDetail || !selectedJobComputed.snapshot_id"
                        @click="handleOpenJobSnapshot()">
                        {{ loading.snapshotDetail ? "加载中..." : "查看快照" }}
                      </el-button>
                      <el-button class="action-button ghost"
                        :disabled="loading.submitJob || loading.jobDetail || selectedJobComputed.status === 'submitting'"
                        @click="handleSubmitJob">
                        {{ loading.submitJob ? "提交中..." : "提交任务" }}
                      </el-button>
                      <el-button class="action-button dark"
                        :disabled="loading.refreshJob || loading.jobDetail || !selectedJobComputed.remote?.task_id"
                        @click="handleRefreshJob">
                        {{ loading.refreshJob ? "刷新中..." : "刷新状态" }}
                      </el-button>
                      <el-button class="action-button ghost danger"
                        :disabled="loading.deleteRemoteTask || !selectedJobComputed.remote?.task_id"
                        @click="handleDeleteRemoteTask({ id: selectedJobComputed.remote?.task_id })">
                        {{ loading.deleteRemoteTask ? "删除中..." : "删除远程任务" }}
                      </el-button>
                    </div>
                  </div>

                  <div class="meta-panel">
                    <div class="meta-row">
                      <span class="meta-label">状态</span>
                      <strong class="meta-value">{{ formatStatus(selectedJobComputed.status) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">供应商</span>
                      <strong class="meta-value">{{ formatProviderName(selectedJobComputed.provider?.name) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">模型</span>
                      <strong class="meta-value">{{ selectedJobComputed.provider?.model || "暂未配置" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">任务接口</span>
                      <strong class="meta-value">{{ formatJobApiKind(selectedJobComputed.provider) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">输入模式</span>
                      <strong class="meta-value">{{ selectedJobRequestSummary.modeLabel }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">图像引用</span>
                      <strong class="meta-value">{{ selectedJobRequestSummary.imageCount }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">输出规格</span>
                      <strong class="meta-value">{{ selectedJobRequestSummary.ratio }} ·
                        {{ selectedJobRequestSummary.resolution }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">时长 / 数量</span>
                      <strong class="meta-value">{{ selectedJobRequestSummary.duration || "未设置" }} 秒 ·
                        {{ selectedJobRequestSummary.count }}
                        条</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">音频 / 尾帧</span>
                      <strong class="meta-value">{{ selectedJobRequestSummary.hasAudio ? "有声" : "无声" }} ·
                        {{ selectedJobRequestSummary.returnLastFrame ? "回传尾帧" : "不回传尾帧" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">远端任务 ID</span>
                      <strong class="meta-value">{{ selectedJobComputed.remote?.task_id || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">任务响应快照</span>
                      <strong class="meta-value">{{ selectedJobComputed.remote?.raw_response_path || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">结果视频</span>
                      <strong class="meta-value">{{ selectedJobComputed.result?.video_path || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">结果封面</span>
                      <strong class="meta-value">{{ selectedJobComputed.result?.cover_path || "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">错误信息</span>
                      <strong class="meta-value">{{ selectedJobComputed.error?.message || "无" }}</strong>
                    </div>
                  </div>

                  <div v-if="selectedJobCoverUrl || selectedJobVideoUrl" class="reference-grid">
                    <div v-if="selectedJobCoverUrl" class="reference-card">
                      <div class="reference-header">
                        <strong class="reference-title">封面</strong>
                        <small class="reference-meta">{{ selectedJobComputed.result?.cover_path }}</small>
                      </div>
                      <el-image class="preview-image" :src="selectedJobCoverUrl"
                        :preview-src-list="selectedJobCoverUrl ? [selectedJobCoverUrl] : []" :initial-index="0"
                        fit="cover" preview-teleported />
                    </div>

                    <div v-if="selectedJobVideoUrl" class="reference-card">
                      <div class="reference-header">
                        <strong class="reference-title">视频</strong>
                        <small class="reference-meta">{{ selectedJobComputed.result?.video_path }}</small>
                      </div>
                      <video class="video-preview" :src="selectedJobVideoUrl" controls preload="metadata" />
                    </div>
                  </div>

                  <div class="form-stack">
                    <label
                      class="code-label">{{ selectedJobHasSubmittedRequest ? "Seedance 最终提交体" : "Seedance 提交草稿" }}</label>
                    <el-input :model-value="selectedJobRequestText" class="field-textarea code-textarea job-code"
                      type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
                  </div>

                  <div
                    v-if="selectedJobComputed.remote?.raw_response_path || Object.keys(selectedJobComputed.remote?.raw_response || {}).length"
                    class="form-stack">
                    <label class="code-label">Seedance Response</label>
                    <el-input :model-value="selectedJobResponseText" class="field-textarea code-textarea job-code"
                      type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
                  </div>
                </template>
              </el-skeleton>
            </div>
          </div>

          <div class="execution-stage">
            <div class="panel-header sub-panel-header execution-stage-header">
              <div class="panel-header-copy">
                <p class="panel-kicker">Remote</p>
                <h3 class="panel-title">远程任务</h3>
              </div>
              <div class="inline-actions compact-actions">
                <el-button class="action-button ghost compact-button"
                  :disabled="remoteTasksListLoading || !state.remoteTasks.length" @click="handleRefreshRemoteTasks">
                  {{ remoteTasksListLoading ? "刷新中..." : "刷新远程任务" }}
                </el-button>
                <span class="pill">{{ state.remoteTasks.length }} 项</span>
              </div>
            </div>

            <div v-loading="remoteTasksListLoading" element-loading-text="远程任务加载中..."
              :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
              element-loading-background="rgba(7, 10, 14, 0.18)"
              class="mini-list compact-card-grid compact-card-grid-3">
              <div v-for="task in state.remoteTasks" :key="getRemoteTaskId(task)" class="mini-card selectable"
                :class="{ active: getRemoteTaskId(task) === state.selectedRemoteTaskId }">
                <div class="item-body compact-card-body" @click="state.selectedRemoteTaskId = getRemoteTaskId(task)">
                  <strong class="item-title">{{ getRemoteTaskId(task) }}</strong>
                  <span class="item-meta">{{ getRemoteTaskStatus(task) }}</span>
                  <small class="item-copy">关联草稿：{{ getRemoteTaskLinkedJob(task)?.id || "暂无" }}</small>
                </div>
                <div class="item-actions item-actions-block">
                  <el-button class="action-button ghost compact-button" :disabled="!getRemoteTaskLinkedJob(task)"
                    @click.stop="handleOpenRemoteTaskJob(task)">
                    打开草稿
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteRemoteTask"
                    @click.stop="handleDeleteRemoteTask(task)">
                    {{ loading.deleteRemoteTask ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
              <div v-if="!state.remoteTasks.length" class="empty-state">当前系列还没有关联的远程任务。</div>
            </div>

            <div v-if="selectedRemoteTaskComputed" class="meta-panel">
              <div class="meta-row">
                <span class="meta-label">远程任务 ID</span>
                <strong class="meta-value">{{ getRemoteTaskId(selectedRemoteTaskComputed) }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">远程状态</span>
                <strong class="meta-value">{{ getRemoteTaskStatus(selectedRemoteTaskComputed) }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">关联草稿</span>
                <strong class="meta-value">{{ getRemoteTaskLinkedJob(selectedRemoteTaskComputed)?.id || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span class="meta-label">结果视频</span>
                <strong class="meta-value">{{ selectedRemoteTaskVideoUrl || "暂无" }}</strong>
              </div>
            </div>

            <div v-if="selectedRemoteTaskCoverUrl || selectedRemoteTaskVideoUrl" class="reference-grid">
              <div v-if="selectedRemoteTaskCoverUrl" class="reference-card">
                <div class="reference-header">
                  <strong class="reference-title">远程封面</strong>
                  <small class="reference-meta">{{ selectedRemoteTaskCoverUrl }}</small>
                </div>
                <el-image class="preview-image" :src="selectedRemoteTaskCoverUrl"
                  :preview-src-list="[selectedRemoteTaskCoverUrl]" :initial-index="0" fit="cover" preview-teleported />
              </div>
              <div v-if="selectedRemoteTaskVideoUrl" class="reference-card">
                <div class="reference-header">
                  <strong class="reference-title">远程视频</strong>
                  <small class="reference-meta">{{ selectedRemoteTaskVideoUrl }}</small>
                </div>
                <video class="video-preview" :src="selectedRemoteTaskVideoUrl" controls preload="metadata" />
              </div>
            </div>

            <div v-if="selectedRemoteTaskComputed" class="form-stack">
              <label class="code-label">Remote Task Payload</label>
              <el-input :model-value="selectedRemoteTaskText" class="field-textarea code-textarea job-code"
                type="textarea" resize="vertical" :autosize="{ minRows: 8, maxRows: 16 }" readonly />
            </div>
          </div>
        </section>
      </aside>
</template>

<script>
import { useWorkspaceContext } from "./workspaceContext";

export default {
  name: "WorkspaceExecutionPanel",
  setup() {
    return useWorkspaceContext();
  }
};
</script>
