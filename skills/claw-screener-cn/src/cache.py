"""
本地缓存机制
"""
import os
import json
import pickle
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "/tmp/claw-screener-cn-cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """生成缓存文件路径"""
        # 使用 hash 避免文件名过长
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str, ttl_hours: int = 24) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            ttl_hours: 缓存过期时间(小时)
        
        Returns:
            缓存数据，如果不存在或过期返回 None
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            # 检查是否过期
            mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
            age = datetime.now() - mtime
            
            if age > timedelta(hours=ttl_hours):
                # 过期，删除
                cache_path.unlink()
                return None
            
            # 读取缓存
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            print(f"Cache read error: {e}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存数据
        
        Returns:
            是否成功
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            return True
        except Exception as e:
            print(f"Cache write error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除指定缓存"""
        cache_path = self._get_cache_path(key)
        try:
            if cache_path.exists():
                cache_path.unlink()
            return True
        except Exception:
            return False
    
    def clear(self, pattern: str = "*") -> int:
        """清空缓存"""
        count = 0
        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                pass
        return count
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            'count': len(files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'cache_dir': str(self.cache_dir)
        }


class DataCache:
    """数据专用缓存"""
    
    def __init__(self):
        self.manager = CacheManager()
    
    def cache_stock_data(self, stock_code: str, data: dict, ttl_hours: int = 4):
        """缓存股票数据 (4小时过期)"""
        key = f"stock_{stock_code}"
        self.manager.set(key, {
            'data': data,
            'cached_at': datetime.now().isoformat()
        })
    
    def get_stock_data(self, stock_code: str) -> Optional[dict]:
        """获取缓存的股票数据"""
        key = f"stock_{stock_code}"
        cached = self.manager.get(key, ttl_hours=4)
        return cached['data'] if cached else None
    
    def cache_index_components(self, index_code: str, stocks: list, ttl_hours: int = 24):
        """缓存指数成分股 (24小时过期)"""
        key = f"index_{index_code}"
        self.manager.set(key, {
            'stocks': stocks,
            'cached_at': datetime.now().isoformat()
        })
    
    def get_index_components(self, index_code: str) -> Optional[list]:
        """获取缓存的指数成分股"""
        key = f"index_{index_code}"
        cached = self.manager.get(key, ttl_hours=24)
        return cached['stocks'] if cached else None
    
    def cache_screening_result(self, stocks: list, result: list, ttl_hours: int = 4):
        """缓存筛选结果"""
        key = f"screening_{hash(tuple(sorted(stocks)))}"
        self.manager.set(key, {
            'result': result,
            'cached_at': datetime.now().isoformat()
        })
    
    def get_screening_result(self, stocks: list) -> Optional[list]:
        """获取缓存的筛选结果"""
        key = f"screening_{hash(tuple(sorted(stocks)))}"
        cached = self.manager.get(key, ttl_hours=4)
        return cached['result'] if cached else None


# 全局缓存实例
_cache = None

def get_cache() -> CacheManager:
    """获取全局缓存实例"""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


def get_data_cache() -> DataCache:
    """获取数据缓存实例"""
    return DataCache()


if __name__ == "__main__":
    # 测试
    cache = CacheManager()
    
    # 写入测试
    cache.set("test_key", {"name": "test", "value": 123})
    
    # 读取测试
    result = cache.get("test_key")
    print(f"Read: {result}")
    
    # 统计
    print(f"Stats: {cache.get_stats()}")
    
    # 清理
    cache.clear()
    print("Cleared")
