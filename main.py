from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from database import engine, Base
from routers import books, reading, sources, auth, excerpts, rewrites, sensitive_words
from routers import templates as rtemplates

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastRead", description="基于FastAPI的在线阅读应用")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板配置
templates = Jinja2Templates(directory="templates")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(books.router, prefix="/api/books", tags=["书籍管理"])
app.include_router(reading.router, prefix="/api/reading", tags=["阅读"])
app.include_router(sources.router, prefix="/api/sources", tags=["书源管理"])
app.include_router(excerpts.router, prefix="/api/excerpts", tags=["摘录管理"])
app.include_router(rtemplates.router, prefix="/api/templates", tags=["模板管理"])
app.include_router(rewrites.router, prefix="/api/rewrites", tags=["重写功能"])
app.include_router(sensitive_words.router, prefix="/api/sensitive-words", tags=["敏感词管理"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

@app.get("/book/{book_id}", response_class=HTMLResponse)
async def read_book(request: Request, book_id: int):
    return templates.TemplateResponse("reader.html", {"request": request, "book_id": book_id})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8777)
