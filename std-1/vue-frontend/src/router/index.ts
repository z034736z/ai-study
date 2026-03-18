import { createRouter, createWebHistory } from 'vue-router'
import AiAnalysis from '@/views/AiAnalysis.vue'

const routes = [
  {
    path: '/',
    redirect: '/analysis'
  },
  {
    path: '/analysis',
    name: 'AiAnalysis',
    component: AiAnalysis,
    meta: {
      title: 'AI 分析'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router