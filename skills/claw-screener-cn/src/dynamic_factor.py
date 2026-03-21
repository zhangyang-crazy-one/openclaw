"""
动态因子加权选股器
基于IC/IR动态调整因子权重

模型逻辑:
1. 计算每个因子的IC (信息系数)
2. 根据IC动态调整因子权重
3. IR = IC * sqrt(N) 最大化

参考: NotebookLM建议 - 基于IC/IR的动态多因子加权模型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json
import os


class DynamicFactorScreener:
    """
    动态因子加权选股器
    
    核心思想:
    - 根据因子历史表现(IC)动态调整权重
    - 剔除长期IC接近0的失效因子
    - 最大化IR (信息比)
    """
    
    def __init__(self, ic_history_file: str = None):
        self.params = {
            'min_ic': 0.02,    # 最小IC阈值
            'max_weight': 0.40,  # 单因子最大权重
            'min_weight': 0.05,  # 单因子最小权重
            'lookback_period': 20,  # IC计算回看期
            'top_n': 30,
        }
        
        # IC历史记录文件
        self.ic_file = ic_history_file or os.path.expanduser(
            '~/.openclaw/workspace/planning/factor_ic_history.json'
        )
        
        # 加载历史IC数据
        self.ic_history = self._load_ic_history()
        
        # 当前因子权重
        self.factor_weights = {
            'roe': 0.25,
            'momentum': 0.20,
            'value': 0.20,
            'growth': 0.15,
            'quality': 0.20,
        }
    
    def _load_ic_history(self) -> Dict:
        """加载历史IC数据"""
        if os.path.exists(self.ic_file):
            try:
                with open(self.ic_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_ic_history(self):
        """保存IC历史"""
        try:
            os.makedirs(os.path.dirname(self.ic_file), exist_ok=True)
            with open(self.ic_file, 'w') as f:
                json.dump(self.ic_history, f, indent=2)
        except Exception as e:
            print(f"保存IC历史失败: {e}")
    
    def _calculate_ic(self, factor_returns: pd.Series, stock_returns: pd.Series) -> float:
        """
        计算信息系数 (IC)
        
        IC = correlation(factor, returns)
        """
        if len(factor_returns) < 5:
            return 0
        
        try:
            # 简单IC: 因子值与下期收益的相关系数
            # 实际应该用因子排名与收益排名的IC (Rank IC)
            corr = factor_returns.rolling(5).corr(stock_returns)
            return corr.iloc[-1] if not pd.isna(corr.iloc[-1]) else 0
        except:
            return 0
    
    def update_factor_weights(self, factor_results: List[Dict], actual_returns: List[float]):
        """
        根据实际收益更新因子权重
        
        Args:
            factor_results: 各因子得分列表
            actual_returns: 实际收益列表
        """
        if len(factor_results) != len(actual_returns) or len(actual_returns) < 5:
            return
        
        # 计算各因子的IC
        factor_ics = {}
        
        for factor_name in self.factor_weights.keys():
            # 获取因子值序列
            factor_values = [r.get(factor_name, 0) for r in factor_results]
            
            # 计算IC
            ic = self._calculate_ic(
                pd.Series(factor_values),
                pd.Series(actual_returns)
            )
            
            factor_ics[factor_name] = ic
            
            # 更新历史IC
            if factor_name not in self.ic_history:
                self.ic_history[factor_name] = []
            
            self.ic_history[factor_name].append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'ic': ic
            })
        
        # 根据IC调整权重
        self._adjust_weights_by_ic(factor_ics)
        
        # 保存
        self._save_ic_history()
        
        print(f"因子权重已更新: {self.factor_weights}")
    
    def _adjust_weights_by_ic(self, factor_ics: Dict[str, float]):
        """根据IC调整权重"""
        # 过滤掉IC太小的因子
        valid_factors = {
            k: v for k, v in factor_ics.items() 
            if abs(v) >= self.params['min_ic']
        }
        
        if not valid_factors:
            print("所有因子IC都太低，保持原权重")
            return
        
        # 计算新权重 (基于IC绝对值)
        total_ic = sum(abs(ic) for ic in valid_factors.values())
        
        new_weights = {}
        for factor_name in self.factor_weights.keys():
            if factor_name in valid_factors:
                # IC越大，权重越高
                raw_weight = abs(valid_factors[factor_name]) / total_ic
                # 限制权重范围
                new_weights[factor_name] = max(
                    self.params['min_weight'],
                    min(self.params['max_weight'], raw_weight)
                )
            else:
                # 失效因子给最小权重
                new_weights[factor_name] = self.params['min_weight']
        
        # 归一化
        total = sum(new_weights.values())
        self.factor_weights = {
            k: v / total for k, v in new_weights.items()
        }
    
    def screen(self, stock_codes: List[str], factor_data: Dict[str, Dict]) -> List[Dict]:
        """
        动态因子筛选
        
        Args:
            stock_codes: 股票列表
            factor_data: {code: {roe: x, momentum: y, ...}}
            
        Returns:
            筛选结果
        """
        results = []
        
        print(f"开始动态因子筛选 ({len(stock_codes)} 只股票)")
        print(f"当前因子权重: {self.factor_weights}")
        
        for code in stock_codes:
            if code not in factor_data:
                continue
            
            data = factor_data[code]
            
            # 计算加权得分
            score = 0
            for factor_name, weight in self.factor_weights.items():
                factor_value = data.get(factor_name, 0)
                score += factor_value * weight
            
            results.append({
                'code': code,
                'score': score,
                'factors': data,
            })
        
        # 排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:self.params['top_n']]
    
    def get_factor_summary(self) -> str:
        """获取因子权重摘要"""
        lines = ["当前动态因子权重:"]
        
        for factor, weight in sorted(
            self.factor_weights.items(), 
            key=lambda x: x[1], 
            reverse=True
        ):
            ic = 0
            if factor in self.ic_history and self.ic_history[factor]:
                recent = self.ic_history[factor][-5:]  # 最近5个
                ic = np.mean([x['ic'] for x in recent])
            
            lines.append(f"  {factor}: {weight:.1%} (IC: {ic:.3f})")
        
        return "\n".join(lines)


class ICTracker:
    """
    IC追踪器 - 记录因子表现
    """
    
    def __init__(self):
        self.records = {}  # {factor: [{date, ic, return}]}
    
    def record(self, factor: str, ic: float, stock_return: float):
        """记录IC"""
        if factor not in self.records:
            self.records[factor] = []
        
        self.records[factor].append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'ic': ic,
            'return': stock_return,
        })
    
    def get_ic_stats(self, factor: str) -> Dict:
        """获取因子IC统计"""
        if factor not in self.records or not self.records[factor]:
            return {'ic_mean': 0, 'ic_std': 0, 'ir': 0}
        
        ics = [r['ic'] for r in self.records[factor]]
        
        ic_mean = np.mean(ics)
        ic_std = np.std(ics)
        
        # IR = IC / IC_std
        ir = ic_mean / ic_std if ic_std > 0 else 0
        
        return {
            'ic_mean': ic_mean,
            'ic_std': ic_std,
            'ir': ir,
            'count': len(ics),
        }
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有因子统计"""
        return {
            factor: self.get_ic_stats(factor) 
            for factor in self.records.keys()
        }


def dynamic_factor_screen(stock_codes: List[str], factor_data: Dict) -> List[Dict]:
    """动态因子筛选主函数"""
    screener = DynamicFactorScreener()
    return screener.screen(stock_codes, factor_data)


if __name__ == "__main__":
    # 演示
    screener = DynamicFactorScreener()
    
    # 模拟因子数据
    factor_data = {
        '300502': {'roe': 38, 'momentum': 6, 'value': 7, 'growth': 8, 'quality': 9},
        '300926': {'roe': 27, 'momentum': -2, 'value': 6, 'growth': 5, 'quality': 7},
        '300308': {'roe': 51, 'momentum': -1, 'value': 8, 'growth': 9, 'quality': 9},
        '300628': {'roe': 69, 'momentum': -8, 'value': 9, 'growth': 7, 'quality': 8},
    }
    
    codes = list(factor_data.keys())
    results = screener.screen(codes, factor_data)
    
    print("\n筛选结果:")
    for r in results:
        print(f"  {r['code']}: {r['score']:.2f}")
    
    print("\n" + screener.get_factor_summary())
