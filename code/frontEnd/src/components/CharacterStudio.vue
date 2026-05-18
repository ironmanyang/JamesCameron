<template>
  <div class="character-studio">
    <div class="studio-header">
      <span>当前系列: {{ currentSeries || '未选择' }}</span>
      <el-button type="primary" icon="el-icon-plus" :disabled="!currentSeries" @click="showAddDialog = true">
        添加角色
      </el-button>
    </div>

    <el-dialog title="添加角色" :visible.sync="showAddDialog" width="500px" @close="resetAddForm">
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="角色名称">
          <el-input v-model="addForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="简述">
          <el-input v-model="addForm.brief" type="textarea" :rows="3" placeholder="请输入角色简述（可选）" />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddCharacter" :loading="generating">生成角色</el-button>
      </span>
    </el-dialog>

    <div v-if="!currentSeries" class="empty-tip">
      请先选择系列
    </div>

    <div v-else-if="loading" class="loading">
      <i class="el-icon-loading"></i> 加载中...
    </div>

    <div v-else-if="characters.length === 0" class="empty-tip">
      暂无角色，点击"添加角色"创建第一个角色
    </div>

    <div v-else class="character-list">
      <el-row :gutter="20">
        <el-col :span="6" v-for="char in characters" :key="char.name">
          <el-card class="character-card" shadow="hover" @click.native="selectCharacter(char)">
            <div class="card-content">
              <div class="thumbnail" v-if="char.front_view">
                <img :src="getLocalFileUrl(char.front_view)" alt="front_view" />
              </div>
              <div class="thumbnail placeholder" v-else>
                <i class="el-icon-user-solid"></i>
              </div>
              <div class="char-name">{{ char.name }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog :title="selectedCharacter" :visible.sync="showDetailDialog" width="900px" top="5vh">
      <div v-if="characterDetail" class="detail-content">
        <el-tabs type="border-card">
          <el-tab-pane label="角色图片">
            <div class="image-grid">
              <div class="image-item" v-for="(path, key) in characterDetail.image_paths" :key="key">
                <p class="image-label">{{ imageLabels[key] || key }}</p>
                <div class="image-wrapper">
                  <img :src="getLocalFileUrl(path)" :alt="key" />
                </div>
                <el-button size="mini" type="warning" @click="handleRegenerate(key)" :loading="regenerating">
                  重新生成
                </el-button>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="角色圣经">
            <div class="bible-content">
              <h4>基本信息</h4>
              <p><strong>角色名:</strong> {{ characterDetail.character_name }}</p>
              <h4>六层描述</h4>
              <el-form label-width="150px" size="small">
                <el-form-item label="Layer1 生理">
                  <el-input v-model="characterDetail.bible.layer_1_biology" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="Layer2 面部">
                  <el-input v-model="characterDetail.bible.layer_2_face" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="Layer3 服装">
                  <el-input v-model="characterDetail.bible.layer_3_costume" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="Layer4 色调">
                  <el-input v-model="characterDetail.bible.layer_4_color_palette" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="Layer5 质感">
                  <el-input v-model="characterDetail.bible.layer_5_texture" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="Layer6 气质">
                  <el-input v-model="characterDetail.bible.layer_6_aura" type="textarea" :rows="2" />
                </el-form-item>
              </el-form>
              <el-button type="primary" @click="handleSaveBible" :loading="saving">保存修改</el-button>
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
  name: 'CharacterStudio',
  data() {
    return {
      characters: [],
      loading: false,
      showAddDialog: false,
      showDetailDialog: false,
      selectedCharacter: null,
      characterDetail: null,
      generating: false,
      regenerating: false,
      saving: false,
      addForm: {
        name: '',
        brief: ''
      },
      imageLabels: {
        front_view: '正面视图',
        side_view: '侧面视图',
        back_view: '背面视图',
        decomposition_sheet: '特征分解图'
      }
    }
  },
  computed: {
    ...mapState(['currentSeries'])
  },
  watch: {
    currentSeries() {
      this.loadCharacters()
    }
  },
  mounted() {
    if (this.currentSeries) {
      this.loadCharacters()
    }
  },
  methods: {
    getLocalFileUrl(filePath) {
      if (!filePath) return ''
      const path = filePath.replace(/\\/g, '/')
      return `http://localhost:8000/api/files?path=${encodeURIComponent(path)}`
    },
    async loadCharacters() {
      if (!this.currentSeries) return
      this.loading = true
      try {
        const response = await axios.get('http://localhost:8000/api/character/list', {
          params: { series_name: this.currentSeries }
        })
        this.characters = response.data.characters || []
      } catch (error) {
        this.$message.error('加载角色列表失败')
      } finally {
        this.loading = false
      }
    },
    async selectCharacter(char) {
      this.selectedCharacter = char.name
      this.showDetailDialog = true
      try {
        const response = await axios.get('http://localhost:8000/api/character/bible', {
          params: {
            series_name: this.currentSeries,
            character_name: char.name
          }
        })
        this.characterDetail = response.data.data
      } catch (error) {
        this.$message.error('加载角色详情失败')
      }
    },
    async handleAddCharacter() {
      if (!this.addForm.name.trim()) {
        this.$message.warning('请输入角色名称')
        return
      }
      this.generating = true
      try {
        const response = await axios.post('http://localhost:8000/api/character/generate-bible', {
          series_name: this.currentSeries,
          character_name: this.addForm.name.trim(),
          brief_description: this.addForm.brief.trim()
        })
        if (response.data.success) {
          this.$message.success(response.data.message)
          this.showAddDialog = false
          this.loadCharacters()
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '生成角色失败'
        this.$message.error(msg)
      } finally {
        this.generating = false
      }
    },
    async handleRegenerate(imageType) {
      this.regenerating = true
      try {
        const response = await axios.post('http://localhost:8000/api/character/regenerate-image', {
          series_name: this.currentSeries,
          character_name: this.selectedCharacter,
          image_type: imageType
        })
        if (response.data.success) {
          this.$message.success(response.data.message)
          this.characterDetail.image_paths[imageType] = response.data.image_path
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '重新生成图片失败'
        this.$message.error(msg)
      } finally {
        this.regenerating = false
      }
    },
    async handleSaveBible() {
      this.saving = true
      try {
        const response = await axios.put('http://localhost:8000/api/character/save-bible', this.characterDetail, {
          params: {
            series_name: this.currentSeries,
            character_name: this.selectedCharacter
          }
        })
        if (response.data.success) {
          this.$message.success(response.data.message)
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '保存失败'
        this.$message.error(msg)
      } finally {
        this.saving = false
      }
    },
    resetAddForm() {
      this.addForm = { name: '', brief: '' }
    }
  }
}
</script>

<style scoped>
.character-studio {
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

.empty-tip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.character-list {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.character-card {
  cursor: pointer;
  margin-bottom: 20px;
}

.card-content {
  text-align: center;
}

.thumbnail {
  width: 100%;
  height: 180px;
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

.char-name {
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
  height: 300px;
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

.bible-content h4 {
  margin: 16px 0 8px;
  color: #409EFF;
}

.bible-content {
  padding: 10px;
}
</style>