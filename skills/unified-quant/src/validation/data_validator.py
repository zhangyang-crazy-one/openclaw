"""
数据交叉验证模块
功能: Baostock ↔ Akshare 双重验证 + SearXNG 实时验证
"""
import akshare as ak
import baostock as bs
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.baostock_login()
        
    def baostock_login(self):
        """登录Baostock"""
        lg = bs.login()
        if lg.error_code != '0':
            print(f"Baostock登录失败: {lg.error_msg}")
            
    def baostock_login_out(self):
        """登出Baostock"""
        bs.logout()
    
    def get_stock_data_baostock(self, stock_code: str, date: str = None) -> Optional[Dict]:
        """获取Baostock股票数据"""
        if date:
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=date,
                end_date=date,
                frequency="d"
            )
        else:
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                frequency="d"
            )
        
        if rs.error_code != '0':
            return None
            
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
            
        if data_list:
            return {
                'date': data_list[0][0],
                'code': data_list[0][1],
                'open': float(data_list[0][2]) if data_list[0][2] else None,
                'high': float(data_list[0][3]) if data_list[0][3] else None,
                'low': float(data_list[0][4]) if data_list[0][4] else None,
                'close': float(data_list[0][5]) if data_list[0][5] else None,
                'volume': float(data_list[0][6]) if data_list[0][6] else None,
            }
        return None
    
    def get_stock_data_akshare(self, stock_code: str, period: str = "daily") -> Optional[Dict]:
        """获取Akshare股票数据"""
        try:
            # 转换为Akshare格式
            if stock_code.startswith('sh.6'):
                code = stock_code.replace('sh.6', '')
                df = ak.stock_zh_a_hist(symbol=code, period=period)
            elif stock_code.startswith('sz.3'):
                code = stock_code.replace('sz.3', '30')
                df = ak.stock_zh_a_hist(symbol=code, period=period)
            else:
                return None
                
            if not df.empty:
                latest = df.iloc[-1]
                return {
                    'date': str(latest['日期']),
                    'open': float(latest['开盘']) if latest['开盘'] else None,
                    'close': float(latest['收盘']) if latest['收盘'] else None,
                    'high': float(latest['最高']) if latest['最高'] else None,
                    'low': float(latest['最低']) if latest['最低'] else None,
                    'volume': float(latest['成交量']) if latest['成交量'] else None,
                }
        except Exception as e:
            print(f"Akshare获取失败: {e}")
        return None
    
    def verify_with_searxng(self, stock_code: str, date: str = None) -> Optional[Dict]:
        """使用SearXNG验证数据是否为实时"""
        # 这里可以调用searxng搜索当前股价
        # 返回搜索结果中的股价信息
        return None
    
    def cross_validate(self, stock_code: str, date: str = None) -> Dict:
        """交叉验证主函数"""
        result = {
            'stock_code': stock_code,
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'baostock': None,
            'akshare': None,
            'match': False,
            'confidence': 0,
            'errors': []
        }
        
        # 获取两个数据源的数据
        bs_data = self.get_stock_data_baostock(stock_code, date)
        akshare_data = self.get_stock_data_akshare(stock_code)
        
        result['baostock'] = bs_data
        result['akshare'] = akshare_data
        
        # 对比验证
        if bs_data and akshare_data:
            close_bs = bs_data.get('close')
            close_ak = akshare_data.get('close')
            
            if close_bs and close_ak:
                diff = abs(close_bs - close_ak)
                diff_pct = diff / close_bs * 100 if close_bs else 0
                
                if diff_pct < 1:  # 差异小于1%
                    result['match'] = True
                    result['confidence'] = 95
                elif diff_pct < 5:
                    result['match'] = True
                    result['confidence'] = 70
                else:
                    result['match'] = False
                    result['confidence'] = 30
                    result['errors'].append(f"数据差异较大: {diff_pct:.2f}%")
        
        # SearXNG验证(可选)
        # searxng_data = self.verify_with_searxng(stock_code, date)
        
        self.baostock_login_out()
        return result
    
    def get_validated_data(self, stock_codes: List[str]) -> Dict:
        """批量验证多只股票"""
        results = {}
        for code in stock_codes:
            results[code] = self.cross_validate(code)
        return results


if __name__ == "__main__":
    validator = DataValidator()
    # 测试
    result = validator.cross_validate("sh.600519")  # 茅台
    print(result)
