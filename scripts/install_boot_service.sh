#!/usr/bin/env bash
# 安装 FastRead 桌面启动器 (macOS / Linux)
# 用法: bash scripts/install_boot_service.sh [--service]
#   --service  额外注册开机自启后台服务 (crontab @reboot)，默认不启用
# 自定义 Python: PYTHON=/path/to/python bash scripts/install_boot_service.sh
set -euo pipefail

SERVICE="${SERVICE:-0}"
case "${1:-}" in
    --service) SERVICE=1 ;;
    --no-service) SERVICE=0 ;;
    -h|--help)
        echo "用法: bash scripts/install_boot_service.sh [--service]"
        echo "  --service  注册开机自启后台服务 (默认仅创建桌面启动器)"
        exit 0
        ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PY_MIN="3.9"

echo "==> 检查 Python"
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
    if [ -x "$PROJECT_DIR/.venv/read/bin/python" ]; then
        PYTHON="$PROJECT_DIR/.venv/read/bin/python"
    elif [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
        PYTHON="$PROJECT_DIR/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        PYTHON="$(command -v python)"
    else
        echo "未找到 python。请先安装 Python ${PY_MIN}+: https://www.python.org/downloads/" >&2
        exit 1
    fi
fi

if ! "$PYTHON" --version >/dev/null 2>&1; then
    echo "无法执行 $PYTHON，请检查 Python 安装。" >&2
    exit 1
fi
echo "   使用 Python: $("$PYTHON" --version 2>&1) ($PYTHON)"

if ! "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int, '$PY_MIN'.split('.'))) else 1)"; then
    echo "Python 版本过低: 需要 ${PY_MIN}+，当前为 $("$PYTHON" --version 2>&1)。请升级 Python。" >&2
    exit 1
fi

echo "==> 安装/更新依赖"
if ! "$PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt"; then
    echo "依赖安装失败。如系统 Python 受管理(PEP 668)，可改用虚拟环境，例如:" >&2
    echo "  $PYTHON -m venv $PROJECT_DIR/.venv && PYTHON=$PROJECT_DIR/.venv/bin/python bash $SCRIPT_DIR/install_boot_service.sh" >&2
    exit 1
fi

if [ "$SERVICE" = "1" ]; then
    echo "==> 配置开机启动 (crontab @reboot)"
    mkdir -p "$PROJECT_DIR/logs"
    CRON_LINE="@reboot mkdir -p $PROJECT_DIR/logs && cd $PROJECT_DIR && $PYTHON $PROJECT_DIR/main.py >> $PROJECT_DIR/logs/cron_boot.log 2>&1"

    if (crontab -l 2>/dev/null || true) | grep -Fqx "$CRON_LINE"; then
        echo "   开机启动任务已存在，跳过。"
    else
        (crontab -l 2>/dev/null || true; echo "$CRON_LINE") | crontab -
        echo "   已添加: $CRON_LINE"
    fi
else
    echo "==> 跳过开机自启后台服务 (使用 --service 参数可启用)"
fi

echo "==> 安装桌面版依赖 (PyQt6 / PyQt6-WebEngine)"
"$PYTHON" -m pip install PyQt6 PyQt6-WebEngine

echo "==> 创建桌面启动器"
case "$(uname)" in
    Darwin)
        APP_NAME="FastRead"
        APP_PATH="/Applications/$APP_NAME.app"
        VERSION="$("$PYTHON" -c "import sys; sys.path.insert(0, '$PROJECT_DIR/app'); import lofig; print(lofig.VERSION)" 2>/dev/null || echo '1.0.0')"
        rm -rf "$APP_PATH"
        mkdir -p "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources"

        if [ -f "$PROJECT_DIR/res/icon.icns" ]; then
            cp "$PROJECT_DIR/res/icon.icns" "$APP_PATH/Contents/Resources/icon.icns"
        fi

        cat > "$APP_PATH/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>FastRead</string>
    <key>CFBundleDisplayName</key>
    <string>FastRead</string>
    <key>CFBundleIdentifier</key>
    <string>com.fastread.desktop</string>
    <key>CFBundleExecutable</key>
    <string>FastRead</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

        cat > "$APP_PATH/Contents/MacOS/$APP_NAME" <<LAUNCHER
#!/bin/bash
cd "$PROJECT_DIR"
exec "$PYTHON" "$PROJECT_DIR/desktop.py"
LAUNCHER
        chmod +x "$APP_PATH/Contents/MacOS/$APP_NAME"
        echo "   已创建: $APP_PATH"
        ;;
    Linux)
        DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
        ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
        DESKTOP_FILE="$DESKTOP_DIR/FastRead.desktop"
        mkdir -p "$DESKTOP_DIR" "$ICON_DIR"

        ICON_LINE=""
        if [ -f "$PROJECT_DIR/res/icon.png" ]; then
            cp "$PROJECT_DIR/res/icon.png" "$ICON_DIR/FastRead.png"
            ICON_LINE="Icon=$ICON_DIR/FastRead.png"
        fi

        cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=FastRead
Comment=FastRead 桌面客户端
Exec="$PYTHON" "$PROJECT_DIR/desktop.py"
Path=$PROJECT_DIR
$ICON_LINE
Terminal=false
DESKTOP
        chmod +x "$DESKTOP_FILE"
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
        fi
        echo "   已创建: $DESKTOP_FILE"
        ;;
    *)
        echo "   不支持的平台: $(uname)，跳过桌面启动器创建。" >&2
        ;;
esac

echo "==> 完成"
