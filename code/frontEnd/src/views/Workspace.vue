<template>
  <div class="workspace">
    <div class="sidebar">
      <h3>系列管理</h3>
      <SeriesSelector />
    </div>
    <div class="content">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="连接测试" name="test">
          <div class="test-panel">
            <h2>连接测试</h2>
            <p v-if="currentSeries">当前系列: {{ currentSeries }}</p>
            <el-button type="primary" @click="testConnection" :loading="loading">
              连接测试
            </el-button>
            <p v-if="result">结果: {{ result }}</p>
          </div>
        </el-tab-pane>
        <el-tab-pane label="剧本编辑" name="script">
          <ScriptEditor />
        </el-tab-pane>
        <el-tab-pane label="角色工程" name="character">
          <CharacterStudio />
        </el-tab-pane>
        <el-tab-pane label="场景工程" name="scene">
          <SceneStudio />
        </el-tab-pane>
        <el-tab-pane label="导演配置" name="director">
          <DirectorPanel />
        </el-tab-pane>
        <el-tab-pane label="视频生成" name="video">
          <VideoQueue />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'
import SeriesSelector from '../components/SeriesSelector.vue'
import ScriptEditor from '../components/ScriptEditor.vue'
import CharacterStudio from '../components/CharacterStudio.vue'
import SceneStudio from '../components/SceneStudio.vue'
import DirectorPanel from '../components/DirectorPanel.vue'
import VideoQueue from '../components/VideoQueue.vue'

export default {
  name: 'Workspace',
  components: {
    SeriesSelector,
    ScriptEditor,
    CharacterStudio,
    SceneStudio,
    DirectorPanel,
    VideoQueue
  },
  data() {
    return {
      activeTab: 'test',
      loading: false,
      result: ''
    }
  },
  computed: {
    ...mapState(['currentSeries'])
  },
  methods: {
    async testConnection() {
      this.loading = true
      this.result = ''
      try {
        const response = await axios.get('http://localhost:8000/api/health')
        this.result = JSON.stringify(response.data)
        this.$message.success('连接成功')
      } catch (error) {
        this.result = '连接失败: ' + (error.message || '未知错误')
        this.$message.error('连接失败')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.workspace {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 300px;
  padding: 20px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.sidebar h3 {
  margin-bottom: 20px;
  color: #303133;
}

.content {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.test-panel {
  padding: 20px;
}

.test-panel h2 {
  margin-bottom: 20px;
  color: #303133;
}

.test-panel p {
  margin: 10px 0;
  font-size: 16px;
  color: #666;
}
</style>