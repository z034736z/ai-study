import pandas as pd
import uuid
import os
from typing import Dict, List, Any
from datetime import datetime


class ExcelService:
    """Excel 文件解析服务"""

    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    def save_file(self, content: bytes, filename: str) -> str:
        """保存上传的文件"""
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1]
        save_name = f"{file_id}{ext}"
        save_path = os.path.join(self.upload_dir, save_name)

        with open(save_path, 'wb') as f:
            f.write(content)

        return save_path

    def read_excel(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """读取Excel所有Sheet"""
        excel_file = pd.ExcelFile(file_path)
        sheets = {}

        for sheet_name in excel_file.sheet_names:
            # 尝试读取，忽略空行
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            # 清理列名中的空格
            df.columns = df.columns.str.strip() if hasattr(df.columns, 'str') else df.columns
            # 删除全空行
            df = df.dropna(how='all')
            sheets[sheet_name] = df

        return sheets

    def get_sheet_info(self, file_path: str) -> Dict[str, Any]:
        """获取Excel文件信息"""
        sheets = self.read_excel(file_path)
        info = {}

        for name, df in sheets.items():
            info[name] = {
                "columns": list(df.columns),
                "rows": len(df),
                "preview": df.head(3).to_dict(orient='records')
            }

        return info

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """规范化列名 - 处理编码问题"""
        # 已知列名映射（基于实际Excel结构）
        column_mapping = {
            '采购单号': '采购单号',
            '医疗机构名称': '医院名称',
            '目录编号': '目录编号',
            '药品品种': '药品品种',
            '药品名称': '药品名称',
            '申报企业': '申报企业',
            '配送企业': '配送企业',
            '委托单号': '委托单号',
            '申报量': '申报量',
            '签约量': '签约量',
            '合同量': '合同量',
            '金额(元)': '金额',
            '成功量': '成功量',
            '签约日期': '签约日期',
            '有效日期': '有效日期',
            '完成日期': '完成日期',
        }

        # 重命名列
        df_normalized = df.rename(columns=column_mapping)
        return df_normalized


# 列名识别（备用方案）
KNOWN_COLUMNS = {
    # Sheet: 医疗机构明细
    '医疗机构明细': ['采购单号', '医院名称', '目录编号', '药品品种', '药品名称',
                   '申报企业', '配送企业', '委托单号', '申报量', '签约量',
                   '合同量', '金额(元)', '成功量', '签约日期', '有效日期', '完成日期'],
    # Sheet: 带量项目明细信息
    '带量项目明细信息': ['编号', '目录编号', '药品品种', '药品名称', '剂型', '医疗机构编码'],
    # Sheet: 带量合同信息
    '带量合同信息': ['编号', '目录编号', '合同号', '申报企业', '医院', '合同量', '签约日期', '生效日期'],
    # Sheet: 带量采购信息
    '带量采购信息': ['编号', '项目名称', '产品类型', '执行开始日期', '执行结束日期', '申报开始日期', '申报结束日期']
}