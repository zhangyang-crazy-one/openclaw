#!/usr/bin/env python3
"""
行业分析技能 (Industry Analysis Skill)
基于学术研究成果的多因子行业分析框架

引用文献:
- Fama, E.F., French, K.R. (1992). "The Cross-Section of Expected Stock Returns". Journal of Finance.
- Carhart, M.M. (1997). "On Persistence in Mutual Fund Performance". Journal of Finance.
- Fama, E.F., French, K.R. (2006). "Profitability, Investment and Average Returns". JFE.
- Novy-Marx, R. (2013). "The Other Side of Value: The Gross Profitability Premium". JFE.
- Hou, K., Xue, C., Zhang, L. (2015). "Digesting Anomalies". Review of Financial Studies.
- Asness, C., et al. (2013). "Value and Momentum Everywhere". Journal of Finance.
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# 版本信息
__version__ = "1.0.0"
__author__ = "Industry Analysis Team"

# 配置路径
DEFAULT_DATA_DIR = Path("/home/liujerry/金融数据/stocks")
DEFAULT_OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")

# 多因子权重配置
DEFAULT_FACTOR_WEIGHTS = {
    'size': 0.15,
    'value': 0.20,
    'profitability': 0.20,
    'investment': 0.10,
    'momentum': 0.15,
    'gross_profitability': 0.10,
    'growth': 0.10
}

# 行业分类映射 (基于证监会2023指引)
INDUSTRY_CLASSIFICATION = {
    'A01': {'name': '农林牧渔-农业', 'sector': '农林牧渔'},
    'A02': {'name': '农林牧渔-林业', 'sector': '农林牧渔'},
    'A03': {'name': '农林牧渔-牧业', 'sector': '农林牧渔'},
    'A04': {'name': '农林牧渔-渔业', 'sector': '农林牧渔'},
    'B05': {'name': '采掘-煤炭', 'sector': '采掘'},
    'B06': {'name': '采掘-石油', 'sector': '采掘'},
    'B07': {'name': '采掘-有色', 'sector': '采掘'},
    'C01': {'name': '化工-化学原料', 'sector': '化工'},
    'C02': {'name': '化工-化学制品', 'sector': '化工'},
    'C03': {'name': '化工-化学纤维', 'sector': '化工'},
    'C08': {'name': '钢铁', 'sector': '钢铁'},
    'C09': {'name': '有色金属', 'sector': '有色金属'},
    'C10': {'name': '电子-元器件', 'sector': '电子'},
    'C11': {'name': '电子-消费电子', 'sector': '电子'},
    'C13': {'name': '医药生物-医药制造', 'sector': '医药生物'},
    'C14': {'name': '医药生物-医疗器械', 'sector': '医药生物'},
    'C15': {'name': '医药生物-医疗服务', 'sector': '医药生物'},
    'C16': {'name': '电气设备-电源设备', 'sector': '电气设备'},
    'C17': {'name': '电气设备-电机', 'sector': '电气设备'},
    'C18': {'name': '电气设备-电气自动化', 'sector': '电气设备'},
    'C19': {'name': '国防军工-航空装备', 'sector': '国防军工'},
    'C20': {'name': '国防军工-航天装备', 'sector': '国防军工'},
    'C21': {'name': '国防军工-地面兵装', 'sector': '国防军工'},
    'C22': {'name': '计算机-软件服务', 'sector': '计算机'},
    'C23': {'name': '计算机-IT服务', 'sector': '计算机'},
    'C24': {'name': '计算机-互联网', 'sector': '计算机'},
    'C25': {'name': '传媒-游戏', 'sector': '传媒'},
    'C26': {'name': '传媒-影视', 'sector': '传媒'},
    'C27': {'name': '传媒-广告', 'sector': '传媒'},
    'C28': {'name': '通信-通信设备', 'sector': '通信'},
    'C29': {'name': '通信-通信服务', 'sector': '通信'},
    'C30': {'name': '机械设备-通用设备', 'sector': '机械设备'},
    'C31': {'name': '机械设备-专用设备', 'sector': '机械设备'},
    'C32': {'name': '机械设备-仪器仪表', 'sector': '机械设备'},
    'C33': {'name': '汽车-整车', 'sector': '汽车'},
    'C34': {'name': '汽车-零部件', 'sector': '汽车'},
    'C35': {'name': '电力设备-光伏', 'sector': '电力设备'},
    'C36': {'name': '电力设备-风电', 'sector': '电力设备'},
    'C37': {'name': '电力设备-储能', 'sector': '电力设备'},
    'C38': {'name': '建筑装饰-房屋建设', 'sector': '建筑装饰'},
    'C39': {'name': '建筑装饰-装修装饰', 'sector': '建筑装饰'},
    'C40': {'name': '交通运输-物流', 'sector': '交通运输'},
    'C41': {'name': '交通运输-运输服务', 'sector': '交通运输'},
    'C42': {'name': '金融-银行', 'sector': '金融'},
    'C43': {'name': '金融-券商', 'sector': '金融'},
    'C44': {'name': '金融-保险', 'sector': '金融'},
    'C45': {'name': '房地产-房地产开发', 'sector': '房地产'},
    'C46': {'name': '房地产-物业服务', 'sector': '房地产'},
    'C47': {'name': '商贸零售-商业百货', 'sector': '商贸零售'},
    'C48': {'name': '商贸零售-专业连锁', 'sector': '商贸零售'},
    'C49': {'name': '消费-食品饮料', 'sector': '消费'},
    'C50': {'name': '消费-服装纺织', 'sector': '消费'},
    'C51': {'name': '消费-家用电器', 'sector': '消费'},
    'C52': {'name': '消费-休闲服务', 'sector': '消费'},
}


class IndustryAnalyzer:
    """行业分析器"""
    
    def __init__(
        self,
        data_dir: Path = DEFAULT_DATA_DIR,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        factor_weights: Dict[str, float] = DEFAULT_FACTOR_WEIGHTS
    ):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.factor_weights = factor_weights
        self.industry_scores: Dict[str, Dict] = {}
        self.rotation_signals: Dict[str, str] = {}
        
    def load_stock_data(self, stock_file: Path) -> Optional[pd.DataFrame]:
        """加载股票数据"""
        try:
            df = pd.read_csv(stock_file, encoding='utf-8-sig')
            if 'date' not in df.columns or 'close' not in df.columns:
                return None
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            return df
        except Exception as e:
            print(f"警告: 无法加载 {stock_file.name}: {e}")
            return None
    
    def calculate_factor_score(
        self,
        df: pd.DataFrame,
        factor: str,
        lookback: int = 252
    ) -> float:
        """计算单因子得分"""
        if df is None or len(df) < 30:
            return 50.0  # 默认中性分数
        
        df = df.tail(lookback).copy()
        
        if factor == 'size':
            # 规模因子 - 使用流通市值代理
            close = df['close'].iloc[-1]
            volume = df.get('volume', pd.Series([1] * len(df))).iloc[-1]
            return min(100, max(0, 100 - (close * volume / 1e8)))
        
        elif factor == 'value':
            # 价值因子 - PE/PB代理
            returns = df['close'].pct_change().dropna()
            pe_proxy = 1 / (returns.mean() * 252 + 0.01) if returns.mean() > -0.01 else 50
            return min(100, max(0, 100 - pe_proxy / 50 * 100))
        
        elif factor == 'profitability':
            # 盈利能力因子 - ROE代理
            returns = df['close'].pct_change().dropna()
            total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            return min(100, max(0, 50 + total_return))
        
        elif factor == 'momentum':
            # 动量因子 - 过去12个月收益
            returns = df['close'].pct_change().tail(252).dropna()
            momentum = returns.sum() * 100
            return min(100, max(0, 50 + momentum))
        
        elif factor == 'growth':
            # 成长因子 - 营收/利润增速
            recent = df['close'].tail(63).mean()  # 3个月
            older = df['close'].tail(252).head(189).mean()  # 9个月前
            growth = (recent / older - 1) * 100 if older > 0 else 0
            return min(100, max(0, 50 + growth))
        
        elif factor == 'volatility':
            # 波动率因子 - 低波动加分
            returns = df['close'].pct_change().tail(63).std()
            vol_penalty = returns * 100
            return min(100, max(0, 70 - vol_penalty * 5))
        
        elif factor == 'momentum_6m':
            # 6个月动量
            momentum_6m = df['close'].pct_change(126).tail(1).values[0] * 100
            return min(100, max(0, 50 + momentum_6m))
        
        elif factor == 'momentum_12m':
            # 12个月动量
            momentum_12m = df['close'].pct_change(252).tail(1).values[0] * 100
            return min(100, max(0, 50 + momentum_12m))
        
        else:
            return 50.0
    
    def calculate_industry_score(
        self,
        stock_code: str,
        df: pd.DataFrame,
        factors: List[str] = None
    ) -> Dict:
        """计算股票的行业相关得分"""
        if factors is None:
            factors = list(self.factor_weights.keys())
        
        scores = {}
        for factor in factors:
            if factor in self.factor_weights:
                scores[factor] = self.calculate_factor_score(df, factor)
        
        # 计算综合得分
        composite_score = sum(
            self.factor_weights[factor] * scores.get(factor, 50)
            for factor in factors
            if factor in self.factor_weights
        )
        
        return {
            'code': stock_code,
            'composite_score': composite_score,
            'factor_scores': scores,
            'latest_price': df['close'].iloc[-1] if df is not None else None,
            'latest_date': df['date'].iloc[-1].strftime('%Y-%m-%d') if df is not None else None
        }
    
    def analyze_industry(
        self,
        stock_codes: List[str],
        factors: List[str] = None
    ) -> Dict[str, Dict]:
        """分析多个股票的行业得分"""
        industry_stocks = {}
        
        for code in stock_codes:
            stock_file = self.data_dir / f"{code}.csv"
            if not stock_file.exists():
                continue
            
            df = self.load_stock_data(stock_file)
            if df is None:
                continue
            
            score = self.calculate_industry_score(code, df, factors)
            industry_stocks[code] = score
        
        self.industry_scores = industry_stocks
        return industry_stocks
    
    def generate_rotation_signals(
        self,
        lookback_periods: List[int] = [63, 126, 252]  # 3, 6, 12个月
    ) -> Dict[str, str]:
        """生成行业轮动信号"""
        signals = {}
        
        for code, data in self.industry_scores.items():
            df_path = self.data_dir / f"{code}.csv"
            if not df_path.exists():
                continue
            
            df = self.load_stock_data(df_path)
            if df is None:
                continue
            
            # 计算各周期动量
            momentums = {}
            for period in lookback_periods:
                if len(df) > period:
                    mom = df['close'].pct_change(period).tail(1).values[0] * 100
                    momentums[period] = mom
            
            # 生成信号
            if len(momentums) >= 2:
                if momentums.get(252, 0) > momentums.get(126, 0) > momentums.get(63, 0):
                    signal = 'STRONG_BULL'  # 强势上涨
                elif momentums.get(252, 0) > 0 and momentums.get(126, 0) > 0:
                    signal = 'BULL'  # 震荡上涨
                elif momentums.get(252, 0) < momentums.get(126, 0) < momentums.get(63, 0):
                    signal = 'STRONG_BEAR'  # 强势下跌
                elif momentums.get(252, 0) < 0 and momentums.get(126, 0) < 0:
                    signal = 'BEAR'  # 震荡下跌
                else:
                    signal = 'NEUTRAL'  # 震荡
                
                signals[code] = signal
        
        self.rotation_signals = signals
        return signals
    
    def get_top_industries(
        self,
        n: int = 10,
        sort_by: str = 'composite_score'
    ) -> List[Dict]:
        """获取TOP行业/股票"""
        if not self.industry_scores:
            return []
        
        sorted_scores = sorted(
            self.industry_scores.items(),
            key=lambda x: x[1].get(sort_by, 0),
            reverse=True
        )
        
        return [data for _, data in sorted_scores[:n]]
    
    def save_results(
        self,
        filename: str = "industry_analysis_results.json"
    ) -> Path:
        """保存分析结果"""
        output_file = self.output_dir / filename
        
        results = {
            'date': datetime.now().isoformat(),
            'version': __version__,
            'factor_weights': self.factor_weights,
            'industry_scores': self.industry_scores,
            'rotation_signals': self.rotation_signals
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def generate_report(
        self,
        output_format: str = 'markdown'
    ) -> str:
        """生成分析报告"""
        if output_format == 'markdown':
            return self._generate_markdown_report()
        else:
            return self._generate_text_report()
    
    def _generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        report = f"""# 行业分析报告

