from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from database import engine, Base
from routers import books, reading, sources, auth

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

@app.get("/debug", response_class=HTMLResponse)
async def debug_page(request: Request):
    return templates.TemplateResponse("debug.html", {"request": request})

@app.get("/test-simple", response_class=HTMLResponse)
async def test_simple(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head><title>简单测试</title></head>
    <body>
        <h1>简单API测试</h1>
        <div id="result">测试中...</div>
        <script>
        async function test() {
            try {
                const response = await fetch('/api/books/1/chapters/1');
                const data = await response.json();
                document.getElementById('result').innerHTML = 
                    `成功！章节: ${data.title}, 内容长度: ${data.content.length}`;
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    `失败: ${error.message}`;
            }
        }
        test();
        </script>
    </body>
    </html>
    """

@app.get("/test-reader", response_class=HTMLResponse)
async def test_reader(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>阅读器API测试</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .result { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1>阅读器API测试</h1>
        <div id="results"></div>
        
        <script>
        async function testAPIs() {
            const resultsDiv = document.getElementById('results');
            
            const tests = [
                {
                    name: '获取书籍信息',
                    url: '/api/books/1',
                    test: (data) => data.title && data.author
                },
                {
                    name: '获取章节列表',
                    url: '/api/books/1/chapters',
                    test: (data) => Array.isArray(data) && data.length > 0
                },
                {
                    name: '获取第一章内容',
                    url: '/api/books/1/chapters/1',
                    test: (data) => data.content && data.content.length > 0
                }
            ];
            
            for (const test of tests) {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result';
                
                try {
                    const response = await fetch(test.url);
                    const data = await response.json();
                    
                    if (response.ok && test.test(data)) {
                        resultDiv.innerHTML = `
                            <div class="success">✅ ${test.name} - 成功</div>
                            <pre>${JSON.stringify(data, null, 2).substring(0, 500)}...</pre>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <div class="error">❌ ${test.name} - 失败</div>
                            <pre>状态: ${response.status}\\n${JSON.stringify(data, null, 2)}</pre>
                        `;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div class="error">❌ ${test.name} - 错误: ${error.message}</div>
                    `;
                }
                
                resultsDiv.appendChild(resultDiv);
            }
        }
        
        document.addEventListener('DOMContentLoaded', testAPIs);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8777)
