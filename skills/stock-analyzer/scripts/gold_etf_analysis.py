#!/usr/bin/env python3
"""
黄金ETF综合分析脚本
结合基本面、技术面、行为金融学
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class GoldETFAnalyzer:
    def __init__(self, symbol="518880"):
        self.symbol = symbol
        self.name = "黄金ETF"
        self.data = {}
        
    def fetch_all_data(self):
        """获取所有数据"""
        print("📥 数据采集中...")
        
        # 1. ETF历史行情
        print("  📈 行情数据...")
        self.data['history'] = ak.fund_etf_hist_em(
            symbol=self.symbol, 
            period="daily", 
            start_date="20250101"
        )
        print(f"    ✅ {len(self.data['history'])}条")
        
        # 2. ETF基本信息
        print("  📋 基本信息...")
        all_etf = ak.fund_etf_spot_em()
        self.data['info'] = all_etf[all_etf['代码'] == self.symbol].iloc[0]
        print(f"    ✅ 获取成功")
        
        # 3. 黄金现货数据
        print("  🥇 黄金数据...")
        self.data['gold'] = ak.spot_golden_benchmark_sge()
        print(f"    ✅ {len(self.data['gold'])}条")
        
        # 4. 市场资金流向
        print("  💰 资金流向...")
        try:
            self.data['money_flow'] = ak.stock_money_flow_hsgt()
            print(f"    ✅ 获取成功")
        except:
            self.data['money_flow'] = None
            print(f"    ⚠️ 获取失败")
            
        return self
    
    def analyze_technical(self):
        """技术面分析"""
        df = self.data['history'].copy()
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期')
        
        close = df['收盘'].astype(float)
        volume = df['成交量'].astype(float)
        
        # 均线
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()
        ma60 = close.rolling(60).mean()
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        
        # KDJ
        low_9 = close.rolling(9).min()
        high_9 = close.rolling(9).max()
        kdj_k = 100 * (close - low_9) / (high_9 - low_9)
        kdj_d = kdj_k.rolling(3).mean()
        kdj_j = 3 * kdj_k - 2 * kdj_d
        
        # 最新值
        latest = {
            'price': close.iloc[-1],
            'ma5': ma5.iloc[-1],
            'ma10': ma10.iloc[-1],
            'ma20': ma20.iloc[-1],
            'ma60': ma60.iloc[-1] if len(ma60) > 0 else None,
            'rsi': rsi.iloc[-1],
            'macd': macd.iloc[-1],
            'macd_signal': signal.iloc[-1],
            'kdj_k': kdj_k.iloc[-1],
            'kdj_d': kdj_d.iloc[-1],
            'kdj_j': kdj_j.iloc[-1],
            'volume': volume.iloc[-1],
            'vol_ma5': volume.iloc[-5:].mean(),
        }
        
        # 涨跌幅
        latest['change_1d'] = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
        latest['change_5d'] = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
        latest['change_20d'] = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20] * 100
        
        # 信号判断
        signals = []
        if latest['price'] > latest['ma5']:
            signals.append("MA5金叉")
        else:
            signals.append("MA5死叉")
            
        if latest['macd'] > latest['macd_signal']:
            signals.append("MACD金叉")
        else:
            signals.append("MACD死叉")
            
        if latest['rsi'] > 70:
            signals.append("RSI超买")
        elif latest['rsi'] < 30:
            signals.append("RSI超卖")
        else:
            signals.append("RSI中性")
            
        latest['signals'] = signals
        
        self.data['technical'] = latest
        return self
    
    def analyze_fundamental(self):
        """基本面分析"""
        info = self.data['info']
        
        # 黄金价格
        gold = self.data['gold']
        gold_latest = gold.iloc[-1]
        gold_price = (gold_latest['晚盘价'] + gold_latest['早盘价']) / 2
        
        # ETF隐含黄金价格 (每份=0.001盎司)
        etf_price = info['最新价']
        etf_gold_price_per_oz = etf_price / 0.001  # ETF价格 / 0.001盎司 = 每盎司价格
        etf_gold_price_per_gram = etf_gold_price_per_oz / 31.1035  # 转换为每克
        
        # 溢价率 = (ETF隐含金价 - 黄金现货价) / 黄金现货价
        premium = (etf_gold_price_per_gram - gold_price) / gold_price * 100
        
        # 计算估值
        fundamental = {
            'etf_price': etf_price,
            'gold_price': gold_price,
            'etf_gold_price': etf_gold_price_per_gram,
            'premium': premium,
            'market_cap': info['流通市值'],
            'shares': info['最新份额'],
            'volume': info['成交量'],
            'turnover': info['换手率'],
            'discount': info['基金折价率'],
            'main_net_inflow': info['主力净流入-净额'],
            'main_net_ratio': info['主力净流入-净占比'],
        }
        
        self.data['fundamental'] = fundamental
        return self
    
    def analyze_behavioral(self):
        """行为金融学分析"""
        tech = self.data['technical']
        fund = self.data['fundamental']
        
        # 1. 资金流向分析
        money_score = 50
        if fund['main_net_ratio'] < -5:
            money_score = 20  # 主力大幅流出
        elif fund['main_net_ratio'] < 0:
            money_score = 35
        elif fund['main_net_ratio'] < 5:
            money_score = 60
        else:
            money_score = 80
            
        # 2. 涨跌分析
        change_score = 50
        if tech['change_5d'] < -5:
            change_score = 20  # 大跌
        elif tech['change_5d'] < 0:
            change_score = 40
        elif tech['change_5d'] < 3:
            change_score = 60
        else:
            change_score = 80
            
        # 3. 情绪分析
        if tech['change_5d'] < -3 and tech['volume'] / tech['vol_ma5'] < 0.8:
            sentiment = "恐慌"
        elif tech['change_5d'] > 5 and tech['volume'] / tech['vol_ma5'] > 1.5:
            sentiment = "亢奋"
        elif tech['change_5d'] > 0:
            sentiment = "乐观"
        else:
            sentiment = "谨慎"
            
        # 4. 行为偏差
        biases = []
        if fund['main_net_ratio'] < -5:
            biases.append("羊群效应(主力流出)")
        if tech['rsi'] < 30:
            biases.append("超卖(逆向机会)")
        if tech['price'] < tech['ma20']:
            biases.append("跌破均线(观望)")
            
        behavioral = {
            'money_score': money_score,
            'change_score': change_score,
            'sentiment': sentiment,
            'biases': biases,
            'volume_ratio': tech['volume'] / tech['vol_ma5'],
        }
        
        # 综合评分
        behavioral['total_score'] = int((money_score + change_score) / 2)
        
        self.data['behavioral'] = behavioral
        return self
    
    def generate_report(self):
        """生成分析报告"""
        tech = self.data['technical']
        fund = self.data['fundamental']
        behav = self.data['behavioral']
        
        print("\n" + "="*70)
        print(f"【黄金ETF({self.symbol})综合分析报告】")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)
        
        # 技术面
        print("\n📈 【技术面分析】")
        print(f"  价格: {tech['price']:.3f}")
        print(f"  MA5: {tech['ma5']:.3f} | MA10: {tech['ma10']:.3f} | MA20: {tech['ma20']:.3f}")
        print(f"  RSI: {tech['rsi']:.1f}")
        print(f"  MACD: {tech['macd']:.4f} vs {tech['macd_signal']:.4f}")
        print(f"  KDJ: K={tech['kdj_k']:.1f} D={tech['kdj_d']:.1f} J={tech['kdj_j']:.1f}")
        print(f"  信号: {', '.join(tech['signals'])}")
        print(f"  涨跌幅: 1日{tech['change_1d']:+.2f}% 5日{tech['change_5d']:+.2f}% 20日{tech['change_20d']:+.2f}%")
        
        # 基本面
        print("\n📋 【基本面分析】")
        print(f"  ETF价格: ¥{fund['etf_price']:.3f}")
        print(f"  黄金价格: ¥{fund['gold_price']:.0f}/克")
        print(f"  溢价率: {fund['premium']:.2f}%")
        print(f"  流通市值: {fund['market_cap']/1e8:.1f}亿")
        print(f"  份额: {fund['shares']/1e8:.2f}亿")
        print(f"  成交量: {fund['volume']/1e4:.1f}万")
        print(f"  换手率: {fund['turnover']:.2f}%")
        print(f"  主力净流入: {fund['main_net_inflow']/1e8:.2f}亿 ({fund['main_net_ratio']:.2f}%)")
        
        # 行为金融
        print("\n🧠 【行为金融学分析】")
        print(f"  资金评分: {behav['money_score']}/100")
        print(f"  涨跌评分: {behav['change_score']}/100")
        print(f"  市场情绪: {behav['sentiment']}")
        print(f"  成交量比: {behav['volume_ratio']:.2f}")
        print(f"  行为偏差: {', '.join(behav['biases']) if behav['biases'] else '无'}")
        
        # 综合评分
        print("\n" + "="*70)
        print("【综合评分】")
        print("="*70)
        
        # 计算总分
        tech_score = 50
        if "MA5金叉" in tech['signals']: tech_score += 15
        if tech['rsi'] < 70 and tech['rsi'] > 30: tech_score += 15
        if "MACD金叉" in tech['signals']: tech_score += 10
        if tech['kdj_k'] < 20: tech_score += 10
        
        fund_score = 50
        if abs(fund['premium']) < 5: fund_score += 25
        if fund['main_net_ratio'] > 0: fund_score += 15
        else: fund_score += 5
        
        behav_score = behav['total_score']
        
        total = int(tech_score * 0.3 + fund_score * 0.4 + behav_score * 0.3)
        
        print(f"  技术面: {tech_score}/100")
        print(f"  基本面: {fund_score}/100")
        print(f"  行为金融: {behav_score}/100")
        print(f"  ─────────────────────")
        print(f"  总分: {total}/100")
        
        # 建议
        if total >= 75:
            rec = "⭐⭐⭐⭐⭐ 强烈买入"
        elif total >= 60:
            rec = "⭐⭐⭐⭐ 买入"
        elif total >= 45:
            rec = "⭐⭐⭐ 持有"
        else:
            rec = "⭐⭐ 卖出"
            
        print(f"\n  建议: {rec}")
        
        return total, rec


def main():
    analyzer = GoldETFAnalyzer("518880")
    analyzer.fetch_all_data()
    analyzer.analyze_technical()
    analyzer.analyze_fundamental()
    analyzer.analyze_behavioral()
    analyzer.generate_report()


if __name__ == "__main__":
    main()
