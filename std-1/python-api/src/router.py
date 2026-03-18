from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict
import uuid
import json
import os
import asyncio

from src.models.schemas import UploadResponse, AnalyzeRequest, AnalyzeResponse
from src.service.excel_service import ExcelService
from src.service.stats_service import StatsService
from src.service.ai_service import AIService

router = APIRouter(prefix="/api", tags=["分析接口"])

# 存储文件信息
file_storage: Dict[str, dict] = {}

# 初始化服务
excel_service = ExcelService(upload_dir="./uploads")
ai_service = AIService()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """上传Excel文件"""
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")

    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")

    # 保存文件
    file_path = excel_service.save_file(content, file.filename)

    # 读取Excel信息
    try:
        sheets = excel_service.read_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取Excel失败: {str(e)}")

    # 生成文件ID
    file_id = str(uuid.uuid4())

    # 存储文件信息
    file_storage[file_id] = {
        "file_path": file_path,
        "filename": file.filename,
        "sheets": sheets
    }

    # 计算总行数
    total_rows = sum(len(df) for df in sheets.values())

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        sheet_names=list(sheets.keys()),
        total_rows=total_rows,
        message="文件上传成功"
    )


@router.get("/sheets/{file_id}")
async def get_sheet_info(file_id: str):
    """获取Excel的Sheet信息"""
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    file_info = file_storage[file_id]
    return excel_service.get_sheet_info(file_info["file_path"])


@router.get("/stats/{file_id}")
async def get_stats(file_id: str):
    """获取统计数据"""
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    file_info = file_storage[file_id]
    stats_service = StatsService(file_info["sheets"])

    return stats_service.get_all_stats()


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """开始AI分析（流式输出）"""
    file_id = request.file_id
    query = request.query or "请分析这批采购数据的关键指标和趋势"

    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    file_info = file_storage[file_id]

    # 生成统计数据摘要
    stats_service = StatsService(file_info["sheets"])
    stats_summary = stats_service.generate_summary_text()

    # 构建Prompt，包含用户查询
    full_prompt = f"""用户问题：{query}

数据摘要：
{stats_summary}

请根据以上数据，针对用户的问题进行详细分析。"""

    prompt = ai_service.build_prompt(full_prompt)

    # 流式返回
    async def event_generator():
        for chunk in ai_service.stream_chat(prompt):
            # SSE格式
            yield f"data: {json.dumps({'content': chunk})}\n\n"
            await asyncio.sleep(0.01)  # 避免阻塞

        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "AI Analysis API"}


# 自动加载Excel文件的ID
_auto_file_id: str = None


@router.get("/load-excel")
async def load_excel_auto():
    """自动加载项目目录下的Excel文件"""
    global _auto_file_id

    # 查找Excel文件
    excel_files = []
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(('.xlsx', '.xls')) and not f.startswith('~'):
                excel_files.append(os.path.join(root, f))

    if not excel_files:
        raise HTTPException(status_code=404, detail="未找到Excel文件")

    # 读取第一个Excel文件
    file_path = excel_files[0]
    try:
        sheets = excel_service.read_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取Excel失败: {str(e)}")

    # 生成文件ID
    file_id = str(uuid.uuid4())
    _auto_file_id = file_id

    # 存储
    file_storage[file_id] = {
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "sheets": sheets
    }

    return {
        "file_id": file_id,
        "filename": os.path.basename(file_path),
        "sheet_names": list(sheets.keys()),
        "total_rows": sum(len(df) for df in sheets.values())
    }


@router.get("/stats/auto")
async def get_stats_auto():
    """自动获取统计数据（每次自动加载）"""
    # 每次都自动加载Excel文件
    load_result = await load_excel_auto()
    file_id = load_result["file_id"]

    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="文件不存在")

    file_info = file_storage[file_id]
    stats_service = StatsService(file_info["sheets"])

    return stats_service.get_all_stats()