# 药品带量采购AI分析系统 - 任务清单

## 项目概述
- **目标**: 构建集采监管AI分析系统，支持逐层分析报告 + 自由问答
- **技术栈**: Flask + LangGraph + MiniMax API + HTML/JS
- **数据**: 固定Excel文件 `带量采购数据.xlsx`

---

## 任务列表

### Phase 1: 基础框架搭建

- [x] **T1.1** 创建项目目录结构
  - `backend/` - 后端代码
  - `frontend/` - 前端页面
  - `requirements.txt` - 依赖文件

- [x] **T1.2** 搭建Flask服务
  - 创建 `backend/app.py` 主应用
  - 配置路由和CORS

- [x] **T1.3** 实现Excel数据加载
  - 创建 `backend/data_loader.py`
  - 读取 `带量采购数据.xlsx`
  - 解析字段并返回JSON

---

### Phase 2: 前端界面开发

- [x] **T2.1** 编写HTML页面（左右布局）
  - 左侧统计面板
  - 右侧对话面板

- [x] **T2.2** 实现统计面板
  - 展示总体概览数据
  - 展示序时进度统计

- [x] **T2.3** 实现对话功能
  - SSE流式接收
  - 分析报告按钮
  - 自由问答输入框

---

### Phase 3: LangGraph集成

- [x] **T3.1** 安装LangGraph依赖
  - 添加到 `requirements.txt`

- [x] **T3.2** 创建LangGraph工作流
  - 创建 `backend/services/ai_service.py`
  - 定义分析节点（7个节点）
  - 定义状态结构 `AnalysisState`
  - 构建DAG流程图

- [x] **T3.3** 实现流式输出
  - 每个节点完成后实时推送结果
  - 前端分块展示

---

### Phase 4: MiniMax API集成

- [x] **T4.1** 配置API连接
  - 创建 `backend/config.py`
  - 配置 API Key 和 Group ID

- [x] **T4.2** 实现AI分析服务
  - 创建 `backend/services/ai_service.py`
  - 实现流式调用（待接入真实API）

- [x] **T4.3** 设计Prompt模板
  - 品种进度分析Prompt
  - 地市医院分析Prompt
  - 28原则分析Prompt
  - 配送企业分析Prompt
  - 落后品种企业分析Prompt

---

### Phase 5: API接口开发

- [x] **T5.1** `/api/data` - 获取数据列表

- [x] **T5.2** `/api/stats` - 获取统计面板数据

- [x] **T5.3** `/api/analyze` - 流式分析报告（报告模式）

- [x] **T5.4** `/api/chat` - 流式对话（问答模式）

- [x] **T5.5** `/api/health` - 健康检查

---

### Phase 6: 测试与优化

- [ ] **T6.1** 功能测试
  - 数据加载测试
  - 统计计算测试
  - AI分析测试
  - 流式输出测试

- [ ] **T6.2** 异常处理
  - API超时处理
  - 数据格式错误处理

- [ ] **T6.3** 界面优化
  - 样式调整
  - 加载状态展示

---

## 验收标准

1. 启动服务后可访问前端页面
2. 左侧显示统计面板（总体概览、序时进度）
3. 点击"分析报告"按钮，右侧流式展示逐层分析结果
4. 可输入问题进行自由问答
5. LangGraph 7个节点按顺序执行并输出

## 文件结构

```
std-2/
├── backend/
│   ├── __init__.py
│   ├── app.py              # Flask主应用（包含HTML前端）
│   ├── config.py           # 配置
│   ├── data_loader.py      # Excel数据加载
│   └── services/
│       ├── __init__.py
│       └── ai_service.py   # AI服务 + LangGraph
├── 带量采购数据.xlsx       # 数据文件
├── requirements.txt        # 依赖
├── plan.md                # 技术方案
└── todo.md                # 任务清单
```

## 启动方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API（可选）
# 编辑 backend/config.py 设置 MINIMAX_API_KEY 和 MINIMAX_GROUP_ID

# 3. 启动服务
cd E:/project/ai-study/std-2
python -m backend.app

# 4. 访问
# 浏览器打开 http://127.0.0.1:5000
```

## 注意事项

- 当前AI模块为模拟实现，需要接入真实的MiniMax API
- 数据字段需根据实际Excel文件调整
- 28原则分析逻辑需根据实际数据优化