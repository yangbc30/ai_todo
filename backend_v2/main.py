from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import openai  # 需要安装: pip install openai

app = FastAPI()

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 OpenAI (需要设置环境变量 OPENAI_API_KEY)
# 或者直接设置: openai.api_key = "your-api-key"
from openai import OpenAI

client = OpenAI(
    api_key="sk-zmyrpclntmuvmufqjclmjczurrexkvzsfcrxthcwzgyffktd",
    base_url="https://api.siliconflow.cn/v1",
)


# ===== 数据模型 =====
class Task(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    completed: bool = False
    created_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"  # low, medium, high


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None


class AITaskRequest(BaseModel):
    prompt: str  # 用户输入的自然语言描述


# ===== 内存存储 =====
tasks_db: dict[str, Task] = {}


# ===== 基础任务操作 =====
@app.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate):
    """创建新任务"""
    new_task = Task(
        id=str(uuid.uuid4()),
        name=task.name,
        description=task.description,
        created_at=datetime.now(),
        due_date=task.due_date,
        priority=task.priority,
    )
    tasks_db[new_task.id] = new_task
    return new_task


@app.get("/tasks", response_model=List[Task])
async def get_all_tasks():
    """获取所有任务"""
    return list(tasks_db.values())


@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """获取单个任务"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    return tasks_db[task_id]


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate):
    """更新任务"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks_db[task_id]
    update_data = task_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

    return task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    del tasks_db[task_id]
    return {"message": "任务已删除"}


# ===== AI 功能 =====
@app.post("/ai/plan-tasks", response_model=List[Task])
async def ai_plan_tasks(request: AITaskRequest):
    """使用 AI 根据自然语言描述规划任务"""
    try:
        # 调用 OpenAI API
        response = client.chat.completions.create(
            model="Qwen/QwQ-32B",
            messages=[
                {
                    "role": "system",
                    "content": """你是一个任务规划助手。根据用户的描述，将其分解为具体的任务步骤。
                    每个任务应该包含：
                    - name: 任务名称（简短明确）
                    - description: 任务描述（详细说明）
                    - priority: 优先级（high/medium/low）
                    
                    请以JSON数组格式返回，例如：
                    [
                        {"name": "任务1", "description": "详细描述", "priority": "high"},
                        {"name": "任务2", "description": "详细描述", "priority": "medium"}
                    ]
                    """,
                },
                {"role": "user", "content": request.prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # 解析 AI 返回的内容
        import json

        ai_tasks = json.loads(response.choices[0].message.content)

        # 创建任务并保存
        created_tasks = []
        for task_data in ai_tasks:
            new_task = Task(
                id=str(uuid.uuid4()),
                name=task_data.get("name", "未命名任务"),
                description=task_data.get("description", ""),
                created_at=datetime.now(),
                priority=task_data.get("priority", "medium"),
            )
            tasks_db[new_task.id] = new_task
            created_tasks.append(new_task)

        return created_tasks

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 处理失败: {str(e)}")


@app.post("/ai/suggest-subtasks/{task_id}", response_model=List[Task])
async def ai_suggest_subtasks(task_id: str):
    """为指定任务生成子任务建议"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")

    parent_task = tasks_db[task_id]

    try:
        response = client.chat.completions.create(
            model="Qwen/QwQ-32B",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个任务分解助手。将给定的任务分解为更小的可执行步骤。",
                },
                {
                    "role": "user",
                    "content": f"请将以下任务分解为子任务：\n任务名称：{parent_task.name}\n任务描述：{parent_task.description}",
                },
            ],
            temperature=0.7,
            max_tokens=300,
        )

        # 这里简化处理，实际应该解析 AI 返回的结构化数据
        ai_response = response.choices[0].message.content

        # 创建示例子任务
        subtasks = []
        for i, line in enumerate(ai_response.split("\n")[:3]):  # 最多3个子任务
            if line.strip():
                subtask = Task(
                    id=str(uuid.uuid4()),
                    name=f"子任务 {i+1}: {line.strip()[:50]}",
                    description=line.strip(),
                    created_at=datetime.now(),
                    priority="medium",
                )
                tasks_db[subtask.id] = subtask
                subtasks.append(subtask)

        return subtasks

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 处理失败: {str(e)}")


# ===== 统计信息 =====
@app.get("/stats")
async def get_stats():
    """获取任务统计信息"""
    all_tasks = list(tasks_db.values())
    completed = sum(1 for t in all_tasks if t.completed)

    return {
        "total": len(all_tasks),
        "completed": completed,
        "pending": len(all_tasks) - completed,
        "by_priority": {
            "high": sum(1 for t in all_tasks if t.priority == "high"),
            "medium": sum(1 for t in all_tasks if t.priority == "medium"),
            "low": sum(1 for t in all_tasks if t.priority == "low"),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
