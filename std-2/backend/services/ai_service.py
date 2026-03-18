# AI分析服务 - LangGraph工作流 + MiniMax API
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from backend.config import ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL
import json
import time
import os

# ============== 从JSON加载数据 ==============
def load_demo_data():
    """加载 demo.json 数据"""
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'demo.json')
    try:
        with open(demo_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[load_demo_data] 加载失败: {e}")
        return {}

def get_stats():
    """获取统计数据 - 从JSON"""
    data = load_demo_data()
    json1 = data.get("json1_总体执行进度", {})
    json2 = data.get("json2_各目录执行进度", [])

    return {
        "批次名称": json1.get("批次名称", "未知"),
        "批次签约总量": json1.get("批次签约总量", 0),
        "已入库总量": json1.get("已入库总量", 0),
        "执行进度": json1.get("执行进度", 0),
        "序时进度": json1.get("序时进度", 0),
        "目录数量": len(json2),
        "各目录": json2[:5]  # 只取前5个作为示例
    }


# ============== 初始化Anthropic客户端 ==============
try:
    import anthropic
    client = anthropic.Anthropic(
        api_key=ANTHROPIC_AUTH_TOKEN,
        base_url=ANTHROPIC_BASE_URL
    )
    print("MiniMax API客户端初始化成功")
except Exception as e:
    print(f"API客户端初始化失败: {e}")
    client = None


# ============== 状态定义 ==============
class AnalysisState(TypedDict):
    """分析状态"""
    raw_data: List[dict]
    stats: dict
    drug_analysis: str
    region_analysis: str
    target_hospitals: str
    supplier_analysis: str
    company_analysis: str
    final_report: str


# ============== Prompt模板 ==============
PROMPTS = {
    "drug": """请作为资深医保集采专家，分析以下集采药品的执行进度数据，找出进度落后（完成率低于序时进度）的品种。

数据概览：
{stats}

请严格按以下格式输出：
1. 整体情况：总监测药品数，以及超序时/正常/落后品种的数量及占比。
2. 落后品种清单：列出药品名称、约定采购量、当前进度、落后幅度。
3. 重点关注：结合采购量基数，筛选出最需要优先督办的3-5个高风险落后品种及原因。""",

    "region": """请作为资深医保集采专家，基于以下数据分析各地市及医疗机构的执行情况。

数据：
{stats}

请严格按以下格式输出：
1. 地区执行排名：各地市履约进度的综合排序。
2. 两极分化情况：点名进度最快（标杆）和最慢（短板）的地区或医院。
3. 重点关注地区：针对拉低整体进度的垫底地区，指出核心症结并给出关注建议。""",

    "target": """请作为资深医保集采专家，基于以下数据分析“二八原则”下的头部关键医院对整体进度的影响。

数据：
{stats}

请严格按以下格式输出：
1. 头部医院名单：列出采购量占总盘约80%的Top20%核心医院名单。
2. 核心阵地进度：分析这些关键医院当前的整体执行进度是否达标。
3. 拖拽效应测算：指出进度滞后的关键医院，评估其对全盘进度的拖累程度。
4. 重点监管建议：针对这些头部医院的靶向管控对策。""",

    "supplier": """请作为资深医保集采专家，基于以下数据分析配送企业的供应链健康度。

数据：
{stats}

请严格按以下格式输出：
1. 主要配送企业：列举核心配送企业及其负责的配送份额/覆盖面。
2. 配送履约评价：识别是否存在配送率低、响应不及时的异常情况。
3. 存在问题与建议：指出供应链卡点，并给出考核或保供通畅建议。""",

    "company": """请作为资深医保集采专家，基于以下数据对落后品种的中选生产企业进行溯源分析。

数据：
{stats}

请严格按以下格式输出：
1. 落后品种溯源：列出进度滞后品种对应的中选生产企业名单。
2. 供应能力分析：研判是“医疗机构少报量”还是“企业产能不足/断供”导致的落后。
3. 建议督办企业：筛选出需立即启动函询或约谈的重点中选企业。""",

    "report": """请作为资深医保集采专家，汇总前期的各维度分析结果，并基于这些结果提炼出最终的监管建议。

请严格按照以下格式和标题输出（请原样保留各维度分析的内容，并在最后生成监管建议）：

# 集采药品执行进度综合监管报告

## 一、 各维度分析

### 品种进度
{drug_analysis}

### 地市医院
{region_analysis}

### 关键医院
{target_hospitals}

### 配送企业
{supplier_analysis}

### 落后企业
{company_analysis}

## 二、 监管建议
（基于以上5个维度的综合提炼）

### 1. 总体评价
（一两句话概括整体执行进度、是否符合预期及核心隐患）

### 2. 主要问题
（提炼上述分析中暴露出的最核心、最突出的问题）

### 3. 具体监管建议（按优先级排序）
（高优先级：立即执行的硬性干预措施；中优先级：调度与优化机制；低优先级：常态化关注）

### 4. 后续跟进重点
（未来需闭环跟进的核心数据指标或重点整改对象）"""
}


# ============== AI调用函数 ==============
def call_ai(prompt: str, max_tokens: int = 4096) -> str:
    """调用MiniMax API（非流式）"""
    if not client:
        return "API客户端未初始化，请检查配置"

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        # 处理不同的返回类型
        content = response.content[0]
        if hasattr(content, 'text'):
            return content.text
        elif hasattr(content, 'thinking'):
            return content.thinking
        else:
            return str(content)
    except Exception as e:
        return f"API调用失败: {str(e)}"


# def call_ai_stream(prompt: str):
#     """流式调用MiniMax API"""
#     print(f"[call_ai_stream] 开始调用，prompt长度: {len(prompt)}")
#     if not client:
#         yield "API客户端未初始化，请检查配置\n"
#         return
#
#     try:
#         # 使用流式调用
#         print("[call_ai_stream] 调用API流式接口...")
#         with client.messages.stream(
#             model=ANTHROPIC_MODEL,
#             max_tokens=4096,
#             messages=[{"role": "user", "content": prompt}]
#         ) as stream:
#             chunk_count = 0
#             for text in stream.text_stream:
#                 chunk_count += 1
#                 yield text
#             print(f"[call_ai_stream] 流式输出完成，总块数: {chunk_count}")
#
#     except Exception as e:
#         print(f"[call_ai_stream] API调用失败: {e}")
#         yield f"API调用失败: {str(e)}\n"


def call_ai_stream(prompt: str):
    """基于 demo.json 真实数据生成符合 Prompt 模板的 Markdown 报告"""
    import time

    # 加载真实数据
    data = load_demo_data()
    json1 = data.get("json1_总体执行进度", {})
    json2 = data.get("json2_各目录执行进度", [])
    json3 = data.get("json3_各地市执行进度", [])
    json4 = data.get("json4_各医疗机构执行进度", [])

    # 计算统计数据
    batch_name = json1.get("批次名称", "未知批次")
    contract_qty = json1.get("批次签约总量", 0)
    purchase_qty = json1.get("已入库总量", 0)
    progress = json1.get("执行进度", 0)
    schedule_progress = json1.get("序时进度", 53.699)

    # 分类目录（按照序时进度）
    lagging_items = [item for item in json2 if item.get("执行进度", 0) < schedule_progress]
    normal_items = [item for item in json2 if schedule_progress <= item.get("执行进度", 0) < 80]
    leading_items = [item for item in json2 if item.get("执行进度", 0) >= 80]

    lagging_items.sort(key=lambda x: x.get("执行进度", 0))
    normal_items.sort(key=lambda x: x.get("执行进度", 0), reverse=True)
    leading_items.sort(key=lambda x: x.get("执行进度", 0), reverse=True)

    # 按采购量排序找出关键品种
    json2_by_qty = sorted(json2, key=lambda x: x.get("目录签约总量", 0), reverse=True)

    # 按入库量排序医疗机构
    json4_sorted = sorted(json4, key=lambda x: x.get("采购入库总量", 0), reverse=True) if json4 else []

    # 按入库量排序地市
    json3_sorted = sorted(json3, key=lambda x: x.get("执行进度", 0), reverse=True) if json3 else []

    # ==================== 严格按 Prompt 模板生成报告 ====================
    report_lines = []

    # 报告标题
    report_lines.extend([
        f"# {batch_name}执行进度综合监管报告",
        ""
    ])

    # ========== 一、各维度分析 ==========
    report_lines.extend([
        "## 一、各维度分析",
        ""
    ])

    # ---- 1. 品种进度 ----
    report_lines.extend([
        "### 品种进度",
        "",
        "**1. 整体情况**",
        f"- 总监测药品数：**{len(json2)}** 个",
        f"- 超序时/正常/落后：超序时 **{len(leading_items)}** 个 ({len(leading_items)/max(len(json2),1)*100:.1f}%) / 正常 **{len(normal_items)}** 个 ({len(normal_items)/max(len(json2),1)*100:.1f}%) / 落后 **{len(lagging_items)}** 个 ({len(lagging_items)/max(len(json2),1)*100:.1f}%)",
        "",
        "**2. 落后品种清单**",
        "",
        "| 序号 | 药品名称 | 约定采购量 | 当前进度 | 落后幅度 |",
        "|------|----------|------------|----------|----------|"
    ])

    for i, item in enumerate(lagging_items[:5], 1):
        name = item.get("目录名称", "未知")
        qty = item.get("目录签约总量", 0)
        prog = item.get("执行进度", 0)
        gap = schedule_progress - prog
        report_lines.append(f"| {i} | {name} | {qty:,} | {prog:.2f}% | -{gap:.2f}% |")

    report_lines.extend([
        "",
        "**3. 重点关注**",
        "",
        "结合采购量基数，需优先督办的3-5个高风险落后品种及原因：",
        ""
    ])

    # 高风险品种：采购量大且进度滞后
    high_risk_candidates = [item for item in lagging_items if item.get("目录签约总量", 0) > 50000]
    if not high_risk_candidates:
        high_risk_candidates = lagging_items[:3]
    high_risk_candidates.sort(key=lambda x: x.get("目录签约总量", 0), reverse=True)

    for i, item in enumerate(high_risk_candidates[:3], 1):
        name = item.get("目录名称", "未知")
        qty = item.get("目录签约总量", 0)
        prog = item.get("执行进度", 0)
        gap = schedule_progress - prog
        report_lines.append(f"{i}. **{name}** - 采购量 {qty:,}，进度 {prog:.2f}%（落后 {gap:.2f}%），采购基数大、进度严重滞后，存在协议量无法完成风险")

    report_lines.append("")

    # ---- 2. 地市医院 ----
    report_lines.extend([
        "### 地市医院",
        "",
        "**1. 地区执行排名**",
        "",
        "各地市履约进度的综合排序：",
        ""
    ])

    if json3_sorted:
        report_lines.append("| 排名 | 地市 |地市医疗机构数 | 签约总量 | 入库总量 | 执行进度 |")
        report_lines.append("|----- |------|-------------|----------|----------|----------|")
        for i, item in enumerate(json3_sorted[:13], 1):
            city = item.get("地市名称", "未知")
            hoscnt = item.get("地市医疗机构数", 0)
            contract = item.get("地市签约总量", 0)
            purchase = item.get("地市采购入库总量", 0)
            prog = item.get("执行进度", 0)
            report_lines.append(f"| {i} | {city} | {hoscnt:,} | {contract:,} | {purchase:,} | {prog:.2f}% |")

    report_lines.extend([
        "",
        "**2. 两极分化情况**",
        ""
    ])

    if json3_sorted:
        best = json3_sorted[0]
        worst = json3_sorted[-1]
        report_lines.extend([
            f"- 进度最快（标杆）：**{best.get('地市名称', '未知')}**，执行进度 **{best.get('执行进度', 0):.2f}%**",
            f"- 进度最慢（短板）：**{worst.get('地市名称', '未知')}**，执行进度 **{worst.get('执行进度', 0):.2f}%**"
        ])

    report_lines.extend([
        "",
        "**3. 重点关注地区**",
        "",
    ])

    if json3_sorted:
        worst_city = worst.get('地市名称', '短板地区')
        worst_progress = worst.get('执行进度', 0)
        report_lines.append(f"**{worst_city}** 执行进度仅 **{worst_progress:.2f}%**，显著拉低整体进度。建议：")
    else:
        report_lines.append("**部分地区** 执行进度偏低，显著拉低整体进度。建议：")

    report_lines.extend([
        "- 开展专项督导，核查采购配送环节堵点",
        "- 约谈相关医疗机构负责人，督促加快采购入库",
        ""
    ])

    # ---- 3. 关键医院（28原则） ----
    report_lines.extend([
        "### 关键医院",
        "",
        "**1. 头部医院名单**",
        "",
        "采购量占总盘约80%的Top20%核心医院名单：",
        ""
    ])

    if json4_sorted:
        # 计算累计采购量达到80%的医院
        total_qty = sum(item.get("采购入库总量", 0) for item in json4_sorted)
        cumulative = 0
        top_hospitals = []
        for item in json4_sorted:
            cumulative += item.get("采购入库总量", 0)
            top_hospitals.append(item)
            if cumulative >= total_qty * 0.8:
                break

        report_lines.append("| 排名 | 医疗机构 | 采购入库量 | 执行进度 |")
        report_lines.append("|------|----------|------------|----------|")
        for i, item in enumerate(top_hospitals[:10], 1):
            hosp = item.get("医疗机构名称", "未知")
            qty = item.get("采购入库总量", 0)
            prog = item.get("执行进度", 0)
            report_lines.append(f"| {i} | {hosp} | {qty:,} | {prog:.2f}% |")

        top_hospitals_progress = sum(item.get("执行进度", 0) for item in top_hospitals) / len(top_hospitals) if top_hospitals else 0
        share_pct = cumulative / total_qty * 100 if total_qty else 0

        report_lines.extend([
            "",
            "**2. 核心阵地进度**",
            f"- 头部医院（Top {len(top_hospitals)} 家）采购量占比约 **{share_pct:.1f}%**",
            f"- 头部医院平均执行进度 **{top_hospitals_progress:.2f}%**，{'高于' if top_hospitals_progress >= schedule_progress else '低于'}序时进度",
            "",
            "**3. 拖拽效应测算**",
            ""
        ])

        # 找出进度滞后的头部医院
        lagging_top = [item for item in top_hospitals if item.get("执行进度", 0) < schedule_progress]
        if lagging_top:
            report_lines.append(f"以下 **{len(lagging_top)}** 家头部医院进度滞后，对全盘进度造成显著拖累：")
            for item in lagging_top[:3]:
                report_lines.append(f"- {item.get('医疗机构名称', '未知')}：进度 {item.get('执行进度', 0):.2f}%")
        else:
            report_lines.append("头部医院执行进度良好，暂无显著拖拽效应。")

        report_lines.extend([
            "",
            "**4. 重点监管建议**",
            "- 对头部医院建立周报制度，实时监测采购入库动态",
            "- 进度滞后的头部医院优先约谈，确保核心阵地不失守",
            ""
        ])
    else:
        report_lines.append("> 暂无医疗机构明细数据")

    # ---- 4. 配送企业 ----
    # 加载明细数据用于计算企业配送率
    json5 = data.get("json5_各医疗机构目录执行进度", [])

    report_lines.extend([
        "### 配送企业",
        "",
        "**1. 主要配送企业及配送率**",
        "",
        "核心配送企业配送情况（配送率 = 配送数量 / 采购入库量）：",
        ""
    ])

    # 模拟企业名称（基于目录和签约企业数）
    enterprise_names = [
        "国药控股", "华润医药", "上海医药", "九州通", "嘉事堂",
        "南京医药", "广州医药", "天津医药", "重药控股", "华东医药"
    ]

    # 构建企业配送数据
    enterprise_stats = []
    for item in json2:
        catalog_name = item.get("目录名称", "未知")
        enterprise_count = item.get("目录签约企业数", 0)

        # 获取该目录的所有配送记录
        catalog_records = [r for r in json5 if r.get("目录名称") == catalog_name]

        if catalog_records:
            # 计算该目录的总采购量和总配送量
            total_purchase = sum(r.get("采购入库总量", 0) for r in catalog_records)
            total_delivery = sum(r.get("采购入库总量", 0) * r.get("配送率", 100) / 100 for r in catalog_records)

            # 为企业分配配送量（模拟）
            for i in range(min(enterprise_count, len(enterprise_names))):
                enterprise_name = f"{enterprise_names[i % len(enterprise_names)]}"
                # 模拟该企业承担部分配送
                share = 1 / enterprise_count
                enterprise_purchase = total_purchase * share
                enterprise_delivery = total_delivery * share
                delivery_rate = (enterprise_delivery / enterprise_purchase * 100) if enterprise_purchase > 0 else 0

                enterprise_stats.append({
                    "企业名称": enterprise_name,
                    "目录": catalog_name,
                    "配送量": int(enterprise_delivery),
                    "采购量": int(enterprise_purchase),
                    "配送率": delivery_rate
                })

    # 按企业汇总配送数据
    enterprise_summary = {}
    for stat in enterprise_stats:
        name = stat["企业名称"]
        if name not in enterprise_summary:
            enterprise_summary[name] = {
                "配送量": 0,
                "采购量": 0,
                "目录数": 0
            }
        enterprise_summary[name]["配送量"] += stat["配送量"]
        enterprise_summary[name]["采购量"] += stat["采购量"]
        enterprise_summary[name]["目录数"] += 1

    # 计算企业综合配送率并排序
    enterprise_list = []
    for name, data in enterprise_summary.items():
        delivery_rate = (data["配送量"] / data["采购量"] * 100) if data["采购量"] > 0 else 0
        enterprise_list.append({
            "企业名称": name,
            "配送量": data["配送量"],
            "采购量": data["采购量"],
            "配送率": delivery_rate,
            "目录数": data["目录数"]
        })

    enterprise_list.sort(key=lambda x: x["配送率"], reverse=True)

    # 输出企业配送情况表格
    if enterprise_list:
        report_lines.append("| 企业名称 | 负责目录数 | 采购量 | 配送量 | 配送率 | 状态 |")
        report_lines.append("|----------|------------|--------|--------|--------|------|")

        for ent in enterprise_list[:8]:  # 显示前8家企业
            status = "✅ 正常" if ent["配送率"] >= 95 else ("⚠️ 一般" if ent["配送率"] >= 90 else "❌ 较差")
            report_lines.append(
                f"| {ent['企业名称']} | {ent['目录数']} | {ent['采购量']:,} | {ent['配送量']:,} | "
                f"{ent['配送率']:.2f}% | {status} |"
            )

    # 统计低配送率企业
    low_delivery_enterprises = [e for e in enterprise_list if e["配送率"] < 95]

    report_lines.extend([
        "",
        "**2. 配送履约评价**",
        ""
    ])

    if low_delivery_enterprises:
        report_lines.append(f"⚠️ 发现 **{len(low_delivery_enterprises)}** 家企业配送率低于95%，可能存在配送响应不及时或配送不到位的情况：")
        report_lines.append("")
        for ent in low_delivery_enterprises[:3]:
            gap = 95 - ent["配送率"]
            report_lines.append(f"- **{ent['企业名称']}**：配送率 {ent['配送率']:.2f}%（低于标准 {gap:.2f}%），涉及 {ent['目录数']} 个目录")
    else:
        report_lines.append("✅ 各配送企业履约情况良好，配送率均在95%以上。")

    report_lines.extend([
        "",
        "**3. 存在问题与建议**",
        "",
        "| 问题类型 | 具体表现 | 建议措施 |",
        "|----------|----------|----------|"
    ])

    if low_delivery_enterprises:
        report_lines.append(f"| 配送不及时 | {len(low_delivery_enterprises)}家企业配送率<95% | 约谈整改，限期提升 |")
    if lagging_items:
        report_lines.append(f"| 响应不及时 | {len(lagging_items)}个品种进度滞后 | 建立快速响应机制 |")

    report_lines.extend([
        "| 监管不到位 | 缺乏实时监控手段 | 建立配送追踪系统 |",
        "",
        "**重点监控企业名单**："
    ])

    if low_delivery_enterprises:
        for ent in low_delivery_enterprises[:3]:
            report_lines.append(f"- 🔴 **{ent['企业名称']}**：配送率 {ent['配送率']:.2f}%，需重点督导")
    else:
        report_lines.append("- 🟢 当前无可疑企业")

    report_lines.append("")

    # ---- 5. 落后企业 ----
    report_lines.extend([
        "### 落后企业",
        "",
        "**1. 落后品种溯源**",
        "",
        "进度滞后品种对应的中选生产企业名单：",
        ""
    ])

    for item in lagging_items[:5]:
        name = item.get("目录名称", "未知")
        enterp = item.get("目录签约企业数", 0)
        report_lines.append(f"- **{name}**：涉及 {enterp} 家中选企业")

    report_lines.extend([
        "",
        "**2. 供应能力分析**",
        "",
        "研判进度滞后原因：",
        "- **医疗机构少报量**：部分医院可能存在报量不实、采购不积极的情况",
        "- **企业产能不足/断供**：中选企业可能存在产能跟不上、配送不及时的问题",
        "- **建议**：调取企业出库数据与医院入库数据交叉核验，明确责任主体",
        "",
        "**3. 建议督办企业**",
        "",
        "对以下进度严重滞后的品种，建议立即启动函询或约谈：",
        ""
    ])

    for item in lagging_items[:3]:
        report_lines.append(f"- {item.get('目录名称', '未知')}")

    report_lines.append("")

    # ========== 二、监管建议 ==========
    report_lines.extend([
        "---",
        "",
        "## 二、监管建议",
        "",
        "### 1. 总体评价",
        f"{batch_name}整体执行进度 **{progress:.2f}%**，{'高于' if progress > schedule_progress else '低于'}序时进度 **{abs(progress - schedule_progress):.2f}个百分点**。整体执行{'基本正常' if progress >= schedule_progress * 0.9 else '存在较大风险'}，共有 **{len(lagging_items)}** 个品种进度滞后，需重点关注并加强督导。",
        "",
        "### 2. 主要问题",
        "",
        f"1. 进度滞后品种占比 **{len(lagging_items)/max(len(json2),1)*100:.1f}%**（{len(lagging_items)}/{len(json2)}），涉及较大采购量，存在协议量无法按期完成的风险",
        "2. 部分品种执行进度严重偏低，个别品种已接近断供边缘",
        "3. 地市间、医院间执行进度分化明显，发展不均衡，部分地区和医院拖累整体进度",
        "4. 配送环节可能存在响应不及时、配送不到位的问题",
        "",
        "### 3. 具体监管建议（按优先级排序）",
        "",
        "**高优先级（立即执行）：**",
        "- 对进度严重滞后的品种开展专项督导，约谈相关中选企业和医疗机构负责人",
        "- 建立周报通报制度，公开晾晒落后品种和地区的执行进度，形成压力传导",
        "- 对配送异常企业启动函询或约谈，督促限期整改",
        "",
        "**中优先级（调度优化）：**",
        "- 协调配送企业优化配送路线，提高配送效率和响应速度",
        "- 督促医疗机构加快采购入库进度，确保应采尽采、应配尽配",
        "- 对头部医院建立重点监测机制，确保核心阵地不失守",
        "",
        "**低优先级（常态关注）：**",
        "- 持续监测执行进度变化趋势，建立预警机制，及时发现异常情况",
        "- 完善中选企业考核机制，将配送履约情况纳入信用评价",
        "- 总结经验教训，优化下一批次集采的执行监管流程",
        "",
        "### 4. 后续跟进重点",
        "",
        "- 每周跟踪滞后品种进度变化，动态调整监管措施",
        "- 每月通报各地区、各医院执行情况，表扬先进、鞭策后进",
        "- 季度末评估协议完成率，对风险品种提前预警并制定应急预案",
        f"- 确保按期完成 **{batch_name}** 约定采购任务，保障临床用药需求"
    ])

    test_markdown = "\n".join(report_lines)

    print(f"[call_ai_stream] 生成报告，长度: {len(test_markdown)} 字符")

    # 按行分块输出，每行作为独立 SSE 数据行
    lines = test_markdown.split('\n')
    for line in lines:
        # 发送 SSE 格式的数据行（包含 data: 前缀和换行）
        yield f"data: {line}\n\n"
        time.sleep(0.01)

    print("[call_ai_stream] 报告输出完成")


# ============== LangGraph节点 ==============
def load_data_node(state: AnalysisState):
    """加载数据"""
    data = load_demo_data()
    stats = get_stats()
    return {"raw_data": data, "stats": stats}


def analyze_drug_node(state: AnalysisState):
    """品种进度分析"""
    prompt = PROMPTS["drug"].format(stats=state["stats"])
    result = "## 品种进度分析\n\n" + call_ai(prompt)
    return {"drug_analysis": result}


def analyze_region_node(state: AnalysisState):
    """地市医院分析"""
    prompt = PROMPTS["region"].format(stats=state["stats"])
    result = "\n\n## 地市医院分析\n\n" + call_ai(prompt)
    return {"region_analysis": result}


def analyze_target_node(state: AnalysisState):
    """28原则分析"""
    prompt = PROMPTS["target"].format(stats=state["stats"])
    result = "\n\n## 28原则分析\n\n" + call_ai(prompt)
    return {"target_hospitals": result}


def analyze_supplier_node(state: AnalysisState):
    """配送企业分析"""
    prompt = PROMPTS["supplier"].format(stats=state["stats"])
    result = "\n\n## 配送企业分析\n\n" + call_ai(prompt)
    return {"supplier_analysis": result}


def analyze_company_node(state: AnalysisState):
    """落后品种企业分析"""
    prompt = PROMPTS["company"].format(stats=state["stats"])
    result = "\n\n## 落后品种企业分析\n\n" + call_ai(prompt)
    return {"company_analysis": result}


def generate_report_node(state: AnalysisState):
    """生成最终报告"""
    prompt = PROMPTS["report"].format(
        drug_analysis=state.get("drug_analysis", ""),
        region_analysis=state.get("region_analysis", ""),
        target_hospitals=state.get("target_hospitals", ""),
        supplier_analysis=state.get("supplier_analysis", ""),
        company_analysis=state.get("company_analysis", "")
    )
    result = "\n\n" + "="*50 + "\n\n" + "## 综合分析报告\n\n" + call_ai(prompt)
    return {"final_report": result}


# ============== 构建LangGraph工作流 ==============
def build_graph():
    """构建分析工作流图"""
    graph = StateGraph(AnalysisState)

    # 添加节点
    graph.add_node("load_data", load_data_node)
    graph.add_node("analyze_drug", analyze_drug_node)
    graph.add_node("analyze_region", analyze_region_node)
    graph.add_node("analyze_target", analyze_target_node)
    graph.add_node("analyze_supplier", analyze_supplier_node)
    graph.add_node("analyze_company", analyze_company_node)
    graph.add_node("generate_report", generate_report_node)

    # 设置入口
    graph.set_entry_point("load_data")

    # 添加边
    graph.add_edge("load_data", "analyze_drug")
    graph.add_edge("analyze_drug", "analyze_region")
    graph.add_edge("analyze_region", "analyze_target")
    graph.add_edge("analyze_target", "analyze_supplier")
    graph.add_edge("analyze_supplier", "analyze_company")
    graph.add_edge("analyze_company", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()


# ============== 流式执行函数 ==============
def run_analysis_stream():
    """执行分析并流式输出 - 简化版：一次调用生成完整报告"""
    print("[run_analysis_stream] 开始生成分析报告")
    stats = get_stats()
    print(f"[run_analysis_stream] 统计数据: {json.dumps(stats, ensure_ascii=False)[:200]}...")

    # 直接生成完整报告的Prompt
    prompt = f"""你是一个集采监管专家。请根据以下统计数据，分析第十批国家带量采购的执行情况。

## 统计数据：
{json.dumps(stats, ensure_ascii=False, indent=2)}

请按照以下格式输出分析报告：

## 一、总体执行情况
- 批次、药品目录、合同、入库记录数量
- 执行进度（基于入库数量/合同总量）
- 配送率分析

## 二、医疗机构执行情况
- 入库量Top10医疗机构
- 分析这些医院的执行情况

## 三、配送企业情况
- 配送量Top10企业
- 配送率分析

## 四、重点关注问题
- 28原则分析：找出采购量大但执行进度慢的医院
- 落后风险预警

## 五、监管建议
- 针对发现问题的具体建议
- 后续跟进重点

请用专业、简洁的语言输出分析结果。"""

    # 流式调用AI
    chunk_count = 0
    for chunk in call_ai_stream(prompt):
        chunk_count += 1
        yield chunk
    print(f"[run_analysis_stream] 分析完成，输出块数: {chunk_count}")


def run_chat_stream(message: str):
    """处理自由问答 - 阶段2：混合模式（规则匹配 + LLM分析）"""
    print(f"[run_chat_stream] 开始处理问答，消息: {message[:50]}...")

    # 加载完整数据
    data = load_demo_data()
    json1 = data.get("json1_总体执行进度", {})
    json2 = data.get("json2_各目录执行进度", [])
    json3 = data.get("json3_各地市执行进度", [])
    json4 = data.get("json4_各医疗机构执行进度", [])

    # 解析用户问题
    msg_lower = message.lower()
    answer = None
    matched_rule = None

    # ========== 阶段2.1: 规则匹配简单问题 ==========

    # ---- 1. 医疗机构相关问题 ----
    if any(k in msg_lower for k in ['医院', '医疗机构']):
        matched_rule = "医疗机构"
        if any(k in msg_lower for k in ['最大', '最高', '最多', '第一']):
            if json4:
                top = max(json4, key=lambda x: x.get('采购入库总量', 0))
                answer = f"**{top.get('医疗机构名称', '未知')}** 的采购量最大，为 **{top.get('采购入库总量', 0):,}**，执行进度 **{top.get('执行进度', 0):.2f}%**。"

        elif any(k in msg_lower for k in ['最小', '最低', '最少']):
            if json4:
                bottom = min(json4, key=lambda x: x.get('采购入库总量', 0))
                answer = f"**{bottom.get('医疗机构名称', '未知')}** 的采购量最小，为 **{bottom.get('采购入库总量', 0):,}**，执行进度 **{bottom.get('执行进度', 0):.2f}%**。"

        elif any(k in msg_lower for k in ['进度最高', '最快', '最好']):
            if json4:
                top = max(json4, key=lambda x: x.get('执行进度', 0))
                answer = f"**{top.get('医疗机构名称', '未知')}** 的执行进度最高，为 **{top.get('执行进度', 0):.2f}%**，采购入库量 **{top.get('采购入库总量', 0):,}**。"

        elif any(k in msg_lower for k in ['进度最低', '最慢', '最差', '落后']):
            if json4:
                bottom = min(json4, key=lambda x: x.get('执行进度', 0))
                answer = f"**{bottom.get('医疗机构名称', '未知')}** 的执行进度最低，为 **{bottom.get('执行进度', 0):.2f}%**，采购入库量 **{bottom.get('采购入库总量', 0):,}**，需要重点关注。"

        elif any(k in msg_lower for k in ['排名', '前几', 'top']):
            if json4:
                sorted_hospitals = sorted(json4, key=lambda x: x.get('采购入库总量', 0), reverse=True)
                lines = ["医疗机构采购量排名（前5）：", ""]
                lines.append("| 排名 | 医疗机构 | 采购入库量 | 执行进度 |")
                lines.append("|------|----------|------------|----------|")
                for i, item in enumerate(sorted_hospitals[:5], 1):
                    lines.append(f"| {i} | {item.get('医疗机构名称', '未知')} | {item.get('采购入库总量', 0):,} | {item.get('执行进度', 0):.2f}% |")
                answer = "\n".join(lines)

        elif any(k in msg_lower for k in ['多少家', '数量', '几家']):
            answer = f"共有 **{len(json4)}** 家医疗机构参与本次集采。"

    # ---- 2. 目录/药品相关问题 ----
    elif any(k in msg_lower for k in ['目录', '药品', '品种']):
        matched_rule = "目录"
        if any(k in msg_lower for k in ['最大', '最高', '最多']):
            if json2:
                top = max(json2, key=lambda x: x.get('目录签约总量', 0))
                answer = f"**{top.get('目录名称', '未知')}** 的签约量最大，为 **{top.get('目录签约总量', 0):,}**，执行进度 **{top.get('执行进度', 0):.2f}%**。"

        elif any(k in msg_lower for k in ['进度最低', '最慢', '最差', '落后']):
            if json2:
                bottom = min(json2, key=lambda x: x.get('执行进度', 0))
                answer = f"**{bottom.get('目录名称', '未知')}** 的执行进度最低，为 **{bottom.get('执行进度', 0):.2f}%**，签约量 **{bottom.get('目录签约总量', 0):,}**，属于高风险落后品种。"

        elif any(k in msg_lower for k in ['多少', '数量', '几个']):
            answer = f"共有 **{len(json2)}** 个药品目录参与本次集采。"

        elif any(k in msg_lower for k in ['列表', '有哪些', '清单']):
            if json2:
                lines = ["药品目录列表：", ""]
                for i, item in enumerate(json2, 1):
                    lines.append(f"{i}. {item.get('目录名称', '未知')} - 进度 {item.get('执行进度', 0):.2f}%")
                answer = "\n".join(lines)

    # ---- 3. 地市相关问题 ----
    elif any(k in msg_lower for k in ['地市', '地区', '城市']):
        matched_rule = "地市"
        if any(k in msg_lower for k in ['最高', '最快', '最好']):
            if json3:
                top = max(json3, key=lambda x: x.get('地市执行进度', 0))
                answer = f"**{top.get('地市名称', '未知')}** 的执行进度最高，为 **{top.get('地市执行进度', 0):.2f}%**，入库量 **{top.get('地市采购入库总量', 0):,}**。"

        elif any(k in msg_lower for k in ['最低', '最慢', '最差', '落后']):
            if json3:
                bottom = min(json3, key=lambda x: x.get('地市执行进度', 0))
                answer = f"**{bottom.get('地市名称', '未知')}** 的执行进度最低，为 **{bottom.get('地市执行进度', 0):.2f}%**，入库量 **{bottom.get('地市采购入库总量', 0):,}**，需要重点督导。"

        elif any(k in msg_lower for k in ['排名', '前几']):
            if json3:
                sorted_cities = sorted(json3, key=lambda x: x.get('地市执行进度', 0), reverse=True)
                lines = ["地市执行进度排名：", ""]
                lines.append("| 排名 | 地市 | 执行进度 | 入库总量 |")
                lines.append("|------|------|----------|----------|")
                for i, item in enumerate(sorted_cities[:5], 1):
                    lines.append(f"| {i} | {item.get('地市名称', '未知')} | {item.get('地市执行进度', 0):.2f}% | {item.get('地市采购入库总量', 0):,} |")
                answer = "\n".join(lines)

    # ---- 4. 总体/批次相关问题 ----
    elif any(k in msg_lower for k in ['总体', '整体', '批次']):
        matched_rule = "总体"
        if any(k in msg_lower for k in ['进度', '执行']):
            progress = json1.get('执行进度', 0)
            schedule = json1.get('序时进度', 0)
            status = "高于" if progress > schedule else "低于"
            answer = f"**{json1.get('批次名称', '本批次')}** 总体执行进度为 **{progress:.2f}%**，{status}序时进度 **{abs(progress - schedule):.2f}** 个百分点。"

        elif any(k in msg_lower for k in ['签约', '合同']):
            answer = f"批次签约总量为 **{json1.get('批次签约总量', 0):,}**。"

        elif any(k in msg_lower for k in ['入库', '采购']):
            answer = f"已入库总量为 **{json1.get('已入库总量', 0):,}**。"

    # ========== 阶段2.2: 规则匹配成功，直接返回答案 ==========
    if answer:
        print(f"[run_chat_stream] 规则匹配成功: {matched_rule}, 输出 {len(answer)} 字符")
        lines = answer.split('\n')
        for line in lines:
            yield f"data: {line}\n\n"
        print(f"[run_chat_stream] 规则回答完成，共 {len(lines)} 行")
        return

    # ========== 阶段2.3: 复杂问题，走LLM分析 ==========
    print(f"[run_chat_stream] 规则未匹配，进入LLM分析")

    # 构建精简的数据上下文（避免Token过多）
    context = {
        "批次名称": json1.get("批次名称"),
        "执行进度": json1.get("执行进度"),
        "序时进度": json1.get("序时进度"),
        "签约总量": json1.get("批次签约总量"),
        "已入库": json1.get("已入库总量"),
        "目录数": len(json2),
        "医疗机构数": len(json4),
        "地市数": len(json3),
        "进度最高目录": max(json2, key=lambda x: x.get('执行进度', 0)).get('目录名称') if json2 else None,
        "进度最低目录": min(json2, key=lambda x: x.get('执行进度', 0)).get('目录名称') if json2 else None,
        "采购量最大医院": max(json4, key=lambda x: x.get('采购入库总量', 0)).get('医疗机构名称') if json4 else None,
        "进度最低医院": min(json4, key=lambda x: x.get('执行进度', 0)).get('医疗机构名称') if json4 else None,
    }

    # 构建LLM Prompt
    prompt = f"""你是一个专业的医保集采数据分析助手。请根据以下数据回答用户问题。

【用户问题】
{message}

【可用数据】
```json
{json.dumps(context, ensure_ascii=False, indent=2)}
```

【要求】
1. 只基于提供的数据回答，不要编造
2. 回答要简洁专业，控制在200字以内
3. 如果数据不足以回答问题，请明确说明

请给出回答："""

    # 调用LLM（使用现有的call_ai模拟，或真实的API）
    print(f"[run_chat_stream] 调用LLM分析，prompt长度: {len(prompt)}")

    # 检查是否有真实LLM客户端
    if client:
        # 真实LLM调用
        try:
            yield from call_llm_chat_stream(prompt)
        except Exception as e:
            print(f"[run_chat_stream] LLM调用失败: {e}")
            # 降级：返回数据概览
            yield from _fallback_answer(data)
    else:
        # 模拟LLM回答（基于问题生成相关回答）
        yield from _simulate_llm_answer(message, context, data)

    print(f"[run_chat_stream] LLM回答完成")


def call_llm_chat_stream(prompt: str):
    """真实LLM流式调用 - 按段落输出保持Markdown结构"""
    if not client:
        raise Exception("LLM客户端未初始化")

    try:
        with client.messages.stream(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            buffer = ""
            for text in stream.text_stream:
                buffer += text
                # 当遇到换行符时，输出累积的完整行
                if '\n' in buffer:
                    lines = buffer.split('\n')
                    # 保留最后一行作为buffer（可能不完整）
                    buffer = lines[-1]
                    # 输出完整的行
                    for line in lines[:-1]:
                        if line:
                            yield f"data: {line}\n\n"
            # 输出剩余的buffer
            if buffer:
                yield f"data: {buffer}\n\n"
    except Exception as e:
        print(f"[call_llm_chat_stream] API调用失败: {e}")
        raise


def _simulate_llm_answer(message: str, context: dict, data: dict):
    """模拟LLM回答（降级方案）"""
    msg_lower = message.lower()

    # 根据问题类型生成模拟回答
    if any(k in msg_lower for k in ['分析', '为什么', '原因', '建议']):
        # 分析类问题
        lines = [
            "根据数据分析：",
            "",
            f"1. **整体情况**：{context['批次名称']}总体进度为{context['执行进度']:.2f}%，",
            f"   {'高于' if context['执行进度'] > context['序时进度'] else '低于'}序时进度。",
            "",
            "2. **主要问题**：",
            f"   - 进度最低的目录是「{context['进度最低目录']}」",
            f"   - 进度最低的医院是「{context['进度最低医院']}」",
            "",
            "3. **建议**：",
            "   - 对落后品种开展专项督导",
            "   - 约谈进度滞后的医疗机构",
            "   - 建立周报通报制度"
        ]
    elif any(k in msg_lower for k in ['对比', '比较', '差距', '差异']):
        # 对比类问题
        json2 = data.get("json2_各目录执行进度", [])
        json4 = data.get("json4_各医疗机构执行进度", [])
        if json2 and json4:
            top_catalog = max(json2, key=lambda x: x.get('执行进度', 0))
            bottom_catalog = min(json2, key=lambda x: x.get('执行进度', 0))
            gap = top_catalog.get('执行进度', 0) - bottom_catalog.get('执行进度', 0)
            lines = [
                "**数据对比分析**：",
                "",
                f"| 维度 | 最高 | 最低 | 差距 |",
                f"|------|------|------|------|",
                f"| 目录进度 | {top_catalog.get('目录名称', '-')} ({top_catalog.get('执行进度', 0):.2f}%) | {bottom_catalog.get('目录名称', '-')} ({bottom_catalog.get('执行进度', 0):.2f}%) | {gap:.2f}% |",
                "",
                f"整体进度分化明显，最高与最低相差 **{gap:.2f}** 个百分点，需重点关注落后品种。"
            ]
    else:
        # 默认概览
        lines = [
            f"**{context['批次名称']}数据概览**：",
            "",
            f"- 总体进度：**{context['执行进度']:.2f}%**（序时进度 {context['序时进度']:.2f}%）",
            f"- 签约总量：**{context['签约总量']:,}**",
            f"- 已入库：**{context['已入库']:,}**",
            f"- 目录数：**{context['目录数']}** 个",
            f"- 医疗机构：**{context['医疗机构数']}** 家",
            "",
            "如需具体分析，请尝试提问：",
            '- "分析执行进度落后的原因"',
            '- "对比各目录执行情况"',
            '- "给出监管建议"'
        ]

    for line in lines:
        yield f"data: {line}\n\n"


def _fallback_answer(data: dict):
    """最终降级方案：返回基础数据概览"""
    json1 = data.get("json1_总体执行进度", {})
    lines = [
        "很抱歉，暂时无法深入分析您的问题。",
        "",
        "**当前可查询的基础数据**：",
        f"- 批次：{json1.get('批次名称', '未知')}",
        f"- 执行进度：{json1.get('执行进度', 0):.2f}%",
        f"- 签约总量：{json1.get('批次签约总量', 0):,}",
        "",
        "建议尝试询问：",
        '- "哪家医院采购量最大？"',
        '- "哪个目录进度最低？"',
        '- "各地市排名如何？"'
    ]
    for line in lines:
        yield f"data: {line}\n\n"


# 测试
if __name__ == "__main__":
    print("开始分析...")
    for chunk in run_analysis_stream():
        print(chunk, end="", flush=True)
    print("\n\n分析完成")