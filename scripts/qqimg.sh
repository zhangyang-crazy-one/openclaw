#!/usr/bin/env bash
# QQ图片快捷命令
# 用法: qqimg <qq号> "<图片下载链接>"
# 示例: qqimg 740884666 "https://multimedia.nt.qq.com.cn/download?..."

# 加载nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 22

cd /home/liujerry/moltbot

# 参数
TARGET="${1:-740884666}"
URL="$2"
SAVE_DIR="/home/liujerry/图片/qq"

if [ -z "$URL" ]; then
    echo "用法: qqimg <target> <图片URL>"
    echo ""
    echo "从QQ消息中复制图片下载链接，然后执行:"
    echo "  qqimg 740884666 'https://multimedia.nt.qq.com.cn/download?...' "
    exit 1
fi

# 下载图片
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="qq_${TIMESTAMP}.jpg"
SAVE_PATH="${SAVE_DIR}/${FILENAME}"

echo "📥 下载QQ图片..."
mkdir -p "$SAVE_DIR"

curl -L -o "$SAVE_PATH" "$URL"

if [ -f "$SAVE_PATH" ]; then
    SIZE=$(stat -c%s "$SAVE_PATH" 2>/dev/null || stat -f%z "$SAVE_PATH" 2>/dev/null)
    echo ""
    echo "✅ 下载成功!"
    echo "   文件: $SAVE_PATH"
    echo "   大小: $SIZE bytes"
    
    # 发送通知
    /home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw message send --target "$TARGET" --message "📥 图片已下载\n📁 $FILENAME\n📊 $SIZE bytes\n💾 $SAVE_PATH"
else
    echo "❌ 下载失败"
fi
