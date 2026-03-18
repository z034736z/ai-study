# Flask 主应用
from flask import Flask, jsonify, Response, stream_with_context, request, render_template, send_file
from flask_cors import CORS
import json
import sys
import os
from io import BytesIO
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import HOST, PORT, DEBUG

app = Flask(__name__, template_folder='.')
CORS(app)

# 加载 demo.json 数据
def load_demo_data():
    """加载 demo.json 数据"""
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'demo.json')
    print(f"[load_demo_data] 尝试加载文件: {demo_path}")
    try:
        with open(demo_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            json1 = data.get("json1_总体执行进度", {})
            json2 = data.get("json2_各目录执行进度", [])
            print(f"[load_demo_data] 加载成功! json1批次: {json1.get('批次名称', 'N/A')}, json2目录数: {len(json2)}")
            return data
    except FileNotFoundError as e:
        print(f"[load_demo_data] 错误: 文件未找到 - {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[load_demo_data] 错误: JSON解析失败 - {e}")
        return {}
    except Exception as e:
        print(f"[load_demo_data] 错误: {e}")
        return {}


@app.route('/')
def index():
    """首页 - 渲染 dl_ai.html 模板"""
    # 预加载数据并验证
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'demo.json')
    file_exists = os.path.exists(demo_path)
    print(f"[index] demo.json 文件存在: {file_exists}, 路径: {demo_path}")

    if file_exists:
        file_size = os.path.getsize(demo_path)
        print(f"[index] demo.json 文件大小: {file_size} bytes")

    return render_template('dl_ai.html')


@app.route('/api/data')
def get_data():
    """获取 demo.json 数据"""
    print("[API /api/data] 收到数据请求")
    data = load_demo_data()
    response_data = {
        "json1": data.get("json1_总体执行进度", {}),
        "json2": data.get("json2_各目录执行进度", []),
        "json3": data.get("json3_各地市执行进度", []),
        "json4": data.get("json4_各医疗机构执行进度", []),
        "json5": data.get("json5_各医疗机构目录执行进度", [])
    }
    print(f"[API /api/data] 返回数据: json1={bool(response_data['json1'])}, json2长度={len(response_data['json2'])}")
    return jsonify(response_data)


@app.route('/api/stats')
def get_statistics():
    """获取统计数据"""
    data = load_demo_data()
    json1 = data.get("json1_总体执行进度", {})

    return jsonify({
        "total_batches": 1,
        "total_drugs": len(data.get("json2_各目录执行进度", [])),
        "total_contracts": json1.get("批次签约总量", 0),
        "total_pospitals": len(data.get("json3_各地市执行进度", [])),
    })


@app.route('/api/analyze')
def analyze():
    """流式分析报告"""
    from backend.services.ai_service import run_analysis_stream
    import time
    print("[API /api/analyze] 收到分析请求", flush=True)

    def generate():
        print("[API /api/analyze] generator started", flush=True)
        chunk_count = 0
        total_chars = 0
        # 立即返回一个空事件，确保连接建立
        yield "data: \n\n"
        for chunk in run_analysis_stream():
            chunk_count += 1
            total_chars += len(chunk)
            # chunk 已包含 SSE 格式，直接透传
            print(f"[API /api/analyze] yielding chunk {chunk_count}, len={len(chunk)}", flush=True)
            yield chunk
        print(f"[API /api/analyze] 流输出完成，总块数: {chunk_count}, 总字符: {total_chars}", flush=True)

    response = Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )
    return response


# @app.route('/api/analyze')
# def chat():
#     """直接返回Markdown测试内容"""
#     markdown_content = '''# 测试标题
# 这是一个包含**三个段落**和简单图表的Markdown测试内容，总字数约100字。

# ## 图表示例
# - 项目1: ★★★☆☆
# - 项目2: ★★★★★
# - 项目3: ★★☆☆☆

# 这是第三个段落，用于完整测试。'''

#     # 将内容按行分割，每行前加 "data: "，最后以两个换行符结束
#     lines = markdown_content.split('\n')
#     sse_data = '\n'.join(f"data: {line}" for line in lines) + '\n\n'

#     return Response(
#         sse_data,
#         mimetype='text/event-stream',
#         headers={'Cache-Control': 'no-cache'}
#     )


