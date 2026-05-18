<template>
  <div class="scene-studio">
    <div class="studio-header">
      <span>当前系列: {{ currentSeries || '未选择' }}</span>
      <el-button type="primary" icon="el-icon-plus" :disabled="!currentSeries" @click="showAddDialog = true">
        添加场景
      </el-button>
    </div>

    <el-dialog title="添加场景" :visible.sync="showAddDialog" width="500px" @close="resetAddForm">
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="场景名称">
          <el-input v-model="addForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="场景描述">
          <el-input v-model="addForm.description" type="textarea" :rows="3" placeholder="请输入场景描述（可选）" />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddScene" :loading="generating">生成场景</el-button>
      </span>
    </el-dialog>

    <div v-if="!currentSeries" class="empty-tip">
      请先选择系列
    </div>

    <div v-else-if="loading" class="loading">
      <i class="el-icon-loading"></i> 加载中...
    </div>

    <div v-else-if="scenes.length === 0" class="empty-tip">
      暂无场景，点击"添加场景"创建第一个场景
    </div>

    <div v-else class="scene-list">
      <el-row :gutter="20">
        <el-col :span="8" v-for="scene in scenes" :key="scene.name">
          <el-card class="scene-card" shadow="hover" @click.native="selectScene(scene)">
            <div class="card-content">
              <div class="thumbnail" v-if="scene.thumbnail">
                <img :src="getLocalFileUrl(scene.thumbnail)" alt="thumbnail" />
              </div>
              <div class="thumbnail placeholder" v-else>
                <i class="el-icon-picture-outline"></i>
              </div>
              <div class="scene-name">{{ scene.name }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog :title="selectedScene" :visible.sync="showDetailDialog" width="1000px" top="5vh">
      <div v-if="sceneDetail" class="detail-content">
        <el-tabs type="border-card">
          <el-tab-pane label="场景图片">
            <div class="image-grid">
              <div class="image-item" v-for="(data, key) in sceneDetail.images" :key="key">
                <p class="image-label">{{ viewLabels[key] || key }}</p>
                <div class="image-wrapper">
                  <img :src="getLocalFileUrl(data.path)" :alt="key" />
                </div>
                <el-button size="mini" type="warning" @click="handleRegenerate(key)" :loading="regenerating">
                  重新生成
                </el-button>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="场景信息">
            <div class="info-content">
              <h4>基本信息</h4>
              <p><strong>场景名:</strong> {{ sceneDetail.scene_name }}</p>
              <p><strong>描述:</strong> {{ sceneDetail.description || '无' }}</p>
              <h4>Prompt 信息</h4>
              <div v-for="(data, key) in sceneDetail.images" :key="key" class="prompt-item">
                <p><strong>{{ viewLabels[key] }}:</strong></p>
                <el-input type="textarea" :value="data.prompt" :rows="2" readonly />
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <div v-else class="loading">
        <i class="el-icon-loading"></i> 加载中...
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'

export default {
  name: 'SceneStudio',
  data() {
    return {
      scenes: [],
      loading: false,
      showAddDialog: false,
      showDetailDialog: false,
      selectedScene: null,
      sceneDetail: null,
      generating: false,
      regenerating: false,
      addForm: {
        name: '',
        description: ''
      },
      viewLabels: {
        establishing: '定场镜头',
        closeup: '特写镜头',
        bird: '俯视镜头',
        detail: '额外角度'
      }
    }
  },
  computed: {
    ...mapState(['currentSeries'])
  },
  watch: {
    currentSeries() {
      this.loadScenes()
    }
  },
  mounted() {
    if (this.currentSeries) {
      this.loadScenes()
    }
  },
  methods: {
    getLocalFileUrl(filePath) {
      if (!filePath) return ''
      const path = filePath.replace(/\\/g, '/')
      return `http://localhost:8000/api/files?path=${encodeURIComponent(path)}`
    },
    async loadScenes() {
      if (!this.currentSeries) return
      this.loading = true
      try {
        const response = await axios.get('http://localhost:8000/api/scene/list', {
          params: { series_name: this.currentSeries }
        })
        this.scenes = response.data.scenes || []
      } catch (error) {
        this.$message.error('加载场景列表失败')
      } finally {
        this.loading = false
      }
    },
    async selectScene(scene) {
      this.selectedScene = scene.name
      this.showDetailDialog = true
      try {
        const response = await axios.get('http://localhost:8000/api/scene/meta', {
          params: {
            series_name: this.currentSeries,
            scene_name: scene.name
          }
        })
        this.sceneDetail = response.data.data
      } catch (error) {
        this.$message.error('加载场景详情失败')
      }
    },
    async handleAddScene() {
      if (!this.addForm.name.trim()) {
        this.$message.warning('请输入场景名称')
        return
      }
      this.generating = true
      try {
        const response = await axios.post('http://localhost:8000/api/scene/generate', {
          series_name: this.currentSeries,
          scene_name: this.addForm.name.trim(),
          description: this.addForm.description.trim()
        })
        if (response.data.success) {
          this.$message.success(response.data.message)
          this.showAddDialog = false
          this.loadScenes()
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '生成场景失败'
        this.$message.error(msg)
      } finally {
        this.generating = false
      }
    },
    async handleRegenerate(viewType) {
      this.regenerating = true
      try {
        const response = await axios.post('http://localhost:8000/api/scene/regenerate-view', {
          series_name: this.currentSeries,
          scene_name: this.selectedScene,
          view_type: viewType
        })
        if (response.data.success) {
          this.$message.success(response.data.message)
          this.sceneDetail.images[viewType].path = response.data.image_path
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '重新生成图片失败'
        this.$message.error(msg)
      } finally {
        this.regenerating = false
      }
    },
    resetAddForm() {
      this.addForm = { name: '', description: '' }
    }
  }
}
</script>

<style scoped>
.scene-studio {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.studio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.studio-header span {
  color: #606266;
}

.empty-tip,
.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.scene-list {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.scene-card {
  cursor: pointer;
  margin-bottom: 20px;
}

.card-content {
  text-align: center;
}

.thumbnail {
  width: 100%;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
}

.thumbnail img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.thumbnail.placeholder {
  color: #c0c4cc;
  font-size: 48px;
}

.scene-name {
  margin-top: 12px;
  font-size: 14px;
  color: #303133;
}

.detail-content {
  max-height: 70vh;
  overflow: auto;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.image-item {
  text-align: center;
}

.image-label {
  margin-bottom: 8px;
  font-weight: bold;
  color: #606266;
}

.image-wrapper {
  width: 100%;
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 10px;
}

.image-wrapper img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.info-content h4 {
  margin: 16px 0 8px;
  color: #409EFF;
}

.info-content p {
  margin: 8px 0;
  color: #606266;
}

.prompt-item {
  margin: 12px 0;
}

.prompt-item p {
  margin-bottom: 4px;
}
</style>