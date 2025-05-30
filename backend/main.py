from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# 允许跨域请求（前端 React Native 需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任务模型（仅包含任务名）
class Task(BaseModel):
    name: str

# 内存存储任务
tasks: List[Task] = []

# 添加任务
@app.post("/tasks", response_model=List[Task])
async def add_task(task: Task):
    tasks.append(task)
    return tasks

# 获取任务列表
@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    return tasks