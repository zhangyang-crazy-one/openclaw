#!/usr/bin/env python3
"""
A股股票分析器 - 个股深度分析
"""
import sys
import json
import argparse

sys.path.insert(0, __file__.rsplit('/', 1)[0])

from data_fetcher import AStockDataFetcher
from technical_indicators import calculate_williams_r, calculate_rsi, calculate_bollinger_bands, calculate_macd, calculate_kdj
from formulas import BuffettFormula, analyze_stock_fundamental


def analyze_single_stock(stock_code: str, name: str = "") -> dict:
    """
    深度分析单只股票
    
    Args:
        stock_code: 股票代码，如 '300502'
        name: 股票名称
    
    Returns:
        分析结果字典
    """
    fetcher = AStockDataFetcher()
    
    result = {
        'code': stock_code,
        'name': name,
        'timestamp': datetime.now().isoformat()
    }
    
    # 1. 获取实时行情
    print("获取实时行情...")
    realtime = fetcher.get_realtime_quote(stock_code)
    if realtime:
        result['realtime'] = realtime
        print(f"  最新价: {realtime.get('price')}")
    
    # 2. 获取历史数据和技术指标
    print("获取历史数据...")
    formatted_code = stock_code.zfill(6)
    if formatted_code.startswith('6'):
        formatted_code = f"sh.{formatted_code}"
    else:
        formatted_code = f"sz.{formatted_code}"
    
    df = fetcher.get_price_data(formatted_code, days=180)
    
    if df is None or len(df) < 30:
        print("  无法获取数据")
        fetcher.close()
        return None
    
    # 计算技术指标
    print("计算技术指标...")
    df['williams_r'] = calculate_williams_r(
        df['high'].astype(float),
        df['low'].astype(float),
        df['close'].astype(float),
        period=14
    )
    
    df['rsi'] = calculate_rsi(df['close'].astype(float), period=14)
    
    df['macd_dif'], df['macd_dea'], df['macd'] = calculate_macd(df['close'].astype(float))
    
    df['kdj_k'], df['kdj_d'], df['kdj_j'] = calculate_kdj(
        df['high'].astype(float),
        df['low'].astype(float),
        df['close'].astype(float)
    )
    
    middle, upper, lower = calculate_bollinger_bands(df['close'].astype(float))
    df['bb_middle'] = middle
    df['bb_upper'] = upper
    df['bb_lower'] = lower
    
    # 获取最新数据
    latest = df.iloc[-1]
    
    # 技术分析结果
    tech_analysis = {
        'price': round(float(latest['close']), 2),
        'change_pct': round(float(latest['pctChg']), 2) if latest['pctChg'] else 0,
        'williams_r': round(float(latest['williams_r']), 2) if latest['williams_r'] else None,
        'rsi': round(float(latest['rsi']), 2) if latest['rsi'] else None,
        'macd': {
            'dif': round(float(latest['macd_dif']), 2) if latest['macd_dif'] else None,
            'dea': round(float(latest['macd_dea']), 2) if latest['macd_dea'] else None,
            'histogram': round(float(latest['macd']), 2) if latest['macd'] else None,
        },
        'kdj': {
            'k': round(float(latest['kdj_k']), 2) if latest['kdj_k'] else None,
            'd': round(float(latest['kdj_d']), 2) if latest['kdj_d'] else None,
            'j': round(float(latest['kdj_j']), 2) if latest['kdj_j'] else None,
        },
        'bollinger': {
            'upper': round(float(latest['bb_upper']), 2) if latest['bb_upper'] else None,
            'middle': round(float(latest['bb_middle']), 2) if latest['bb_middle'] else None,
            'lower': round(float(latest['bb_lower']), 2) if latest['bb_lower'] else None,
        }
    }
    
    # 技术信号判断
    signals = []
    
    # Williams %R
    wr = tech_analysis['williams_r']
    if wr and wr <= -80:
        signals.append(("Williams %R", "超卖-可能反弹", "买入信号"))
    elif wr and wr <= -70:
        signals.append(("Williams %R", "接近超卖", "关注"))
    
    # RSI
    rsi = tech_analysis['rsi']
    if rsi and rsi <= 30:
        signals.append(("RSI", "超卖", "关注"))
    elif rsi and rsi >= 70:
        signals.append(("RSI", "超买", "风险"))
    
    # KDJ
    kdj_j = tech_analysis['kdj']['j']
    if kdj_j and kdj_j < 0:
        signals.append(("KDJ", "J值为负", "超卖信号"))
    elif kdj_j and kdj_j > 100:
        signals.append(("KDJ", "J值超100", "超买信号"))
    
    # MACD
    macd_hist = tech_analysis['macd']['histogram']
    if macd_hist and macd_hist > 0:
        signals.append(("MACD", "多头", "看涨"))
    elif macd_hist and macd_hist < 0:
        signals.append(("MACD", "空头", "看跌"))
    
    # 布林带
    price = tech_analysis['price']
    bb_lower = tech_analysis['bollinger']['lower']
    if bb_lower and price <= bb_lower * 1.03:
        signals.append(("布林带", "触及下轨", "支撑位"))
    
    tech_analysis['signals'] = signals
    
    result['technical'] = tech_analysis
    
    # 3. 基本面分析
    print("获取基本面数据...")
    financial = fetcher.get_financial_data(stock_code)
    
    if financial:
        result['fundamental'] = financial
        
        # 简化巴菲特分析
        if financial.get('roe'):
            roe = float(financial['roe'])
            rating = "优秀" if roe > 15 else "良好" if roe > 10 else "一般" if roe > 5 else "较差"
            result['fundamental_analysis'] = {
                'roe': roe,
                'rating': rating
            }
    
    # 4. 综合建议
    print("生成综合建议...")
    
    # 评分
    score = 0
    
    # 技术面评分
    if wr and wr <= -80:
        score += 3
    elif wr and wr <= -70:
        score += 1
    
    if rsi and rsi <= 30:
        score += 2
    
    if macd_hist and macd_hist > 0:
        score += 1
    
    # 基本面评分
    if financial:
        if financial.get('roe'):
            roe = float(financial['roe'])
            if roe > 15:
                score += 3
            elif roe > 10:
                score += 2
            elif roe > 5:
                score += 1
    
    # 综合评级
    if score >= 7:
        recommendation = "强烈推荐"
    elif score >= 5:
        recommendation = "建议关注"
    elif score >= 3:
        recommendation = "中性观望"
    else:
        recommendation = "建议回避"
    
    result['score'] = score
    result['recommendation'] = recommendation
    
    fetcher.close()
    
    return result


