#!/bin/bash
# A股数据补全计划 - 4天完成
# Day 1: 识别并补全缺失K线
# Day 2: 更新全量K线到最新
# Day 3: 数据清洗
# Day 4: 验证

echo "=== A股数据补全计划 ==="
echo "开始时间: $(date)"
echo ""

# Step 1: 识别缺失的股票
echo "[Day 1] Step 1: 识别缺失的股票..."
python3 << 'EOF'
import pandas as pd
from pathlib import Path
import subprocess

# 获取A股列表
try:
    import akshare as ak
    df = ak.stock_info_a_code_name()
    all_codes = set(df[df['code'].str.match(r'^(600|601|603|000|001|002|300|688)')]['code'].tolist())
    print(f"市场总股票数: {len(all_codes)}")
except Exception as e:
    print(f"获取市场列表失败: {e}")
    all_codes = set()

# 已有K线
stocks_dir = Path("/home/liujerry/金融数据/stocks")
existing = set(f.stem for f in stocks_dir.glob("*.csv"))
print(f"已有K线: {len(existing)}")

# 缺失
missing = all_codes - existing
print(f"缺失K线: {len(missing)}")

# 保存缺失列表
with open("/tmp/missing_stocks.txt", "w") as f:
    for code in sorted(missing):
        f.write(f"{code}\n")

print(f"缺失列表已保存: /tmp/missing_stocks.txt")
EOF

echo ""
echo "缺失股票已识别，下一步将更新..."
