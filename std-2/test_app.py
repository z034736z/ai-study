# 测试用例 - 集采监管AI分析系统
import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, DATA_FILE
from backend.data_loader import load_data, get_stats


class TestConfig:
    """配置测试"""

    def test_api_config(self):
        """测试API配置是否正确"""
        assert ANTHROPIC_AUTH_TOKEN is not None
        assert ANTHROPIC_AUTH_TOKEN != "your-api-key-here"
        assert "sk-sp-" in ANTHROPIC_AUTH_TOKEN
        print(f"API配置: {ANTHROPIC_BASE_URL}, Model: {ANTHROPIC_MODEL}")

    def test_data_file_exists(self):
        """测试数据文件是否存在"""
        assert os.path.exists(DATA_FILE), f"数据文件不存在: {DATA_FILE}"
        print(f"数据文件: {DATA_FILE}")


class TestDataLoader:
    """数据加载测试"""

    def test_load_data(self):
        """测试数据加载"""
        data = load_data()
        assert isinstance(data, list), "数据应该是列表"
        assert len(data) > 0, "数据不应为空"
        print(f"加载了 {len(data)} 条数据")

    def test_get_stats(self):
        """测试统计功能"""
        stats = get_stats()
        assert isinstance(stats, dict), "统计数据应该是字典"
        assert "total_drugs" in stats, "缺少total_drugs字段"
        assert "total_hospitals" in stats, "缺少total_hospitals字段"
        assert "total_companies" in stats, "缺少total_companies字段"
        print(f"统计结果: {stats}")


class TestAI:
    """AI服务测试"""

    def test_call_ai(self):
        """测试AI调用"""
        from backend.services.ai_service import call_ai

        prompt = "你好，请用一句话介绍你自己"
        result = call_ai(prompt)

        assert result is not None, "AI返回不应为空"
        assert "API调用失败" not in result, "API调用失败"
        assert len(result) > 0, "AI返回内容为空"
        print(f"AI响应: {result[:100]}...")

    def test_call_ai_stream(self):
        """测试流式AI调用"""
        from backend.services.ai_service import call_ai_stream

        prompt = "你好，请用一句话介绍你自己"
        chunks = []
        for chunk in call_ai_stream(prompt):
            if chunk:
                chunks.append(chunk)
                print(f"流式块: {chunk[:50]}...")

        assert len(chunks) > 0, "流式输出为空"
        full_text = "".join(chunks)
        assert len(full_text) > 0, "流式输出内容为空"
        print(f"完整流式输出: {full_text[:100]}...")


class TestAPI:
    """API接口测试"""

    @pytest.fixture
    def app(self, tmp_path):
        """创建测试Flask应用"""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from backend.app import app
        app.config['TESTING'] = True
        return app

    def test_health(self, app):
        """测试健康检查接口"""
        with app.test_client() as client:
            response = client.get('/api/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            print("健康检查通过")

    def test_data(self, app):
        """测试数据接口"""
        with app.test_client() as client:
            response = client.get('/api/data')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) > 0
            print(f"数据接口返回 {len(data)} 条")

    def test_stats(self, app):
        """测试统计接口"""
        with app.test_client() as client:
            response = client.get('/api/stats')
            assert response.status_code == 200
            data = response.get_json()
            assert "total_drugs" in data
            print(f"统计接口: {data}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])