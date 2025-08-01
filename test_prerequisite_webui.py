#!/usr/bin/env python3
"""
在Web UI中测试prerequisite功能
"""
import requests
import json
import time

def test_webui_prerequisite():
    """测试Web UI中的prerequisite功能"""
    print("🧪 测试Web UI中的prerequisite功能...")
    
    # 检查Web UI是否运行
    try:
        response = requests.get("http://localhost:7788", timeout=10)
        if response.status_code != 200:
            print(f"❌ Web UI不可访问: {response.status_code}")
            return False
        print("✅ Web UI正常运行")
    except Exception as e:
        print(f"❌ 无法连接到Web UI: {e}")
        return False
    
    print("\n📋 测试说明:")
    print("1. 访问 http://localhost:7788")
    print("2. 在Prerequisite框中输入以下代码:")
    print("   ```python")
    print("   PLACEHOLDERS = {}")
    print("   PLACEHOLDERS['TEST_URL'] = 'https://www.google.com'")
    print("   ```")
    print("3. 在任务框中输入: 'open TEST_URL'")
    print("4. 点击Submit Task按钮")
    print("5. 观察是否正确打开Google网站")
    
    print("\n🔍 检查容器日志以验证:")
    print("docker logs -f web-ui-test-container | grep -E '(placeholder|PLACEHOLDER|替换)'")
    
    return True

def check_container_logs():
    """检查容器日志中的placeholder相关信息"""
    print("\n🔍 检查容器日志...")
    import subprocess
    
    try:
        # 检查容器是否运行
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=web-ui-test-container", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if "web-ui-test-container" not in result.stdout:
            print("❌ 容器未运行，请先启动: ./test_docker_local.sh")
            return False
        
        print("✅ 容器正在运行")
        
        # 获取最近的日志
        result = subprocess.run(
            ["docker", "logs", "--tail", "50", "web-ui-test-container"],
            capture_output=True, text=True, timeout=10
        )
        
        logs = result.stdout + result.stderr
        
        # 查找placeholder相关的日志
        placeholder_logs = []
        for line in logs.split('\n'):
            if any(keyword in line.lower() for keyword in ['placeholder', '替换', 'replacing']):
                placeholder_logs.append(line)
        
        if placeholder_logs:
            print("📋 找到placeholder相关日志:")
            for log in placeholder_logs[-5:]:  # 显示最近5条
                print(f"  {log}")
        else:
            print("ℹ️  暂未发现placeholder相关日志")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查日志失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 开始测试Web UI中的prerequisite功能...")
    
    # 测试Web UI可访问性
    webui_test = test_webui_prerequisite()
    
    # 检查容器日志
    log_test = check_container_logs()
    
    print(f"\n📊 测试结果:")
    print(f"  - Web UI可访问性: {'✅ 通过' if webui_test else '❌ 失败'}")
    print(f"  - 容器日志检查: {'✅ 通过' if log_test else '❌ 失败'}")
    
    if webui_test:
        print("\n🎯 下一步:")
        print("1. 手动在Web UI中测试prerequisite功能")
        print("2. 观察浏览器视图中的实时截图")
        print("3. 检查任务是否正确执行")
        print("4. 如果测试成功，就可以部署到云端了")
    else:
        print("\n⚠️  需要先解决Web UI访问问题")
