<template>
  <section class="column column-main">
    <template v-if="workspaceStep === 'script'">
      <section class="panel hero-panel">
        <div class="hero-grid hero-grid-compact">
          <div class="hero-copy hero-copy-compact">
            <div class="panel-header hero-header">
              <div>
                <p class="panel-kicker">当前系列</p>
                <h2>{{ selectedSeries?.name || "尚未选择系列" }}</h2>
              </div>
              <span v-if="selectedSeries" class="series-slug">{{ selectedSeries.slug }}</span>
            </div>
            <p class="hero-lead hero-lead-compact">
              当前工作区会跟随已选系列切换，右侧统计只显示这个系列的角色、场景、分镜板和任务数量。
            </p>
          </div>

          <div class="hero-summary">
            <div class="summary-grid summary-grid-compact">
              <article class="summary-card">
                <span>角色</span>
                <strong>{{ state.assets.characters }}</strong>
              </article>
              <article class="summary-card">
                <span>场景</span>
                <strong>{{ state.assets.scenes }}</strong>
              </article>
              <article class="summary-card">
                <span>分镜板</span>
                <strong>{{ state.assets.storyboards }}</strong>
              </article>
              <article class="summary-card">
                <span>任务</span>
                <strong>{{ state.assets.jobs }}</strong>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section v-loading="episodesPanelLoading" element-loading-text="剧集面板加载中..."
        :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
        element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">剧集</p>
            <h2>剧本与结构化拆解</h2>
          </div>
          <div class="inline-actions panel-header-actions">
            <el-input v-model="forms.episodeName" class="field inline-field" type="text" placeholder="输入剧集名称" />
            <el-button class="action-button dark no-shrink" :disabled="loading.createEpisode"
              @click="handleCreateEpisode">
              {{ loading.createEpisode ? "创建中..." : "新建剧集" }}
            </el-button>
          </div>
        </div>

        <div class="episode-strip">
          <div v-for="item in state.episodes" :key="item.id" class="episode-chip"
            :class="{ active: item.id === state.selectedEpisodeId }">
            <div class="item-body episode-item-body" @click="state.selectedEpisodeId = item.id">
              <template v-if="isEditingEpisode(item.id)">
                <div class="item-editor">
                  <el-input v-model="inlineEditing.episodeName" class="field item-inline-field" type="text"
                    placeholder="输入剧集名称" />
                  <span>{{ item.id }}</span>
                </div>
              </template>
              <template v-else>
                <strong>{{ item.name }}</strong>
                <span>{{ item.id }}</span>
              </template>
            </div>
            <div class="item-actions episode-item-actions">
              <el-button v-if="isEditingEpisode(item.id)" class="action-button dark compact-button"
                :disabled="loading.updateEpisode" @click.stop="handleUpdateEpisode(item)">
                {{ loading.updateEpisode ? "保存中..." : "保存" }}
              </el-button>
              <el-button v-else class="action-button ghost compact-button" @click.stop="startEpisodeEdit(item)">
                编辑
              </el-button>
              <el-button v-if="isEditingEpisode(item.id)" class="action-button ghost compact-button"
                @click.stop="cancelEpisodeEdit">
                取消
              </el-button>
              <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteEpisode"
                @click.stop="handleDeleteEpisode(item)">
                {{ loading.deleteEpisode ? "删除中..." : "删除" }}
              </el-button>
            </div>
          </div>
        </div>
      </section>

      <section class="editor-grid">
        <article v-loading="rawScriptPanelLoading" element-loading-text="剧本处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel editor-panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">原始剧本</p>
              <h2>剧本输入区</h2>
            </div>
            <div class="inline-actions compact-actions panel-header-actions">
              <el-button class="action-button ghost" :disabled="loading.analyzeScript" @click="handleAnalyzeScript">
                {{ loading.analyzeScript ? "分析中..." : "AI 拆解剧本" }}
              </el-button>
              <el-button class="action-button dark" :disabled="loading.saveRaw" @click="handleSaveRawScript">
                {{ loading.saveRaw ? "保存中..." : "保存原稿" }}
              </el-button>
            </div>
          </div>
          <el-input v-model="state.rawScript" class="field-textarea editor-textarea" type="textarea"
            :autosize="{ minRows: 22, maxRows: 30 }" resize="auto" placeholder="在这里粘贴或编写原始剧本内容。" />
        </article>

        <article v-loading="parsedScriptPanelLoading" element-loading-text="解析结果处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel editor-panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">结构化结果</p>
              <h2>解析 JSON</h2>
            </div>
            <div class="inline-actions compact-actions panel-header-actions">
              <el-button-group class="segmented-button-group">
                <el-button color="var(--ui-accent-solid)" :plain="parsedScriptViewMode !== 'readable'" dark
                  @click="parsedScriptViewMode = 'readable'">
                  可读视图
                </el-button>
                <el-button color="var(--ui-accent-solid)" :plain="parsedScriptViewMode !== 'raw'" dark
                  @click="parsedScriptViewMode = 'raw'">
                  原生结构
                </el-button>

              </el-button-group>
              <el-button class="action-button dark" :disabled="loading.saveParsed" @click="handleSaveParsedScript">
                {{ loading.saveParsed ? "保存中..." : "保存 JSON" }}
              </el-button>
            </div>
          </div>
          <template v-if="parsedScriptViewMode === 'raw'">
            <el-input v-model="state.parsedScriptText" class="field-textarea editor-textarea code-textarea"
              type="textarea" :autosize="{ minRows: 22, maxRows: 30 }" resize="auto" placeholder="" />
          </template>
          <template v-else>
            <div v-if="parsedScriptObject" class="readable-script-view">
              <div v-if="parsedScriptReadableOutline" class="meta-panel">
                <div class="meta-row">
                  <span>剧集标题</span>
                  <strong>{{ formatReadableField(parsedScriptReadableOutline["剧集标题"]) }}</strong>
                </div>
                <div class="meta-row">
                  <span>场景总数</span>
                  <strong>{{ parsedScriptReadableOutline["场景总数"] ?? 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span>角色总览</span>
                  <strong>{{ (parsedScriptReadableOutline["角色总览"] || []).join("、") || "暂无" }}</strong>
                </div>
              </div>


              <div v-if="parsedScriptReadableScenes.length" class="form-stack">
                <div v-for="(scene, sceneIndex) in parsedScriptReadableScenes"
                  :key="scene.scene_id || scene.readable?.['场景编号']" class="meta-panel">
                  <template v-if="isEditingParsedScene(sceneIndex)">
                    <div class="script-scene-editor grid-span-full">
                      <div class="meta-row-wide">
                        <span>场景编号</span>
                        <strong>{{ getReadableSceneInfo(scene)["场景编号"] ?? scene.scene_id ?? "暂无" }}</strong>
                      </div>
                      <div class="split-grid">
                        <div class="meta-row">
                          <span>场景地点</span>
                          <el-input v-model="parsedSceneEditing.location" class="field" type="text"
                            placeholder="场景地点" />
                        </div>
                        <div class="meta-row">
                          <span>时间</span>
                          <el-input v-model="parsedSceneEditing.time" class="field" type="text" placeholder="时间" />
                        </div>
                        <div class="meta-row meta-row-wide">
                          <span>场景摘要</span>
                          <el-input v-model="parsedSceneEditing.summary" class="field-textarea compact" type="textarea"
                            :autosize="{ minRows: 2, maxRows: 4 }" placeholder="场景摘要" />
                        </div>
                      </div>

                      <div class="script-scene-actions">
                        <el-button class="action-button dark compact-button"
                          @click.stop="saveParsedSceneEdit(sceneIndex)">
                          保存场景
                        </el-button>
                        <el-button class="action-button ghost compact-button" @click.stop="cancelParsedSceneEdit">
                          取消
                        </el-button>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div class="meta-row-wide">
                      <span>场景编号</span>
                      <strong>{{ getReadableSceneInfo(scene)[" 场景编号"] ?? scene.scene_id ?? "暂无" }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>场景地点</span>
                      <strong>{{ formatReadableField(getReadableSceneInfo(scene)["场景地点"] || scene.location) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>时间</span>
                      <strong>{{ formatReadableField(getReadableSceneInfo(scene)["时间"] || scene.time) }}</strong>
                    </div>
                    <div class="meta-row">
                      <span>镜头数</span>
                      <strong>{{ getReadableSceneInfo(scene)["镜头数"] ?? (scene.shots || []).length }}</strong>
                    </div>
                    <div class="meta-row meta-row-wide">
                      <span>场景摘要</span>
                      <strong>{{ formatReadableField(getReadableSceneInfo(scene)["场景摘要"] || scene.summary) }}</strong>
                    </div>
                    <div class="script-scene-actions">
                      <el-button class="action-button ghost compact-button"
                        @click.stop="startParsedSceneEdit(scene, sceneIndex)">
                        修改场景
                      </el-button>
                    </div>
                  </template>

                  <div v-if="(scene.shots || []).length" class="mini-list grid-span-full">
                    <div v-for="(shot, shotIndex) in scene.shots || []"
                      :key="`${scene.scene_id || 'scene'}-${shot.shot_id || getReadableShotInfo(shot)['镜头编号']}`"
                      class="mini-card">
                      <div class="item-body">
                        <template v-if="isEditingParsedShot(sceneIndex, shotIndex)">
                          <div class="script-shot-editor">
                            <strong>镜头 {{ getReadableShotInfo(shot)["镜头编号"] ?? shot.shot_id ?? "?" }}</strong>
                            <el-input v-model="parsedShotEditing.description" class="field-textarea compact"
                              type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="画面描述" />
                            <div class="split-grid">
                              <el-input v-model="parsedShotEditing.cameraAngle" class="field" type="text"
                                placeholder="机位角度" />
                              <el-input v-model="parsedShotEditing.cameraMovement" class="field" type="text"
                                placeholder="运镜方式" />
                            </div>
                            <el-input v-model="parsedShotEditing.cameraShotSize" class="field" type="text"
                              placeholder="景别" />
                            <el-input v-model="parsedShotEditing.charactersText" class="field" type="text"
                              placeholder="角色，多个角色用 顿号 / 逗号 分隔" />
                            <el-input v-model="parsedShotEditing.dialoguesText" class="field-textarea compact"
                              type="textarea" :autosize="{ minRows: 2, maxRows: 5 }"
                              placeholder="对白，一行一句，例如：乌萨奇: 小八小八，别睡啦！" />
                            <div class="split-grid">
                              <el-input v-model="parsedShotEditing.emotion" class="field" type="text"
                                placeholder="情绪" />
                              <el-input v-model="parsedShotEditing.beat" class="field" type="text" placeholder="剧情节拍" />
                            </div>
                            <div class="script-shot-actions">
                              <el-button class="action-button dark compact-button"
                                @click.stop="saveParsedShotEdit(sceneIndex, shotIndex)">
                                保存修改
                              </el-button>
                              <el-button class="action-button ghost compact-button" @click.stop="cancelParsedShotEdit">
                                取消
                              </el-button>
                              <el-button class="action-button dark compact-button"
                                :disabled="loading.importParsedShot || !state.selectedStoryboardId"
                                @click.stop="handleImportReadableShot(scene, shot, sceneIndex, shotIndex)">
                                {{ loading.importParsedShot ? "导入中..." : "导入为镜头卡草稿" }}
                              </el-button>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <strong>镜头 {{ getReadableShotInfo(shot)["镜头编号"] ?? shot.shot_id ?? "?" }}</strong>
                          <small>{{ formatReadableField(getReadableShotInfo(shot)["画面描述"] || shot.description) }}</small>
                          <small>{{ formatReadableField(getReadableShotInfo(shot)["镜头信息"] || shot.camera?.summary || formatLegacyCameraSummary(shot.camera)) }}</small>
                          <small>角色：{{ formatReadableField(getReadableShotInfo(shot)["出场角色"] || (shot.characters ||
                            []).join("、")) }}</small>
                          <small>对白：{{ formatReadableField(getReadableShotInfo(shot)["对白"] ||
                            formatDialogueEntries(shot.dialogues)) }}</small>
                          <small>情绪 / 节拍：{{ formatReadableField(getReadableShotInfo(shot)["情绪"] || shot.emotion) }} ·
                            {{ formatReadableField(getReadableShotInfo(shot)["剧情节拍"] || shot.beat) }}</small>
                          <div class="script-shot-actions">
                            <el-button class="action-button ghost compact-button"
                              @click.stop="startParsedShotEdit(scene, shot, sceneIndex, shotIndex)">
                              修改分镜
                            </el-button>
                            <el-button class="action-button dark compact-button"
                              :disabled="loading.importParsedShot || !state.selectedStoryboardId"
                              @click.stop="handleImportReadableShot(scene, shot, sceneIndex, shotIndex)">
                              {{ loading.importParsedShot ? "导入中..." : "导入为镜头卡草稿" }}
                            </el-button>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>

                  <div class="grid-span-full">


                    <el-button class="action-button warm full-width"
                      :disabled="loading.importParsedShot || !state.selectedStoryboardId || !parsedScriptReadableScenes.length"
                      @click="handleImportAllReadableShots">
                      {{ loading.importParsedShot ? "导入中..." : "全部导入为镜头卡草稿" }}
                    </el-button>
                  </div>

                </div>
              </div>

              <div v-else class="empty-state">当前解析结果还没有场景内容。</div>
            </div>
            <div v-else class="empty-state">当前 JSON 不是合法格式，无法切换到可读视图。</div>
          </template>
        </article>
      </section>
    </template>

    <template v-else-if="workspaceStep === 'assets'">
      <section class="studio-grid">
        <article v-loading="characterCreatePanelLoading" element-loading-text="角色列表处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">角色</p>
              <h2>角色创建</h2>
            </div>
          </div>

          <div class="form-stack compact-create-form">
            <div class="compact-form-grid compact-form-grid-2">
              <el-input v-model="forms.characterName" class="field" type="text" placeholder="输入角色名称" />
              <div class="action-tile">
                <el-button class="action-button warm" :disabled="loading.createCharacter" @click="handleCreateCharacter">
                  {{ loading.createCharacter ? "创建中..." : "新建角色" }}
                </el-button>
              </div>
              <el-input v-model="forms.characterBrief" class="field-textarea compact form-span-full" type="textarea"
                resize="vertical" placeholder="输入角色简介、身份、性格等描述" />
              <p class="inline-note form-span-full">
                支持两种入口：先用文字描述创建角色；如果是固定角色，也可以在创建后上传官图或参考图，再进行生成。
              </p>
            </div>
          </div>

          <div class="mini-list compact-card-grid compact-card-grid-3">
            <div v-for="item in state.characters" :key="item.id" class="mini-card selectable"
              :class="{ active: item.id === state.selectedCharacterId, editing: isEditingCharacter(item.id) }">
              <div class="item-body compact-card-body" @click="state.selectedCharacterId = item.id">
                <template v-if="isEditingCharacter(item.id)">
                  <div class="item-editor">
                    <el-input v-model="inlineEditing.characterName" class="field" type="text" placeholder="输入角色名称" />
                    <el-input v-model="inlineEditing.characterBrief" class="field-textarea compact" type="textarea"
                      :autosize="{ minRows: 5, maxRows: 15 }" resize="vertical" placeholder="输入角色简介、身份、性格等描述" />
                  </div>
                </template>
                <template v-else>
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.id }}</span>
                  <small>{{ formatStatus(item.status) }}</small>
                  <small>{{ item.brief || "暂无角色简介" }}</small>
                </template>
              </div>
              <div class="item-actions item-actions-block">
                <el-button v-if="isEditingCharacter(item.id)" class="action-button dark compact-button"
                  :disabled="loading.updateCharacter" @click.stop="handleUpdateCharacter(item)">
                  {{ loading.updateCharacter ? "保存中..." : "保存" }}
                </el-button>
                <el-button v-else class="action-button ghost compact-button" @click.stop="startCharacterEdit(item)">
                  编辑
                </el-button>
                <el-button v-if="isEditingCharacter(item.id)" class="action-button ghost compact-button"
                  @click.stop="cancelCharacterEdit">
                  取消
                </el-button>
                <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteCharacter"
                  @click.stop="handleDeleteCharacter(item)">
                  {{ loading.deleteCharacter ? "删除中..." : "删除" }}
                </el-button>
              </div>
            </div>
          </div>
        </article>

        <article v-loading="sceneCreatePanelLoading" element-loading-text="场景列表处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">场景</p>
              <h2>场景创建</h2>
            </div>
          </div>

          <div class="form-stack compact-create-form">
            <div class="compact-form-grid compact-form-grid-2">
              <el-input v-model="forms.sceneName" class="field" type="text" placeholder="输入场景名称" />
              <div class="action-tile">
                <el-button class="action-button warm" :disabled="loading.createScene" @click="handleCreateScene">
                  {{ loading.createScene ? "创建中..." : "新建场景" }}
                </el-button>
              </div>
              <el-input v-model="forms.sceneDescription" class="field-textarea compact form-span-full" type="textarea"
                resize="vertical" placeholder="输入场景环境、氛围、时代、空间信息" />
            </div>
          </div>

          <div class="mini-list compact-card-grid compact-card-grid-3">
            <div v-for="item in state.scenes" :key="item.id" class="mini-card selectable"
              :class="{ active: item.id === state.selectedSceneId, editing: isEditingScene(item.id) }">
              <div class="item-body compact-card-body" @click="state.selectedSceneId = item.id">
                <template v-if="isEditingScene(item.id)">
                  <div class="item-editor">
                    <el-input v-model="inlineEditing.sceneName" class="field" type="text" placeholder="输入场景名称" />
                    <el-input v-model="inlineEditing.sceneDescription" class="field-textarea compact" type="textarea"
                      resize="vertical" placeholder="输入场景环境、氛围、时代、空间信息" />
                  </div>
                </template>
                <template v-else>
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.id }}</span>
                  <small>{{ formatStatus(item.status) }}</small>
                  <small>{{ item.description || "暂无场景描述" }}</small>
                </template>
              </div>
              <div class="item-actions item-actions-block">
                <el-button v-if="isEditingScene(item.id)" class="action-button dark compact-button"
                  :disabled="loading.updateScene" @click.stop="handleUpdateScene(item)">
                  {{ loading.updateScene ? "保存中..." : "保存" }}
                </el-button>
                <el-button v-else class="action-button ghost compact-button" @click.stop="startSceneEdit(item)">
                  编辑
                </el-button>
                <el-button v-if="isEditingScene(item.id)" class="action-button ghost compact-button"
                  @click.stop="cancelSceneEdit">
                  取消
                </el-button>
                <el-button class="action-button ghost danger compact-button" :disabled="loading.deleteScene"
                  @click.stop="handleDeleteScene(item)">
                  {{ loading.deleteScene ? "删除中..." : "删除" }}
                </el-button>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section class="lab-grid">
        <article v-loading="characterLabPanelLoading" element-loading-text="角色素材处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">角色工坊</p>
              <h2>角色圣经</h2>
            </div>
            <div class="inline-actions panel-header-actions">
              <el-button class="action-button warm" :disabled="loading.characterAssets || !selectedCharacter"
                @click="handleGenerateCharacterAssets('reference_plus_text')">
                {{ loading.characterAssets ? "生成中..." : (hasUploadedCharacterSourceImages ? "参考图+文字生成" : "按文字生成角色圣经") }}
              </el-button>
              <el-button v-if="hasUploadedCharacterSourceImages" class="action-button dark"
                :disabled="loading.characterAssets || !selectedCharacter"
                @click="handleGenerateCharacterAssets('reference_subject_only')">
                {{ loading.characterAssets ? "生成中..." : "仅按参考图生成拼图" }}
              </el-button>
            </div>
          </div>

          <div v-if="selectedCharacter" class="lab-stack">
            <div class="focus-card">
              <span>当前角色</span>
              <strong>{{ selectedCharacter.name }}</strong>
              <small>{{ selectedCharacter.id }} · {{ formatStatus(selectedCharacter.status) }}</small>
            </div>

            <div class="upload-panel">
              <div>
                <strong>上传角色参考图</strong>
                <p class="upload-copy">
                  适用于固定角色。上传后，角色生成会优先参考你提供的图片，而不是只靠文字描述。
                </p>
                <p class="upload-copy">
                  你可以选择两种生成方式：`参考图+文字生成` 会结合当前角色描述；`仅按参考图生成拼图` 会把上传图作为唯一主体来源，只生成三视图和特征分解拼图。
                </p>
              </div>
              <input ref="characterSourceInput" class="hidden-file-input" type="file" accept="image/*" multiple
                @change="handleCharacterSourceFileChange" />
              <div class="upload-actions">
                <el-button class="action-button ghost" @click="characterSourceInput?.click()">
                  选择参考图
                </el-button>
                <span
                  class="upload-count">{{ characterSourceFiles.length ? `已选 ${characterSourceFiles.length} 张` : "未选择文件" }}</span>
              </div>
              <el-button class="action-button dark" :disabled="loading.characterUpload || !characterSourceFiles.length"
                @click="handleUploadCharacterSourceImages">
                {{ loading.characterUpload ? "上传中..." : "上传参考图" }}
              </el-button>
            </div>

            <div v-if="selectedCharacterSourceEntries.length" class="reference-grid">
              <div v-for="image in selectedCharacterSourceEntries" :key="image.key" class="reference-card">
                <div class="reference-header">
                  <strong>上传参考</strong>
                  <small>{{ image.label }}</small>
                </div>
                <el-button class="action-button ghost danger compact-button"
                  :disabled="loading.deleteCharacterSourceImage" @click="handleDeleteCharacterSourceImage(image.path)">
                  {{ loading.deleteCharacterSourceImage ? "删除中..." : "删除参考图" }}
                </el-button>
                <el-image class="preview-image" :src="assetUrl(image.path)"
                  :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover" preview-teleported />
              </div>
            </div>

            <div class="anchor-grid">
              <article v-for="([key, value]) in selectedCharacterAnchorEntries" :key="key" class="anchor-card">
                <span>{{ formatAnchorKey(key) }}</span>
                <strong>{{ value || "待生成" }}</strong>
              </article>
            </div>

            <div class="reference-grid">
              <div v-for="image in selectedCharacterImageEntries" :key="image.key"
                class="reference-card reference-card-large media-span-two">
                <div class="reference-header">
                  <strong>{{ image.label }}</strong>
                  <small>{{ image.path || "尚未生成" }}</small>
                </div>
                <el-image v-if="image.path" class="preview-image preview-image-large" :src="assetUrl(image.path)"
                  :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="contain"
                  preview-teleported />
                <div v-else class="reference-empty">待生成</div>
              </div>
            </div>

            <div v-if="state.selectedCharacterBible" class="meta-panel">
              <div class="meta-row">
                <span>角色概述</span>
                <strong>{{ state.selectedCharacterBible.summary || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>核心身份</span>
                <strong>{{ state.selectedCharacterBible.bible?.core_identity || "暂无" }}</strong>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">选择一个角色后，可上传角色参考图并生成单张角色圣经拼图。</div>
        </article>

        <article v-loading="sceneLabPanelLoading" element-loading-text="场景素材处理中..."
          :element-loading-svg="loadingSpinnerSvg" :element-loading-svg-view-box="loadingSpinnerViewBox"
          element-loading-background="rgba(7, 10, 14, 0.18)" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">场景工坊</p>
              <h2>场景包</h2>
            </div>
            <el-button class="action-button warm" :disabled="loading.sceneAssets || !selectedScene"
              @click="handleGenerateSceneAssets">
              {{ loading.sceneAssets ? "生成中..." : "生成场景参考拼图" }}
            </el-button>
          </div>

          <div v-if="selectedScene" class="lab-stack">
            <div class="focus-card">
              <span>当前场景</span>
              <strong>{{ selectedScene.name }}</strong>
              <small>{{ selectedScene.id }} · {{ formatStatus(selectedScene.status) }}</small>
            </div>

            <div class="reference-grid">
              <div v-for="image in selectedSceneImageEntries" :key="image.key" class="reference-card">
                <div class="reference-header">
                  <strong>{{ image.label }}</strong>
                  <small>{{ image.path || "尚未生成" }}</small>
                </div>
                <el-image v-if="image.path" class="preview-image" :src="assetUrl(image.path)"
                  :preview-src-list="singlePreviewList(image.path)" :initial-index="0" fit="cover" preview-teleported />
                <div v-else class="reference-empty">待生成</div>
              </div>
            </div>

            <div v-if="state.selectedScenePackage" class="meta-panel">
              <div class="meta-row">
                <span>场景概述</span>
                <strong>{{ state.selectedScenePackage.summary || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>光线</span>
                <strong>{{ state.selectedScenePackage.visual_profile?.lighting || "暂无" }}</strong>
              </div>
              <div class="meta-row">
                <span>色调</span>
                <strong>{{ state.selectedScenePackage.visual_profile?.palette || "暂无" }}</strong>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">选择一个场景后可查看场景包和单张场景参考拼图。</div>
        </article>
      </section>
    </template>
  </section>
</template>

<script>
import { useWorkspaceContext } from "./workspaceContext";

export default {
  name: "WorkspaceMainPanel",
  setup() {
    return useWorkspaceContext();
  }
};
</script>
