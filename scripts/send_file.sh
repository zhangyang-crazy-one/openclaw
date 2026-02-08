#!/usr/bin/env bash
# 发送本地文件到QQ
# 使用方法: bash send_file.sh <target> <file_path> [caption]

# 加载nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 使用Node 22
nvm use 22

# 参数检查
if [ $# -lt 2 ]; then
    echo "用法: $0 <target> <file_path> [caption]"
    echo "示例: $0 740884666 /path/to/image.png 这是图片"
    echo "示例: $0 740884666 /path/to/report.pdf 报告文件"
    exit 1
fi

TARGET="$1"
FILE_PATH="$2"
CAPTION="${3:-}"

cd /home/liujerry/moltbot

# 设置邮箱密码环境变量
export QQ_IMAP_PASSWORD="auoopvlygaoybbci"

# 运行发送脚本
python3 << 'PYEOF'
import sys
import os
import subprocess

TARGET = "$TARGET"
FILE_PATH = "$FILE_PATH"
CAPTION = "$CAPTION"

# 验证文件存在
if not os.path.exists(FILE_PATH):
    print(f"❌ 文件不存在: {FILE_PATH}")
    sys.exit(1)

# 获取文件扩展名
import os.path
ext = os.path.splitext(FILE_PATH)[1].lower()

# 根据文件类型选择发送方式
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
AUDIO_EXT = {'.mp3', '.wav', '.ogg', '.flac', '.silk', '.m4a'}
VIDEO_EXT = {'.mp4', '.mov', '.webm', '.mkv', '.avi'}

if ext in IMAGE_EXT:
    media_type = "image"
elif ext in AUDIO_EXT:
    media_type = "record"
elif ext in VIDEO_EXT:
    media_type = "video"
else:
    media_type = "file"

print(f"📎 发送文件: {FILE_PATH}")
print(f"   类型: {media_type}")
print(f"   目标: {TARGET}")
if CAPTION:
    print(f"   备注: {CAPTION}")

# 构建CQ码
from cqcode import buildCqMessage

# 使用file://协议
file_url = f"file://{os.path.abspath(FILE_PATH)}"

message = buildCqMessage({
    "text": CAPTION,
    "mediaUrl": file_url,
    "mediaType": media_type,
})

print(f"\n📤 消息内容: {message[:100]}...")
print("\n✅ 准备发送...")
PYEOF

echo ""
echo "通过 OpenClaw 发送..."

/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw message send --target "$TARGET" --message "📎 文件: $(basename $FILE_PATH)"
