<template>
  <div class="chat-container" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- 侧边栏 -->
    <ChatSidebar
      :collapsed="sidebarCollapsed"
      :has-messages="hasMessages"
      @toggle="toggleSidebar"
      @clear-chat="clearChat"
    />

    <!-- 主聊天区 -->
    <div class="chat-main">
      <!-- 消息列表 -->
      <div ref="messagesRef" class="messages-area" @scroll="handleScroll">
        <div class="messages-wrapper">
          <!-- 欢迎消息 -->
          <div v-if="!hasMessages" class="welcome-section">
            <div class="welcome-header">
              <div class="welcome-icon">🤖</div>
              <h2 class="welcome-title">带量采购数据分析助手</h2>
              <p class="welcome-subtitle">基于国家药品集中采购数据，为您提供智能分析服务</p>
            </div>

            <!-- 核心指标展示 -->
            <div v-if="statsData?.overall" class="stats-overview">
              <div class="stat-box">
                <div class="stat-box-value">{{ formatNumber(statsData.overall.count) }}</div>
                <div class="stat-box-label">采购记录</div>
              </div>
              <div class="stat-box">
                <div class="stat-box-value">{{ formatAmount(statsData.overall.total_amount) }}</div>
                <div class="stat-box-label">合同总金额</div>
              </div>
              <div class="stat-box">
                <div class="stat-box-value">{{ statsData.overall.success_rate.toFixed(1) }}%</div>
                <div class="stat-box-label">签约成功率</div>
              </div>
            </div>

            <!-- 功能卡片 -->
            <div class="feature-cards">
              <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">多维分析</div>
                <div class="feature-desc">按产品、企业、地市等维度深入分析</div>
              </div>
              <div class="feature-card">
                <div class="feature-icon">📈</div>
                <div class="feature-title">趋势洞察</div>
                <div class="feature-desc">发现数据变化趋势和规律</div>
              </div>
              <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <div class="feature-title">智能问答</div>
                <div class="feature-desc">自然语言交互，即时获取答案</div>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-else-if="hasMessages" class="messages-list">
            <ChatMessage
              v-for="message in messages"
              :key="message.id"
              :message="message"
              @regenerate="regenerateLastMessage"
            />
          </div>

          <!-- 空状态调试 -->
          <div v-else class="debug-empty">
            <p>Messages: {{ messages.length }}</p>
            <p>HasMessages: {{ hasMessages }}</p>
          </div>

          <!-- 底部占位 -->
          <div class="messages-end"></div>
        </div>
      </div>

      <!-- 输入区域 -->
      <ChatInput
        v-model="inputMessage"
        :quick-questions="quickQuestions"
        :is-thinking="isThinking"
        :show-quick-questions="messages.length <= 2"
        @send="sendMessage"
        @stop="stopGeneration"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import ChatSidebar from './ChatSidebar.vue'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import { useChat } from '@/composables/useChat'

// 使用聊天逻辑
const {
  messages,
  isThinking,
  inputMessage,
  statsData,
  loading,
  errorMsg,
  sidebarCollapsed,
  quickQuestions,
  hasMessages,
  sendMessage: originalSendMessage,
  stopGeneration,
  loadStats,
  regenerateLastMessage,
  clearChat,
  toggleSidebar,
  formatAmount,
  formatNumber,
  initChat
} = useChat()

// 本地状态
const messagesRef = ref<HTMLElement>()
const isAtBottom = ref(true)

// 发送消息并滚动到底部
const sendMessage = async (content: string) => {
  console.log('ChatContainer.sendMessage called:', content)
  console.log('Current messages count before send:', messages.value.length)
  await originalSendMessage(content)
  console.log('Messages count after send:', messages.value.length)
  scrollToBottom()
}

// 计算属性调试
watch(messages, () => {
  console.log('Messages changed, count:', messages.value.length, 'hasMessages:', hasMessages.value)
}, { deep: true })

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      isAtBottom.value = true
    }
  })
}

// 处理滚动
const handleScroll = () => {
  if (!messagesRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesRef.value
  isAtBottom.value = scrollHeight - scrollTop - clientHeight < 50
}

// 监听消息变化，自动滚动
watch(messages, () => {
  if (isAtBottom.value) {
    scrollToBottom()
  }
}, { deep: true })

// 初始化
onMounted(() => {
  initChat()
  loadStats()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100%;
  width: 100%;
  background: #f5f7fa;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* 消息区域 */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  scroll-behavior: smooth;
}

.messages-wrapper {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.messages-end {
  height: 24px;
  flex-shrink: 0;
}

/* 欢迎区域 */
.welcome-section {
  padding: 48px 24px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.welcome-header {
  text-align: center;
  margin-bottom: 32px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

/* 统计数据概览 */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-box {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-box-value {
  font-size: 24px;
  font-weight: 700;
  color: #1677ff;
  margin-bottom: 4px;
  font-family: monospace;
}

.stat-box-label {
  font-size: 13px;
  color: #6b7280;
}

/* 功能卡片 */
.feature-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.feature-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
  cursor: pointer;
}

.feature-card:hover {
  border-color: #1677ff;
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.1);
  transform: translateY(-2px);
}

.feature-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.feature-desc {
  font-size: 12px;
  color: #6b7280;
}

/* 消息列表 */
.messages-list {
  display: flex;
  flex-direction: column;
  padding: 8px 0;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .stats-overview,
  .feature-cards {
    grid-template-columns: 1fr;
  }

  .welcome-section {
    padding: 24px 16px;
  }
}

@media (max-width: 1280px) {
  .stats-overview {
    grid-template-columns: repeat(3, 1fr);
  }

  .feature-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
