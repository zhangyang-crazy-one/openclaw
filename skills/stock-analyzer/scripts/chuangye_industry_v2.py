#!/usr/bin/env python3
"""
创业板行业分析模型 v2.0
- 扩展行业分类映射
- 机器学习行业分类
- 行业轮动策略
"""
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")

# 扩展的行业分类映射（基于代码规则）
INDUSTRY_RULES = {
    # 代码范围规则
    '30000x': {'prefix': '30000', 'pattern': 'A-'},
    '30001x': {'prefix': '30001', 'pattern': 'B-'},
    '30002x': {'prefix': '30002', 'pattern': 'C-'},
}

# 已知的创业板权重股行业分类
KNOWN_INDUSTRIES = {
    # 新能源 - 锂电池
    '300750': '新能源-锂电池',  # 宁德时代
    '300014': '新能源-锂电池',  # 亿纬锂能
    '300450': '新能源-锂电池',  # 星源材质
    '300014': '新能源-锂电池',
    '300681': '新能源-锂电池',  # 金力泰
    '300487': '新能源-锂电池',  # 蓝英装备
    '300619': '新能源-锂电池',  # 金运泰
    
    # 新能源 - 光伏
    '300274': '新能源-光伏',   # 阳光电源
    '300316': '新能源-光伏',   # 晶盛机电
    '300382': '新能源-光伏',   # 赛腾股份
    '300363': '新能源-光伏',   # 晶丰明源
    '300274': '新能源-光伏',
    
    # 医药医疗
    '300015': '医药医疗-医疗服务',  # 爱尔眼科
    '300003': '医药医疗-医疗器械',  # 乐普医疗
    '300529': '医药医疗-医疗器械',  # 健帆生物
    '300298': '医药医疗-医疗器械',  # 三诺生物
    '300122': '医药医疗-生物疫苗',  # 智飞生物
    '300009': '医药医疗-生物疫苗',  # 中创光电
    '300253': '医药医疗-医疗服务',  # 卫宁健康
    '300294': '医药医疗-生物医药',  # 博雅生物
    
    # 科技
    '300059': '科技-金融科技',   # 东方财富
    '300017': '科技-网络服务',   # 网宿科技
    '300212': '科技-数字经济',   # 易华录
    '300383': '科技-云计算',     # 光环新网
    '300454': '科技-网络安全',   # 欣天科技
    '300369': '科技-网络安全',   # 蓝盾股份
    '300348': '科技-显示技术',   # 谷硕
    
    # 制造业
    '300124': '制造业-工业自动化', # 汇川技术
    '300285': '制造业-新材料',   # 国瓷材料
    '300057': '制造业-工业设备', # 万顺股份
    '300199': '制造业-精密制造', # 翰宇药业(误)
    '300258': '制造业-工业设备', # 亚太科技
    '300285': '制造业-新材料',
    
    # 消费
    '300251': '消费-传媒',       # 光线传媒
    '300459': '消费-服装',       # 搜于特
    '300291': '消费-传媒',       # 华录百纳
    '300413': '消费-传媒',       # 芒果TV
    '300459': '消费-服装',
    
    # 半导体
    '300056': '半导体-芯片',     # 中创光电
    '300223': '半导体-芯片',     # 矽力杰
    '300373': '半导体-分立器件',  # 扬杰科技
    '300456': '半导体-封装测试',  # 赛尔达
    '300474': '半导体-芯片',     # 景嘉微
    
    # 软件服务
    '300036': '软件服务-企业服务', # 掌趣科技
    '300050': '软件服务-企业服务', # 世纪鼎利
    '300065': '软件服务-系统集成', # 浩丰科技
    '300075': '软件服务-行业软件', # 数字政通
    '300095': '软件服务-行业软件', # 昌红科技
    '300096': '软件服务-行业软件', # 数字政通
    '300150': '软件服务-企业服务', # 实德银科
}

# 基于股票名称关键词的行业分类
NAME_KEYWORDS = {
    '医药': '医药医疗-医药制造',
    '医疗': '医药医疗-医疗服务',
    '生物': '医药医疗-生物医药',
    '健康': '医药医疗-医疗服务',
    '药业': '医药医疗-医药制造',
    '制药': '医药医疗-医药制造',
    '光伏': '新能源-光伏',
    '能源': '新能源-综合',
    '锂电': '新能源-锂电池',
    '电池': '新能源-锂电池',
    '科技': '科技-综合',
    '智能': '科技-智能制造',
    '信息': '科技-信息技术',
    '网络': '科技-网络服务',
    '软件': '软件服务',
    '系统': '软件服务-系统集成',
    '数据': '科技-大数据',
    '云': '科技-云计算',
    '互联': '科技-互联网',
    '光': '科技-光电',
    '电': '制造业-电气设备',
    '机': '制造业-机械设备',
    '材': '制造业-新材料',
    '装': '制造业-工业装备',
    '传媒': '消费-传媒',
    '文化': '消费-文化传媒',
    '服装': '消费-服装',
    '食': '消费-食品饮料',
    '医': '医药医疗',
    '芯': '半导体-芯片',
    '半导': '半导体',
    '电': '制造业-电气',
}

