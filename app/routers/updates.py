import os
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app.lofig import Config, VERSION, logger

router = APIRouter()

PRODUCT_ID = 4
SKIP_DIRS = {'.git', 'config', 'data', 'logs', 'sources', '__pycache__'}


def _ver_key(v):
    return tuple(int(x) for x in str(v).split('.') if x.isdigit())


def _update_server():
    return str(Config.client_config().get('update_server', 'https://prod.ailyf.cn')).rstrip('/')


async def _latest_version():
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{_update_server()}/api/products/{PRODUCT_ID}/latest")
        r.raise_for_status()
        data = r.json()
    return (data.get('latest_version') or {}).get('version', '').lstrip('v')


@router.get("/update/check")
async def check_update():
    try:
        latest = await _latest_version()
        return {
            "current": VERSION,
            "latest": latest,
            "upgrade": Config.client_config().get('upgrade', 'auto'),
            "has_update": bool(latest) and _ver_key(latest) > _ver_key(VERSION),
            "url": f"{_update_server()}/downloads/fastread/fastread-{latest}.zip"
        }
    except Exception as e:
        logger.warning("update check failed: %s", e)
        return {"error": str(e)}


_update_lock = threading.Lock()

class UpdateConfigModel(BaseModel):
    update_server: str = ""
    upgrade: str = "auto"


@router.get("/update/config")
async def get_update_config():
    client = Config.client_config()
    return {
        "update_server": client.get("update_server", "https://prod.ailyf.cn"),
        "upgrade": client.get("upgrade", "auto"),
    }


@router.post("/update/config")
async def save_update_config(request: UpdateConfigModel):
    client = Config.client_config()
    if request.update_server.strip():
        client["update_server"] = request.update_server.strip()
    client["upgrade"] = request.upgrade.strip() or "auto"
    Config.save(Config.all_configs())
    return {"message": "更新设置已保存"}


def _extract_zip(zip_path, dest):
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            if member.endswith('/'):
                continue
            parts = member.split('/')
            rel = '/'.join(parts[1:]) if len(parts) > 1 else parts[0]
            if not rel:
                continue
            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with zf.open(member) as src, open(out, 'wb') as dst:
                shutil.copyfileobj(src, dst)


def _overwrite_from(staging, root):
    for dirpath, dirnames, filenames in os.walk(staging):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), staging)
            if rel.split(os.sep)[0] in SKIP_DIRS:
                continue
            dst = os.path.join(root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(dirpath, fn), dst)


def _run_migrate(root):
    migrate = os.path.join(root, 'tools', 'migrate_db.py')
    if not os.path.isfile(migrate):
        return "未找到迁移脚本 tools/migrate_db.py"
    python_exe = sys.executable
    if os.path.basename(python_exe).lower() == "pythonservice.exe":
        python_exe = os.path.join(sys.exec_prefix, "python.exe")
    r = subprocess.run([python_exe, migrate, "migrate"], capture_output=True, text=True)
    if r.returncode != 0:
        return f"数据库迁移失败:\n{(r.stdout or '') + (r.stderr or '')}"
    return ""


@router.post("/update/apply")
async def apply_update():
    if not _update_lock.acquire(blocking=False):
        return {"status": "busy", "message": "更新正在进行中"}
    try:
        try:
            latest = await _latest_version()
            if not latest or _ver_key(latest) <= _ver_key(VERSION):
                return {"status": "no_update", "message": "已是最新版本"}
        except Exception as e:
            logger.warning("update check failed: %s", e)
            return {"status": "error", "message": f"检查更新失败: {e}"}

        tmp = tempfile.mkdtemp(prefix='fastread_upd_')
        try:
            zip_url = f"{_update_server()}/downloads/fastread/fastread-{latest}.zip"
            zip_path = os.path.join(tmp, 'update.zip')
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    async with client.stream("GET", zip_url) as r:
                        r.raise_for_status()
                        with open(zip_path, 'wb') as f:
                            async for chunk in r.aiter_bytes(65536):
                                f.write(chunk)
            except Exception as e:
                return {"status": "error", "message": f"下载更新包失败: {e}"}

            try:
                bad = zipfile.ZipFile(zip_path).testzip()
                if bad:
                    return {"status": "error", "message": f"更新包损坏 ({bad})"}
            except zipfile.BadZipFile:
                return {"status": "error", "message": "更新包无效"}

            staging = os.path.join(tmp, 'staging')
            os.makedirs(staging)
            _extract_zip(zip_path, staging)

            if not os.path.isfile(os.path.join(staging, 'main.py')):
                return {"status": "error", "message": "更新包内容不完整"}

            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            try:
                _overwrite_from(staging, root)
            except PermissionError:
                logger.exception("update overwrite denied")
                return {"status": "error", "message": "覆盖更新失败: 权限不足, 请以管理员权限运行或重新运行安装程序"}
            except Exception as e:
                logger.exception("update overwrite failed")
                return {"status": "error", "message": f"覆盖更新失败: {e}"}

            logger.info("update applied to v%s", latest)
            migrate_msg = _run_migrate(root)
            if migrate_msg:
                logger.warning("migrate after update: %s", migrate_msg)
                return {"status": "success", "message": f"已更新到 v{latest}, 数据库迁移失败: {migrate_msg}"}
            return {"status": "success", "message": f"已更新到 v{latest}, 请重启程序/服务生效"}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    finally:
        _update_lock.release()
