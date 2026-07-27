"""HTML page routes."""

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Render the chat page."""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page(request: Request):
    """Render the knowledge management page."""
    return templates.TemplateResponse("knowledge.html", {"request": request})


@router.get("/m1", response_class=HTMLResponse)
async def m1_page(request: Request):
    """Render the M1 rule extraction workbench."""
    return templates.TemplateResponse("m1.html", {"request": request})


@router.get("/collaboration")
async def collaboration_redirect():
    """Redirect collaboration entry to the chat page."""
    return RedirectResponse(url="/chat")
