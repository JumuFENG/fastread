from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
from app.lofig import Config

router = APIRouter()

class AIConfigModel(BaseModel):
    api_url: str = ""
    api_key: str = ""
    model: str = ""

class AIGenerateRequest(BaseModel):
    prompt: str
    context: Optional[str] = None

@router.get("/config")
async def get_ai_config():
    """获取AI配置"""
    return Config.ai_config()

@router.post("/config")
async def save_ai_config(request: AIConfigModel):
    """保存AI配置"""
    ai_cfg = Config.ai_config()
    ai_cfg.clear()
    ai_cfg.update(request.dict())
    Config.save(Config.all_configs())
    return {"message": "AI配置已保存"}

@router.post("/generate")
async def ai_generate(request: AIGenerateRequest):
    """调用AI生成内容"""
    ai_cfg = Config.ai_config()
    api_url = ai_cfg.get("api_url", "").strip()
    api_key = ai_cfg.get("api_key", "").strip()
    if not api_url or not api_key:
        raise HTTPException(status_code=400, detail="请先在设置中配置AI API地址和密钥")

    model = ai_cfg.get("model", "").strip() or "gpt-4o-mini"

    user_msg = request.prompt
    if request.context:
        user_msg = f"原始内容：\n{request.context}\n\n创作要求：\n{request.prompt}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一名小说创作助手，根据要求生成或改写小说内容，保持文风与语境一致，直接输出正文。"},
            {"role": "user", "content": user_msg}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                api_url,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"AI接口返回错误: {e.response.status_code}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"AI接口连接失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI调用失败: {str(e)}")

    if not content:
        raise HTTPException(status_code=500, detail="AI未返回内容")
    return {"content": content}
