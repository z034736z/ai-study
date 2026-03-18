import pandas as pd
from typing import Dict, List, Any
import re


class StatsService:
    """数据统计服务 - 按7个维度进行分析"""

    def __init__(self, sheets_data: Dict[str, pd.DataFrame]):
        self.sheets = sheets_data
        # 智能匹配核心数据Sheet - 查找包含采购/明细/合同的Sheet
        self.main_df = self._find_main_sheet()
        # 智能列名映射
        self.column_map = self._build_column_map()

    def _find_main_sheet(self) -> pd.DataFrame:
        """查找核心数据Sheet"""
        # 优先查找包含"采购"的Sheet
        for name in self.sheets.keys():
            if '采购' in name:
                return self.sheets[name]

        # 其次查找包含"明细"的Sheet
        for name in self.sheets.keys():
            if '明细' in name:
                return self.sheets[name]

        # 如果都没找到，返回第一个非空的Sheet
        for name, df in self.sheets.items():
            if not df.empty and len(df.columns) > 5:
                return df

        return pd.DataFrame()

    def _build_column_map(self) -> Dict[str, str]:
        """构建智能列名映射"""
        if self.main_df.empty:
            return {}

        # 尝试识别关键列
        col_map = {}
        cols = list(self.main_df.columns)

        for col in cols:
            col_lower = str(col).lower()
            # 金额相关列
            if '金额' in str(col) or 'amount' in col_lower or 'total' in col_lower:
                if '金额' not in col_map:
                    col_map['金额'] = col
            # 合同量相关
            elif '合同' in str(col) and '量' in str(col):
                if '合同量' not in col_map:
                    col_map['合同量'] = col
            # 申报量
            elif '申报' in str(col) and '量' in str(col):
                if '申报量' not in col_map:
                    col_map['申报量'] = col
            # 签约量
            elif '签约' in str(col) and '量' in str(col):
                if '签约量' not in col_map:
                    col_map['签约量'] = col
            # 成功量
            elif '成功' in str(col) and '量' in str(col):
                if '成功量' not in col_map:
                    col_map['成功量'] = col
            # 医院名称
            elif '医院' in str(col) and '名' in str(col):
                if '医院名称' not in col_map:
                    col_map['医院名称'] = col
            # 药品品种
            elif '品种' in str(col) and '药' in str(col):
                if '药品品种' not in col_map:
                    col_map['药品品种'] = col
            # 药品名称
            elif '药品' in str(col) and '名称' in str(col):
                if '药品名称' not in col_map:
                    col_map['药品名称'] = col
            # 申报企业
            elif '申报' in str(col) and '企业' in str(col):
                if '申报企业' not in col_map:
                    col_map['申报企业'] = col
            # 配送企业
            elif '配送' in str(col) and '企业' in str(col):
                if '配送企业' not in col_map:
                    col_map['配送企业'] = col
            # 采购单号
            elif '采购' in str(col) and ('号' in str(col) or '单' in str(col)):
                if '采购单号' not in col_map:
                    col_map['采购单号'] = col

        return col_map

    def get_col(self, key: str) -> str:
        """获取实际列名"""
        return self.column_map.get(key, key)

    def extract_city(self, hospital_name: str) -> str:
        """从医院名称提取地市信息"""
        if pd.isna(hospital_name):
            return '未知'

        # 常见地市匹配
        cities = [
            '浙江省', '江苏省', '广东省', '山东省', '河南省', '四川省',
            '湖北省', '湖南省', '河北省', '安徽省', '福建省', '江西省',
            '辽宁省', '吉林省', '黑龙江省', '陕西省', '云南省', '贵州省',
            '甘肃省', '青海省', '内蒙古', '新疆', '宁夏', '海南',
            '北京', '上海', '天津', '重庆', '深圳', '广州', '杭州',
            '南京', '武汉', '成都', '郑州', '长沙', '沈阳', '西安'
        ]

        for city in cities:
            if city in str(hospital_name):
                return city

        # 尝试从 "xxx大学附属xxx医院" 提取省份
        match = re.search(r'^(.*?)(?:大学|省|市)', str(hospital_name))
        if match:
            return match.group(1)[:4] if len(match.group(1)) >= 2 else '未知'

        return '未知'

    def get_overall_stats(self) -> Dict[str, Any]:
        """整体统计"""
        if self.main_df.empty:
            return {"count": 0, "total_amount": 0, "total_quantity": 0}

        df = self.main_df

        # 使用智能列名
        amount_col = self.get_col('金额')
        qty_col = self.get_col('合同量')
        sign_col = self.get_col('签约量')
        apply_col = self.get_col('申报量')
        success_col = self.get_col('成功量')

        total_amount = df[amount_col].sum() if amount_col in df.columns else 0
        total_qty = df[qty_col].sum() if qty_col in df.columns else 0
        total_signed = df[sign_col].sum() if sign_col in df.columns else 0
        total_applied = df[apply_col].sum() if apply_col in df.columns else 0
        total_success = df[success_col].sum() if success_col in df.columns else 0

        return {
            "count": len(df),
            "total_amount": float(total_amount) if pd.notna(total_amount) else 0,
            "total_quantity": int(total_qty) if pd.notna(total_qty) else 0,
            "total_signed": int(total_signed) if pd.notna(total_signed) else 0,
            "total_applied": int(total_applied) if pd.notna(total_applied) else 0,
            "success_rate": round(total_success / max(total_applied, 1) * 100, 2) if total_applied else 0
        }

    def get_dimension_stats(self, dimension: str, top_n: int = 10) -> Dict[str, Any]:
        """按指定维度统计"""
        if self.main_df.empty:
            return {"dimension": dimension, "items": [], "total": 0}

        df = self.main_df.copy()

        # 智能列名 - 只使用存在的列
        amount_col = self.get_col('金额') if self.get_col('金额') in df.columns else None
        qty_col = self.get_col('合同量') if self.get_col('合同量') in df.columns else None
        id_col = self.get_col('采购单号') if self.get_col('采购单号') in df.columns else None

        # 如果没有ID列，使用第一列
        if not id_col:
            id_col = df.columns[0]

        # 根据维度选择分组字段
        dimension_map = {
            '品种': self.get_col('药品品种') if self.get_col('药品品种') in df.columns else None,
            '地市': None,  # 需要特殊处理
            '医院': self.get_col('医院名称') if self.get_col('医院名称') in df.columns else None,
            '产品': self.get_col('药品名称') if self.get_col('药品名称') in df.columns else None,
            '申报企业': self.get_col('申报企业') if self.get_col('申报企业') in df.columns else None,
            '配送企业': self.get_col('配送企业') if self.get_col('配送企业') in df.columns else None
        }

        field = dimension_map.get(dimension)

        if dimension == '地市':
            hospital_col = self.get_col('医院名称') if self.get_col('医院名称') in df.columns else None
            if hospital_col:
                df['地市'] = df[hospital_col].apply(self.extract_city)
                field = '地市'
            else:
                return {"dimension": dimension, "items": [], "error": "医院名称列不存在"}

        if not field or field not in df.columns:
            return {"dimension": dimension, "items": [], "error": f"字段 {field} 不存在"}

        # 构建聚合参数字典 - 只添加存在的列
        agg_dict = {id_col: 'count'}
        if amount_col and amount_col in df.columns:
            agg_dict[amount_col] = 'sum'
        if qty_col and qty_col in df.columns:
            agg_dict[qty_col] = 'sum'

        # 分组统计
        grouped = df.groupby(field, as_index=False).agg(agg_dict)

        if amount_col and amount_col in grouped.columns:
            grouped = grouped.sort_values(amount_col, ascending=False)
        elif id_col in grouped.columns:
            grouped = grouped.sort_values(id_col, ascending=False)

        # 构建结果
        items = []
        for _, row in grouped.head(top_n).iterrows():
            item = {
                "name": row[field],
                "count": int(row.get(id_col, 0)) if id_col in row else 0,
                "amount": float(row.get(amount_col, 0)) if amount_col and amount_col in row and pd.notna(row.get(amount_col)) else 0,
                "quantity": int(row.get(qty_col, 0)) if qty_col and qty_col in row and pd.notna(row.get(qty_col)) else 0
            }
            items.append(item)

        return {
            "dimension": dimension,
            "total": len(grouped),
            "items": items
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有维度的统计数据"""
        dimensions = ['品种', '地市', '医院', '产品', '申报企业', '配送企业']

        result = {
            "overall": self.get_overall_stats(),
            "dimensions": {}
        }

        for dim in dimensions:
            result["dimensions"][dim] = self.get_dimension_stats(dim)

        return result

    def generate_summary_text(self) -> str:
        """生成数据摘要文本（用于AI分析）"""
        stats = self.get_all_stats()
        overall = stats['overall']

        summary = f"""
## 数据概览

- 采购记录总数：{overall.get('count', 0)} 条
- 合同总金额：{overall.get('total_amount', 0):,.2f} 元
- 合同总数量：{overall.get('total_quantity', 0):,} 单位
- 申报总数量：{overall.get('total_applied', 0):,} 单位
- 签约总数量：{overall.get('total_signed', 0):,} 单位
- 成功率：{overall.get('success_rate', 0)}%

"""

        # 添加各维度Top数据
        for dim, dim_data in stats['dimensions'].items():
            items = dim_data.get('items', [])
            if items:
                summary += f"### {dim}维度 Top 5\n"
                for i, item in enumerate(items[:5], 1):
                    name = item.get('name', '未知')
                    amount = item.get('amount', 0)
                    qty = item.get('quantity', 0)
                    summary += f"{i}. {name}: 金额 {amount:,.2f} 元, 数量 {qty:,}\n"
                summary += "\n"

        return summary