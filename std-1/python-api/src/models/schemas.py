from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: str
    sheet_names: List[str]
    total_rows: int
    message: str


class StatsSummary(BaseModel):
    """统计数据摘要"""
    dimension: str
    count: int
    total_amount: float
    total_quantity: int
    top_items: List[Dict[str, Any]]


class AnalyzeRequest(BaseModel):
    """分析请求"""
    file_id: str
    query: Optional[str] = None  # 用户查询内容
    dimensions: Optional[List[str]] = None  # 指定分析维度


class AnalyzeResponse(BaseModel):
    """分析响应"""
    task_id: str
    message: str


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    result: Optional[str] = None