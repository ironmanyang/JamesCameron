<template>
      <aside class="column column-right">
        <section v-loading="storyboardConfigPanelLoading" element-loading-text="分镜配置处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div class="panel-header-copy">
              <p class="panel-kicker">分镜</p>
              <h2 class="panel-title">镜头配置</h2>
            </div>
            <el-button class="action-button dark" :disabled="loading.createStoryboard" @click="handleCreateStoryboard">
              {{ loading.createStoryboard ? "创建中..." : "新建分镜板" }}
            </el-button>
          </div>

          <div class="mini-list compact-card-grid compact-card-grid-3">
            <div v-for="item in filteredStoryboards" :key="item.id" class="mini-card selectable"
              :class="{ active: item.id === state.selectedStoryboardId }">
              <div class="item-body compact-card-body" @click="state.selectedStoryboardId = item.id">
                <strong class="item-title">{{ item.id }}</strong>
                <span class="item-meta">{{ item.episode_id }}</span>
                <small class="item-copy">{{ formatStoryboardProductionMode(item.production_mode) }}</small>
                <small class="item-copy">{{ item.shot_ids.length }} 个镜头</small>
              </div>
              <div class="item-actions item-actions-block">
                <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteStoryboard"
                  @click.stop="handleDeleteStoryboard(item)">
                  {{ loading.deleteStoryboard ? "删除中..." : "删除" }}
                </el-button>
              </div>
            </div>
          </div>

          <div v-if="selectedStoryboard" v-loading="storyboardDetailLoading" element-loading-text="分镜板详情加载中..."
            :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
            element-loading-background="rgba(7, 10, 14, 0.16)" class="subsection storyboard-detail-section">
            <div class="panel-header sub-panel-header">
              <div class="panel-header-copy">
                <p class="panel-kicker">生产模式</p>
                <h3 class="panel-title">{{ formatStoryboardProductionMode(selectedStoryboardProductionMode) }}</h3>
              </div>
              <el-button-group class="segmented-button-group no-shrink">
                <el-button v-for="item in storyboardProductionModeOptions" :key="item.value"
                  color="var(--ui-accent-solid)" :plain="selectedStoryboardProductionMode !== item.value" dark
                  @click="handleChangeStoryboardProductionMode(item.value)">
                  {{ item.label }}
                </el-button>
              </el-button-group>
            </div>
            <p class="inline-note">
              {{ selectedStoryboardProductionMode === "shot_pipeline"
                ? "分镜生产模式以单镜头为最小生成单元：一张镜头卡对应一份镜头包与一条 Seedance 任务草稿，适合稳定生产与后期拼接。"
                : "场景直出模式以整段场景为最小生成单元：不创建单镜头卡，后续会围绕场景摘要、节拍与参考设定一次生成整段视频。" }}
            </p>
          </div>

          <template v-if="selectedStoryboardProductionMode === 'shot_pipeline'">
            <div class="subsection">
              <h3 class="section-title">新建镜头</h3>
              <div class="form-stack compact-story-form">
                <div class="compact-form-grid compact-form-grid-2">
                  <el-select v-model="forms.shotSceneId" class="field-select" placeholder="选择关联场景" clearable>
                    <el-option v-for="item in state.scenes" :key="item.id" :label="`${item.name} · ${item.id}`"
                      :value="item.id" />
                  </el-select>

                  <el-select v-model="forms.shotInputMode" class="field-select" placeholder="选择 Seedance 输入模式">
                    <el-option v-for="item in shotInputModeOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                </div>

                <div class="compact-form-grid compact-form-grid-4">
                  <el-select v-model="forms.shotAspectRatio" class="field-select" placeholder="视频比例">
                    <el-option v-for="item in shotAspectRatioOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                  <el-select v-model="forms.shotResolution" class="field-select" placeholder="分辨率">
                    <el-option v-for="item in shotResolutionOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>

                  <el-input-number v-model="forms.shotDuration" class="field-number" :min="1" :max="15" :step="1">
                    <template #suffix>
                      <span class="field-suffix">秒</span>
                    </template>
                  </el-input-number>
                  <el-select v-model="forms.shotGenerationCount" class="field-select" placeholder="生成数量">
                    <el-option v-for="item in shotGenerationCountOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                </div>

                <div class="compact-form-grid compact-form-grid-3">
                  <div class="checkbox-tile">
                    <el-checkbox v-model="forms.shotGenerateAudio">需要声音</el-checkbox>
                  </div>
                  <el-select v-model="forms.shotSize" class="field-select" placeholder="镜头景别">
                    <el-option v-for="item in shotSizeOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>

                  <el-select v-model="forms.shotMovement" class="field-select" placeholder="运镜方式">
                    <el-option v-for="item in shotMovementOptions" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                </div>

                <div v-if="isReferenceMode(forms.shotInputMode)" class="shot-media-panel">
                  <div class="shot-media-header">
                    <div class="shot-media-copy">
                      <strong class="shot-media-title">参考生成</strong>
                      <p class="upload-copy">将自动注入角色圣经拼图与场景参考拼图，不需要上传首尾帧。</p>
                    </div>
                    <small class="shot-media-badge">{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).totalCount }}
                      张系统参考</small>
                  </div>
                  <div class="meta-list compact-meta-list">
                    <div class="meta-item">
                      <span class="meta-label">角色圣经拼图</span>
                      <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).characterCount }}</strong>
                    </div>
                    <div class="meta-item">
                      <span class="meta-label">场景参考拼图</span>
                      <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).sceneCount }}</strong>
                    </div>
                    <div class="meta-item">
                      <span class="meta-label">角色匹配</span>
                      <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).characterNames.join("、") || "未选角色" }}</strong>
                    </div>
                    <div class="meta-item">
                      <span class="meta-label">场景匹配</span>
                      <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, forms.shotSceneId).sceneName || "未选场景" }}</strong>
                    </div>
                  </div>
                </div>

                <div v-else-if="isFirstLastFrameMode(forms.shotInputMode)" class="shot-media-panel">
                  <div class="shot-media-header">
                    <div class="shot-media-copy">
                      <strong class="shot-media-title">首尾帧生成</strong>
                      <p class="upload-copy">首帧必传，尾帧可选。本模式不会注入角色圣经拼图和场景参考拼图。</p>
                    </div>
                    <small class="shot-media-badge">{{ getShotMediaEntries(forms).length }} 张图片</small>
                  </div>

                  <div class="shot-media-grid">
                    <label class="shot-upload-tile">
                      <span class="shot-upload-chip">首帧</span>
                      <strong class="shot-upload-title">上传首帧图</strong>
                      <small class="shot-upload-copy">必传，用于确定开场画面</small>
                      <input class="shot-upload-input" type="file" accept="image/*"
                        @change="handleShotMediaUpload(forms, 'first_frame', $event)" />
                    </label>

                    <label class="shot-upload-tile">
                      <span class="shot-upload-chip">尾帧</span>
                      <strong class="shot-upload-title">上传尾帧图</strong>
                      <small class="shot-upload-copy">可选，用于约束结尾状态</small>
                      <input class="shot-upload-input" type="file" accept="image/*"
                        @change="handleShotMediaUpload(forms, 'last_frame', $event)" />
                    </label>
                  </div>

                  <div v-if="getShotMediaEntries(forms).length" class="reference-grid shot-media-preview-grid">
                    <div v-for="image in getShotMediaEntries(forms)" :key="image.key"
                      class="reference-card shot-media-card">
                      <div class="reference-header">
                        <strong class="reference-title">{{ image.label }}</strong>
                        <small class="reference-meta">{{ image.path }}</small>
                      </div>
                      <el-button class="action-button ghost danger compact-button" :disabled="loading.shotMediaUpload"
                        @click="removeShotMediaEntry(forms, image.kind, image.path)">
                        移除
                      </el-button>
                      <el-image class="preview-image" :src="assetUrl(image.path)"
                        :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                        preview-teleported />
                    </div>
                  </div>
                </div>

                <div class="compact-form-grid compact-form-grid-2">
                  <el-input v-model="forms.shotLighting" class="field" type="text" placeholder="输入光线关键词" />
                  <el-input v-model="forms.shotPalette" class="field" type="text" placeholder="输入色调关键词" />
                </div>

                <div class="compact-panel-grid">
                  <div class="story-binding-panel">
                    <div class="story-binding-header">
                      <strong class="story-binding-title">剧情绑定</strong>
                      <small class="story-binding-copy">镜头卡自身保存剧情描述、对白与原文摘录，镜头包组装优先使用这里。</small>
                    </div>
                    <el-input v-model="forms.shotStoryDescription" class="field-textarea compact" type="textarea"
                      :autosize="{ minRows: 2, maxRows: 4 }" placeholder="剧情描述：这个镜头里具体拍什么" />
                    <div class="split-grid">
                      <el-input v-model="forms.shotStoryEmotion" class="field" type="text" placeholder="情绪基调" />
                      <el-input v-model="forms.shotStoryBeat" class="field" type="text" placeholder="剧情节拍 / 动作节点" />
                    </div>
                    <el-input v-model="forms.shotStoryDialogue" class="field-textarea compact" type="textarea"
                      :autosize="{ minRows: 2, maxRows: 5 }" placeholder="对白，一行一句，例如：乌萨奇: 小八小八，别睡啦！" />
                    <el-input v-model="forms.shotStoryRawExcerpt" class="field-textarea compact" type="textarea"
                      :autosize="{ minRows: 2, maxRows: 6 }" placeholder="剧本原文摘录，可直接粘贴当前镜头对应的原始剧本片段" />
                  </div>

                  <div class="story-binding-panel">
                    <div class="story-binding-header">
                      <strong class="story-binding-title">角色锚点策略</strong>
                      <small class="story-binding-copy">默认自动按景别抽取角色锚点；如有必要，可对当前镜头里的单个角色单独覆盖。</small>
                    </div>
                    <el-select v-model="forms.shotAnchorMode" class="field-select" placeholder="选择默认锚点策略">
                      <el-option v-for="option in shotAnchorModeOptions" :key="option.value" :label="option.label"
                        :value="option.value" />
                    </el-select>
                    <div v-if="state.selectedCharacterIds.length" class="compact-form-grid compact-form-grid-2 compact-stack">
                      <div v-for="characterId in state.selectedCharacterIds" :key="`create-anchor-${characterId}`"
                        class="split-grid">
                        <div class="inline-label">
                          {{state.characters.find((item) => item.id === characterId)?.name || characterId}}
                        </div>
                        <el-select :model-value="getShotAnchorOverrideValue(forms, characterId)" class="field-select"
                          placeholder="跟随默认策略"
                          @update:model-value="setShotAnchorOverrideValue(forms, characterId, $event)">
                          <el-option v-for="option in shotAnchorModeOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                      </div>
                    </div>
                  </div>
                </div>

                <el-checkbox-group v-model="state.selectedCharacterIds" class="check-grid compact-check-grid">
                  <el-checkbox v-for="item in state.characters" :key="item.id" :value="item.id" class="check-card">
                    {{ item.name }}
                  </el-checkbox>
                </el-checkbox-group>

                <el-button class="action-button warm primary-action" :disabled="loading.createShot"
                  @click="handleCreateShot">
                  {{ loading.createShot ? "创建中..." : "生成镜头卡" }}
                </el-button>
              </div>
            </div>

            <div class="mini-list compact-card-grid compact-card-grid-3 shot-card-grid">
              <h3 class="section-title">导入的静头卡最好编辑一下，因为时间之类的都是默认的</h3>
              <div class="subsection-header">
                <div class="inline-actions compact-actions">
                  <el-button class="action-button ghost compact-button" @click="selectAllShotsForBatch">
                    全选批次
                  </el-button>
                  <el-button class="action-button ghost compact-button" @click="clearShotSelection">
                    清空勾选
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.clearShots"
                    @click="handleClearShots">
                    {{ loading.clearShots ? "清空中..." : "清空镜头卡" }}
                  </el-button>
                </div>
              </div>
              <div v-for="item in state.shots" :key="item.id" class="mini-card selectable"
                :class="{ active: item.id === state.selectedShotId, editing: isEditingShot(item.id) }">
                <div class="item-body compact-card-body" @click="state.selectedShotId = item.id">
                  <template v-if="isEditingShot(item.id)">
                    <div class="item-editor">
                      <el-select v-model="inlineEditing.shotSceneId" class="field-select" placeholder="选择关联场景">
                        <el-option v-for="scene in state.scenes" :key="scene.id" :label="`${scene.name} · ${scene.id}`"
                          :value="scene.id" />
                      </el-select>
                      <el-select v-model="inlineEditing.shotInputMode" class="field-select"
                        placeholder="选择 Seedance 输入模式">
                        <el-option v-for="option in shotInputModeOptions" :key="option.value" :label="option.label"
                          :value="option.value" />
                      </el-select>
                      <div class="split-grid">
                        <el-select v-model="inlineEditing.shotAspectRatio" class="field-select" placeholder="视频比例">
                          <el-option v-for="option in shotAspectRatioOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                        <el-select v-model="inlineEditing.shotResolution" class="field-select" placeholder="分辨率">
                          <el-option v-for="option in shotResolutionOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                      </div>
                      <div class="split-grid">
                        <el-input-number v-model="inlineEditing.shotDuration" class="field-number" :min="1" :max="15"
                          :step="1">
                          <template #suffix>
                            <span class="field-suffix">秒</span>
                          </template>
                        </el-input-number>
                        <el-select v-model="inlineEditing.shotGenerationCount" class="field-select" placeholder="生成数量">
                          <el-option v-for="option in shotGenerationCountOptions" :key="option.value"
                            :label="option.label" :value="option.value" />
                        </el-select>
                      </div>
                      <el-checkbox v-model="inlineEditing.shotGenerateAudio">需要声音</el-checkbox>
                      <div v-if="isReferenceMode(inlineEditing.shotInputMode)"
                        class="shot-media-panel inline-shot-media-panel">
                        <div class="shot-media-header">
                          <div class="shot-media-copy">
                            <strong class="shot-media-title">参考生成</strong>
                            <p class="upload-copy">将自动注入角色圣经拼图与场景参考拼图，不展示首尾帧上传。</p>
                          </div>
                          <small class="shot-media-badge">{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).totalCount }}
                            张系统参考</small>
                        </div>
                        <div class="meta-list compact-meta-list">
                          <div class="meta-item">
                            <span class="meta-label">角色圣经拼图</span>
                            <strong class="meta-value">{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).characterCount }}</strong>
                          </div>
                          <div class="meta-item">
                            <span class="meta-label">场景参考拼图</span>
                            <strong class="meta-value">{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).sceneCount }}</strong>
                          </div>
                          <div class="meta-item">
                            <span class="meta-label">角色匹配</span>
                            <strong class="meta-value">{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).characterNames.join("、") || "未选角色" }}</strong>
                          </div>
                          <div class="meta-item">
                            <span class="meta-label">场景匹配</span>
                            <strong class="meta-value">{{ getAutoReferenceSummary(inlineEditing.shotCharacterIds, inlineEditing.shotSceneId).sceneName || "未选场景" }}</strong>
                          </div>
                        </div>
                      </div>
                      <div v-else-if="isFirstLastFrameMode(inlineEditing.shotInputMode)"
                        class="shot-media-panel inline-shot-media-panel">
                        <div class="shot-media-header">
                          <div class="shot-media-copy">
                            <strong class="shot-media-title">首尾帧生成</strong>
                            <p class="upload-copy">首帧必传，尾帧可选。本模式不会注入角色圣经拼图和场景参考拼图。</p>
                          </div>
                          <small class="shot-media-badge">{{ getShotMediaEntries(inlineEditing).length }} 张图片</small>
                        </div>

                        <div class="shot-media-grid">
                          <label class="shot-upload-tile">
                            <span class="shot-upload-chip">首帧</span>
                            <strong class="shot-upload-title">替换首帧图</strong>
                            <small class="shot-upload-copy">必传，用于确定开场画面</small>
                            <input class="shot-upload-input" type="file" accept="image/*"
                              @change="handleShotMediaUpload(inlineEditing, 'first_frame', $event)" />
                          </label>

                          <label class="shot-upload-tile">
                            <span class="shot-upload-chip">尾帧</span>
                            <strong class="shot-upload-title">替换尾帧图</strong>
                            <small class="shot-upload-copy">可选，用于约束结尾状态</small>
                            <input class="shot-upload-input" type="file" accept="image/*"
                              @change="handleShotMediaUpload(inlineEditing, 'last_frame', $event)" />
                          </label>
                        </div>

                        <div v-if="getShotMediaEntries(inlineEditing).length"
                          class="reference-grid shot-media-preview-grid">
                          <div v-for="image in getShotMediaEntries(inlineEditing)" :key="image.key"
                            class="reference-card shot-media-card">
                            <div class="reference-header">
                              <strong class="reference-title">{{ image.label }}</strong>
                              <small class="reference-meta">{{ image.path }}</small>
                            </div>
                            <el-button class="action-button ghost danger compact-button"
                              :disabled="loading.shotMediaUpload"
                              @click="removeShotMediaEntry(inlineEditing, image.kind, image.path)">
                              移除
                            </el-button>
                            <el-image class="preview-image" :src="assetUrl(image.path)"
                              :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                              preview-teleported />
                          </div>
                        </div>
                      </div>
                      <div class="split-grid">
                        <el-select v-model="inlineEditing.shotSize" class="field-select" placeholder="镜头景别">
                          <el-option v-for="option in shotSizeOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                        <el-select v-model="inlineEditing.shotMovement" class="field-select" placeholder="运镜方式">
                          <el-option v-for="option in shotMovementOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                      </div>
                      <div class="split-grid">
                        <el-input v-model="inlineEditing.shotLighting" class="field" type="text"
                          placeholder="输入光线关键词" />
                        <el-input v-model="inlineEditing.shotPalette" class="field" type="text" placeholder="输入色调关键词" />
                      </div>
                      <div class="story-binding-panel">
                        <div class="story-binding-header">
                          <strong class="story-binding-title">剧情绑定</strong>
                          <small class="story-binding-copy">这里的描述、对白、摘录会直接参与镜头包组装。</small>
                        </div>
                        <el-input v-model="inlineEditing.shotStoryDescription" class="field-textarea compact"
                          type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="剧情描述：这个镜头里具体拍什么" />
                        <div class="split-grid">
                          <el-input v-model="inlineEditing.shotStoryEmotion" class="field" type="text"
                            placeholder="情绪基调" />
                          <el-input v-model="inlineEditing.shotStoryBeat" class="field" type="text"
                            placeholder="剧情节拍 / 动作节点" />
                        </div>
                        <el-input v-model="inlineEditing.shotStoryDialogue" class="field-textarea compact"
                          type="textarea" :autosize="{ minRows: 2, maxRows: 5 }"
                          placeholder="对白，一行一句，例如：乌萨奇: 小八小八，别睡啦！" />
                        <el-input v-model="inlineEditing.shotStoryRawExcerpt" class="field-textarea compact"
                          type="textarea" :autosize="{ minRows: 2, maxRows: 6 }"
                          placeholder="剧本原文摘录，可直接粘贴当前镜头对应的原始剧本片段" />
                      </div>
                      <div class="story-binding-panel">
                        <div class="story-binding-header">
                          <strong class="story-binding-title">角色锚点策略</strong>
                          <small class="story-binding-copy">先用全局策略控制当前镜头，再按角色做局部覆盖。</small>
                        </div>
                        <el-select v-model="inlineEditing.shotAnchorMode" class="field-select" placeholder="选择默认锚点策略">
                          <el-option v-for="option in shotAnchorModeOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                        </el-select>
                        <div v-if="inlineEditing.shotCharacterIds.length" class="compact-form-grid compact-form-grid-2 compact-stack">
                          <div v-for="characterId in inlineEditing.shotCharacterIds" :key="`edit-anchor-${characterId}`"
                            class="split-grid">
                            <div class="inline-label">
                              {{state.characters.find((item) => item.id === characterId)?.name || characterId}}
                            </div>
                            <el-select :model-value="getShotAnchorOverrideValue(inlineEditing, characterId)"
                              class="field-select" placeholder="跟随默认策略"
                              @update:model-value="setShotAnchorOverrideValue(inlineEditing, characterId, $event)">
                              <el-option v-for="option in shotAnchorModeOptions" :key="option.value"
                                :label="option.label" :value="option.value" />
                            </el-select>
                          </div>
                        </div>
                      </div>
                      <el-checkbox-group v-model="inlineEditing.shotCharacterIds" class="check-grid compact-check-grid">
                        <el-checkbox v-for="character in state.characters" :key="character.id" :value="character.id"
                          class="check-card">
                          {{ character.name }}
                        </el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </template>
                  <template v-else>
                    <strong class="item-title">{{ item.id }}</strong>
                    <small class="item-copy">{{ getShotStoryDisplay(item, "description") }}</small>
                    <small class="item-copy">对白：{{ formatDialogueEntries(item.dialogue) || "暂无" }}</small>
                    <small class="item-copy">情绪 / 节拍：{{ getShotStoryDisplay(item, "emotion") }} ·
                      {{ getShotStoryDisplay(item, "beat") }}</small>
                    <span class="item-meta">{{ formatShotInputMode(item.media?.mode) }}</span>
                    <small class="item-copy">锚点：{{ formatShotAnchorMode(item.anchor_strategy?.mode) }}<template
                        v-if="countShotAnchorOverrides(item.anchor_strategy?.per_character, item.characters)"> · {{
                          countShotAnchorOverrides(item.anchor_strategy?.per_character, item.characters) }}
                        个角色覆盖</template></small>
                    <span class="item-meta">{{ formatShotAspectRatio(item.visual.aspect_ratio) }} ·
                      {{ formatShotResolution(item.visual.resolution) }}</span>
                    <span class="item-meta">{{ formatShotSize(item.visual.shot_size) }} ·
                      {{ formatShotMovement(item.visual.camera_movement) }}</span>
                    <small class="item-copy">场景：{{ formatSceneLabel(item.scene_id) }}</small>
                    <small class="item-copy">输出：{{ item.visual.duration_seconds }} 秒 · {{ item.visual.generation_count || 1 }} 条 ·
                      {{ item.media?.generate_audio ? "有声" : "无声" }}</small>
                    <small class="item-copy">光线：{{ formatShotKeyword(item.visual.lighting) }} · 色调：{{
                      formatShotKeyword(item.visual.palette)
                    }}</small>
                    <small class="item-copy">参考：{{ isReferenceMode(item.media?.mode) ? "角色圣经拼图 + 场景参考拼图" :
                      isFirstLastFrameMode(item.media?.mode) ? "首帧/尾帧" : "纯文字" }}</small>
                    <small class="item-copy">{{ (item.characters || []).length }} 个角色</small>
                  </template>
                </div>
                <div class="item-actions item-actions-block">
                  <el-button v-if="!isEditingShot(item.id)" class="action-button compact-button"
                    :class="isShotSelectedForBatch(item.id) ? 'warm' : 'ghost'"
                    @click.stop="toggleShotSelection(item.id)">
                    {{ isShotSelectedForBatch(item.id) ? "已选入批次" : "选入批次" }}
                  </el-button>
                  <el-button v-if="isEditingShot(item.id)" class="action-button dark compact-button"
                    :disabled="loading.updateShot" @click.stop="handleUpdateShot(item)">
                    {{ loading.updateShot ? "保存中..." : "保存" }}
                  </el-button>
                  <el-button v-else class="action-button ghost compact-button" @click.stop="startShotEdit(item)">
                    编辑
                  </el-button>
                  <el-button v-if="isEditingShot(item.id)" class="action-button ghost compact-button"
                    @click.stop="cancelShotEdit">
                    取消
                  </el-button>
                  <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteShot"
                    @click.stop="handleDeleteShot(item)">
                    {{ loading.deleteShot ? "删除中..." : "删除" }}
                  </el-button>
                </div>
              </div>
            </div>
          </template>

          <div v-else class="subsection">
            <h3 class="section-title">场景直出配置</h3>
            <div class="form-stack compact-story-form">
              <div class="compact-form-grid compact-form-grid-2">
                <el-select v-model="forms.shotSceneId" class="field-select" placeholder="选择要直出的场景" clearable>
                  <el-option v-for="item in state.scenes" :key="item.id" :label="`${item.name} · ${item.id}`"
                    :value="item.id" />
                </el-select>

                <el-select v-model="forms.shotInputMode" class="field-select" placeholder="选择 Seedance 输入模式">
                  <el-option v-for="item in shotInputModeOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
              </div>

              <div class="compact-form-grid compact-form-grid-4">
                <el-select v-model="forms.shotAspectRatio" class="field-select" placeholder="视频比例">
                  <el-option v-for="item in shotAspectRatioOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
                <el-select v-model="forms.shotResolution" class="field-select" placeholder="分辨率">
                  <el-option v-for="item in shotResolutionOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>

                <el-input-number v-model="forms.shotDuration" class="field-number" :min="1" :max="15" :step="1">
                  <template #suffix>
                    <span class="field-suffix">秒</span>
                  </template>
                </el-input-number>
                <el-select v-model="forms.shotGenerationCount" class="field-select" placeholder="生成数量">
                  <el-option v-for="item in shotGenerationCountOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
              </div>

              <div class="compact-form-grid compact-form-grid-3">
                <div class="checkbox-tile">
                  <el-checkbox v-model="forms.shotGenerateAudio">需要声音</el-checkbox>
                </div>
                <el-select v-model="forms.shotSize" class="field-select" placeholder="主镜头景别">
                  <el-option v-for="item in shotSizeOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>

                <el-select v-model="forms.shotMovement" class="field-select" placeholder="主运镜方式">
                  <el-option v-for="item in shotMovementOptions" :key="item.value" :label="item.label"
                    :value="item.value" />
                </el-select>
              </div>

              <div v-if="isReferenceMode(forms.shotInputMode)" class="shot-media-panel">
                <div class="shot-media-header">
                  <div class="shot-media-copy">
                    <strong class="shot-media-title">参考生成</strong>
                    <p class="upload-copy">自动注入角色圣经拼图与场景参考拼图，用于整段场景视频的角色和空间稳定。</p>
                  </div>
                  <small class="shot-media-badge">{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).totalCount }}
                    张系统参考</small>
                </div>
                <div class="meta-list compact-meta-list">
                  <div class="meta-item">
                    <span class="meta-label">角色圣经拼图</span>
                    <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).characterCount }}</strong>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">场景参考拼图</span>
                    <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).sceneCount }}</strong>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">角色匹配</span>
                    <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).characterNames.join("、") || "未选角色" }}</strong>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">场景匹配</span>
                    <strong class="meta-value">{{ getAutoReferenceSummary(state.selectedCharacterIds, getSceneDirectSceneId()).sceneName || "未选场景" }}</strong>
                  </div>
                </div>
              </div>

              <div v-else-if="isFirstLastFrameMode(forms.shotInputMode)" class="shot-media-panel">
                <div class="shot-media-header">
                  <div class="shot-media-copy">
                    <strong class="shot-media-title">首尾帧生成</strong>
                    <p class="upload-copy">首帧必传，尾帧可选。场景直出时会围绕首尾帧完成整段剧情过程。</p>
                  </div>
                  <small class="shot-media-badge">{{ getShotMediaEntries(forms).length }} 张图片</small>
                </div>

                <div class="shot-media-grid">
                  <label class="shot-upload-tile">
                    <span class="shot-upload-chip">首帧</span>
                    <strong class="shot-upload-title">上传首帧图</strong>
                    <small class="shot-upload-copy">必传，用于定义开场画面</small>
                    <input class="shot-upload-input" type="file" accept="image/*"
                      @change="handleShotMediaUpload(forms, 'first_frame', $event)" />
                  </label>

                  <label class="shot-upload-tile">
                    <span class="shot-upload-chip">尾帧</span>
                    <strong class="shot-upload-title">上传尾帧图</strong>
                    <small class="shot-upload-copy">可选，用于约束结尾状态</small>
                    <input class="shot-upload-input" type="file" accept="image/*"
                      @change="handleShotMediaUpload(forms, 'last_frame', $event)" />
                  </label>
                </div>

                <div v-if="getShotMediaEntries(forms).length" class="reference-grid shot-media-preview-grid">
                  <div v-for="image in getShotMediaEntries(forms)" :key="image.key"
                    class="reference-card shot-media-card">
                    <div class="reference-header">
                      <strong class="reference-title">{{ image.label }}</strong>
                      <small class="reference-meta">{{ image.path }}</small>
                    </div>
                    <el-button class="action-button ghost danger compact-button" :disabled="loading.shotMediaUpload"
                      @click="removeShotMediaEntry(forms, image.kind, image.path)">
                      移除
                    </el-button>
                    <el-image class="preview-image" :src="assetUrl(image.path)"
                      :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover"
                      preview-teleported />
                  </div>
                </div>
              </div>

              <div class="compact-form-grid compact-form-grid-2">
                <el-input v-model="forms.shotLighting" class="field" type="text" placeholder="输入光线关键词" />
                <el-input v-model="forms.shotPalette" class="field" type="text" placeholder="输入色调关键词" />
              </div>

              <el-checkbox-group v-model="state.selectedCharacterIds" class="check-grid compact-check-grid">
                <el-checkbox v-for="item in state.characters" :key="item.id" :value="item.id" class="check-card">
                  {{ item.name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
        </section>

      </aside>
</template>

<script>
import { useWorkspaceContext } from "./workspaceContext";

export default {
  name: "WorkspaceStoryboardPanel",
  setup() {
    return useWorkspaceContext();
  }
};
</script>
