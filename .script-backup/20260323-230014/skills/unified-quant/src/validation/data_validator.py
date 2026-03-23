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
        # 如果没有指定日期，获取最近30天的数据
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if date:
            start_date = date
            end_date = date
            
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,code,open,high,low,close,volume,amount,turn,pctChg",
            start_date=start_date,
            end_date=end_date,
            frequency="d"
        )
        
        if rs.error_code != '0':
            return None
            
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        # 返回最新一条数据
        if data_list:
            d = data_list[-1]  # 最新数据
            return {
                'date': d[0],
                'code': d[1],
                'open': float(d[2]) if d[2] else None,
                'high': float(d[3]) if d[3] else None,
                'low': float(d[4]) if d[4] else None,
                'close': float(d[5]) if d[5] else None,
                'volume': float(d[6]) if d[6] else None,
            }
        return None
    
    def get_stock_data_akshare(self, stock_code: str, period: str = "daily") -> Optional[Dict]:
        """获取Akshare股票数据"""
        try:
            # 转换为Akshare格式 (直接去掉前缀)
            # sh.600519 -> 600519
            # sz.300001 -> 300001
            if stock_code.startswith('sh.'):
                code = stock_code.replace('sh.', '')
            elif stock_code.startswith('sz.'):
                code = stock_code.replace('sz.', '')
            else:
                code = stock_code
            
            df = ak.stock_zh_a_hist(symbol=code, period=period)
            
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
        bs_data = self.get_stock_data_baostock(stock_code, None)  # 获取最新数据
        akshare_data = self.get_stock_data_akshare(stock_code)
        
        result['baostock'] = bs_data
        result['akshare'] = akshare_data
        
        # 对比验证 - 使用相同日期的数据
        if bs_data and akshare_data:
            bs_date = bs_data.get('date')
            ak_date = akshare_data.get('date')
            
            # 如果日期相同，对比价格
            if bs_date and ak_date and bs_date == ak_date:
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
            else:
                # 日期不同，设置为低置信度
                result['confidence'] = 50
                result['errors'].append(f"日期不同: Baostock={bs_date}, Akshare={ak_date}")
        
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
