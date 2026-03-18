<template>
  <div
    class="chat-message"
    :class="[message.role, message.type]"
    :data-message-id="message.id"
  >
    <!-- AI头像 -->
    <div v-if="message.role === 'assistant'" class="avatar ai-avatar">
      <div class="avatar-inner">🤖</div>
    </div>

    <!-- 消息内容区 -->
    <div class="message-content-wrapper">
      <!-- 发送者名称 -->
      <div class="message-header">
        <span class="sender-name">{{ senderName }}</span>
        <span class="message-time">{{ formatTime }}</span>
      </div>

      <!-- 消息气泡 -->
      <div class="message-bubble">
        <!-- 文本消息 -->
        <template v-if="message.type === 'text'">
          <div class="text-content" v-html="renderedContent"></div>
        </template>

        <!-- 思考中状态 -->
        <template v-else-if="message.type === 'thinking'">
          <div class="thinking-content">
            <div class="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="thinking-text">{{ message.content }}</span>
          </div>
          <div class="thinking-steps">
            <div
              v-for="(step, index) in thinkingSteps"
              :key="index"
              class="thinking-step"
              :class="{ active: currentStep >= index }"
            >
              <el-icon v-if="currentStep > index"><Check /></el-icon>
              <el-icon v-else-if="currentStep === index" class="is-loading"><Loading /></el-icon>
              <span v-else class="step-dot"></span>
              <span class="step-text">{{ step }}</span>
            </div>
          </div>
        </template>

        <!-- 数据卡片消息 -->
        <template v-else-if="message.type === 'data'">
          <div class="data-cards">
            <div
              v-for="(card, index) in message.metadata?.data"
              :key="index"
              class="data-card-item"
            >
              <div class="card-label">{{ card.label }}</div>
              <div class="card-value">{{ card.value }}</div>
              <div v-if="card.change" class="card-change" :class="card.changeType">
                {{ card.change }}
              </div>
            </div>
          </div>
        </template>

        <!-- 图表消息 -->
        <template v-else-if="message.type === 'chart'">
          <div class="chart-container">
            <div ref="chartRef" class="chart-placeholder">
              <el-icon><PieChart /></el-icon>
              <span>图表展示区域</span>
            </div>
          </div>
        </template>

        <!-- 表格消息 -->
        <template v-else-if="message.type === 'table'">
          <div class="table-container">
            <el-table :data="message.metadata?.tableData" size="small" max-height="300">
              <el-table-column
                v-for="col in message.metadata?.columns"
                :key="col.prop"
                :prop="col.prop"
                :label="col.label"
                :width="col.width"
              />
            </el-table>
          </div>
        </template>
      </div>

      <!-- 消息操作 -->
      <div v-if="showActions" class="message-actions">
        <button class="action-btn" @click="copyContent" title="复制">
          <el-icon><DocumentCopy /></el-icon>
        </button>
        <button
          v-if="message.role === 'assistant' && message.type === 'text'"
          class="action-btn"
          @click="$emit('regenerate')"
          title="重新生成"
        >
          <el-icon><Refresh /></el-icon>
        </button>
        <button
          v-if="message.role === 'assistant'"
          class="action-btn"
          @click="toggleFeedback('like')"
          :class="{ active: feedback === 'like' }"
          title="有用"
        >
          <el-icon><Top /></el-icon>
        </button>
        <button
          v-if="message.role === 'assistant'"
          class="action-btn"
          @click="toggleFeedback('dislike')"
          :class="{ active: feedback === 'dislike' }"
          title="无用"
        >
          <el-icon><Bottom /></el-icon>
        </button>
      </div>
    </div>

    <!-- 用户头像 -->
    <div v-if="message.role === 'user'" class="avatar user-avatar">
      <div class="avatar-inner">👤</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Check,
  Loading,
  DocumentCopy,
  Refresh,
  Top,
  Bottom,
  PieChart
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { Message } from '@/types/chat'

interface Props {
  message: Message
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true
})

