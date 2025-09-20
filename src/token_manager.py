"""
Token管理模块
负责管理K2Think的token池，实现轮询、负载均衡和失效标记
"""
import os
import json
import logging
import threading

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 导入安全日志函数
try:
    from src.utils import safe_log_error, safe_log_info, safe_log_warning
except ImportError:
    # 如果导入失败，提供简单的替代函数
    def safe_log_error(logger, msg, exc=None):
        try:
            if exc:
                logger.error(f"{msg}: {str(exc)}")
            else:
                logger.error(msg)
        except:
            print(f"Log error: {msg}")
    
    def safe_log_info(logger, msg):
        try:
            logger.info(msg)
        except:
            print(f"Log info: {msg}")
    
    def safe_log_warning(logger, msg):
        try:
            logger.warning(msg)
        except:
            print(f"Log warning: {msg}")

class TokenManager:
    """Token管理器 - 支持轮询、负载均衡和失效标记"""
    
    def __init__(self, tokens_file: str = "tokens.txt", max_failures: int = 3, allow_empty: bool = False):
        """
        初始化token管理器
        
        Args:
            tokens_file: token文件路径
            max_failures: 最大失败次数，超过后标记为失效
            allow_empty: 是否允许空的token文件（用于自动更新模式）
        """
        self.tokens_file = tokens_file
        self.max_failures = max_failures
        self.tokens: List[Dict] = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.allow_empty = allow_empty
        
        # 连续失效检测
        self.consecutive_failures = 0
        self.consecutive_failure_threshold = 2  # 连续失效阈值
        self.force_refresh_callback = None  # 强制刷新回调函数
        
        # 上游服务连续报错检测
        self.consecutive_upstream_errors = 0
        self.upstream_error_threshold = 2  # 上游服务连续报错阈值
        self.last_upstream_error_time = None
        
        # 加载tokens
        self.load_tokens()
        
        if not self.tokens and not allow_empty:
            raise ValueError(f"未找到有效的token，请检查文件: {tokens_file}")
    
    def load_tokens(self) -> None:
        """从文件加载token列表"""
        try:
            if not os.path.exists(self.tokens_file):
                raise FileNotFoundError(f"Token文件不存在: {self.tokens_file}")
            
            with open(self.tokens_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.tokens = []
            valid_token_index = 0
            for line in lines:
                token = line.strip()
                # 忽略空行和注释行
                if token and not token.startswith('#'):
                    self.tokens.append({
                        'token': token,
                        'failures': 0,
                        'is_active': True,
                        'last_used': None,
                        'last_failure': None,
                        'index': valid_token_index
                    })
                    valid_token_index += 1
            
            safe_log_info(logger, f"成功加载 {len(self.tokens)} 个token")
            
        except Exception as e:
            safe_log_error(logger, "加载token文件失败", e)
            raise
    

    def get_next_token(self) -> Optional[str]:
        """
        获取下一个可用的token（轮询算法）
        
        Returns:
            可用的token字符串，如果没有可用token则返回None
        """
        with self.lock:
            active_tokens = [t for t in self.tokens if t['is_active']]
            
            if not active_tokens:
                if self.allow_empty:
                    safe_log_warning(logger, "没有可用的token，可能正在等待自动更新")
                else:
                    safe_log_warning(logger, "没有可用的token")
                return None
            
            # 轮询算法：从当前索引开始寻找下一个可用token
            attempts = 0
            while attempts < len(self.tokens):
                token_info = self.tokens[self.current_index]
                
                if token_info['is_active']:
                    # 更新使用时间
                    token_info['last_used'] = datetime.now()
                    token = token_info['token']
                    
                    # 移动到下一个索引
                    self.current_index = (self.current_index + 1) % len(self.tokens)
                    
                    logger.debug(f"分配token (索引: {token_info['index']}, 失败次数: {token_info['failures']})")
                    return token
                
                # 移动到下一个token
                self.current_index = (self.current_index + 1) % len(self.tokens)
                attempts += 1
            
            safe_log_warning(logger, "所有token都已失效")
            return None
    
    def mark_token_failure(self, token: str, error_message: str = "") -> bool:
        """
        标记token使用失败
        
        Args:
            token: 失败的token
            error_message: 错误信息
            
        Returns:
            如果token被标记为失效返回True，否则返回False
        """
        with self.lock:
            for token_info in self.tokens:
                if token_info['token'] == token:
                    token_info['failures'] += 1
                    token_info['last_failure'] = datetime.now()
                    
                    # 检查是否是上游服务错误（401等认证错误）
                    is_upstream_error = self._is_upstream_error(error_message)
                    
                    if is_upstream_error:
                        # 增加上游服务连续报错计数
                        self.consecutive_upstream_errors += 1
                        self.last_upstream_error_time = datetime.now()
                        
                        safe_log_warning(logger, f"上游服务错误 (索引: {token_info['index']}, "
                                     f"失败次数: {token_info['failures']}/{self.max_failures}, "
                                     f"连续上游错误: {self.consecutive_upstream_errors}): {error_message}")
                        
                        # 检查上游服务连续报错触发条件
                        self._check_consecutive_upstream_errors()
                    else:
                        # 增加连续失效计数
                        self.consecutive_failures += 1
                        
                        safe_log_warning(logger, f"Token失败 (索引: {token_info['index']}, "
                                     f"失败次数: {token_info['failures']}/{self.max_failures}, "
                                     f"连续失效: {self.consecutive_failures}): {error_message}")
                        
                        # 检查连续失效触发条件
                        self._check_consecutive_failures()
                    
                    # 检查是否达到最大失败次数
                    if token_info['failures'] >= self.max_failures:
                        token_info['is_active'] = False
                        safe_log_error(logger, f"Token已失效 (索引: {token_info['index']}, "
                                   f"失败次数: {token_info['failures']})")
                        return True
                    
                    return False
            
            safe_log_warning(logger, "未找到匹配的token进行失败标记")
            return False
    
    def mark_token_success(self, token: str) -> None:
        """
        标记token使用成功（重置失败计数）
        
        Args:
            token: 成功的token
        """
        with self.lock:
            for token_info in self.tokens:
                if token_info['token'] == token:
                    if token_info['failures'] > 0:
                        safe_log_info(logger, f"Token恢复 (索引: {token_info['index']}, "
                                  f"重置失败次数: {token_info['failures']} -> 0)")
                        token_info['failures'] = 0
                    
                    # 成功请求重置上游服务错误计数
                    if self.consecutive_upstream_errors > 0:
                        safe_log_info(logger, f"重置上游服务连续错误计数: {self.consecutive_upstream_errors} -> 0")
                        self.consecutive_upstream_errors = 0
                    
                    # 注意：不再自动重置连续失效计数，只有手动重置或强制刷新成功后才重置
                    return
    
    def get_token_stats(self) -> Dict:
        """
        获取token池统计信息
        
        Returns:
            包含统计信息的字典
        """
        with self.lock:
            total = len(self.tokens)
            active = sum(1 for t in self.tokens if t['is_active'])
            inactive = total - active
            
            failure_distribution = {}
            for token_info in self.tokens:
                failures = token_info['failures']
                failure_distribution[failures] = failure_distribution.get(failures, 0) + 1
            
            return {
                'total_tokens': total,
                'active_tokens': active,
                'inactive_tokens': inactive,
                'current_index': self.current_index,
                'failure_distribution': failure_distribution,
                'max_failures': self.max_failures
            }
    
    def reset_token(self, token_index: int) -> bool:
        """
        重置指定索引的token（清除失败计数，重新激活）
        
        Args:
            token_index: token索引
            
        Returns:
            重置成功返回True，否则返回False
        """
        with self.lock:
            if 0 <= token_index < len(self.tokens):
                token_info = self.tokens[token_index]
                old_failures = token_info['failures']
                old_active = token_info['is_active']
                
                token_info['failures'] = 0
                token_info['is_active'] = True
                token_info['last_failure'] = None
                
                safe_log_info(logger, f"Token重置 (索引: {token_index}, "
                           f"失败次数: {old_failures} -> 0, "
                           f"状态: {old_active} -> True)")
                return True
            
            safe_log_warning(logger, f"无效的token索引: {token_index}")
            return False
    
    def reset_all_tokens(self) -> None:
        """重置所有token（清除所有失败计数，重新激活所有token）"""
        with self.lock:
            reset_count = 0
            for token_info in self.tokens:
                if token_info['failures'] > 0 or not token_info['is_active']:
                    token_info['failures'] = 0
                    token_info['is_active'] = True
                    token_info['last_failure'] = None
                    reset_count += 1
            
            safe_log_info(logger, f"重置了 {reset_count} 个token，当前活跃token数: {len(self.tokens)}")
    
    def reload_tokens(self) -> None:
        """重新加载token文件"""
        safe_log_info(logger, "重新加载token文件...")
        old_count = len(self.tokens)
        self.load_tokens()
        new_count = len(self.tokens)
        
        safe_log_info(logger, f"Token重新加载完成: {old_count} -> {new_count}")
    
    def get_token_by_index(self, index: int) -> Optional[Dict]:
        """根据索引获取token信息"""
        with self.lock:
            if 0 <= index < len(self.tokens):
                return self.tokens[index].copy()
            return None
    
    def set_force_refresh_callback(self, callback):
        """
        设置强制刷新回调函数
        
        Args:
            callback: 当需要强制刷新时调用的异步函数
        """
        self.force_refresh_callback = callback
        safe_log_info(logger, "已设置强制刷新回调函数")
    
    def _is_upstream_error(self, error_message: str) -> bool:
        """
        判断是否为上游服务错误
        
        Args:
            error_message: 错误信息
            
        Returns:
            如果是上游服务错误返回True，否则返回False
        """
        # 检查常见的上游服务错误标识
        upstream_error_indicators = [
            "上游服务错误: 401",
            "401",
            "unauthorized",
            "invalid token",
            "authentication failed",
            "token expired"
        ]
        
        error_lower = error_message.lower()
        return any(indicator.lower() in error_lower for indicator in upstream_error_indicators)
    
    def _check_consecutive_upstream_errors(self):
        """
        检查上游服务连续报错情况，触发强制刷新机制
        """
        if self.consecutive_upstream_errors >= self.upstream_error_threshold:
            safe_log_warning(logger, f"检测到连续{self.consecutive_upstream_errors}个上游服务错误，触发强制刷新机制")
            
            # 重置上游错误计数，避免重复触发
            self.consecutive_upstream_errors = 0
            
            if self.force_refresh_callback:
                self._trigger_force_refresh("上游服务连续报错")
            else:
                safe_log_warning(logger, "未设置强制刷新回调函数，无法自动刷新token池")
    
    def _check_consecutive_failures(self):
        """
        检查连续失效情况，触发强制刷新机制
        """
        # 只有在token池数量大于2时才检查连续失效
        if len(self.tokens) <= 2:
            logger.debug(f"Token池数量({len(self.tokens)})不足，跳过连续失效检查")
            return
        
        if self.consecutive_failures >= self.consecutive_failure_threshold:
            safe_log_warning(logger, f"检测到连续{self.consecutive_failures}个token失效，触发强制刷新机制")
            
            if self.force_refresh_callback:
                self._trigger_force_refresh("连续token失效")
            else:
                safe_log_warning(logger, "未设置强制刷新回调函数，无法自动刷新token池")
    
    def _trigger_force_refresh(self, reason: str):
        """
        触发强制刷新
        
        Args:
            reason: 触发原因
        """
        try:
            # 异步调用强制刷新
            import asyncio
            import threading
            
            def run_async_callback():
                try:
                    # 创建新的事件循环（如果当前线程没有）
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # 运行强制刷新（现在是同步函数）
                    self.force_refresh_callback()
                    
                    safe_log_info(logger, f"强制刷新已触发 - 原因: {reason}")
                    
                except Exception as e:
                    safe_log_error(logger, "执行强制刷新回调失败", e)
            
            # 在新线程中执行，避免阻塞当前操作
            refresh_thread = threading.Thread(target=run_async_callback, daemon=True)
            refresh_thread.start()
            
        except Exception as e:
            safe_log_error(logger, "启动强制刷新线程失败", e)
    
    def get_consecutive_failures(self) -> int:
        """获取当前连续失效次数"""
        return self.consecutive_failures
    
    def get_consecutive_upstream_errors(self) -> int:
        """获取当前上游服务连续错误次数"""
        return self.consecutive_upstream_errors
    
    def reset_consecutive_failures(self):
        """重置连续失效计数"""
        with self.lock:
            old_count = self.consecutive_failures
            old_upstream_count = self.consecutive_upstream_errors
            
            self.consecutive_failures = 0
            self.consecutive_upstream_errors = 0
            
            if old_count > 0:
                safe_log_info(logger, f"手动重置连续失效计数: {old_count} -> 0")
            if old_upstream_count > 0:
                safe_log_info(logger, f"手动重置上游服务连续错误计数: {old_upstream_count} -> 0")
    

