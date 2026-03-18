# 带量采购 AI 分析系统

> 基于阿里云 Minimax 大模型的带量采购数据分析工具

## 项目概述

本系统从**国家药品集中采购专家**的视角，对带量采购Excel数据进行AI分析，按以下维度进行次第分析：
- 整体情况
- 品种维度
- 地市维度
- 医院维度
- 产品维度
- 申报企业维度
- 配送企业维度

## 技术架构

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus |
| 后端 | Python FastAPI |
| AI | 阿里云 Minimax API (abab6.5s-chat) |
| 数据处理 | Pandas + openpyxl |

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- 阿里云 Minimax API Key

### 2. 配置 AI API

编辑 `python-api/.env` 文件：

```env
MINIMAX_API_KEY=你的API密钥
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=abab6.5s-chat
```

### 3. 启动服务

```bash
# 启动后端 (端口 8000)
cd python-api
pip install -r requirements.txt
python -m src.main

# 启动前端 (端口 3000)
cd vue-frontend
npm install
npm run dev
```

### 4. 访问系统

- 前端页面: http://localhost:3000
- API文档: http://localhost:8000/docs

## 使用流程

1. 打开浏览器访问 http://localhost:3000
2. 拖拽或点击上传带量采购Excel文件
3. 等待系统解析并显示统计数据
4. 点击"开始AI分析"按钮
5. 查看AI流式输出的分析报告

## 项目结构

```
ai-study/
├── python-api/                 # 后端服务
│   ├── src/
│   │   ├── main.py            # FastAPI入口
│   │   ├── router.py          # API路由
│   │   ├── service/
│   │   │   ├── excel_service.py   # Excel解析
│   │   │   ├── stats_service.py   # 数据统计
│   │   │   └── ai_service.py      # AI分析
│   │   └── models/
│   │       └── schemas.py         # 数据模型
│   ├── .env                    # 环境配置
│   └── uploads/                # 上传文件目录
│
└── vue-frontend/              # 前端应用
    ├── src/
    │   ├── main.ts            # 入口
    │   ├── App.vue            # 根组件
    │   ├── api/analysis.ts    # API调用
    │   ├── router/            # 路由
    │   └── views/AiAnalysis.vue # 分析页面
    └── index.html
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传Excel文件 |
| `/api/stats/{file_id}` | GET | 获取统计数据 |
| `/api/analyze` | POST | AI分析(流式输出) |
| `/api/health` | GET | 健康检查 |

## Excel 数据要求

系统支持包含以下Sheet的Excel文件：
- 医疗机构采购表（必需）- 核心数据
- 批次信息表
- 批次目录信息表
- 批次合同信息表

## 注意事项

1. 首次使用需配置 Minimax API Key
2. Excel文件大小限制 50MB
3. 当前为演示模式，未配置API时使用模拟数据

## 开发相关

```bash
# 代码格式化
black python-api/src/
isort python-api/src/

# 代码检查
flake8 python-api/src/
```