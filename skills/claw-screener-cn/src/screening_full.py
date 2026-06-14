#!/usr/bin/env python3
"""
A股股票筛选器 - 完整版 (技术面 + 基本面 + DCF估值)
使用本地真实财务数据 - 修复数据单位
"""
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# 自选股列表
WATCHLIST = [
    ('300276', '三丰智能'),
    ('300199', '翰宇药业'),
    ('301381', '待确认'),
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
    ('300926', '博俊科技'),
]

DATA_DIR = Path("/home/liujerry/金融数据/stocks")
FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")


def get_stock_data_path(code: str) -> Path:
    """获取股票数据路径"""
    return DATA_DIR / f"{code}.csv"

sys.path.insert(0, __file__.rsplit('/', 1)[0])

from cache import get_data_cache
from advanced_analysis import CarlsonQualityScore
from formulas import FormulaEngine, FinancialData, FormulaStatus


def load_financial_data(stock_code: str) -> dict:
    """从本地CSV加载真实财务数据 (单位: 亿元)"""
    code = str(stock_code).zfill(6)
    if code.startswith('6'):
        code_with_exchange = f"sh.{code}"
    else:
        code_with_exchange = f"sz.{code}"
    
    result = {}
    
    # profit.csv 单位: 亿元, 亿股
    profit_file = FINANCIAL_DIR / "profit.csv"
    if profit_file.exists():
        try:
            df = pd.read_csv(profit_file)
            row = df[df['code'] == code_with_exchange]
            if not row.empty:
                row = row.iloc[0]
                # ROE: 小数 -> 百分比
                if 'roeAvg' in row and pd.notna(row['roeAvg']):
                    result['roe'] = float(row['roeAvg']) * 100
                # 净利润率: 小数 -> 百分比
                if 'npMargin' in row and pd.notna(row['npMargin']):
                    result['net_profit_margin'] = float(row['npMargin']) * 100
                # 毛利率: 小数 -> 百分比
                if 'gpMargin' in row and pd.notna(row['gpMargin']):
                    result['gross_margin'] = float(row['gpMargin']) * 100
                # 净利润: 元 (约120亿)
                if 'netProfit' in row and pd.notna(row['netProfit']):
                    result['net_profit'] = float(row['netProfit']) / 100000000  # 元 -> 亿元
                # 每股收益: 元
                if 'epsTTM' in row and pd.notna(row['epsTTM']):
                    result['eps'] = float(row['epsTTM'])
                # 营业收入: 亿元
                if 'MBRevenue' in row and pd.notna(row['MBRevenue']):
                    result['revenue'] = float(row['MBRevenue'])
                # 总股本: 股 (profit.csv中 hardcoded 为0，从 EPS 反推)
                if 'totalShare' in row and pd.notna(row['totalShare']) and float(row['totalShare']) > 0:
                    result['total_shares'] = float(row['totalShare'])
                elif 'epsTTM' in row and pd.notna(row['epsTTM']) and float(row['epsTTM']) > 0 \
                     and 'netProfit' in row and pd.notna(row['netProfit']) and float(row['netProfit']) > 0:
                    # EPS = netProfit / totalShares => totalShares = netProfit / EPS
                    result['total_shares'] = float(row['netProfit']) / float(row['epsTTM'])
                else:
                    result['total_shares'] = 100000000  # fallback 1亿股
                # 流通股本: 股
                if 'liqaShare' in row and pd.notna(row['liqaShare']) and float(row['liqaShare']) > 0:
                    result['float_shares'] = float(row['liqaShare'])
                else:
                    result['float_shares'] = result.get('total_shares', 100000000) * 0.8  # 估算80%流通
                # 报告期
                if 'pubDate' in row and pd.notna(row['pubDate']):
                    result['report_date'] = str(row['pubDate'])
        except Exception as e:
            print(f"  加载失败: {e}")
    
    return result


