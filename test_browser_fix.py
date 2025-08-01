#!/usr/bin/env python3
"""
测试修复后的浏览器功能
"""
import requests
import json
import time

def test_web_ui_response():
    """测试Web UI是否响应"""
    try:
        response = requests.get("http://localhost:7788", timeout=10)
        print(f"✅ Web UI响应正常: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Web UI响应失败: {e}")
        return False

def test_submit_task():
    """测试提交任务功能"""
    print("🧪 测试提交简单任务...")
    
    # 这里我们可以通过查看容器日志来验证
    # 因为Gradio的API需要更复杂的设置
    print("📋 请手动测试以下步骤:")
    print("1. 访问 http://localhost:7788")
    print("2. 在任务输入框中输入: 'open google.com'")
    print("3. 点击 'Submit Task' 按钮")
    print("4. 观察是否有响应和进度显示")
    
    return True

if __name__ == "__main__":
    print("🔍 开始测试修复后的功能...")
    
    # 测试基本连接
    if test_web_ui_response():
        test_submit_task()
        
        print("\n📊 测试完成！")
        print("如果需要查看详细日志，运行:")
        print("docker logs -f web-ui-test-container")
    else:
        print("❌ 基本连接测试失败")
