import axios from 'axios'

const request = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000
})

// 请求拦截
request.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    return Promise.reject(error)
  }
)

// 文件上传
export const uploadApi = (formData: FormData) => {
  return request.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取Sheet信息
export const getSheetInfo = (fileId: string) => {
  return request.get(`/api/sheets/${fileId}`)
}

// 获取统计数据
export const getStats = (fileId: string) => {
  return request.get(`/api/stats/${fileId}`)
}

// AI分析
export const analyzeApi = (fileId: string, dimensions?: string[]) => {
  return request.post('/api/analyze', {
    file_id: fileId,
    dimensions: dimensions || []
  })
}

// 健康检查
export const healthCheck = () => {
  return request.get('/api/health')
}