def get_buffett_format(stock_code: str) -> dict:
    """获取巴菲特公式格式 - 使用真实数据从buffett_supplementary.csv"""
    import pandas as pd
    
    result = {}
    
    try:
        # 从buffett_supplementary.csv读取真实数据
        buffett_df = pd.read_csv('/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv')
        # buffett code 列实际名为 code_x (int64); screening 调用时传 'sz.000001'/'sh.600001' 或纯数字
        # 兼容两种格式 (lstrip '0' 让 000001 和 1 都能 match)
        code_str = str(stock_code)
        code_int_match = None
        if code_str.startswith(('sz.', 'sh.')):
            code_int_match = code_str.split('.', 1)[1]
        elif code_str.isdigit():
            code_int_match = code_str
        if code_int_match:
            # int 比较 (处理 000001 vs 1 leading zero 不一致)
            try:
                code_int = int(code_int_match)
                rows = buffett_df[buffett_df['code_x'] == code_int]
            except ValueError:
                rows = buffett_df[buffett_df['code_x'].astype(str) == code_int_match]
        else:
            rows = buffett_df[buffett_df['code_x'].astype(str) == stock_code]
        
        if rows.empty:
            print(f"  [警告] {code_int_match or stock_code}不在buffett_supplementary.csv中")
            return {}
        
        # 获取最新一条数据 (按 report_date 排序取末行, 避免 iloc[-1] 抓到非该 code 的错行)
        rows = rows.sort_values('report_date')
        b = rows.iloc[-1]
        
        # 获取报告日期
        report_date = str(b['report_date'])[:10] if pd.notna(b['report_date']) else '2025-09-30'
        
        # 现金 (元)
        cash = b['cash']
        # 短期负债 (元)
        short_debt = b['short_debt']
        # 长期负债 (元)
        long_debt = b['long_debt']
        # 总负债 (元)
        liabilities = b['total_liabilities']
        # 所有者权益 (元)
        equity = b['equity']
        # 流动资产 (元)
        current_assets = b['current_assets']
        # 流动负债 (元)
        current_liabilities = b['current_liabilities']
        # 总资产 (元)
        total_assets = b['total_assets']
        # 营业收入 (元)
        revenue = b['revenue']
        # 净利润 (元)
        net_income = b['net_income']
        # 营业利润 (元)
        operating_profit = b['operating_profit']
        # 利息支出 (元)
        interest_expense = b['interest_expense']
        # 经营现金流 - 关键发现：buffett_supplementary.csv中所有字段单位不一致！
        # cash/revenue/net_income/equity等: 单位是元
        # operating_cash_flow: 单位是亿元（不是元），需要×1e8转换
        # 验证：300750(宁德) NI=722亿, OCF=1332亿(1332亿经营现金流合理，OCF/NI=184%)
        operating_cash_flow = b['operating_cash_flow']
        if pd.isna(operating_cash_flow) or operating_cash_flow == 0:
            operating_cash_flow = 0
        else:
            # 统一视为亿元，转换为元
            operating_cash_flow = operating_cash_flow * 1e8
        
        # 映射到FinancialData格式
        result['CashAndCashEquivalentsAtCarryingValue'] = {'value': cash, 'end_date': report_date, 'form': '10-K'}
        result['ShortTermDebt'] = {'value': short_debt, 'end_date': report_date, 'form': '10-K'}
        result['LongTermDebt'] = {'value': long_debt, 'end_date': report_date, 'form': '10-K'}
        result['Liabilities'] = {'value': liabilities, 'end_date': report_date, 'form': '10-K'}
        result['StockholdersEquity'] = {'value': equity, 'end_date': report_date, 'form': '10-K'}
        result['NetIncomeLoss'] = {'value': net_income, 'end_date': report_date, 'form': '10-K'}
        result['Revenues'] = {'value': revenue, 'end_date': report_date, 'form': '10-K'}
        result['OperatingIncomeLoss'] = {'value': operating_profit, 'end_date': report_date, 'form': '10-K'}
        result['CurrentAssets'] = {'value': current_assets, 'end_date': report_date, 'form': '10-K'}
        result['CurrentLiabilities'] = {'value': current_liabilities, 'end_date': report_date, 'form': '10-K'}
        result['Assets'] = {'value': total_assets, 'end_date': report_date, 'form': '10-K'}
        result['InterestExpense'] = {'value': interest_expense, 'end_date': report_date, 'form': '10-K'}
        result['CashFlowFromContinuingOperatingActivities'] = {'value': operating_cash_flow, 'end_date': report_date, 'form': '10-K'}
        result['FreeCashFlow'] = {'value': operating_cash_flow * 0.8, 'end_date': report_date, 'form': '10-K'}
        
    except Exception as e:
        print(f"  [错误] get_buffett_format读取失败: {e}")
        return {}
    
    return result