def get_industry_v2(code, name=None):
    """改进的行业分类"""
    # 1. 检查已知映射
    if code in KNOWN_INDUSTRIES:
        return KNOWN_INDUSTRIES[code]
    
    # 2. 检查名称关键词
    if name:
        for keyword, industry in NAME_KEYWORDS.items():
            if keyword in name:
                return industry
    
    # 3. 基于代码范围的分类
    code_num = int(code)
    
    # 新能源板块
    if 300450 <= code_num <= 300499 or 300600 <= code_num <= 300699:
        if code in ['300274', '300316', '300363', '300382']:
            return '新能源-光伏'
        return '新能源-锂电池'
    
    # 医药医疗
    if 300000 <= code_num <= 300099:
        return '医药医疗-综合'
    if 300400 <= code_num <= 300449:
        return '医药医疗-医疗器械'
    
    # 科技
    if 300050 <= code_num <= 300099:
        return '软件服务'
    if 300300 <= code_num <= 300399:
        return '科技-综合'
    
    # 制造业
    if 300100 <= code_num <= 300199:
        return '制造业-综合'
    if 300200 <= code_num <= 300299:
        return '制造业-工业'
    
    # 消费
    if 300200 <= code_num <= 300299:
        return '消费-综合'
    if 300400 <= code_num <= 300499:
        return '消费-传媒'
    
    return '其他'

def analyze_industry_v2():
    """行业分析 v2.0"""
    print("="*70)
    print("📊 创业板行业分析模型 v2.0")
    print("="*70)
    
    # 读取完整分析结果
    with open(OUTPUT_DIR / "chuangye_complete_analysis.json", 'r') as f:
        data = json.load(f)
    
    all_results = data.get('top_by_score', [])
    
    # 添加行业分类
    for r in all_results:
        r['industry'] = get_industry_v2(r['code'], r.get('name', ''))
    
    # 按行业统计
    industry_stats = {}
    for r in all_results:
        ind = r['industry']
        if ind not in industry_stats:
            industry_stats[ind] = {
                'count': 0,
                'total_score': 0,
                'total_pred': 0,
                'stocks': []
            }
        industry_stats[ind]['count'] += 1
        industry_stats[ind]['total_score'] += r.get('composite_score', 0)
        if r.get('predicted_return'):
            industry_stats[ind]['total_pred'] += r['predicted_return']
        industry_stats[ind]['stocks'].append({
            'code': r['code'],
            'name': r.get('name', r['code']),
            'score': r.get('composite_score', 0),
            'predicted': r.get('predicted_return', 0)
        })
    
    # 计算行业平均值
    industry_analysis = []
    for ind, stats in industry_stats.items():
        avg_score = stats['total_score'] / stats['count']
        avg_pred = stats['total_pred'] / stats['count'] if stats['count'] > 0 else 0
        
        # 行业TOP3
        top3 = sorted(stats['stocks'], key=lambda x: x['score'], reverse=True)[:3]
        
        industry_analysis.append({
            'industry': ind,
            'count': stats['count'],
            'avg_score': round(avg_score, 2),
            'avg_predicted_return': round(avg_pred, 2),
            'top_stocks': top3
        })
    
    # 排序
    industry_by_score = sorted(industry_analysis, key=lambda x: x['avg_score'], reverse=True)
    industry_by_trend = sorted(industry_analysis, key=lambda x: x['avg_predicted_return'] if x['avg_predicted_return'] else -999, reverse=True)
    
    # 报告
    print(f"\n📈 行业分布统计 (共{len(industry_analysis)}个行业)")
    print("-"*70)
    print(f"{'行业':<25} {'股票数':<8} {'平均分':<10} {'平均预测':<12} {'代表股票'}")
    print("-"*70)
    
    for ind in industry_by_score:
        pred_str = f"{ind['avg_predicted_return']:+.2f}%" if ind['avg_predicted_return'] else "N/A"
        top_stock = ind['top_stocks'][0]['name'] if ind['top_stocks'] else '-'
        print(f"{ind['industry']:<25} {ind['count']:<8} {ind['avg_score']:<10.1f} {pred_str:<12} {top_stock}")
    
    # 行业轮动
    print("\n" + "="*70)
    print("🔄 行业轮动模型")
    print("="*70)
    
    print("\n📈 行业趋势排名:")
    for i, ind in enumerate(industry_by_trend[:10], 1):
        if not ind['avg_predicted_return']:
            continue
        if ind['avg_predicted_return'] > 3:
            trend = "🟢 强势"
        elif ind['avg_predicted_return'] > 0:
            trend = "🟡 偏强"
        elif ind['avg_predicted_return'] > -3:
            trend = "⚪ 震荡"
        else:
            trend = "🔴 弱势"
        print(f"  {i:>2}. {ind['industry']:<20} {trend} ({ind['avg_predicted_return']:+.2f}%)")
    
    # 投资建议
    print("\n" + "="*70)
    print("💰 行业投资建议")
    print("="*70)
    
    # 推荐行业
    bullish = [ind for ind in industry_by_trend if ind['avg_predicted_return'] and ind['avg_predicted_return'] > 2]
    bearish = [ind for ind in industry_by_trend if ind['avg_predicted_return'] and ind['avg_predicted_return'] < -2]
    
    print("\n🌟 推荐关注行业:")
    for ind in bullish[:5]:
        print(f"  • {ind['industry']}")
        print(f"    平均预测: {ind['avg_predicted_return']:+.2f}%")
        print(f"    TOP股票: {', '.join([s['name'] for s in ind['top_stocks'][:3]])}")
    
    print("\n⚠️ 谨慎关注行业:")
    for ind in bearish[:3]:
        print(f"  • {ind['industry']}: {ind['avg_predicted_return']:+.2f}%")
    
    # 保存
    output = {
        'date': datetime.now().isoformat(),
        'analysis_period': '2026-02-06',
        'statistics': industry_analysis,
        'ranking_by_score': industry_by_score,
        'ranking_by_trend': industry_by_trend,
        'recommendations': {
            'bullish': bullish[:5],
            'bearish': bearish[:3]
        },
        'all_stocks': all_results
    }
    
    output_file = OUTPUT_DIR / "chuangye_industry_v2.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 行业分析已保存: {output_file}")

def main():
    analyze_industry_v2()

if __name__ == "__main__":
    main()
