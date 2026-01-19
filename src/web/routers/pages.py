"""
页面路由 - 渲染 HTML 页面
"""
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# 模板目录 (src/web/templates)
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页 - 导航入口"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """聊天界面"""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page(request: Request):
    """知识库管理页面"""
    return templates.TemplateResponse("knowledge.html", {"request": request})


@router.get("/collaboration")
async def collaboration_redirect():
    """协作会话页面 - 重定向到聊天页面"""
    return RedirectResponse(url="/chat")