def calculate_dcf(financial_data: dict, price: float) -> dict:
    """计算DCF估值 (单位: 亿元)"""
    # 优先使用真实的经营现金流数据
    cash_flow_data = financial_data.get('CashFlowFromContinuingOperatingActivities', {})
    if cash_flow_data:
        operating_cash_flow = cash_flow_data.get('value', 0)
        # 转换单位：元 -> 亿元
        fcf_yi = operating_cash_flow / 1e8 if operating_cash_flow > 0 else 0
    else:
        # 降级：使用净利润估算
        net_profit = financial_data.get('net_profit', 0)
        fcf_yi = net_profit * 0.8
    
    if fcf_yi <= 0:
        return {'error': '现金流数据不足'}
    
    # 总股本 (股)
    total_shares = financial_data.get('total_shares', 100000000)
    
    # 增长率 (基于ROE)
    roe = financial_data.get('roe', 10)
    # 如果ROE是百分比形式(如15)而不是小数形式(如0.15)，自动转换
    if roe > 1:
        roe = roe / 100
    growth = min(max(roe, -0.05), 0.20)
    
    # 参数
    discount_rate = 0.10
    terminal_growth = 0.025
    
    # 10年现金流折现
    pv = 0
    projected_fcf = fcf_yi
    
    for year in range(1, 11):
        projected_fcf *= (1 + growth)
        pv += projected_fcf / ((1 + discount_rate) ** year)
    
    # 终值
    terminal_value = (projected_fcf * (1 + terminal_growth)) / max(0.0001, discount_rate - terminal_growth)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** 10)
    
    # 内在价值 (亿元)
    intrinsic_equity = pv + discounted_terminal
    # 每股价值 (元)
    shares_yi = total_shares / 100000000  # 亿股
    if shares_yi <= 0:
        shares_yi = 1.0  # 默认1亿股避免除零
    intrinsic_per_share = intrinsic_equity / shares_yi
    
    # 上涨空间
    upside = None
    if price and price > 0:
        upside = (intrinsic_per_share / price - 1) * 100
    
    # 评级
    if upside is not None:
        if upside >= 50:
            rating = "🚀 严重低估"
        elif upside >= 20:
            rating = "⭐ 低估"
        elif upside >= 0:
            rating = "➡️ 合理"
        elif upside >= -20:
            rating = "⚠️ 高估"
        else:
            rating = "🚨 严重高估"
    else:
        rating = "N/A"
    
    return {
        'fcf_yi': round(fcf_yi, 2),
        'growth_rate': round(growth * 100, 2),
        'intrinsic_per_share': round(intrinsic_per_share, 2),
        'current_price': price,
        'upside_percent': round(upside, 2) if upside else None,
        'rating': rating
    }


def calculate_williams_r(high, low, close, period=14):
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    diff = highest_high - lowest_low
    diff = diff.replace(0, pd.NA)
    wr = ((highest_high - close) / diff) * -100
    return wr


def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(prices, period=20, std_dev=2.0):
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return middle, upper, lower


def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = (dif - dea) * 2
    return dif, dea, macd


