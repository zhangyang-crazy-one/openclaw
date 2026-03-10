#!/usr/bin/env python3
"""
A股股票筛选器 - 综合筛选 (技术面 + 基本面)
结合 Williams %R 超卖信号和巴菲特公式
"""
import sys
import json
import argparse
from datetime import datetime

# 添加 src 目录到路径
sys.path.insert(0, __file__.rsplit('/', 1)[0])

from data_fetcher import AStockDataFetcher
from technical_indicators import calculate_williams_r, calculate_rsi, calculate_bollinger_bands, interpret_williams_r
from formulas import BuffettFormula, analyze_stock_fundamental


def format_stock_code(code: str) -> str:
    """格式化股票代码"""
    code = code.strip().zfill(6)
    if code.startswith('6'):
        return f"sh.{code}"
    elif code.startswith('0') or code.startswith('3'):
        return f"sz.{code}"
    return code


def analyze_stock_technical(fetcher: AStockDataFetcher, stock_code: str, name: str = "") -> dict:
    """分析股票技术面"""
    formatted_code = format_stock_code(stock_code)
    
    # 获取价格数据
    df = fetcher.get_price_data(formatted_code, days=90)
    
    if df is None or len(df) < 30:
        return None
    
    # 计算技术指标
    df['williams_r'] = calculate_williams_r(
        df['high'].astype(float),
        df['low'].astype(float),
        df['close'].astype(float),
        period=14
    )
    
    df['rsi'] = calculate_rsi(df['close'].astype(float), period=14)
    
    middle, upper, lower = calculate_bollinger_bands(df['close'].astype(float))
    df['bb_middle'] = middle
    df['bb_upper'] = upper
    df['bb_lower'] = lower
    
    # 获取最新数据
    latest = df.iloc[-1]
    
    price = latest['close']
    wr = latest['williams_r']
    rsi = latest['rsi']
    bb_lower = latest['bb_lower']
    
    # 判断信号
    signal = "观望"
    if wr <= -80:
        signal = "超卖-买入"
    elif wr <= -70:
        signal = "超卖-关注"
    elif rsi <= 30:
        signal = "RSI超卖-关注"
    
    # 判断是否触及布林下轨
    near_bb_lower = False
    if bb_lower and price <= bb_lower * 1.03:
        near_bb_lower = True
        signal = signal.replace("关注", "接近布林下轨-关注").replace("买入", "布林下轨-买入")
    
    return {
        'code': stock_code,
        'name': name,
        'price': round(price, 2) if price else None,
        'williams_r': round(wr, 2) if wr else None,
        'rsi': round(rsi, 2) if rsi else None,
        'bb_lower': round(bb_lower, 2) if bb_lower else None,
        'signal': signal,
        'near_bb_lower': near_bb_lower
    }


def analyze_stock_fundamental_wrapper(fetcher: AStockDataFetcher, stock_code: str) -> dict:
    """分析股票基本面"""
    # 获取财务数据
    financial_data = fetcher.get_financial_data(stock_code)
    
    if financial_data is None:
        return None
    
    # 转换为巴菲特公式需要的格式
    # A股财务数据通常单位是万元
    data = {
        'cash_equivalents': financial_data.get('total_assets', 0) * 0.1 if financial_data.get('total_assets') else 0,  # 估算
        'short_term_debt': 0,
        'total_debt': 0,
        'total_liabilities': financial_data.get('total_assets', 0) * 0.4 if financial_data.get('total_assets') else 0,  # 估算
        'total_equity': financial_data.get('total_assets', 0) * 0.6 if financial_data.get('total_assets') else 0,  # 估算
        'net_profit': financial_data.get('net_profit', 0),
        'revenue': financial_data.get('revenue', 0),
        'operating_profit': financial_data.get('net_profit', 0) * 1.2,  # 估算
        'current_assets': financial_data.get('total_assets', 0) * 0.3 if financial_data.get('total_assets') else 0,  # 估算
        'current_liabilities': financial_data.get('total_assets', 0) * 0.2 if financial_data.get('total_assets') else 0,  # 估算
        'total_assets': financial_data.get('total_assets', 0),
        'interest_expense': 0,
        'cash_from_operations': financial_data.get('net_profit', 0) * 1.1,  # 估算
        'capex': financial_data.get('net_profit', 0) * 0.2,  # 估算
    }
    
    # 简化分析 - 使用ROE作为主要指标
    roe = financial_data.get('roe', 0)
    pe = financial_data.get('pe', 0)
    pb = financial_data.get('pb', 0)
    
    # 基本面评分
    score = 0
    if roe and roe > 15:
        score += 3
    elif roe and roe > 10:
        score += 2
    elif roe and roe > 5:
        score += 1
    
    if pe and pe > 0 and pe < 20:
        score += 2
    elif pe and pe > 0 and pe < 30:
        score += 1
    
    if pb and pb > 0 and pb < 3:
        score += 2
    elif pb and pb > 0 and pb < 5:
        score += 1
    
    return {
        'roe': roe,
        'pe': pe,
        'pb': pb,
        'fundamental_score': score,
        'rating': "优秀" if score >= 6 else "良好" if score >= 4 else "一般"
    }


