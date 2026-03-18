<template>
  <aside class="chat-sidebar" :class="{ collapsed: collapsed }">
    <!-- 折叠按钮 -->
    <button class="collapse-btn" @click="$emit('toggle')">
      <el-icon :size="16">
        <ArrowLeft v-if="!collapsed" />
        <ArrowRight v-else />
      </el-icon>
    </button>

    <!-- 展开内容 -->
    <template v-if="!collapsed">
      <!-- 1. 总体情况 - 使用 json1 -->
      <div class="sidebar-section">
        <h3 class="section-title">
          <el-icon><DataLine /></el-icon>
          总体情况
        </h3>
        <div v-if="loading" class="loading-text">加载中...</div>
        <div v-else-if="error" class="error-text">{{ error }}</div>
        <div v-else-if="overallData" class="overall-card">
          <div class="overall-header">
            <span class="batch-name">{{ overallData.批次名称 }}</span>
            <el-tag size="small" :type="getProgressType(overallData.执行进度)">
              {{ overallData.执行进度.toFixed(1) }}%
            </el-tag>
          </div>
          <div class="overall-stats">
            <div class="stat-row">
              <span class="stat-label">执行周期</span>
              <span class="stat-value">{{ overallData.批次执行周期 }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">签约总量</span>
              <span class="stat-value highlight">{{ formatNumber(overallData.批次签约总量) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">已入库量</span>
              <span class="stat-value highlight">{{ formatNumber(overallData.已入库总量) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">执行进度</span>
              <el-progress :percentage="Number(overallData.执行进度.toFixed(1))" :stroke-width="6" :show-text="false" />
            </div>
            <div class="stat-row">
              <span class="stat-label">序时进度</span>
              <span class="stat-value">{{ overallData.序时进度.toFixed(1) }}%</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-data">暂无数据</div>
      </div>

      <!-- 2. 各地市执行进度 - 使用 json3 -->
      <div class="sidebar-section data-section">
        <h3 class="section-title">
          <el-icon><Location /></el-icon>
          各地市执行进度
        </h3>
        <div v-if="cityData.length > 0" class="data-list">
          <div
            v-for="(item, index) in cityData"
            :key="index"
            class="data-item"
          >
            <div class="item-header">
              <span class="item-name" :title="item.地市名称">{{ item.地市名称 }}</span>
              <el-tag size="small" :type="getProgressType(item.地市执行进度)">
                {{ item.地市执行进度.toFixed(1) }}%
              </el-tag>
            </div>
            <div class="item-stats">
              <div class="item-stat">
                <span class="stat-label-small">签约总量</span>
                <span class="stat-value-small">{{ formatNumber(item.地市签约总量) }}</span>
              </div>
              <div class="item-stat">
                <span class="stat-label-small">入库总量</span>
                <span class="stat-value-small">{{ formatNumber(item.地市采购入库总量) }}</span>
              </div>
            </div>
            <div class="item-progress">
              <el-progress :percentage="Number(item.地市执行进度.toFixed(1))" :stroke-width="4" :show-text="false" />
            </div>
          </div>
        </div>
        <div v-else class="empty-data">暂无数据</div>
      </div>

      <!-- 3. 快捷操作 -->
      <div class="sidebar-section actions-section">
        <h3 class="section-title">
          <el-icon><Operation /></el-icon>
          快捷操作
        </h3>
        <div class="quick-actions">
          <el-button
            type="primary"
            size="small"
            @click="$emit('clear-chat')"
            :disabled="!hasMessages"
          >
            <el-icon><Delete /></el-icon>
            清空对话
          </el-button>
          <el-button
            type="info"
            size="small"
            @click="loadData"
            :loading="loading"
          >
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
      </div>
    </template>

    <!-- 折叠状态：只显示图标 -->
    <template v-else>
      <div class="collapsed-icons">
        <el-tooltip content="总体情况" placement="right">
          <div class="collapsed-icon" @click="$emit('toggle')">
            <el-icon><DataLine /></el-icon>
          </div>
        </el-tooltip>
        <el-tooltip content="清空对话" placement="right">
          <div class="collapsed-icon" @click="$emit('clear-chat')">
            <el-icon><Delete /></el-icon>
          </div>
        </el-tooltip>
      </div>
    </template>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  DataLine,
  Location,
  Operation,
  ArrowLeft,
  ArrowRight,
  Delete,
  Refresh
} from '@element-plus/icons-vue'

interface Props {
  collapsed: boolean
  hasMessages: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  toggle: []
  'clear-chat': []
}>()

// 数据状态
const loading = ref(false)
const error = ref('')
const overallData = ref<any>(null)
const cityData = ref<any[]>([])

// 加载 JSON 数据
const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    // 从 demo.json 加载数据
    const response = await fetch('/demo.json')
    if (!response.ok) {
      throw new Error('无法加载数据文件')
    }
    const data = await response.json()

    // 解析 json1_总体执行进度
    if (data.json1_总体执行进度) {
      overallData.value = data.json1_总体执行进度
    }

    // 解析 json3_各地市执行进度
    if (data.json3_各地市执行进度 && Array.isArray(data.json3_各地市执行进度)) {
      cityData.value = data.json3_各地市执行进度
    }
  } catch (err: any) {
    error.value = err.message || '加载数据失败'
    console.error('加载 demo.json 失败:', err)
  } finally {
    loading.value = false
  }
}

// 格式化数字
const formatNumber = (num: number): string => {
  if (!num && num !== 0) return '-'
  return num.toLocaleString('zh-CN')
}

// 根据进度获取标签类型
const getProgressType = (progress: number): string => {
  if (progress >= 80) return 'success'
  if (progress >= 50) return 'warning'
  return 'danger'
}

// 初始化加载数据
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.chat-sidebar {
  width: 340px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.chat-sidebar.collapsed {
  width: 60px;
}

.collapse-btn {
  position: absolute;
  right: -12px;
  top: 20px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
  color: #6b7280;
}

.collapse-btn:hover {
  background: #f3f4f6;
  color: #1677ff;
  border-color: #1677ff;
}

.sidebar-section {
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.sidebar-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title .el-icon {
  color: #1677ff;
}

/* 总体情况卡片 */
.overall-card {
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e0efff;
}

.overall-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #d1e3ff;
}

.batch-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.overall-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.stat-row .stat-label {
  color: #6b7280;
  width: 70px;
  flex-shrink: 0;
}

.stat-row .stat-value {
  color: #374151;
  flex: 1;
}

.stat-row .stat-value.highlight {
  color: #1677ff;
  font-weight: 600;
  font-family: monospace;
  font-size: 14px;
}

.stat-row .el-progress {
  flex: 1;
}

/* 各地市执行进度 */
.data-section {
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.data-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  max-height: calc(100vh - 420px);
}

.data-item {
  background: #f9fafb;
  border-radius: 10px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.data-item:hover {
  background: #f0f7ff;
  border-color: #bfdbfe;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60%;
}

.item-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.item-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label-small {
  font-size: 11px;
  color: #9ca3af;
}

.stat-value-small {
  font-size: 12px;
  color: #1677ff;
  font-weight: 500;
  font-family: monospace;
}

.item-progress .el-progress {
  width: 100%;
}

.empty-data {
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
  padding: 20px;
}

.loading-text,
.error-text {
  text-align: center;
  font-size: 12px;
  padding: 16px;
  color: #6b7280;
}

.error-text {
  color: #ef4444;
}

/* 快捷操作 */
.actions-section {
  flex-shrink: 0;
  padding: 12px 16px;
  background: #fafafa;
}

.quick-actions {
  display: flex;
  flex-direction: row;
  gap: 10px;
}

.quick-actions .el-button {
  flex: 1;
  justify-content: center;
}

/* 折叠状态 */
.collapsed-icons {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60px;
  gap: 16px;
}

.collapsed-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
}

.collapsed-icon:hover {
  background: #f3f4f6;
  color: #1677ff;
}
</style>
