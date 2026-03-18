import os
import json
import requests
from typing import Generator, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AIService:
    """AI 分析服务 - 调用阿里云 Minimax API"""

    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY", "")
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
        self.model = os.getenv("MINIMAX_MODEL", "abab6.5s-chat")

    def build_prompt(self, stats_summary: str, dimension: str = "全部") -> str:
        """构建分析Prompt"""
        prompt = f"""你是一位资深的**国家药品集中采购专家**，具备丰富的药品采购数据分析经验。请基于以下带量采购的Excel数据，进行专业的深度分析。

## 数据来源
Excel数据分析统计结果

## 数据摘要
{stats_summary}

## 分析要求

请你从以下维度进行次第分析：

1. **整体情况**：采购总量、金额、覆盖品种数、整体趋势
2. **品种维度**：各药品品种的采购分布、主要品种占比
3. **地市维度**：各地区采购分布、重点城市分析
4. **医院维度**：重点医院采购情况、医院采购特点
5. **产品维度**：具体产品规格剂型分析、主流产品规格
6. **申报企业维度**：各企业中标情况、市场集中度分析
7. **配送企业维度**：配送企业覆盖情况、配送能力分析

请给出专业的分析报告，要求：
- 语言专业、严谨
- 数据解读准确
- 包含关键发现和趋势分析
- 如有异常数据，请特别指出
- 使用Markdown格式输出，层次分明

请开始分析："""
        return prompt

    def stream_chat(self, prompt: str) -> Generator[str, None, None]:
        """流式调用 Minimax API"""
        if not self.api_key or self.api_key == "your-minimax-api-key-here":
            # 如果没有配置API，返回模拟流式输出
            yield from self._simulate_stream(prompt)
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一位专业的国家药品集中采购分析专家。"},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 4096
        }

        try:
            response = requests.post(
                f"{self.base_url}/text/chatcompletion_v2",
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )

            if response.status_code != 200:
                # API调用失败，返回错误信息
                yield f"错误: API返回状态码 {response.status_code}\n"
                yield f"请检查API配置是否正确。\n"
                return

            # 解析SSE流
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data.strip() == '[DONE]':
                            break
                        try:
                            json_data = json.loads(data)
                            if 'choices' in json_data:
                                delta = json_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.Timeout:
            yield "错误: API请求超时，请检查网络连接。\n"
        except requests.exceptions.RequestException as e:
            yield f"错误: API请求失败 - {str(e)}\n"
        except Exception as e:
            yield f"错误: {str(e)}\n"

    def _simulate_stream(self, prompt: str) -> Generator[str, None, None]:
        """模拟流式输出（当未配置API时使用）"""
        sample_response = """
# 带量采购数据分析报告

## 一、整体情况分析

根据统计数据，本次带量采购呈现出以下整体特点：

- **采购规模**：合同总金额较大，覆盖多个药品品类
- **执行周期**：涵盖2025年全年采购周期
- **参与主体**：涉及多家医院、申报企业和配送企业

## 二、各维度分析

### 1. 品种维度分析

从药品品种维度来看，采购主要集中在常用药品领域，各品种采购量差异明显。

### 2. 地市维度分析

采购覆盖多个地市，各地市采购量存在一定差异，重点城市采购量较大。

### 3. 医院维度分析

大型三甲医院采购量位居前列，体现了集中采购的规模效应。

### 4. 产品维度分析

具体产品规格中，主流规格采购量较大，特殊规格相对较少。

### 5. 申报企业维度分析

多家企业参与投标，市场竞争较为充分。

### 6. 配送企业维度分析

配送企业覆盖范围广，配送能力总体较强。

## 三、结论与建议

1. 整体采购运行平稳，履约率较高
2. 建议继续优化品种结构，提高采购效率
3. 加强配送企业监管，确保供应及时

---
*注：当前为演示模式，请配置 Minimax API Key 以获取真实AI分析结果。*
"""
        # 模拟打字机效果
        for char in sample_response:
            yield char
            import time
            time.sleep(0.01)

    def analyze(self, stats_summary: str) -> str:
        """非流式分析（一次性返回）"""
        prompt = self.build_prompt(stats_summary)

        # 收集所有流式输出
        result = ""
        for chunk in self.stream_chat(prompt):
            result += chunk

        return result