def analyze_stock(code, name):
    file_path = get_stock_data_path(code)
    
    if not file_path.exists():
        return {'code': code, 'name': name, 'error': '行情数据不存在'}
    
    try:
        df = pd.read_csv(file_path)
        
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            return {'code': code, 'name': name, 'error': '数据格式错误'}
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.tail(90)
        
        if len(df) < 30:
            return {'code': code, 'name': name, 'error': f'数据不足{len(df)}天'}
        
        # 技术指标
        df['williams_r'] = calculate_williams_r(df['high'], df['low'], df['close'])
        df['rsi'] = calculate_rsi(df['close'])
        df['bb_middle'], df['bb_upper'], df['bb_lower'] = calculate_bollinger_bands(df['close'])
        df['macd_dif'], df['macd_dea'], df['macd'] = calculate_macd(df['close'])
        
        latest = df.iloc[-1]
        
        price = latest['close']
        wr = latest['williams_r']
        rsi_val = latest['rsi']
        bb_lower = latest['bb_lower']
        macd_dif = latest['macd_dif']
        macd_dea = latest['macd_dea']
        
        # 技术信号
        tech_signals = []
        tech_score = 0
        
        if pd.notna(wr):
            if wr <= -80:
                tech_signals.append(("WR", "超卖", "⭐⭐⭐"))
                tech_score += 3
            elif wr <= -70:
                tech_signals.append(("WR", "接近超卖", "⭐"))
                tech_score += 1
        
        if pd.notna(rsi_val):
            if rsi_val <= 30:
                tech_signals.append(("RSI", "超卖", "⭐"))
                tech_score += 1
            elif rsi_val >= 70:
                tech_signals.append(("RSI", "超买", "⚠️"))
        
        if pd.notna(bb_lower) and pd.notna(price):
            if price <= bb_lower * 1.03:
                tech_signals.append(("布林", "触下轨", "⭐"))
                tech_score += 1
        
        if pd.notna(macd_dif) and pd.notna(macd_dea):
            if macd_dif > macd_dea:
                tech_signals.append(("MACD", "金叉", "✅"))
                tech_score += 1
            else:
                tech_signals.append(("MACD", "死叉", "❌"))
        
        # 财务数据
        financial_data = load_financial_data(code)
        
        # 巴菲特公式
        buffett_data = get_buffett_format(code)
        buffett_result = None
        if buffett_data:
            try:
                fd = FinancialData(buffett_data)
                engine = FormulaEngine(fd)
                buffett_result = engine.evaluate_all()
            except:
                pass
        
        # Carlson
        carlson = CarlsonQualityScore(financial_data, {'price': price})
        carlson_score = carlson.compute_total_score()
        carlson_rating = carlson.get_rating()
        
        # DCF
        dcf_result = calculate_dcf(financial_data, price)
        
        # 总分
        total_score = tech_score + (carlson_score // 10)
        
        if total_score >= 6:
            recommendation = "🚀 强烈推荐"
        elif total_score >= 4:
            recommendation = "⭐ 建议关注"
        elif total_score >= 2:
            recommendation = "👀 观察"
        else:
            recommendation = "➡️ 观望"
        
        return {
            'code': code, 'name': name, 'price': round(price, 2) if pd.notna(price) else None,
            'williams_r': round(wr, 2) if pd.notna(wr) else None,
            'rsi': round(rsi_val, 2) if pd.notna(rsi_val) else None,
            'macd': f"{'金叉' if macd_dif > macd_dea else '死叉'}",
            'tech_score': tech_score,
            'tech_signals': tech_signals,
            'financial_data': financial_data,
            'buffett_result': [(r.name, r.status.value, r.message) for r in buffett_result] if buffett_result else [],
            'carlson_score': carlson_score,
            'carlson_rating': carlson_rating,
            'dcf': dcf_result,
            'total_score': total_score,
            'recommendation': recommendation,
        }
    except Exception as e:
        return {'code': code, 'name': name, 'error': str(e)}


def main():
    print("=" * 90)
    print("📊 A股自选股综合分析报告 (真实财务 + 技术面 + 巴菲特公式 + DCF估值)")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 90)
    
    results = []
    
    for code, name in WATCHLIST:
        print(f"\n分析 {code} {name}...")
        financial_data = load_financial_data(code)
        if financial_data:
            print(f"  ✅ ROE={financial_data.get('roe', 0):.1f}% 净利润={financial_data.get('net_profit', 0):.1f}亿")
        result = analyze_stock(code, name)
        results.append(result)
    
    # 排序
    results_with_score = [r for r in results if 'total_score' in r]
    results_with_score.sort(key=lambda x: x['total_score'], reverse=True)
    
    # 输出
    print("\n" + "=" * 90)
    print("📈 符合买入条件 (总分 >= 4)")
    print("=" * 90)
    
    for r in results_with_score:
        if r['total_score'] < 4:
            continue
        dcf = r.get('dcf', {})
        fin = r.get('financial_data', {})
        
        print(f"\n{r['code']} {r['name']}")
        print(f"   价格: {r['price']} | WR: {r['williams_r']} | RSI: {r['rsi']} | MACD: {r['macd']}")
        print(f"   技术: {r['tech_score']}/6 | Carlson: {r['carlson_score']} ({r['carlson_rating']})")
        
        buffett = r.get('buffett_result', [])
        passed = sum(1 for _, s, _ in buffett if s == 'PASS')
        print(f"   巴菲特: {passed}/10")
        
        if fin:
            print(f"   财务: ROE={fin.get('roe', 0):.1f}% | 净利率={fin.get('net_profit_margin', 0):.1f}% | 净利润={fin.get('net_profit', 0):.1f}亿")
        
        if 'error' not in dcf:
            print(f"   DCF: 内在={dcf.get('intrinsic_per_share', 'N/A')}元 | 当前={dcf.get('current_price', 'N/A')}元 | 上涨={dcf.get('upside_percent', 'N/A')}% {dcf.get('rating', '')}")
        
        print(f"   ➡️ {r['recommendation']}")
    
    # 表格
    print("\n" + "=" * 90)
    print("📊 全部股票状态")
    print("=" * 90)
    print(f"{'代码':8} {'名称':8} {'价格':>7} {'WR':>7} {'RSI':>5} {'MACD':>4} {'技术':>4} {'巴菲':>4} {'Carlson':>7} {'DCF上涨':>8} {'总分'}")
    print("-" * 90)
    
    for r in results_with_score:
        buffett = r.get('buffett_result', [])
        passed = sum(1 for _, s, _ in buffett if s == 'PASS')
        dcf = r.get('dcf', {})
        upside = dcf.get('upside_percent', 'N/A')
        upside_str = f"{upside:>7.1f}%" if upside not in [None, 'N/A'] else "     N/A"
        
        print(f"{r['code']:8} {r['name']:8} {r['price']:>7.2f} {r['williams_r']:>7.1f} {r['rsi']:>5.1f} {r['macd']:>4} {r['tech_score']:>4} {passed:>4} {r['carlson_score']:>7} {upside_str} {r['total_score']}")
    
    print("=" * 90)
    return results


