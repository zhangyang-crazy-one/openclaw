# Stagehand 数据文件夹结构

## 📁 文件夹结构

```
~/stagehand_data/
├── github/                    # GitHub 相关数据
│   ├── repositories/          # 仓库信息
│   └── searches/             # 搜索结果
├── taobao/                   # 淘宝数据
│   ├── excel/                # Excel 表格
│   └── json/                 # 原始数据 JSON
└── screenshots/              # 截图
    ├── github/               # GitHub 截图
    └── taobao/               # 淘宝截图
```

## 📊 当前数据

### 淘宝数据
```
~/stagehand_data/taobao/
├── taobao_32g_memory_final_*.xlsx   # 32G 服务器内存价格表 ⭐
├── taobao_32g_result_*.json          # 原始采集数据
└── excel/
    └── (Excel 文件)
```

### 截图
```
~/stagehand_data/screenshots/
├── github_*.png          # GitHub 相关截图
└── taobao_*.png          # 淘宝相关截图
```

## 🚀 常用命令

### 打开淘宝数据文件夹
```bash
open ~/stagehand_data/taobao/
```

### 查看最新 Excel
```bash
ls -lt ~/stagehand_data/taobao/*.xlsx | head -3
```

### 查看截图
```bash
ls -la ~/stagehand_data/screenshots/
```

## 📝 采集历史

- **2026-02-08**: 淘宝 32G 服务器内存价格采集
  - 商品数: 10 个
  - 价格范围: ¥519 - ¥4993
  - 文件: `taobao_32g_memory_final_*.xlsx`
