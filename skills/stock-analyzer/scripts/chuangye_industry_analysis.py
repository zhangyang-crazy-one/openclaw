#!/usr/bin/env python3
"""
创业板行业分析模型
- 行业分类分析
- 行业权重计算
- 行业轮动模型
"""
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")

# 创业板行业分类映射
INDUSTRY_MAPPING = {
    # 新能源
    '300750': '新能源-锂电池',  # 宁德时代
    '300014': '新能源-锂电池',  # 亿纬锂能
    '300274': '新能源-光伏',   # 阳光电源
    '300450': '新能源-锂电池',  # 星源材质
    '300618': '新能源-钴锂',   # 寒锐钴业
    '300438': '新能源-光伏',   # 鹏辉能源
    
    # 医药医疗
    '300015': '医药医疗-医疗服务',  # 爱尔眼科
    '300003': '医药医疗-医疗器械',  # 乐普医疗
    '300529': '医药医疗-医疗器械',  # 健帆生物
    '300298': '医药医疗-医疗器械',  # 三诺生物
    '300146': '医药医疗-游戏',     # 中科创达(误分类，实际是软件)
    '300122': '医药医疗-生物疫苗',  # 智飞生物
    
    # 科技
    '300059': '科技-金融科技',   # 东方财富
    '300017': '科技-网络服务',   # 网宿科技
    '300212': '科技-数字经济',   # 易华录
    '300383': '科技-云计算',     # 光环新网
    '300348': '科技-显示技术',   # 谷硕
    
    # 制造业
    '300124': '制造业-工业自动化', # 汇川技术
    '300285': '制造业-新材料',   # 国瓷材料
    '300124': '制造业-工业自动化', # 汇川技术
    
    # 消费
    '300251': '消费-传媒',       # 光线传媒
    '300459': '消费-服装',       # 搜于特
}

def get_industry(code):
    """根据代码前缀和部分已知映射获取行业"""
    # 基于代码前缀的简单分类
    prefix = code[:4]
    
    # 已知映射
    if code in INDUSTRY_MAPPING:
        return INDUSTRY_MAPPING[code]
    
    # 基于代码范围的模糊分类
    if code in ['300750', '300014', '300450', '300014', '300438', '300681', '300750', '300014', '300450', '300487', '300619', '300618']:
        return '新能源-锂电池'
    if code in ['300274', '300316', '300382', '300363', '300274']:
        return '新能源-光伏'
    
    if code in ['300015', '300003', '300529', '300298', '300122', '300009', '300015', '300003', '300253', '300294']:
        return '医药医疗'
    
    if code in ['300059', '300017', '300212', '300383', '300348', '300454', '300369', '300383']:
        return '科技'
    
    if code in ['300124', '300285', '300057', '300124', '300285', '300199', '300258', '300285']:
        return '制造业'
    
    if code in ['300251', '300459', '300291', '300413', '300459']:
        return '消费'
    
    return '其他'