def main():
    parser = argparse.ArgumentParser(description='A股股票深度分析')
    parser.add_argument('stock_code', help='股票代码，如 300502')
    parser.add_argument('--name', '-n', help='股票名称')
    parser.add_argument('--output', '-o', help='输出JSON文件路径')
    
    args = parser.parse_args()
    
    print(f"分析股票: {args.stock_code} {args.name or ''}")
    print("=" * 50)
    
    result = analyze_single_stock(args.stock_code, args.name)
    
    if result is None:
        print("分析失败")
        sys.exit(1)
    
    # 打印结果
    print("\n" + "=" * 50)
    print("分析结果")
    print("=" * 50)
    
    print(f"\n📊 {result['code']} {result['name']}")
    print(f"综合评分: {result['score']}/10")
    print(f"综合建议: {result['recommendation']}")
    
    if result.get('technical'):
        tech = result['technical']
        print(f"\n📈 技术分析:")
        print(f"  当前价格: {tech['price']}")
        print(f"  Williams %R: {tech['williams_r']}")
        print(f"  RSI(14): {tech['rsi']}")
        
        print(f"  MACD: DIF={tech['macd']['dif']}, DEA={tech['macd']['dea']}")
        
        print(f"  KDJ: K={tech['kdj']['k']}, D={tech['kdj']['d']}, J={tech['kdj']['j']}")
        
        print(f"  布林带: {tech['bollinger']['upper']}/{tech['bollinger']['middle']}/{tech['bollinger']['lower']}")
        
        if tech['signals']:
            print(f"\n  技术信号:")
            for indicator, status, action in tech['signals']:
                print(f"    - {indicator}: {status} → {action}")
    
    if result.get('fundamental'):
        fund = result['fundamental']
        print(f"\n📋 基本面:")
        if fund.get('roe'):
            print(f"  净资产收益率(ROE): {fund['roe']}%")
        if fund.get('pe'):
            print(f"  市盈率(PE): {fund['pe']}")
        if fund.get('pb'):
            print(f"  市净率(PB): {fund['pb']}")
    
    if result.get('fundamental_analysis'):
        fa = result['fundamental_analysis']
        print(f"  基本面评级: {fa['rating']}")
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    from datetime import datetime
    main()
