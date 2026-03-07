#!/bin/bash
# 同步上游前备份重要脚本
# 防止上游同步时删除本地自定义脚本

BACKUP_DIR="/home/liujerry/moltbot/.script-backup/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=== 备份重要脚本 ==="

# 备份 scripts 目录中的自定义脚本
SCRIPTS=(
    "scripts/email_stat.py"
    "scripts/premarket_conservative.py"
    "scripts/academic_final.py"
    "scripts/moltbook_knowledge_sync.py"
    "scripts/moltbook_knowledge_sync_v3.py"
    "scripts/auto_extract_knowledge.py"
    "scripts/hypothesis_generator.py"
    "scripts/fars_system.py"
    "scripts/paper_reviewer.py"
    "scripts/research_workflow.py"
    "scripts/data_quality_monitor.py"
    "scripts/voice_report.py"
    "scripts/context/load_state.py"
    "scripts/context/task_wrapper.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "/home/liujerry/moltbot/$script" ]; then
        mkdir -p "$BACKUP_DIR/$(dirname $script)"
        cp -n "/home/liujerry/moltbot/$script" "$BACKUP_DIR/$script" 2>/dev/null
        echo "备份: $script"
    fi
done

# 备份 skills 目录中的自定义脚本
SKILLS=(
    "skills/unified-quant/unified_analysis_v2.py"
    "skills/unified-quant/src/probability_model.py"
    "skills/unified-quant/src/paper_citation.py"
    "skills/unified-quant/src/report_generator.py"
    "skills/unified-quant/src/validation/data_validator.py"
    "skills/unified-quant/src/local_data_loader.py"
    "skills/unified-quant/src/collect_batch_simple.py"
    "skills/unified-quant/src/collect_a_stock_batch.py"
)

for script in "${SKILLS[@]}"; do
    if [ -f "/home/liujerry/moltbot/$script" ]; then
        mkdir -p "$BACKUP_DIR/$(dirname $script)"
        cp -n "/home/liujerry/moltbot/$script" "$BACKUP_DIR/$script" 2>/dev/null
        echo "备份: $script"
    fi
done

echo ""
echo "=== 备份完成: $BACKUP_DIR ==="
echo "如需恢复，运行: cp -r $BACKUP_DIR/* /home/liujerry/moltbot/"
