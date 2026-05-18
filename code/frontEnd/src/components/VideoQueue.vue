<template>
  <div class="video-queue">
    <div class="queue-header">
      <span>当前系列: {{ currentSeries || '未选择' }}</span>
      <div class="header-actions">
        <el-select v-model="currentEpisode" placeholder="选择集数" style="width: 120px; margin-right: 12px;">
          <el-option v-for="ep in 12" :key="ep" :label="`第${ep}集`" :value="ep" />
        </el-select>
        <el-button type="primary" :disabled="!currentSeries" @click="loadScriptShots">
          加载分镜
        </el-button>
        <el-button type="success" :disabled="!canGenerate" @click="handleGenerate">
          提交生成
        </el-button>
        <el-button type="danger" :disabled="!currentSeries || tasks.length === 0" @click="handleClear">
          清空队列
        </el-button>
      </div>
    </div>

    <div v-if="!currentSeries" class="empty-tip">
      请先选择系列
    </div>

    <div v-else class="queue-body">
      <div class="shot-selector" v-if="availableShots.length > 0">
        <h4>选择要生成的镜头</h4>
        <el-checkbox-group v-model="selectedShotIds">
          <el-checkbox v-for="shot in availableShots" :key="shot.shot_id" :label="shot.shot_id">
            {{ shot.shot_id }} - {{ shot.description.substring(0, 30) }}...
          </el-checkbox>
        </el-checkbox-group>
        <div class="selector-actions">
          <el-button size="mini" @click="selectAll">全选</el-button>
          <el-button size="mini" @click="selectNone">取消全选</el-button>
        </div>
      </div>

      <div class="tasks-section">
        <h4>生成任务队列</h4>
        <el-table :data="tasks" style="width: 100%" v-if="tasks.length > 0">
          <el-table-column prop="shot_id" label="镜头" width="80" />
          <el-table-column prop="status" label="状态" width="100">
            <template slot-scope="scope">
              <el-tag :type="getStatusType(scope.row.status)" size="small">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="prompt" label="Prompt" show-overflow-tooltip />
          <el-table-column label="操作" width="120">
            <template slot-scope="scope">
              <a
                v-if="scope.row.status === 'completed' && scope.row.output_path"
                :href="getFileUrl(scope.row.output_path)"
                download
                class="download-link"
              >
                下载
              </a>
              <span v-else-if="scope.row.status === 'failed'" class="error-text">
                {{ scope.row.error || '失败' }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-tasks">
          暂无任务，点击"加载分镜"后选择镜头提交生成
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'

export default {
  name: 'VideoQueue',
  data() {
    return {
      availableShots: [],
      selectedShotIds: [],
      tasks: [],
      currentEpisode: 1,
      pollingTimer: null
    }
  },
  computed: {
    ...mapState(['currentSeries']),
    canGenerate() {
      return this.currentSeries && this.selectedShotIds.length > 0
    }
  },
  watch: {
    currentSeries() {
      this.stopPolling()
      this.availableShots = []
      this.selectedShotIds = []
      this.tasks = []
    }
  },
  beforeDestroy() {
    this.stopPolling()
  },
  methods: {
    async loadScriptShots() {
      if (!this.currentSeries) return
      try {
        const response = await axios.get(
          `http://localhost:8000/api/storyboard/script/${this.currentSeries}/${this.currentEpisode}`
        )
        this.availableShots = response.data.shots || []
        this.selectedShotIds = this.availableShots.map(s => s.shot_id)
        await this.loadTasks()
      } catch (error) {
        this.$message.error('加载分镜失败')
      }
    },
    async loadTasks() {
      if (!this.currentSeries) return
      try {
        const response = await axios.get(
          `http://localhost:8000/api/video/tasks/${this.currentSeries}`
        )
        this.tasks = response.data.tasks || []
      } catch (error) {
        console.error('Failed to load tasks:', error)
      }
    },
    async handleGenerate() {
      if (!this.canGenerate) return
      try {
        const response = await axios.post('http://localhost:8000/api/video/generate', {
          series_name: this.currentSeries,
          episode: this.currentEpisode,
          shot_ids: this.selectedShotIds
        })
        if (response.data.success) {
          this.$message.success(response.data.message)
          this.selectedShotIds = []
          await this.loadTasks()
          this.startPolling()
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '提交失败'
        this.$message.error(msg)
      }
    },
    async handleClear() {
      try {
        await axios.delete(`http://localhost:8000/api/video/tasks/${this.currentSeries}`)
        this.tasks = []
        this.$message.success('任务队列已清空')
      } catch (error) {
        this.$message.error('清空失败')
      }
    },
    startPolling() {
      this.stopPolling()
      this.pollingTimer = setInterval(() => {
        this.loadTasks()
      }, 3000)
    },
    stopPolling() {
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
    },
    selectAll() {
      this.selectedShotIds = this.availableShots.map(s => s.shot_id)
    },
    selectNone() {
      this.selectedShotIds = []
    },
    getStatusType(status) {
      const types = {
        'pending': 'info',
        'processing': 'warning',
        'completed': 'success',
        'failed': 'danger'
      }
      return types[status] || 'info'
    },
    getStatusText(status) {
      const texts = {
        'pending': '等待中',
        'processing': '生成中',
        'completed': '已完成',
        'failed': '失败'
      }
      return texts[status] || status
    },
    getFileUrl(filePath) {
      if (!filePath) return '#'
      const path = filePath.replace(/\\/g, '/')
      return `file:///${path}`
    }
  }
}
</script>

<style scoped>
.video-queue {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.queue-header span {
  color: #606266;
}

.header-actions {
  display: flex;
  align-items: center;
}

.empty-tip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.queue-body {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.shot-selector {
  margin-bottom: 30px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.shot-selector h4 {
  margin-bottom: 12px;
  color: #303133;
}

.selector-actions {
  margin-top: 12px;
}

.tasks-section h4 {
  margin-bottom: 12px;
  color: #303133;
}

.empty-tasks {
  padding: 40px;
  text-align: center;
  color: #909399;
  background: #fafafa;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
}

.download-link {
  color: #409EFF;
  text-decoration: none;
}

.download-link:hover {
  text-decoration: underline;
}

.error-text {
  color: #F56C6C;
  font-size: 12px;
}
</style>