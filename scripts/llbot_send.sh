#!/usr/bin/env bash
# 使用 llbot 发送文件到QQ
# 用法: llbot_send <target> <file_path> [caption]

LLBOT="/home/liujerry/下载/software/LLBot-CLI-linux-x64/llbot"

if [ $# -lt 2 ]; then
    echo "用法: $0 <target> <file_path> [caption]"
    echo "示例: $0 740884666 /home/liujerry/金融数据/stocks/600519.csv 贵州茅台数据"
    exit 1
fi

TARGET="$1"
FILE_PATH="$2"
CAPTION="${3:-}"

echo "📤 通过 llbot 发送文件..."
echo "   文件: $FILE_PATH"
echo "   目标: $TARGET"

# 发送文件
$LLBOT send --target "$TARGET" --file "$FILE_PATH"

# 如果有备注，发送备注消息
if [ -n "$CAPTION" ]; then
    sleep 2
    $LLBOT send --target "$TARGET" --message "$CAPTION"
fi