def run_screening(stock_list: list, min_score: int = 5, top_n: int = 10, 
                  use_technical: bool = True, use_fundamental: bool = True) -> list:
    """
    运行筛选
    
    Args:
        stock_list: 股票列表 [(code, name), ...]
        min_score: 最小基本面分数
        top_n: 返回前N只
        use_technical: 使用技术面筛选
        use_fundamental: 使用基本面筛选
    
    Returns:
        筛选结果列表
    """
    fetcher = AStockDataFetcher()
    results = []
    
    print(f"开始筛选 {len(stock_list)} 只股票...")
    
    for i, (code, name) in enumerate(stock_list):
        if (i + 1) % 50 == 0:
            print(f"  已处理 {i+1}/{len(stock_list)}")
        
        try:
            # 技术面分析
            technical = None
            if use_technical:
                technical = analyze_stock_technical(fetcher, code, name)
            
            # 基本面分析
            fundamental = None
            if use_fundamental:
                fundamental = analyze_stock_fundamental_wrapper(fetcher, code)
            
            if technical is None and fundamental is None:
                continue
            
            # 综合评分
            total_score = 0
            signals = []
            
            if technical:
                if technical['williams_r'] and technical['williams_r'] <= -80:
                    total_score += 3
                    signals.append("超卖")
                elif technical['williams_r'] and technical['williams_r'] <= -70:
                    total_score += 1
                    signals.append("接近超卖")
            
            if fundamental:
                total_score += fundamental.get('fundamental_score', 0)
            
            # 判断是否通过筛选
            passed = total_score >= min_score
            
            result = {
                'code': code,
                'name': name,
                'technical': technical,
                'fundamental': fundamental,
                'total_score': total_score,
                'signals': signals,
                'passed': passed
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"  处理 {code} 时出错: {e}")
            continue
    
    fetcher.close()
    
    # 按分数排序
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    return results[:top_n]


def main():
    parser = argparse.ArgumentParser(description='A股股票筛选器')
    parser.add_argument('--stocks', nargs='+', help='股票代码列表 (如 300502 600000)')
    parser.add_argument('--index', type=str, help='指数代码 (000300/399006)')
    parser.add_argument('--min-score', type=int, default=3, help='最小综合分数')
    parser.add_argument('--top-n', type=int, default=10, help='返回前N只')
    parser.add_argument('--no-technical', action='store_true', help='不使用技术面筛选')
    parser.add_argument('--no-fundamental', action='store_true', help='不使用基本面筛选')
    parser.add_argument('--output', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    
    # 获取股票列表
    stock_list = []
    
    if args.stocks:
        stock_list = [(s, "") for s in args.stocks]
    elif args.index:
        fetcher = AStockDataFetcher()
        stocks = fetcher.get_index_components(args.index)
        stock_list = [(s, "") for s in stocks]
        fetcher.close()
    else:
        # 默认自选股
        stock_list = [
            ('300276', '三丰智能'),
            ('300199', '翰宇药业'),
            ('300502', '新易盛'),
            ('300394', '天孚通信'),
            ('300308', '中际旭创'),
            ('300628', '亿联网络'),
            ('300573', '兴齐眼药'),
            ('300533', '冰川网络'),
            ('300274', '阳光电源'),
            ('300251', '光线传媒'),
            ('300604', '长川科技'),
            ('300456', '赛微电子'),
        ]
    
    # 运行筛选
    results = run_screening(
        stock_list,
        min_score=args.min_score,
        top_n=args.top_n,
        use_technical=not args.no_technical,
        use_fundamental=not args.no_fundamental
    )
    
    # 输出结果
    print("\n" + "=" * 60)
    print(f"筛选结果 (共 {len(results)} 只股票通过)")
    print("=" * 60)
    
    for i, r in enumerate(results, 1):
        tech = r.get('technical', {})
        fund = r.get('fundamental', {})
        
        print(f"\n{i}. {r['code']} {r['name']}")
        print(f"   综合分数: {r['total_score']}")
        
        if tech:
            wr = tech.get('williams_r', 'N/A')
            signal = tech.get('signal', 'N/A')
            print(f"   技术面: WR={wr}, 信号={signal}")
        
        if fund:
            roe = fund.get('roe', 'N/A')
            rating = fund.get('rating', 'N/A')
            print(f"   基本面: ROE={roe}%, 评级={rating}")
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
