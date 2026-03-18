<template>
  <div class="chat-input-area">
    <!-- 快捷问题 -->
    <div v-if="showQuickQuestions" class="quick-questions">
      <span class="quick-label">💡 推荐问题：</span>
      <div class="question-tags">
        <button
          v-for="q in quickQuestions.slice(0, 4)"
          :key="q.id"
          class="question-tag"
          @click="selectQuickQuestion(q)"
          :title="q.query"
        >
          <span class="tag-icon">{{ q.icon }}</span>
          <span class="tag-text">{{ q.label }}</span>
        </button>
      </div>
    </div>

    <!-- 输入框容器 -->
    <div class="input-container" :class="{ focused: isFocused }">
      <!-- 输入框 -->
      <textarea
        ref="textareaRef"
        v-model="localValue"
        class="chat-textarea"
        :placeholder="placeholder"
        :disabled="disabled || isThinking"
        :rows="1"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.enter.shift.exact="insertNewline"
        @input="autoResize"
      />

      <!-- 输入工具栏 -->
      <div class="input-toolbar">
        <div class="toolbar-left">
          <el-tooltip content="上传文件（即将支持）" placement="top">
            <button class="toolbar-btn" disabled>
              <el-icon><Paperclip /></el-icon>
            </button>
          </el-tooltip>
          <span class="input-hint">Enter 发送，Shift+Enter 换行</span>
        </div>

        <div class="toolbar-right">
          <!-- 停止生成按钮 -->
          <button
            v-if="isThinking"
            class="send-btn stop-btn"
            @click="$emit('stop')"
          >
            <el-icon><VideoPause /></el-icon>
            停止
          </button>
          <!-- 发送按钮 -->
          <button
            v-else
            class="send-btn"
            :class="{ active: canSend }"
            :disabled="!canSend"
            @click="sendMessage"
          >
            <el-icon><Promotion /></el-icon>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Paperclip, Promotion, VideoPause } from '@element-plus/icons-vue'
import type { QuickQuestion } from '@/types/chat'

interface Props {
  modelValue: string
  quickQuestions: QuickQuestion[]
  isThinking: boolean
  disabled?: boolean
  placeholder?: string
  showQuickQuestions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '输入您的问题，例如：分析各产品的采购金额分布...',
  showQuickQuestions: true
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: [message: string]
  stop: []
}>()

// 本地状态
const localValue = ref(props.modelValue)
const isFocused = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()

// 同步外部值
watch(() => props.modelValue, (val) => {
  localValue.value = val
  nextTick(autoResize)
})

// 同步内部值
watch(localValue, (val) => {
  emit('update:modelValue', val)
})

// 是否可以发送
const canSend = computed(() => {
  return localValue.value.trim().length > 0 && !props.isThinking
})

// 发送消息
const sendMessage = () => {
  if (!canSend.value) return
  emit('send', localValue.value.trim())
  localValue.value = ''
  nextTick(() => {
    autoResize()
    textareaRef.value?.focus()
  })
}

// 选择快捷问题
const selectQuickQuestion = (q: QuickQuestion) => {
  emit('send', q.query)
}

// 插入换行
const insertNewline = () => {
  localValue.value += '\n'
  nextTick(autoResize)
}

// 自动调整高度
const autoResize = () => {
  const textarea = textareaRef.value
  if (!textarea) return

  textarea.style.height = 'auto'
  const newHeight = Math.min(textarea.scrollHeight, 200)
  textarea.style.height = newHeight + 'px'
}

// 聚焦
const focus = () => {
  textareaRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.chat-input-area {
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
  padding: 16px 24px;
}

/* 快捷问题 */
.quick-questions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.quick-label {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}

.question-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  overflow-x: auto;
}

.question-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.question-tag:hover {
  background: #eff6ff;
  border-color: #1677ff;
  color: #1677ff;
}

.tag-icon {
  font-size: 14px;
}

.tag-text {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 输入容器 */
.input-container {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
  transition: all 0.2s;
}

.input-container.focused {
  background: #ffffff;
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

/* 文本域 */
.chat-textarea {
  width: 100%;
  min-height: 24px;
  max-height: 200px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  line-height: 1.6;
  color: #1f2937;
  resize: none;
  font-family: inherit;
}

.chat-textarea::placeholder {
  color: #9ca3af;
}

.chat-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 工具栏 */
.input-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.toolbar-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #6b7280;
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-hint {
  font-size: 12px;
  color: #9ca3af;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 发送按钮 */
.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn.active {
  background: #1677ff;
  color: white;
  cursor: pointer;
}

.send-btn.active:hover {
  background: #0056d6;
}

.send-btn.stop-btn {
  width: auto;
  padding: 0 16px;
  background: #fef2f2;
  color: #ef4444;
  gap: 6px;
  font-size: 13px;
  cursor: pointer;
}

.send-btn.stop-btn:hover {
  background: #fee2e2;
}
</style>
