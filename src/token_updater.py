"""
Token更新服务模块
定期运行get_tokens.py来更新token池
"""
import os
import time
import logging
import threading
import subprocess
from typing import Optional
from datetime import datetime, timedelta
from src.utils import safe_log_error, safe_log_info, safe_log_warning
# 移除循环导入，Config在需要时动态导入

logger = logging.getLogger(__name__)

class TokenUpdater:
    """Token更新服务 - 定期更新token池"""
    
    def __init__(self, 
                 update_interval: int = 86400,  # 默认24小时更新一次
                 get_tokens_script: str = "get_tokens.py",
                 accounts_file: str = "accounts.txt",
                 tokens_file: str = "tokens.txt"):
        """
        初始化Token更新器
        
        Args:
            update_interval: 更新间隔（秒）
            get_tokens_script: get_tokens.py脚本路径
            accounts_file: 账户文件路径
            tokens_file: tokens文件路径
        """
        self.update_interval = update_interval
        self.get_tokens_script = get_tokens_script
        self.accounts_file = accounts_file
        self.tokens_file = tokens_file
        
        self.is_running = False
        self.update_thread: Optional[threading.Thread] = None
        self.last_update: Optional[datetime] = None
        self.update_count = 0
        self.error_count = 0
        self.is_updating = False
        self.last_error: Optional[str] = None
        
        logger.info(f"Token更新器初始化完成 - 更新间隔: {update_interval}秒")
        
        # 清理可能遗留的临时文件
        self.cleanup_all_temp_files()
    
    def _check_files_exist(self) -> bool:
        """检查必要文件是否存在"""
        if not os.path.exists(self.get_tokens_script):
            safe_log_error(logger, f"get_tokens.py脚本不存在: {self.get_tokens_script}")
            return False
        
        if not os.path.exists(self.accounts_file):
            safe_log_error(logger, f"账户文件不存在: {self.accounts_file}")
            return False
        
        return True
    
    def _run_token_update(self) -> bool:
        """运行token更新脚本（原子性更新）"""
        if self.is_updating:
            logger.warning("Token更新已在进行中，跳过此次更新")
            return False
            
        self.is_updating = True
        self.last_error = None
        temp_tokens_file = f"{self.tokens_file}.tmp"
        
        try:
            logger.info("开始更新token池...")
            
            # 使用临时文件进行更新，避免服务中断
            result = subprocess.run(
                ["python", self.get_tokens_script, self.accounts_file, temp_tokens_file],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                # 检查临时文件是否生成且不为空
                if os.path.exists(temp_tokens_file) and os.path.getsize(temp_tokens_file) > 0:
                    try:
                        # 原子性替换：重命名临时文件为正式文件
                        if os.path.exists(self.tokens_file):
                            # 备份当前文件
                            backup_file = f"{self.tokens_file}.backup"
                            if os.path.exists(backup_file):
                                os.remove(backup_file)  # 删除旧备份
                            os.rename(self.tokens_file, backup_file)
                        
                        os.rename(temp_tokens_file, self.tokens_file)
                        
                        logger.info("Token更新成功，文件已原子性替换")
                        logger.debug(f"更新输出: {result.stdout}")
                        self.update_count += 1
                        self.last_update = datetime.now()
                        
                        # 通知需要重新加载token管理器
                        self._notify_token_reload()
                        
                        return True
                    except Exception as rename_error:
                        error_msg = f"文件重命名失败: {rename_error}"
                        logger.error(error_msg)
                        self.last_error = error_msg
                        self._cleanup_temp_file(temp_tokens_file)
                        self.error_count += 1
                        return False
                else:
                    error_msg = "Token更新失败 - 临时文件为空或不存在"
                    logger.error(error_msg)
                    self.last_error = error_msg
                    self._cleanup_temp_file(temp_tokens_file)
                    self.error_count += 1
                    return False
            else:
                error_msg = f"Token更新失败 - 返回码: {result.returncode}, 错误: {result.stderr}"
                logger.error(error_msg)
                self.last_error = error_msg
                self._cleanup_temp_file(temp_tokens_file)
                self.error_count += 1
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = "Token更新超时"
            logger.error(error_msg)
            self.last_error = error_msg
            self._cleanup_temp_file(temp_tokens_file)
            self.error_count += 1
            return False
        except Exception as e:
            error_msg = f"Token更新异常: {e}"
            logger.error(error_msg)
            self.last_error = error_msg
            self._cleanup_temp_file(temp_tokens_file)
            self.error_count += 1
            return False
        finally:
            self.is_updating = False
    
    def _cleanup_temp_file(self, temp_file: str):
        """清理临时文件"""
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"已清理临时文件: {temp_file}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def cleanup_all_temp_files(self):
        """清理所有相关的临时文件"""
        temp_patterns = [
            f"{self.tokens_file}.tmp",
            f"{self.tokens_file}.backup"
        ]
        
        cleaned_count = 0
        for pattern in temp_patterns:
            try:
                if os.path.exists(pattern):
                    os.remove(pattern)
                    logger.info(f"已清理遗留文件: {pattern}")
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"清理遗留文件失败 {pattern}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"共清理了 {cleaned_count} 个遗留文件")
        else:
            logger.debug("没有发现需要清理的遗留文件")
        
        return cleaned_count
    
    def _notify_token_reload(self):
        """通知需要重新加载token管理器"""
        try:
            # 导入Config来触发token重新加载
            from src.config import Config
            if Config._token_manager is not None:
                Config._token_manager.reload_tokens()
                logger.info("Token管理器已重新加载")
        except Exception as e:
            logger.warning(f"通知token重新加载失败: {e}")
    

    def _update_loop(self):
        """更新循环"""
        logger.info("Token更新服务启动")
        
        # # 首次启动时，如果tokens.txt中没有token（非#开头），立即更新一次
        # 判断tokens.txt中的token数量
        if os.path.exists(self.tokens_file):
            with open(self.tokens_file, "r") as f:
                lines = f.readlines()
                lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
                if len(lines) < 1:
                    # 动态导入Config避免循环导入
                    from src.config import Config
                    if Config.ENABLE_TOKEN_AUTO_UPDATE:
                        logger.info("首次启动时，tokens.txt中没有token（非#开头），立即更新一次")
                        self._run_token_update()
        
        while self.is_running:
            try:
                time.sleep(self.update_interval)
                
                if not self.is_running:
                    break
                
                if self._check_files_exist():
                    self._run_token_update()
                else:
                    logger.warning("跳过此次更新 - 必要文件不存在")
                    
            except Exception as e:
                safe_log_error(logger, "更新循环异常", e)
                time.sleep(60)  # 异常时等待1分钟再继续
    
    def start(self) -> bool:
        """启动token更新服务"""
        if self.is_running:
            logger.warning("Token更新服务已在运行")
            return False
        
        if not self._check_files_exist():
            logger.error("启动失败 - 必要文件不存在")
            return False
        
        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("Token更新服务已启动")
        return True
    
    def stop(self):
        """停止token更新服务"""
        if not self.is_running:
            logger.warning("Token更新服务未在运行")
            return
        
        self.is_running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        
        logger.info("Token更新服务已停止")
    
    def force_update(self) -> bool:
        """强制立即更新token"""
        if not self._check_files_exist():
            logger.error("强制更新失败 - 必要文件不存在")
            return False
        
        logger.info("执行强制token更新")
        return self._run_token_update()
    
    async def force_update_async(self) -> bool:
        """异步强制立即更新token"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.force_update)
    
    def get_status(self) -> dict:
        """获取更新服务状态"""
        return {
            "is_running": self.is_running,
            "is_updating": self.is_updating,
            "update_interval": self.update_interval,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "update_count": self.update_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "next_update": (
                (self.last_update + timedelta(seconds=self.update_interval)).isoformat()
                if self.last_update else None
            ),
            "files": {
                "get_tokens_script": os.path.exists(self.get_tokens_script),
                "accounts_file": os.path.exists(self.accounts_file),
                "tokens_file": os.path.exists(self.tokens_file)
            }
        }