@app.route('/api/chat')
def chats():
    """流式对话"""
    message = request.args.get('message', '')
    print(f"[API /api/chat] 收到消息: {message[:50]}...")
    from backend.services.ai_service import run_chat_stream

    @stream_with_context
    def generate():
        chunk_count = 0
        total_chars = 0
        # 立即返回一个空事件，确保连接建立
        yield "data: \n\n"
        for chunk in run_chat_stream(message):
            chunk_count += 1
            total_chars += len(chunk)
            # chunk 已包含 SSE 格式，直接透传
            yield chunk
        print(f"[API /api/chat] 流输出完成，总块数: {chunk_count}, 总字符: {total_chars}")

    response = Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )
    return response


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    """导出分析报告为PDF"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from datetime import datetime
    import re
    import html

    try:
        # 获取前端传来的数据
        data = request.get_json()
        md_content = data.get('content', '')
        title = data.get('title', '集采分析报告')

        print(f"[API /api/export/pdf] 收到导出请求，内容长度: {len(md_content)} 字符")

        # 注册中文字体（尝试常用字体）
        font_names = ['SimSun', 'Microsoft YaHei', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei']
        chinese_font = 'Helvetica'  # 默认fallback
        for font_name in font_names:
            try:
                # 尝试注册字体
                pdfmetrics.registerFont(TTFont(font_name, f'{font_name}.ttf'))
                chinese_font = font_name
                break
            except:
                continue

        # 创建PDF文档
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # 定义样式
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            fontName=chinese_font,
            fontSize=18,
            leading=24,
            alignment=1,  # 居中
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a1a')
        ))
        styles.add(ParagraphStyle(
            name='ChineseHeading1',
            fontName=chinese_font,
            fontSize=14,
            leading=20,
            spaceAfter=12,
            spaceBefore=16,
            textColor=colors.HexColor('#2c2c2c'),
            borderColor=colors.HexColor('#007aff'),
            borderWidth=2,
            borderPadding=5
        ))
        styles.add(ParagraphStyle(
            name='ChineseHeading2',
            fontName=chinese_font,
            fontSize=12,
            leading=18,
            spaceAfter=10,
            spaceBefore=12,
            textColor=colors.HexColor('#444')
        ))
        styles.add(ParagraphStyle(
            name='ChineseBody',
            fontName=chinese_font,
            fontSize=10,
            leading=16,
            spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            name='ChineseMeta',
            fontName=chinese_font,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#666'),
            alignment=1  # 居中
        ))

        # 构建PDF内容
        story = []

        # 标题
        story.append(Paragraph(title, styles['ChineseTitle']))
        story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}", styles['ChineseMeta']))
        story.append(Spacer(1, 0.5*cm))

        # 解析Markdown并转换为PDF元素
        lines = md_content.split('\n')
        i = 0
        table_data = None
        in_table = False

        while i < len(lines):
            line = lines[i].strip()

            # 处理表格
            if line.startswith('|') and line.endswith('|'):
                if not in_table:
                    table_data = []
                    in_table = True
                # 解析表格行
                cells = [cell.strip() for cell in line[1:-1].split('|')]
                # 跳过分隔行（包含 --- 或 ===）
                if not all(c.replace('-', '').replace('=', '') == '' for c in cells):
                    table_data.append(cells)
                i += 1
                continue
            elif in_table:
                # 表格结束，创建表格
                if len(table_data) > 0:
                    # 创建表格
                    table = Table(table_data, colWidths=[doc.width/len(table_data[0])]*len(table_data[0]))
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f7')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1d1d1f')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
                        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 0.3*cm))
                in_table = False
                table_data = None

            # 处理标题
            if line.startswith('# '):
                story.append(Paragraph(line[2:], styles['ChineseHeading1']))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['ChineseHeading2']))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['ChineseHeading2']))
            elif line.startswith('**') and line.endswith('**') and len(line) > 4:
                # 粗体段落
                text = line[2:-2]
                story.append(Paragraph(f"<b>{text}</b>", styles['ChineseBody']))
            elif line.startswith('- ') or line.startswith('* '):
                # 列表项
                text = line[2:]
                # 处理粗体标记
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
                story.append(Paragraph(f"• {text}", styles['ChineseBody']))
            elif line.startswith('> '):
                # 引用
                story.append(Paragraph(line[2:], styles['ChineseBody']))
            elif line == '---' or line == '***':
                # 分隔线
                story.append(Spacer(1, 0.5*cm))
            elif line:
                # 普通段落，处理内联格式
                text = line
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)  # 粗体
                text = html.escape(text)  # 转义HTML特殊字符
                text = text.replace('\*\*', '')  # 移除未匹配的标记
                story.append(Paragraph(text, styles['ChineseBody']))
            else:
                # 空行
                story.append(Spacer(1, 0.2*cm))

            i += 1

        # 处理最后可能未闭合的表格
        if in_table and table_data:
            table = Table(table_data, colWidths=[doc.width/len(table_data[0])]*len(table_data[0]))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1d1d1f')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
                ('FONTNAME', (0, 1), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            story.append(table)

        # 添加页脚说明
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("— 本报告由集采监管AI分析系统自动生成，仅供参考 —", styles['ChineseMeta']))

        # 生成PDF
        doc.build(story)
        pdf_buffer.seek(0)

        # 生成文件名
        filename = f"集采分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        print(f"[API /api/export/pdf] PDF生成成功，大小: {len(pdf_buffer.getvalue())} 字节")

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[API /api/export/pdf] 生成PDF失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"PDF生成失败: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