defineEmits<{
  regenerate: []
}>()

// 反馈状态
const feedback = ref<'like' | 'dislike' | null>(null)

// 思考步骤
const thinkingSteps = ['解析问题', '检索数据', '分析计算', '生成回答']
const currentStep = ref(1)

// 计算发送者名称
const senderName = computed(() => {
  return props.message.role === 'user' ? '您' : 'AI 助手'
})

// 格式化时间
const formatTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
})

// 渲染内容（简单的markdown解析）
const renderedContent = computed(() => {
  let content = props.message.content

  // 转义HTML
  content = content.replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // 粗体 **text**
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // 斜体 *text*
  content = content.replace(/\*(.*?)\*/g, '<em>$1</em>')

  // 代码 `code`
  content = content.replace(/`(.*?)`/g, '<code>$1</code>')

  // 换行
  content = content.replace(/\n/g, '<br>')

  return content
})

// 复制内容
const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

// 切换反馈
const toggleFeedback = (type: 'like' | 'dislike') => {
  feedback.value = feedback.value === type ? null : type
  ElMessage.success(feedback.value ? '感谢您的反馈！' : '已取消反馈')
}

// 模拟思考步骤动画
if (props.message.type === 'thinking') {
  const interval = setInterval(() => {
    if (currentStep.value < thinkingSteps.length - 1) {
      currentStep.value++
    } else {
      clearInterval(interval)
    }
  }, 800)
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  animation: messageIn 0.2s ease-out;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 用户消息右对齐 */
.chat-message.user {
  flex-direction: row-reverse;
}

/* 头像 */
.avatar {
  flex-shrink: 0;
}

.avatar-inner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: #f3f4f6;
}

.ai-avatar .avatar-inner {
  background: linear-gradient(135deg, #1677ff 0%, #0056d6 100%);
}

.user-avatar .avatar-inner {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

/* 消息内容包装器 */
.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 85%;
}

.chat-message.user .message-content-wrapper {
  align-items: flex-end;
}

/* 消息头部 */
.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #9ca3af;
}

.chat-message.user .message-header {
  flex-direction: row-reverse;
}

.sender-name {
  font-weight: 500;
}

.message-time {
  font-size: 11px;
}

/* 消息气泡 */
.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.chat-message.user .message-bubble {
  background: #1677ff;
  color: white;
  border-color: #1677ff;
}

/* 文本内容 */
.text-content {
  font-size: 14px;
  line-height: 1.7;
  color: #1f2937;
}

.chat-message.user .text-content {
  color: white;
}

.text-content :deep(strong) {
  font-weight: 600;
}

.text-content :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

.chat-message.user .text-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

/* 思考中状态 */
.thinking-content {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  background: #1677ff;
  border-radius: 50%;
  animation: dotPulse 1.4s ease-in-out infinite;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%, 100% { transform: scale(0.8); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 1; }
}

.thinking-text {
  font-size: 14px;
  color: #6b7280;
}

.thinking-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #9ca3af;
  transition: color 0.3s;
}

.thinking-step.active {
  color: #1677ff;
}

.step-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #d1d5db;
}

.thinking-step .el-icon {
  font-size: 14px;
}

/* 数据卡片 */
.data-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.data-card-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  text-align: center;
}

.card-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.card-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.card-change {
  font-size: 11px;
  margin-top: 4px;
}

.card-change.up {
  color: #52c41a;
}

.card-change.down {
  color: #f5222d;
}

/* 图表容器 */
.chart-container {
  min-height: 200px;
}

.chart-placeholder {
  height: 200px;
  background: #f9fafb;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #9ca3af;
}

.chart-placeholder .el-icon {
  font-size: 48px;
}

/* 表格容器 */
.table-container {
  overflow-x: auto;
}

/* 消息操作 */
.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-message:hover .message-actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f3f4f6;
  color: #6b7280;
}

.action-btn.active {
  color: #1677ff;
  background: #eff6ff;
}
</style>
