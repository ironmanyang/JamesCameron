<template>
  <div class="script-editor">
    <div class="editor-header">
      <span>当前系列: {{ currentSeries || '未选择' }}</span>
      <el-button
        type="primary"
        :loading="analyzing"
        :disabled="!currentSeries || !rawScript.trim()"
        @click="handleAnalyze"
      >
        AI 拆解
      </el-button>
    </div>
    <div class="editor-body">
      <div class="input-panel">
        <h4>原始剧本</h4>
        <el-input
          type="textarea"
          v-model="rawScript"
          :rows="20"
          placeholder="请输入原始剧本内容..."
        />
      </div>
      <div class="output-panel">
        <h4>拆解结果</h4>
        <div v-if="analyzedScript" class="json-view">
          <pre>{{ JSON.stringify(analyzedScript, null, 2) }}</pre>
        </div>
        <div v-else class="empty-tip">
          点击"AI拆解"按钮生成结构化剧本
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'

export default {
  name: 'ScriptEditor',
  data() {
    return {
      rawScript: '',
      analyzedScript: null,
      analyzing: false
    }
  },
  computed: {
    ...mapState(['currentSeries'])
  },
  methods: {
    async handleAnalyze() {
      if (!this.currentSeries) {
        this.$message.warning('请先选择系列')
        return
      }
      this.analyzing = true
      this.analyzedScript = null
      try {
        const response = await axios.post('http://localhost:8000/api/script/analyze', {
          series_name: this.currentSeries,
          raw_text: this.rawScript
        })
        if (response.data.success) {
          this.analyzedScript = response.data.data
          this.$message.success(response.data.message)
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '剧本拆解失败'
        this.$message.error(msg)
      } finally {
        this.analyzing = false
      }
    }
  }
}
</script>

<style scoped>
.script-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.editor-header span {
  color: #606266;
}

.editor-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.input-panel,
.output-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

.input-panel {
  border-right: 1px solid #e4e7ed;
}

h4 {
  margin-bottom: 12px;
  color: #303133;
}

.json-view {
  flex: 1;
  overflow: auto;
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
}

.json-view pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  color: #606266;
}

.empty-tip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
}
</style>