<template>
  <div class="ai-analysis-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <div class="logo">
          <span class="logo-icon">💊</span>
          <span class="logo-text">带量采购数据分析</span>
        </div>
        <el-tag size="small" type="success" effect="dark">AI 助手</el-tag>
      </div>
      <div class="header-right">
        <el-tooltip content="数据已加载" placement="bottom">
          <div class="status-indicator" :class="{ online: !loading }">
            <span class="status-dot"></span>
            <span class="status-text">{{ loading ? '加载中' : '在线' }}</span>
          </div>
        </el-tooltip>
        <el-button
          type="primary"
          size="small"
          :icon="Refresh"
          :loading="loading"
          @click="reloadData"
        >
          刷新数据
        </el-button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="page-content">
      <ChatContainer ref="chatContainerRef" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import ChatContainer from '@/components/chat/ChatContainer.vue'

const chatContainerRef = ref<InstanceType<typeof ChatContainer>>()
const loading = ref(false)

// 重新加载数据
const reloadData = async () => {
  loading.value = true
  try {
    await chatContainerRef.value?.loadStats()
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 1000)
})
</script>

<style scoped>
.ai-analysis-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

/* 页面头部 */
.page-header {
  height: 60px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 状态指示器 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #9ca3af;
}

.status-indicator.online {
  color: #52c41a;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
}

.status-indicator.online .status-dot {
  background: #52c41a;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-text {
  font-size: 13px;
}

/* 主内容区 */
.page-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  min-height: 0;
}

.page-content > * {
  width: 100%;
  height: 100%;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    padding: 0 16px;
  }

  .logo-text {
    font-size: 16px;
  }

  .header-right .el-button {
    display: none;
  }
}
</style>