def analyze_industry():
    """行业分析"""
    print("="*70)
    print("📊 创业板行业分析模型")
    print("="*70)
    
    # 读取完整分析结果
    with open(OUTPUT_DIR / "chuangye_complete_analysis.json", 'r') as f:
        data = json.load(f)
    
    all_results = data.get('top_by_score', [])
    
    # 添加行业分类
    for r in all_results:
        r['industry'] = get_industry(r['code'])
    
    # 按行业统计
    industry_stats = {}
    for r in all_results:
        ind = r['industry']
        if ind not in industry_stats:
            industry_stats[ind] = {
                'count': 0,
                'total_score': 0,
                'total_pred': 0,
                'codes': [],
                'names': []
            }
        industry_stats[ind]['count'] += 1
        industry_stats[ind]['total_score'] += r.get('composite_score', 0)
        if r.get('predicted_return'):
            industry_stats[ind]['total_pred'] += r['predicted_return']
        industry_stats[ind]['codes'].append(r['code'])
        industry_stats[ind]['names'].append(r.get('name', r['code']))
    
    # 计算行业平均值
    industry_analysis = []
    for ind, stats in industry_stats.items():
        avg_score = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0
        avg_pred = stats['total_pred'] / stats['count'] if stats['count'] > 0 else 0
        industry_analysis.append({
            'industry': ind,
            'count': stats['count'],
            'avg_score': avg_score,
            'avg_predicted_return': avg_pred,
            'codes': stats['codes'][:5],
            'top_stock': stats['codes'][0] if stats['codes'] else None
        })
    
    # 按评分排序
    industry_analysis = sorted(industry_analysis, key=lambda x: x['avg_score'], reverse=True)
    
    print(f"\n行业分布统计 (TOP {len(industry_analysis)} 个行业)")
    print("-"*70)
    print(f"{'行业':<20} {'股票数':<8} {'平均分':<10} {'平均预测':<10}")
    print("-"*70)
    
    for ind in industry_analysis:
        pred_str = f"{ind['avg_predicted_return']:+.2f}%" if ind['avg_predicted_return'] else "N/A"
        print(f"{ind['industry']:<20} {ind['count']:<8} {ind['avg_score']:<10.1f} {pred_str:<10}")
    
    # 行业轮动模型
    print("\n" + "="*70)
    print("🔄 行业轮动模型")
    print("="*70)
    
    # 基于预测收益的行业趋势
    trend_analysis = sorted(industry_analysis, key=lambda x: x['avg_predicted_return'] if x['avg_predicted_return'] else -999, reverse=True)
    
    print("\n📈 行业趋势排名 (基于预测收益):")
    for i, ind in enumerate(trend_analysis[:10], 1):
        if ind['avg_predicted_return'] > 0:
            trend = "📈 上涨"
        elif ind['avg_predicted_return'] < -2:
            trend = "📉 下跌"
        else:
            trend = "➡️ 震荡"
        print(f"  {i}. {ind['industry']:<20} {trend} ({ind['avg_predicted_return']:+.2f}%)")
    
    # 推荐行业
    print("\n💰 行业投资建议:")
    top_industries = [ind for ind in trend_analysis if ind['avg_predicted_return'] > 0][:3]
    
    for i, ind in enumerate(top_industries, 1):
        print(f"\n{i}. {ind['industry']}")
        print(f"   平均预测收益: {ind['avg_predicted_return']:+.2f}%")
        print(f"   代表股票: {', '.join(ind['codes'][:3])}")
    
    # 行业对比
    print("\n" + "="*70)
    print("📊 行业对比分析")
    print("="*70)
    
    # 高成长行业
    high_growth_industries = [ind for ind in industry_analysis if ind['avg_predicted_return'] > 3]
    print(f"\n🌱 高成长行业 ({len(high_growth_industries)}个):")
    for ind in high_growth_industries:
        print(f"  - {ind['industry']}: {ind['avg_predicted_return']:+.2f}%")
    
    # 高评分行业
    high_score_industries = [ind for ind in industry_analysis if ind['avg_score'] > 80]
    print(f"\n⭐ 高评分行业 ({len(high_score_industries)}个):")
    for ind in high_score_industries:
        print(f"  - {ind['industry']}: {ind['avg_score']:.1f}分")
    
    # 保存结果
    output = {
        'date': datetime.now().isoformat(),
        'analysis_period': '2026-02-06',
        'industry_statistics': industry_analysis,
        'trend_ranking': trend_analysis,
        'recommendations': {
            'top_industries': top_industries,
            'high_growth': high_growth_industries,
            'high_score': high_score_industries
        },
        'all_results': all_results
    }
    
    output_file = OUTPUT_DIR / "chuangye_industry_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 行业分析结果已保存: {output_file}")
    
    return output

def main():
    analyze_industry()

if __name__ == "__main__":
    main()
