# test_api.py - API 测试用例
# 可以使用 Python requests 库运行这些测试

import requests
import json
from datetime import datetime

# API 基础地址
BASE_URL = "http://localhost:8000"

# 用于存储测试中创建的任务 ID
created_task_ids = []

def print_response(response):
    """美化打印响应结果"""
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"响应内容: {response.text}")
    print("-" * 50)

# ========== 1. 创建任务测试 ==========
print("=== 测试 1: 创建任务 ===")

# 测试 1.1: 创建基础任务
test_1_1 = {
    "name": "完成项目报告",
    "description": "准备季度项目总结报告",
    "priority": "high"
}
response = requests.post(f"{BASE_URL}/tasks", json=test_1_1)
print("创建高优先级任务:")
print_response(response)
if response.status_code == 200:
    created_task_ids.append(response.json()["id"])

# 测试 1.2: 创建带截止日期的任务
test_1_2 = {
    "name": "准备会议材料",
    "description": "下周一的部门会议",
    "due_date": "2024-12-25T14:00:00",
    "priority": "medium"
}
response = requests.post(f"{BASE_URL}/tasks", json=test_1_2)
print("创建带截止日期的任务:")
print_response(response)
if response.status_code == 200:
    created_task_ids.append(response.json()["id"])

# 测试 1.3: 创建最简任务（只有名称）
test_1_3 = {
    "name": "买牛奶"
}
response = requests.post(f"{BASE_URL}/tasks", json=test_1_3)
print("创建最简任务:")
print_response(response)
if response.status_code == 200:
    created_task_ids.append(response.json()["id"])

# ========== 2. 获取任务测试 ==========
print("\n=== 测试 2: 获取任务 ===")

# 测试 2.1: 获取所有任务
response = requests.get(f"{BASE_URL}/tasks")
print("获取所有任务列表:")
print_response(response)

# 测试 2.2: 获取单个任务
if created_task_ids:
    task_id = created_task_ids[0]
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    print(f"获取单个任务 (ID: {task_id}):")
    print_response(response)

# 测试 2.3: 获取不存在的任务
response = requests.get(f"{BASE_URL}/tasks/nonexistent-id")
print("获取不存在的任务:")
print_response(response)

# ========== 3. 更新任务测试 ==========
print("\n=== 测试 3: 更新任务 ===")

if created_task_ids:
    task_id = created_task_ids[0]
    
    # 测试 3.1: 标记任务完成
    update_3_1 = {
        "completed": True
    }
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_3_1)
    print("标记任务为完成:")
    print_response(response)
    
    # 测试 3.2: 更新多个字段
    update_3_2 = {
        "name": "完成项目报告（已修改）",
        "priority": "low",
        "description": "已经完成大部分，只需要最后审核"
    }
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_3_2)
    print("更新任务的多个字段:")
    print_response(response)

# ========== 4. AI 功能测试 ==========
print("\n=== 测试 4: AI 功能 ===")

# 测试 4.1: AI 规划任务
ai_request = {
    "prompt": "我需要组织一个生日派对，大约20人参加"
}
response = requests.post(f"{BASE_URL}/ai/plan-tasks", json=ai_request)
print("AI 规划生日派对任务:")
print_response(response)

# 注意：这个测试需要配置有效的 OpenAI API Key
# 如果没有配置，会返回 500 错误

# 测试 4.2: AI 建议子任务
if created_task_ids:
    task_id = created_task_ids[1]
    response = requests.post(f"{BASE_URL}/ai/suggest-subtasks/{task_id}")
    print(f"AI 为任务生成子任务建议:")
    print_response(response)

# ========== 5. 统计信息测试 ==========
print("\n=== 测试 5: 获取统计信息 ===")

response = requests.get(f"{BASE_URL}/stats")
print("任务统计信息:")
print_response(response)

# ========== 6. 删除任务测试 ==========
print("\n=== 测试 6: 删除任务 ===")

if created_task_ids:
    # 测试 6.1: 删除存在的任务
    task_id = created_task_ids[-1]
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
    print(f"删除任务 (ID: {task_id}):")
    print_response(response)
    
    # 测试 6.2: 再次获取已删除的任务
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    print("尝试获取已删除的任务:")
    print_response(response)

# ========== 7. 错误处理测试 ==========
print("\n=== 测试 7: 错误处理 ===")

# 测试 7.1: 缺少必需字段
invalid_task = {
    "description": "这个任务没有名称"
}
response = requests.post(f"{BASE_URL}/tasks", json=invalid_task)
print("创建缺少必需字段的任务:")
print_response(response)

# 测试 7.2: 错误的数据类型
invalid_update = {
    "completed": "yes"  # 应该是 boolean
}
if created_task_ids:
    response = requests.put(f"{BASE_URL}/tasks/{created_task_ids[0]}", json=invalid_update)
    print("使用错误数据类型更新:")
    print_response(response)