if __name__ == "__main__":
    main()


def add_dividend_screening():
    """将分红评分集成到筛选系统"""
    import pandas as pd
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from dividend_screener import DividendScreener
    
    screener = DividendScreener()
    
    # 读取股票列表
    financial_dir = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
    profit_file = financial_dir / "profit.csv"
    
    df_profit = pd.read_csv(profit_file)
    stock_codes = df_profit['code'].unique()
    
    results = []
    for code in stock_codes:
        code_str = str(code).split('.')[-1]  # 去掉 sh. sz. 前缀
        div_data = screener.get_dividend_data(code_str)
        if div_data['has_dividend_history']:
            results.append({
                'code': code_str,
                'dividend_score': div_data['dividend_score'],
                'consecutive_years': div_data['consecutive_years'],
                'dividend_yield': div_data['dividend_yield'],
                'last_dividend': div_data['last_dividend'],
                'pass': div_data['pass_screening']
            })
    
    df_result = pd.DataFrame(results)
    df_result = df_result.sort_values('dividend_score', ascending=False)
    
    output_file = Path("/home/liujerry/金融数据/screening_results/dividend_screening_latest.csv")
    df_result.to_csv(output_file, index=False)
    print(f"分红筛选完成，共{len(df_result)}只有分红记录的股票")
    print(f"通过筛选: {df_result['pass'].sum()}只")
    print(f"结果保存: {output_file}")
    return df_result

if __name__ == "__main__":
    # 修复：有两个 __main__ 块！第二个会覆盖第一个。
    # 默认跑主分析流程（14只自选股），而非全量分红筛选
    main()
    # 需要全量分红筛选时请取消注释下面这行：
    # add_dividend_screening()