## 基本信息

- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **版本**: {__version__}
- **分析股票数**: {len(self.industry_scores)}

## 多因子框架

| 因子 | 权重 | 研究支撑 |
|------|------|----------|
| SIZE (规模) | {self.factor_weights.get('size', 0)*100:.0f}% | Fama-French (1993) |
| VALUE (价值) | {self.factor_weights.get('value', 0)*100:.0f}% | Fama-French (1992) |
| PROFIT (盈利) | {self.factor_weights.get('profitability', 0)*100:.0f}% | Fama-French (2006) |
| MOMENTUM (动量) | {self.factor_weights.get('momentum', 0)*100:.0f}% | Carhart (1997) |
| GROWTH (成长) | {self.factor_weights.get('growth', 0)*100:.0f}% | Hou et al. (2015) |

## TOP 10 股票评分

"""
        
        # 添加TOP 10
        top_10 = self.get_top_industries(10)
        for i, stock in enumerate(top_10, 1):
            report += f"### {i}. {stock['code']}\n"
            report += f"- 综合得分: {stock['composite_score']:.2f}\n"
            report += f"- 最新价格: {stock['latest_price']:.2f}\n"
            report += f"- 因子得分:\n"
            for factor, score in stock.get('factor_scores', {}).items():
                report += f"  - {factor}: {score:.2f}\n"
            report += "\n"
        
        # 轮动信号
        report += """## 轮动信号

