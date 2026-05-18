<template>
  <div class="director-panel">
    <div class="panel-header">
      <span>当前系列: {{ currentSeries || '未选择' }}</span>
      <div class="header-actions">
        <el-select v-model="currentEpisode" placeholder="选择集数" style="width: 120px; margin-right: 12px;">
          <el-option :label="'第1集'" :value="1" />
          <el-option :label="'第2集'" :value="2" />
          <el-option :label="'第3集'" :value="3" />
        </el-select>
        <el-button type="primary" :disabled="!currentSeries" @click="loadData">
          加载分镜
        </el-button>
        <el-button type="success" :disabled="!currentSeries || shots.length === 0" @click="handleSave">
          保存配置
        </el-button>
      </div>
    </div>

    <div v-if="!currentSeries" class="empty-tip">
      请先选择系列
    </div>

    <div v-else-if="loading" class="loading">
      <i class="el-icon-loading"></i> 加载中...
    </div>

    <div v-else-if="shots.length === 0" class="empty-tip">
      暂无分镜数据，请先在剧本编辑中生成剧本
    </div>

    <div v-else class="shot-list">
      <el-collapse v-model="activeShots">
        <el-collapse-item v-for="shot in shots" :key="shot.shot_id" :name="shot.shot_id">
          <template slot="title">
            <div class="shot-title">
              <span class="shot-id">镜头 {{ shot.shot_id }}</span>
              <span class="shot-desc">{{ shot.description }}</span>
            </div>
          </template>
          <div class="shot-config">
            <div class="config-section">
              <h4>基本信息</h4>
              <p><strong>位置:</strong> {{ shot.location || '未知' }}</p>
              <p><strong>时间:</strong> {{ shot.time || '未知' }}</p>
              <p><strong>角色:</strong> {{ shot.characters ? shot.characters.join(', ') : '无' }}</p>
              <p><strong>情绪:</strong> {{ shot.emotion || '未知' }}</p>
            </div>

            <div class="config-section">
              <h4>导演配置</h4>
              <el-form label-width="100px" size="small">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="画幅">
                      <el-select v-model="shot.config.aspect_ratio">
                        <el-option v-for="opt in options.aspect_ratio" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="风格">
                      <el-select v-model="shot.config.style">
                        <el-option v-for="opt in options.style" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="分辨率">
                      <el-select v-model="shot.config.resolution">
                        <el-option v-for="opt in options.resolution" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="景别">
                      <el-select v-model="shot.config.shot_size">
                        <el-option v-for="opt in options.shot_size" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="机位角度">
                      <el-select v-model="shot.config.angle">
                        <el-option v-for="opt in options.angle" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="运镜">
                      <el-select v-model="shot.config.movement">
                        <el-option v-for="opt in options.movement" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="光影">
                      <el-select v-model="shot.config.lighting">
                        <el-option v-for="opt in options.lighting" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="色彩">
                      <el-select v-model="shot.config.color_tone">
                        <el-option v-for="opt in options.color_tone" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="节奏">
                      <el-select v-model="shot.config.pace">
                        <el-option v-for="opt in options.pace" :key="opt" :label="opt" :value="opt" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="时长(秒)">
                      <el-input-number v-model="shot.config.duration" :min="2" :max="15" :step="0.5" />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'

export default {
  name: 'DirectorPanel',
  data() {
    return {
      shots: [],
      loading: false,
      saving: false,
      currentEpisode: 1,
      activeShots: [],
      options: {
        aspect_ratio: ["16:9", "9:16", "1:1", "21:9"],
        style: ["写实", "2D动画", "3D卡通", "赛博朋克", "水墨", "定格", "皮克斯", "日漫"],
        resolution: ["720p", "1080p", "2K", "4K"],
        shot_size: ["大远景", "全景", "中景", "近景", "特写", "大特写"],
        angle: ["平视", "俯视", "仰视", "荷兰角", "过肩", "POV"],
        movement: ["固定", "推", "拉", "摇", "移", "跟", "升降", "手持晃动"],
        lighting: ["自然光", "黄金时刻", "阴天", "霓虹灯", "顶光", "侧逆光", "剪影"],
        color_tone: ["暖色", "冷色", "高饱和", "低饱和", "黑白", "复古胶片"],
        pace: ["缓慢抒情", "正常叙事", "快速紧张", "MV跳跃"]
      }
    }
  },
  computed: {
    ...mapState(['currentSeries'])
  },
  methods: {
    async loadData() {
      if (!this.currentSeries) {
        this.$message.warning('请先选择系列')
        return
      }
      this.loading = true
      try {
        const [scriptRes, storyRes] = await Promise.all([
          axios.get(`http://localhost:8000/api/storyboard/script/${this.currentSeries}/${this.currentEpisode}`),
          axios.get(`http://localhost:8000/api/storyboard/${this.currentSeries}/${this.currentEpisode}`)
        ])

        const scriptShots = scriptRes.data.shots || []
        const savedShots = storyRes.data.shots || []

        const savedMap = {}
        savedShots.forEach(s => {
          savedMap[s.shot_id] = s.config
        })

        this.shots = scriptShots.map(shot => ({
          ...shot,
          config: savedMap[shot.shot_id] || {
            aspect_ratio: "16:9",
            style: "写实",
            resolution: "1080p",
            shot_size: "中景",
            angle: "平视",
            movement: "固定",
            lighting: "自然光",
            color_tone: "暖色",
            pace: "正常叙事",
            duration: 5.0
          }
        }))

        if (this.shots.length > 0) {
          this.activeShots = [this.shots[0].shot_id]
        }
      } catch (error) {
        this.$message.error('加载分镜数据失败')
      } finally {
        this.loading = false
      }
    },
    async handleSave() {
      if (!this.currentSeries || this.shots.length === 0) return

      this.saving = true
      try {
        const shotsData = this.shots.map(shot => ({
          shot_id: shot.shot_id,
          description: shot.description,
          characters: shot.characters,
          location: shot.location,
          config: shot.config
        }))

        const response = await axios.post(
          `http://localhost:8000/api/storyboard/${this.currentSeries}/${this.currentEpisode}`,
          shotsData
        )

        if (response.data.success) {
          this.$message.success(response.data.message)
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '保存失败'
        this.$message.error(msg)
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.director-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header span {
  color: #606266;
}

.header-actions {
  display: flex;
  align-items: center;
}

.empty-tip,
.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.shot-list {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.shot-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.shot-id {
  font-weight: bold;
  color: #409EFF;
}

.shot-desc {
  color: #606266;
  font-size: 13px;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shot-config {
  padding: 10px 20px;
}

.config-section {
  margin-bottom: 20px;
}

.config-section h4 {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
  color: #409EFF;
}

.config-section p {
  margin: 6px 0;
  color: #606266;
  font-size: 14px;
}
</style>