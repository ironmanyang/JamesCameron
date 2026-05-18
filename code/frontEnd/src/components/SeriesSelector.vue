<template>
  <div class="series-selector">
    <el-select
      v-model="selectedSeries"
      placeholder="请选择系列"
      filterable
      allow-create
      default-first-option
      @change="onSeriesChange"
      style="width: 240px;"
    >
      <el-option
        v-for="item in seriesList"
        :key="item"
        :label="item"
        :value="item"
      >
      </el-option>
    </el-select>
    <el-button type="primary" icon="el-icon-plus" @click="showDialog = true">
      新建系列
    </el-button>

    <el-dialog
      title="新建系列"
      :visible.sync="showDialog"
      width="400px"
      @close="resetDialog"
    >
      <el-form @submit.native.prevent>
        <el-form-item label="系列名称">
          <el-input
            v-model="newSeriesName"
            placeholder="请输入系列名称"
            @keyup.enter.native="handleCreate"
          />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState, mapActions } from 'vuex'

export default {
  name: 'SeriesSelector',
  data() {
    return {
      seriesList: [],
      selectedSeries: null,
      showDialog: false,
      newSeriesName: '',
      creating: false
    }
  },
  computed: {
    ...mapState(['currentSeries'])
  },
  watch: {
    currentSeries(val) {
      this.selectedSeries = val
    }
  },
  mounted() {
    this.loadSeriesList()
  },
  methods: {
    ...mapActions(['selectSeries', 'addSeries']),
    async loadSeriesList() {
      try {
        const response = await axios.get('http://localhost:8000/api/series')
        this.seriesList = response.data.series_list || []
      } catch (error) {
        this.$message.error('加载系列列表失败')
      }
    },
    onSeriesChange(value) {
      this.selectSeries(value)
    },
    async handleCreate() {
      if (!this.newSeriesName.trim()) {
        this.$message.warning('请输入系列名称')
        return
      }
      this.creating = true
      try {
        const response = await axios.post('http://localhost:8000/api/series', {
          name: this.newSeriesName.trim()
        })
        if (response.data.success) {
          this.$message.success(response.data.message)
          this.addSeries(this.newSeriesName.trim())
          this.selectedSeries = this.newSeriesName.trim()
          this.loadSeriesList()
          this.showDialog = false
        } else {
          this.$message.warning(response.data.message)
        }
      } catch (error) {
        const msg = error.response?.data?.detail || '创建系列失败'
        this.$message.error(msg)
      } finally {
        this.creating = false
      }
    },
    resetDialog() {
      this.newSeriesName = ''
      this.creating = false
    }
  }
}
</script>

<style scoped>
.series-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>