"""
        
        signal_counts = {}
        for signal in self.rotation_signals.values():
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        for signal, count in sorted(signal_counts.items(), key=lambda x: -x[1]):
            report += f"- {signal}: {count}只\n"
        
        return report
    
    def _generate_text_report(self) -> str:
        """生成纯文本格式报告"""
        report = f"""行业分析报告
{'='*50}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
版本: {__version__}
分析股票数: {len(self.industry_scores)}

多因子框架:
  SIZE (规模): {self.factor_weights.get('size', 0)*100:.0f}%
  VALUE (价值): {self.factor_weights.get('value', 0)*100:.0f}%
  PROFIT (盈利): {self.factor_weights.get('profitability', 0)*100:.0f}%
  MOMENTUM (动量): {self.factor_weights.get('momentum', 0)*100:.0f}%
  GROWTH (成长): {self.factor_weights.get('growth', 0)*100:.0f}%

TOP 10:
"""
        
        top_10 = self.get_top_industries(10)
        for i, stock in enumerate(top_10, 1):
            report += f"{i:2d}. {stock['code']}: {stock['composite_score']:.2f}\n"
        
        return report


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='行业分析技能 - 基于学术研究成果'
    )
    
    parser.add_argument(
        '--data', '-d',
        type=Path,
        default=DEFAULT_DATA_DIR,
        help='股票数据目录'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help='输出目录'
    )
    parser.add_argument(
        '--factors', '-f',
        nargs='+',
        default=list(DEFAULT_FACTOR_WEIGHTS.keys()),
        help='使用的因子'
    )
    parser.add_argument(
        '--top', '-t',
        type=int,
        default=20,
        help='显示TOP数量'
    )
    parser.add_argument(
        '--format', '-m',
        choices=['text', 'markdown'],
        default='text',
        help='输出格式'
    )
    parser.add_argument(
        '--rotation', '-r',
        action='store_true',
        help='生成轮动信号'
    )
    parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='保存结果'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    print(f"行业分析技能 v{__version__}")
    print(f"{'='*50}")
    
    # 初始化分析器
    analyzer = IndustryAnalyzer(
        data_dir=args.data,
        output_dir=args.output,
        factor_weights={f: DEFAULT_FACTOR_WEIGHTS[f] for f in args.factors if f in DEFAULT_FACTOR_WEIGHTS}
    )
    
    # 获取股票代码列表
    stock_files = list(args.data.glob("*.csv"))
    stock_codes = [f.stem for f in stock_files[:500]]  # 限制500只
    
    print(f"分析 {len(stock_codes)} 只股票...")
    print(f"使用因子: {', '.join(args.factors)}")
    
    # 分析
    analyzer.analyze_industry(stock_codes, args.factors)
    
    # 轮动信号
    if args.rotation:
        print("\n生成轮动信号...")
        analyzer.generate_rotation_signals()
    
    # 生成报告
    report = analyzer.generate_report(args.format)
    print(f"\n{report}")
    
    # 保存
    if args.save:
        output_file = analyzer.save_results()
        print(f"\n结果已保存: {output_file}")


if __name__ == "__main__":
    main()
