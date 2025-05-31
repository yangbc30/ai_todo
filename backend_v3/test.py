# test_api_v2.py - 改进后的 API 测试用例
import requests
import json
import time
from datetime import datetime, date, timedelta

# API 基础地址
BASE_URL = "http://localhost:8000"

# 用于存储测试中创建的任务 ID
created_task_ids = []
ai_job_id = None

def print_response(response, title=""):
    """美化打印响应结果"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"响应内容: {response.text}")
    print("-" * 60)

def cleanup():
    """清理测试数据"""
    print("\n清理测试数据...")
    for task_id in created_task_ids:
        try:
            requests.delete(f"{BASE_URL}/tasks/{task_id}")
        except:
            pass
    created_task_ids.clear()

# ========== 1. 基础任务 CRUD 测试 ==========
def test_basic_crud():
    print("\n" + "="*50)
    print("测试 1: 基础任务 CRUD 操作")
    print("="*50)

    # 1.1 创建完整任务
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    task_data = {
        "name": "完成项目文档",
        "description": "编写项目的技术文档和用户手册",
        "priority": "high",
        "due_date": tomorrow,
        "estimated_hours": 4.5,
        "scheduled_date": date.today().isoformat(),
        "tags": ["文档", "重要"]
    }
    response = requests.post(f"{BASE_URL}/tasks", json=task_data)
    print_response(response, "创建完整任务")
    if response.status_code == 200:
        task = response.json()
        created_task_ids.append(task["id"])
        
        # 验证返回的字段
        assert task["name"] == task_data["name"]
        assert task["priority"] == "high"
        assert task["estimated_hours"] == 4.5
        assert task["status"] == "pending"
        assert task["completed"] == False
        print("✓ 任务创建成功，所有字段正确")

    # 1.2 创建最简任务
    simple_task = {"name": "买咖啡"}
    response = requests.post(f"{BASE_URL}/tasks", json=simple_task)
    print_response(response, "创建最简任务")
    if response.status_code == 200:
        created_task_ids.append(response.json()["id"])

    # 1.3 获取所有任务
    response = requests.get(f"{BASE_URL}/tasks")
    print_response(response, "获取所有任务")
    tasks = response.json()
    assert len(tasks) >= 2
    print(f"✓ 成功获取 {len(tasks)} 个任务")

    # 1.4 更新任务状态
    if created_task_ids:
        task_id = created_task_ids[0]
        update_data = {
            "status": "in_progress",
            "estimated_hours": 5.0
        }
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data)
        print_response(response, "更新任务状态")
        assert response.json()["status"] == "in_progress"
        print("✓ 任务状态更新成功")

    # 1.5 标记任务完成
    if created_task_ids:
        task_id = created_task_ids[0]
        update_data = {"completed": True}
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data)
        print_response(response, "标记任务完成")
        task = response.json()
        assert task["completed"] == True
        assert task["status"] == "completed"
        print("✓ 任务完成状态同步更新")

# ========== 2. 日历功能测试 ==========
def test_calendar_features():
    print("\n" + "="*50)
    print("测试 2: 日历功能")
    print("="*50)

    # 2.1 创建不同日期的任务
    today = date.today()
    tasks_to_create = [
        {
            "name": "今天截止的任务",
            "due_date": datetime.now().isoformat(),
            "priority": "high"
        },
        {
            "name": "明天截止的任务",
            "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "priority": "medium"
        },
        {
            "name": "计划今天执行的任务",
            "scheduled_date": today.isoformat(),
            "priority": "medium"
        },
        {
            "name": "下月截止的任务",
            "due_date": (datetime.now() + timedelta(days=35)).isoformat(),
            "priority": "low"
        }
    ]

    for task_data in tasks_to_create:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        if response.status_code == 200:
            created_task_ids.append(response.json()["id"])
    
    print(f"创建了 {len(tasks_to_create)} 个不同日期的任务")

    # 2.2 获取当月日历数据
    year = today.year
    month = today.month
    response = requests.get(f"{BASE_URL}/tasks/calendar/{year}/{month}")
    print_response(response, f"获取 {year}年{month}月 日历数据")
    
    calendar_data = response.json()
    today_str = today.isoformat()
    
    if today_str in calendar_data:
        today_tasks = calendar_data[today_str]
        print(f"✓ 今天有 {len(today_tasks['due'])} 个截止任务")
        print(f"✓ 今天有 {len(today_tasks['scheduled'])} 个计划任务")
    
    # 2.3 获取下月日历数据
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1
    response = requests.get(f"{BASE_URL}/tasks/calendar/{next_year}/{next_month}")
    print_response(response, f"获取 {next_year}年{next_month}月 日历数据")

# ========== 3. 异步 AI 任务规划测试 ==========
def test_async_ai_planning():
    print("\n" + "="*50)
    print("测试 3: 异步 AI 任务规划")
    print("="*50)

    # 3.1 提交 AI 规划请求
    ai_request = {
        "prompt": "准备一个技术分享会，主题是人工智能在日常生活中的应用",
        "max_tasks": 3
    }
    response = requests.post(f"{BASE_URL}/ai/plan-tasks/async", json=ai_request)
    print_response(response, "提交 AI 规划请求")
    
    if response.status_code == 200:
        result = response.json()
        job_id = result["job_id"]
        assert result["status"] == "processing"
        print(f"✓ 任务已提交，Job ID: {job_id}")
        
        # 3.2 轮询任务状态
        max_attempts = 30  # 最多等待60秒
        attempt = 0
        while attempt < max_attempts:
            time.sleep(2)  # 每2秒检查一次
            response = requests.get(f"{BASE_URL}/ai/jobs/{job_id}")
            job_status = response.json()
            
            print(f"检查状态 (尝试 {attempt + 1}/{max_attempts}): {job_status['status']}")
            
            if job_status["status"] == "completed":
                print_response(response, "AI 任务完成")
                tasks = job_status["result"]
                assert len(tasks) <= 3
                print(f"✓ AI 生成了 {len(tasks)} 个任务")
                
                # 记录创建的任务ID
                for task in tasks:
                    created_task_ids.append(task["id"])
                break
            elif job_status["status"] == "failed":
                print(f"✗ AI 任务失败: {job_status.get('error', '未知错误')}")
                break
            
            attempt += 1
        else:
            print("✗ AI 任务超时")

    # 3.3 测试任务数量限制
    ai_request = {
        "prompt": "组织一场大型技术会议，包括场地、嘉宾、议程、宣传等所有方面",
        "max_tasks": 2
    }
    response = requests.post(f"{BASE_URL}/ai/plan-tasks/async", json=ai_request)
    if response.status_code == 200:
        job_id = response.json()["job_id"]
        print(f"测试任务数量限制，Job ID: {job_id}")
        
        # 等待完成
        time.sleep(5)
        response = requests.get(f"{BASE_URL}/ai/jobs/{job_id}")
        if response.json()["status"] == "completed":
            tasks = response.json()["result"]
            assert len(tasks) <= 2
            print(f"✓ 任务数量限制生效，生成了 {len(tasks)} 个任务")

# ========== 4. AI 智能调度测试 ==========
def test_ai_scheduling():
    print("\n" + "="*50)
    print("测试 4: AI 智能调度")
    print("="*50)

    # 4.1 创建多个不同优先级和截止日期的任务
    test_tasks = [
        {
            "name": "紧急任务 - 今天截止",
            "priority": "high",
            "due_date": datetime.now().isoformat(),
            "estimated_hours": 2
        },
        {
            "name": "重要任务 - 明天截止",
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "estimated_hours": 3
        },
        {
            "name": "普通任务 - 本周截止",
            "priority": "medium",
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "estimated_hours": 1
        },
        {
            "name": "低优先级任务",
            "priority": "low",
            "estimated_hours": 4
        }
    ]

    task_ids = []
    for task_data in test_tasks:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        if response.status_code == 200:
            task_id = response.json()["id"]
            created_task_ids.append(task_id)
            task_ids.append(task_id)

    # 4.2 测试智能调度（所有未完成任务）
    response = requests.post(f"{BASE_URL}/ai/schedule-tasks", json={})
    print_response(response, "AI 智能调度所有任务")
    
    if response.status_code == 200:
        schedule = response.json()
        print("\n调度结果分析:")
        for period in ["today", "tomorrow", "this_week", "later"]:
            tasks = schedule.get(period, [])
            print(f"- {period}: {len(tasks)} 个任务")
            for task in tasks:
                print(f"  • {task['name']} (优先级: {task['priority']})")
        
        # 验证高优先级任务应该被优先安排
        today_tasks = schedule.get("today", [])
        high_priority_today = sum(1 for t in today_tasks if t["priority"] == "high")
        print(f"\n✓ 今天安排了 {high_priority_today} 个高优先级任务")

    # 4.3 测试指定任务的调度
    if len(task_ids) >= 2:
        request_data = {
            "task_ids": task_ids[:2]  # 只调度前两个任务
        }
        response = requests.post(f"{BASE_URL}/ai/schedule-tasks", json=request_data)
        print_response(response, "AI 智能调度指定任务")

# ========== 5. 统计信息测试 ==========
def test_statistics():
    print("\n" + "="*50)
    print("测试 5: 增强的统计信息")
    print("="*50)

    # 5.1 创建测试数据
    # 创建一个逾期任务
    overdue_task = {
        "name": "逾期任务",
        "due_date": (datetime.now() - timedelta(days=2)).isoformat(),
        "priority": "high"
    }
    response = requests.post(f"{BASE_URL}/tasks", json=overdue_task)
    if response.status_code == 200:
        created_task_ids.append(response.json()["id"])

    # 创建一个今日到期任务
    due_today_task = {
        "name": "今日到期任务",
        "due_date": datetime.now().replace(hour=23, minute=59).isoformat(),
        "priority": "medium"
    }
    response = requests.post(f"{BASE_URL}/tasks", json=due_today_task)
    if response.status_code == 200:
        created_task_ids.append(response.json()["id"])

    # 5.2 获取统计信息
    response = requests.get(f"{BASE_URL}/stats")
    print_response(response, "获取增强的统计信息")
    
    stats = response.json()
    print("\n统计分析:")
    print(f"- 总任务数: {stats['total']}")
    print(f"- 已完成: {stats['completed']}")
    print(f"- 待完成: {stats['pending']}")
    print(f"- 今日到期: {stats['due_today']}")
    print(f"- 已逾期: {stats['overdue']}")
    print(f"\n按优先级统计:")
    for priority in ["high", "medium", "low"]:
        print(f"- {priority}: {stats['by_priority'][priority]}")
    print(f"\n按状态统计:")
    for status in ["pending", "in_progress", "completed"]:
        print(f"- {status}: {stats['by_status'][status]}")

# ========== 6. 错误处理测试 ==========
def test_error_handling():
    print("\n" + "="*50)
    print("测试 6: 错误处理")
    print("="*50)

    # 6.1 无效的任务数据
    invalid_task = {
        "description": "缺少必需的 name 字段"
    }
    response = requests.post(f"{BASE_URL}/tasks", json=invalid_task)
    print_response(response, "创建无效任务")
    assert response.status_code == 422

    # 6.2 更新不存在的任务
    response = requests.put(f"{BASE_URL}/tasks/invalid-id", json={"name": "新名称"})
    print_response(response, "更新不存在的任务")
    assert response.status_code == 404

    # 6.3 无效的日期格式
    invalid_date_task = {
        "name": "无效日期任务",
        "due_date": "2024-13-45"  # 无效的日期
    }
    response = requests.post(f"{BASE_URL}/tasks", json=invalid_date_task)
    print_response(response, "创建无效日期的任务")
    assert response.status_code == 422

    # 6.4 无效的优先级
    invalid_priority = {
        "name": "无效优先级任务",
        "priority": "super-high"  # 无效的优先级
    }
    response = requests.post(f"{BASE_URL}/tasks", json=invalid_priority)
    print_response(response, "创建无效优先级的任务")
    # 注意：这个可能会成功，因为 priority 是 Optional[str]

# ========== 7. 边界条件测试 ==========
def test_edge_cases():
    print("\n" + "="*50)
    print("测试 7: 边界条件")
    print("="*50)

    # 7.1 空任务名称
    empty_name = {"name": ""}
    response = requests.post(f"{BASE_URL}/tasks", json=empty_name)
    print_response(response, "创建空名称任务")

    # 7.2 超长任务名称
    long_name = {
        "name": "这是一个非常非常非常长的任务名称" * 10,
        "description": "测试超长文本处理"
    }
    response = requests.post(f"{BASE_URL}/tasks", json=long_name)
    print_response(response, "创建超长名称任务")
    if response.status_code == 200:
        created_task_ids.append(response.json()["id"])

    # 7.3 负数预计时长
    negative_hours = {
        "name": "负数时长任务",
        "estimated_hours": -5
    }
    response = requests.post(f"{BASE_URL}/tasks", json=negative_hours)
    print_response(response, "创建负数时长任务")
    if response.status_code == 200:
        created_task_ids.append(response.json()["id"])

    # 7.4 获取不存在的月份日历
    response = requests.get(f"{BASE_URL}/tasks/calendar/2024/13")
    print_response(response, "获取无效月份的日历")

# ========== 主测试函数 ==========
def main():
    print("="*60)
    print("FastAPI 备忘录 API 测试套件 v2.0")
    print("="*60)
    
    try:
        # 运行所有测试
        test_basic_crud()
        test_calendar_features()
        test_async_ai_planning()
        test_ai_scheduling()
        test_statistics()
        test_error_handling()
        test_edge_cases()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        cleanup()

if __name__ == "__main__":
    main()