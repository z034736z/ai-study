// 消息类型定义
export type MessageType = 'text' | 'data' | 'chart' | 'table' | 'thinking'

export interface Message {
  id: string
  type: MessageType
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  metadata?: {
    data?: any
    chartType?: string
    tableData?: any[]
    columns?: any[]
  }
}

// 统计数据类型
export interface DimensionItem {
  name: string
  count: number
  amount: number
  quantity: number
}

export interface Dimension {
  dimension: string
  total: number
  items: DimensionItem[]
  error?: string
}

export interface StatsData {
  overall: {
    count: number
    total_amount: number
    total_quantity: number
    total_applied: number
    total_signed: number
    success_rate: number
  }
  dimensions: {
    '产品': Dimension
    '品种': Dimension
    '申报企业': Dimension
    '配送企业': Dimension
    '地市': Dimension
    '医院': Dimension
  }
}

// 快捷问题类型
export interface QuickQuestion {
  id: string
  label: string
  query: string
  icon?: string
}

// 数据概览卡片配置
export interface StatCardConfig {
  label: string
  key: string
  unit?: string
  format?: 'currency' | 'number' | 'percent'
  color: string
}

// 侧边栏状态
export interface SidebarState {
  collapsed: boolean
  activeDimension: string
}

// 批次信息类型
export interface BatchInfo {
  batchName: string
  contractCount: number
  progress: number
}

// 目录信息类型
export interface CatalogItem {
  name: string
  contractQty: number
  progress: number
}

// 分析维度
export type AnalysisDimension = 'batch' | 'catalog' | 'enterprise' | 'delivery' | 'hospital'

export interface DimensionConfig {
  key: AnalysisDimension
  label: string
  icon: string
  dataKey: string
}
