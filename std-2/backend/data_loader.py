# 数据加载模块
import pandas as pd
from datetime import datetime
from backend.config import DATA_FILE


def load_all_data():
    """加载所有Sheet数据"""
    try:
        xlsx = pd.ExcelFile(DATA_FILE)
        data = {}
        for sheet in xlsx.sheet_names:
            df = pd.read_excel(xlsx, sheet_name=sheet)
            # 处理日期字段
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]':
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
            data[sheet] = df.to_dict(orient='records')
        return data
    except Exception as e:
        print(f"加载数据错误: {e}")
        return {}


def load_data():
    """兼容旧接口，返回主数据"""
    data = load_all_data()
    if '批次信息表' in data:
        return data['批次信息表']
    return []


def get_stats():
    """获取统计数据 - 基于入库时间计算执行进度，配送率=配送数量/采购数量"""
    try:
        xlsx = pd.ExcelFile(DATA_FILE)

        # 读取各Sheet
        batch_info = pd.read_excel(xlsx, sheet_name='批次信息表')
        catalog = pd.read_excel(xlsx, sheet_name='批次目录信息表')
        contract = pd.read_excel(xlsx, sheet_name='批次合同信息表')
        purchase = pd.read_excel(xlsx, sheet_name='医疗机构采购表')

        # ========== 基础统计 ==========
        total_batches = len(batch_info)
        total_drugs = len(catalog)
        total_contracts = len(contract)
        total_purchases = len(purchase)

        # 医疗机构统计
        hospitals = purchase['医疗机构名称'].unique() if '医疗机构名称' in purchase.columns else []
        total_hospitals = len(hospitals)

        # 企业统计
        companies = set()
        if '申报企业' in contract.columns:
            companies.update(contract['申报企业'].dropna().unique())
        if '申报企业' in purchase.columns:
            companies.update(purchase['申报企业'].dropna().unique())
        if '配送企业' in purchase.columns:
            companies.update(purchase['配送企业'].dropna().unique())
        total_companies = len(companies)

        # ========== 采购量统计 ==========
        if '入库数量' in purchase.columns:
            total_purchase_qty = purchase['入库数量'].sum()
        else:
            total_purchase_qty = 0

        if '配送数量' in purchase.columns:
            total_delivery_qty = purchase['配送数量'].sum()
        else:
            total_delivery_qty = 0

        if '合同量' in contract.columns:
            total_contract_qty = contract['合同量'].sum()
        else:
            total_contract_qty = 0

        # 配送率 = 配送数量 / 采购数量
        delivery_rate = (total_delivery_qty / total_purchase_qty * 100) if total_purchase_qty > 0 else 0

        # ========== 执行进度统计（基于入库时间） ==========
        today = datetime.now().date()
        progress_data = []
        over_schedule = 0
        normal = 0
        behind = 0

        # 计算各批次执行进度
        for _, row in batch_info.iterrows():
            batch_name = row.get('批次名称', '未知批次')
            batch_code = row.get('批次编号', '')

            # 获取该批次的目录和合同
            batch_catalog = catalog[catalog['批次编号'] == batch_code] if '批次编号' in catalog.columns else pd.DataFrame()
            batch_contract = contract[contract['批次编号'] == batch_code] if '批次编号' in contract.columns else pd.DataFrame()

            # 该批次下的所有采购记录
            # 通过目录编号关联
            cat_codes = batch_catalog['目录编号'].tolist() if len(batch_catalog) > 0 else []
            batch_purchases = purchase[purchase['目录编号'].isin(cat_codes)] if '目录编号' in purchase.columns else pd.DataFrame()

            if '执行开始日期' in row and '执行结束日期' in row:
                start_date = pd.to_datetime(row['执行开始日期'], errors='coerce')
                end_date = pd.to_datetime(row['执行结束日期'], errors='coerce')

                if pd.notna(start_date) and pd.notna(end_date):
                    start = start_date.date()
                    end = end_date.date()
                    total_days = (end - start).days
                    elapsed_days = (today - start).days

                    # 序时进度 = 已过天数 / 总天数
                    schedule_progress = min(100, max(0, elapsed_days / total_days * 100)) if total_days > 0 else 0

                    # 实际进度 = 基于入库时间的入库量 / 合同总量
                    if '入库日期' in batch_purchases.columns and len(batch_purchases) > 0:
                        # 只统计已入库的
                        batch_purchases = batch_purchases.dropna(subset=['入库日期'])
                        actual_purchase = batch_purchases['入库数量'].sum() if '入库数量' in batch_purchases.columns else 0
                    else:
                        actual_purchase = 0

                    contract_qty = batch_contract['合同量'].sum() if '合同量' in batch_contract.columns and len(batch_contract) > 0 else 0
                    actual_progress = (actual_purchase / contract_qty * 100) if contract_qty > 0 else 0

                    # 进度状态判定
                    if actual_progress > schedule_progress * 1.1:
                        over_schedule += 1
                        status = "超序时"
                    elif actual_progress < schedule_progress * 0.9:
                        behind += 1
                        status = "落后"
                    else:
                        normal += 1
                        status = "正常"

                    progress_data.append({
                        'name': batch_name,
                        'schedule_progress': round(schedule_progress, 1),
                        'actual_progress': round(actual_progress, 1),
                        'contract_qty': int(contract_qty),
                        'actual_purchase': int(actual_purchase),
                        'start': start.strftime('%Y-%m-%d'),
                        'end': end.strftime('%Y-%m-%d'),
                        'elapsed': elapsed_days,
                        'total': total_days,
                        'status': status
                    })

        # ========== 医疗机构统计 ==========
        hospital_stats = {}
        if '医疗机构名称' in purchase.columns and '入库数量' in purchase.columns:
            hos_purchase = purchase.groupby('医疗机构名称').agg({
                '入库数量': 'sum',
                '配送数量': 'sum' if '配送数量' in purchase.columns else 'count'
            }).reset_index()
            hos_purchase['配送率'] = (hos_purchase['配送数量'] / hos_purchase['入库数量'] * 100).round(1)
            hospital_stats = hos_purchase.sort_values('入库数量', ascending=False).head(10).to_dict('records')

        # ========== 配送企业统计 ==========
        supplier_stats = {}
        if '配送企业' in purchase.columns and '配送数量' in purchase.columns:
            sup_stats = purchase.groupby('配送企业').agg({
                '配送数量': 'sum',
                '入库数量': 'sum'
            }).reset_index()
            sup_stats['配送率'] = (sup_stats['配送数量'] / sup_stats['入库数量'] * 100).round(1)
            supplier_stats = sup_stats.sort_values('配送数量', ascending=False).head(10).to_dict('records')

        # ========== 药品统计 ==========
        drug_stats = {}
        if '目录编号' in purchase.columns and '药品名称' in catalog.columns:
            # 按药品统计入库量
            drug_purchase = purchase.groupby('目录编号').agg({
                '入库数量': 'sum',
                '配送数量': 'sum' if '配送数量' in purchase.columns else 'count'
            }).reset_index()
            # 关联药品名称
            drug_purchase = drug_purchase.merge(catalog[['目录编号', '药品名称', '药品规格']], on='目录编号', how='left')
            drug_purchase['配送率'] = (drug_purchase['配送数量'] / drug_purchase['入库数量'] * 100).round(1)
            drug_stats = drug_purchase.sort_values('入库数量', ascending=False).head(10).to_dict('records')

        return {
            # 基础统计
            "total_batches": total_batches,
            "total_drugs": total_drugs,
            "total_contracts": total_contracts,
            "total_purchases": total_purchases,
            "total_hospitals": total_hospitals,
            "total_companies": total_companies,
            # 采购量统计
            "total_contract_qty": int(total_contract_qty),
            "total_purchase_qty": int(total_purchase_qty),
            "total_delivery_qty": int(total_delivery_qty),
            "delivery_rate": round(delivery_rate, 1),
            # 执行进度
            "over_schedule": over_schedule,
            "normal": normal,
            "behind": behind,
            "progress_data": progress_data,
            # 明细统计
            "hospital_stats": hospital_stats,
            "supplier_stats": supplier_stats,
            "drug_stats": drug_stats
        }
    except Exception as e:
        import traceback
        print(f"统计错误: {e}")
        traceback.print_exc()
        return {
            "total_batches": 0, "total_drugs": 0, "total_contracts": 0,
            "total_purchases": 0, "total_hospitals": 0, "total_companies": 0,
            "total_contract_qty": 0, "total_purchase_qty": 0, "total_delivery_qty": 0,
            "delivery_rate": 0, "over_schedule": 0, "normal": 0, "behind": 0,
            "progress_data": [], "hospital_stats": [], "supplier_stats": [], "drug_stats": []
        }


if __name__ == "__main__":
    import json
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    stats = get_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))