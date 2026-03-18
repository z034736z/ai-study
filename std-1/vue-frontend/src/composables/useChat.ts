import { ref, computed } from 'vue'
import type { Message, StatsData, QuickQuestion, AnalysisDimension } from '@/types/chat'

// 生成唯一ID
const generateId = () => Math.random().toString(36).substring(2, 9)

// 预设快捷问题
const defaultQuickQuestions: QuickQuestion[] = [
  { id: '1', label: '按产品维度分析', query: '请分析各产品的采购金额分布情况', icon: '📦' },
  { id: '2', label: '按企业维度分析', query: '请分析申报企业的采购情况', icon: '🏢' },
  { id: '3', label: '按地市维度分析', query: '请分析各地市的采购分布', icon: '📍' },
  { id: '4', label: '时间趋势分析', query: '请分析采购数据的时间趋势', icon: '📈' },
  { id: '5', label: '成功率分析', query: '请分析各产品的签约成功率', icon: '✅' },
  { id: '6', label: '金额排名', query: '请列出采购金额排名前十的产品', icon: '🏆' },
]

export function useChat() {
  // 状态
  const messages = ref<Message[]>([])
  const isThinking = ref(false)
  const inputMessage = ref('')
  const currentStream = ref<ReadableStreamDefaultReader<Uint8Array> | null>(null)
  const statsData = ref<StatsData | null>(null)
  const loading = ref(false)
  const errorMsg = ref('')
  const sidebarCollapsed = ref(false)
  const activeDimension = ref<AnalysisDimension>('batch')
  const quickQuestions = ref<QuickQuestion[]>(defaultQuickQuestions)
  const currentFileId = ref<string>('')

  // 欢迎消息
  const welcomeMessage: Message = {
    id: generateId(),
    type: 'text',
    role: 'assistant',
    content: '👋 欢迎使用**带量采购数据分析助手**！\n\n我可以帮您：\n• 分析采购数据的各个维度\n• 发现数据中的趋势和规律\n• 生成专业的分析报告\n• 回答关于带量采购的各类问题\n\n请从下方选择一个问题开始，或直接输入您的问题。',
    timestamp: Date.now(),
  }

  // 初始化
  const initChat = () => {
    messages.value = [welcomeMessage]
  }

  // 发送消息
  const sendMessage = async (content: string) => {
    console.log('sendMessage called with:', content)
    if (!content.trim()) return

    // 添加用户消息
    const userMessage: Message = {
      id: generateId(),
      type: 'text',
      role: 'user',
      content: content.trim(),
      timestamp: Date.now(),
    }
    messages.value = [...messages.value, userMessage]
    console.log('User message added, messages count:', messages.value.length)
    inputMessage.value = ''

    // 显示思考状态
    isThinking.value = true

    // 添加思考中消息
    const thinkingMessage: Message = {
      id: generateId(),
      type: 'thinking',
      role: 'assistant',
      content: '正在分析数据...',
      timestamp: Date.now(),
    }
    messages.value = [...messages.value, thinkingMessage]
    console.log('Thinking message added, messages count:', messages.value.length)

    try {
      console.log('Calling analyze API with file_id:', currentFileId.value)
      // 调用流式API
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_id: currentFileId.value || 'latest',
          query: content.trim(),
          dimensions: []
        })
      })

      console.log('API response status:', response.status)

      if (!response.ok) {
        throw new Error(`分析请求失败: ${response.status}`)
      }

      // 移除思考消息
      messages.value = messages.value.filter(m => m.id !== thinkingMessage.id)
      console.log('Thinking message removed, messages count:', messages.value.length)

      // 创建AI响应消息
      const aiMessageId = generateId()
      let aiMessage: Message = {
        id: aiMessageId,
        type: 'text',
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      }
      messages.value = [...messages.value, aiMessage]
      console.log('AI message created, messages count:', messages.value.length)

      // 读取流式响应
      const reader = response.body?.getReader()
      currentStream.value = reader || null

      if (reader) {
        console.log('Starting to read stream...')
        const decoder = new TextDecoder()
        let buffer = ''
        let contentBuffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            console.log('Stream reading done')
            break
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.content) {
                  contentBuffer += data.content
                }
              } catch (e) {
                // 忽略解析错误
              }
            }
          }

          // 更新消息内容 - 创建新对象以触发响应式更新
          aiMessage = { ...aiMessage, content: contentBuffer }
          messages.value = messages.value.map(m => m.id === aiMessageId ? aiMessage : m)
        }

        // 处理最后剩余的buffer
        if (buffer.startsWith('data: ')) {
          try {
            const data = JSON.parse(buffer.slice(6))
            if (data.content) {
              contentBuffer += data.content
            }
          } catch (e) {
            // 忽略解析错误
          }
        }

        // 最终更新
        aiMessage = { ...aiMessage, content: contentBuffer }
        messages.value = messages.value.map(m => m.id === aiMessageId ? aiMessage : m)
        console.log('Stream complete, final content length:', contentBuffer.length)
      } else {
        console.error('No reader available')
      }
    } catch (error: any) {
      console.error('Error in sendMessage:', error)
      // 移除思考消息
      messages.value = messages.value.filter(m => m.type !== 'thinking')

      // 添加模拟AI响应（当后端不可用时）
      const aiMessageId = generateId()
      let aiMessage: Message = {
        id: aiMessageId,
        type: 'text',
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      }
      messages.value = [...messages.value, aiMessage]

      // 模拟流式输出
      const mockResponse = generateMockResponse(content.trim())
      console.log('Using mock response, length:', mockResponse.length)

      // 逐字显示模拟流式输出
      let displayedContent = ''
      for (let i = 0; i < mockResponse.length; i++) {
        displayedContent += mockResponse[i]
        aiMessage = { ...aiMessage, content: displayedContent }
        messages.value = messages.value.map(m => m.id === aiMessageId ? aiMessage : m)
        await new Promise(resolve => setTimeout(resolve, 10))
      }
    } finally {
      isThinking.value = false
      currentStream.value = null
      console.log('sendMessage complete, final messages count:', messages.value.length)
    }
  }

  // 停止生成
  const stopGeneration = () => {
    if (currentStream.value) {
      currentStream.value.cancel()
      currentStream.value = null
      isThinking.value = false
      // 移除思考消息
      messages.value = messages.value.filter(m => m.type !== 'thinking')
    }
  }

  // 加载统计数据 - 现在从 demo.json 加载
  const loadStats = async () => {
    loading.value = true
    errorMsg.value = ''
    try {
      const response = await fetch('/demo.json')
      if (!response.ok) {
        throw new Error('无法加载数据文件')
      }
      const data = await response.json()

      // 构建符合 StatsData 格式的数据
      if (data.json1_总体执行进度) {
        const json1 = data.json1_总体执行进度
        statsData.value = {
          overall: {
            count: json1.批次签约总量 || 0,
            total_amount: json1.已入库总量 || 0,
            total_quantity: json1.批次签约总量 || 0,
            total_applied: json1.批次签约总量 || 0,
            total_signed: json1.已入库总量 || 0,
            success_rate: json1.执行进度 || 0
          },
          dimensions: {
            '产品': { dimension: '产品', total: 0, items: [] },
            '品种': { dimension: '品种', total: 0, items: [] },
            '申报企业': { dimension: '申报企业', total: 0, items: [] },
            '配送企业': { dimension: '配送企业', total: 0, items: [] },
            '地市': { dimension: '地市', total: 0, items: [] },
            '医院': { dimension: '医院', total: 0, items: [] }
          }
        }

        // 从 json3 构建地市数据
        if (data.json3_各地市执行进度) {
          const cityItems = data.json3_各地市执行进度.map((item: any) => ({
            name: item.地市名称,
            count: item.地市签约总量,
            amount: item.地市采购入库总量,
            quantity: item.地市签约总量
          }))
          statsData.value.dimensions['地市'] = {
            dimension: '地市',
            total: cityItems.length,
            items: cityItems
          }
        }
      }
    } catch (error: any) {
      errorMsg.value = '数据加载失败: ' + (error.message || '请检查数据文件')
      console.error('加载数据失败:', error)
      statsData.value = null
    } finally {
      loading.value = false
    }
  }

  // 模拟数据函数已移除 - 只使用真实Excel数据

  // 重新生成最后一条消息
  const regenerateLastMessage = async () => {
    const lastUserMessage = [...messages.value]
      .reverse()
      .find(m => m.role === 'user')

    if (lastUserMessage) {
      // 移除最后一条AI回复
      const lastAiIndex = messages.value.findIndex(
        m => m.role === 'assistant' && m.timestamp > lastUserMessage.timestamp
      )
      if (lastAiIndex !== -1) {
        messages.value = messages.value.slice(0, lastAiIndex)
      }
      await sendMessage(lastUserMessage.content)
    }
  }

  // 清空对话
  const clearChat = () => {
    messages.value = [welcomeMessage]
  }

  // 切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  // 格式化金额
  const formatAmount = (amount: number): string => {
    if (!amount) return '-'
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      maximumFractionDigits: 0
    }).format(amount)
  }

  // 格式化数字
  const formatNumber = (num: number): string => {
    if (!num && num !== 0) return '-'
    return num.toLocaleString('zh-CN')
  }

  // 生成AI响应（后端不可用时显示提示）
  const generateMockResponse = (query: string): string => {
    return `⚠️ **系统提示**

当前无法连接到后端AI服务，请检查：
1. 后端服务是否已启动（python-api）
2. 网络连接是否正常
3. 后端服务地址配置是否正确

您的问题「${query}」已收到，请确保后端服务正常运行后重试。`
  }

  return {
    // 状态
    messages,
    isThinking,
    inputMessage,
    statsData,
    loading,
    errorMsg,
    sidebarCollapsed,
    activeDimension,
    quickQuestions,

    // 计算属性
    hasMessages: computed(() => messages.value.length > 1),

    // 方法
    initChat,
    sendMessage,
    stopGeneration,
    loadStats,
    regenerateLastMessage,
    clearChat,
    toggleSidebar,
    formatAmount,
    formatNumber,
  }
}
