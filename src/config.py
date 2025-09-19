"""
配置管理模块
统一管理所有环境变量和配置项
"""
import os
import logging
from typing import List
from dotenv import load_dotenv
from src.token_manager import TokenManager
from src.token_updater import TokenUpdater

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # API认证配置
    VALID_API_KEY: str = os.getenv("VALID_API_KEY", "")
    # 移除硬编码的K2THINK_TOKEN，使用token管理器
    K2THINK_API_URL: str = os.getenv("K2THINK_API_URL", "https://www.k2think.ai/api/chat/completions")
    
    # Token管理配置
    TOKENS_FILE: str = os.getenv("TOKENS_FILE", "tokens.txt")
    MAX_TOKEN_FAILURES: int = int(os.getenv("MAX_TOKEN_FAILURES", "3"))
    
    # Token自动更新配置
    ENABLE_TOKEN_AUTO_UPDATE: bool = os.getenv("ENABLE_TOKEN_AUTO_UPDATE", "false").lower() == "true"
    TOKEN_UPDATE_INTERVAL: int = int(os.getenv("TOKEN_UPDATE_INTERVAL", "86400"))  # 默认24小时
    ACCOUNTS_FILE: str = os.getenv("ACCOUNTS_FILE", "accounts.txt")
    GET_TOKENS_SCRIPT: str = os.getenv("GET_TOKENS_SCRIPT", "get_tokens.py")
    
    # Token管理器实例（延迟初始化）
    _token_manager: TokenManager = None
    _token_updater: TokenUpdater = None
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # 功能开关
    TOOL_SUPPORT: bool = os.getenv("TOOL_SUPPORT", "true").lower() == "true"
    DEBUG_LOGGING: bool = os.getenv("DEBUG_LOGGING", "false").lower() == "true"
    ENABLE_ACCESS_LOG: bool = os.getenv("ENABLE_ACCESS_LOG", "true").lower() == "true"
    
    # 性能配置
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "60"))
    MAX_KEEPALIVE_CONNECTIONS: int = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20"))
    MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "100"))
    STREAM_DELAY: float = float(os.getenv("STREAM_DELAY", "0.05"))
    STREAM_CHUNK_SIZE: int = int(os.getenv("STREAM_CHUNK_SIZE", "50"))
    MAX_STREAM_TIME: float = float(os.getenv("MAX_STREAM_TIME", "10.0"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # CORS配置
    CORS_ORIGINS: List[str] = (
        os.getenv("CORS_ORIGINS", "*").split(",") 
        if os.getenv("CORS_ORIGINS", "*") != "*" 
        else ["*"]
    )
    
    @classmethod
    def validate(cls) -> None:
        """验证必需的配置项"""
        if not cls.VALID_API_KEY:
            raise ValueError("错误：VALID_API_KEY 环境变量未设置。请在 .env 文件中提供一个安全的API密钥。")
        
        # 验证token文件是否存在
        if not os.path.exists(cls.TOKENS_FILE):
            if cls.ENABLE_TOKEN_AUTO_UPDATE:
                # 如果启用了自动更新，检查必要的文件是否存在
                if not os.path.exists(cls.ACCOUNTS_FILE):
                    raise ValueError(f"错误：启用了token自动更新，但账户文件 {cls.ACCOUNTS_FILE} 不存在。请创建账户文件或禁用自动更新。")
                if not os.path.exists(cls.GET_TOKENS_SCRIPT):
                    raise ValueError(f"错误：启用了token自动更新，但脚本文件 {cls.GET_TOKENS_SCRIPT} 不存在。")
                
                # 创建一个空的token文件，让token更新服务来处理
                print(f"Token文件 {cls.TOKENS_FILE} 不存在，已启用自动更新。创建空token文件，等待更新服务生成...")
                try:
                    with open(cls.TOKENS_FILE, 'w', encoding='utf-8') as f:
                        f.write("# Token文件将由自动更新服务生成\n")
                    print("空token文件已创建，服务启动后将自动更新token池。")
                except Exception as e:
                    raise ValueError(f"错误：无法创建token文件 {cls.TOKENS_FILE}: {e}")
            else:
                # 如果没有启用自动更新，则要求手动提供token文件
                raise ValueError(f"错误：Token文件 {cls.TOKENS_FILE} 不存在。请手动创建token文件或启用自动更新功能（设置 ENABLE_TOKEN_AUTO_UPDATE=true）。")
        
        # 验证数值范围
        if cls.PORT < 1 or cls.PORT > 65535:
            raise ValueError(f"错误：PORT 值 {cls.PORT} 不在有效范围内 (1-65535)")
        
        if cls.REQUEST_TIMEOUT <= 0:
            raise ValueError(f"错误：REQUEST_TIMEOUT 必须大于0，当前值: {cls.REQUEST_TIMEOUT}")
        
        if cls.STREAM_DELAY < 0:
            raise ValueError(f"错误：STREAM_DELAY 不能为负数，当前值: {cls.STREAM_DELAY}")
    
    @classmethod
    def setup_logging(cls) -> None:
        """设置日志配置"""
        import sys
        
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        
        log_level = level_map.get(cls.LOG_LEVEL, logging.INFO)
        
        # 确保日志输出使用UTF-8编码
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 确保标准输出使用UTF-8编码
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    
    @classmethod
    def get_token_manager(cls) -> TokenManager:
        """获取token管理器实例（单例模式）"""
        if cls._token_manager is None:
            cls._token_manager = TokenManager(
                tokens_file=cls.TOKENS_FILE,
                max_failures=cls.MAX_TOKEN_FAILURES,
                allow_empty=cls.ENABLE_TOKEN_AUTO_UPDATE  # 自动更新模式下允许空文件
            )
            # 如果启用了自动更新，设置强制刷新回调
            if cls.ENABLE_TOKEN_AUTO_UPDATE:
                cls._setup_force_refresh_callback()
        return cls._token_manager
    
    @classmethod
    def get_token_updater(cls) -> TokenUpdater:
        """获取token更新器实例（单例模式）"""
        if cls._token_updater is None:
            cls._token_updater = TokenUpdater(
                update_interval=cls.TOKEN_UPDATE_INTERVAL,
                get_tokens_script=cls.GET_TOKENS_SCRIPT,
                accounts_file=cls.ACCOUNTS_FILE,
                tokens_file=cls.TOKENS_FILE
            )
            # 如果token_manager已存在且启用了自动更新，建立连接
            if cls._token_manager is not None and cls.ENABLE_TOKEN_AUTO_UPDATE:
                cls._setup_force_refresh_callback()
        return cls._token_updater
    
    @classmethod
    def reload_tokens(cls) -> None:
        """重新加载token"""
        if cls._token_manager is not None:
            cls._token_manager.reload_tokens()
    
    @classmethod
    def _setup_force_refresh_callback(cls) -> None:
        """设置强制刷新回调函数"""
        if cls._token_manager is not None and cls._token_updater is None:
            # 确保token_updater已被初始化
            cls.get_token_updater()
        
        if cls._token_manager is not None and cls._token_updater is not None:
            # 设置强制刷新回调
            def force_refresh_callback():
                try:
                    logging.getLogger(__name__).info("连续token失效触发强制刷新")
                    success = cls._token_updater.force_update()
                    if success:
                        # 强制刷新成功后，重新加载token管理器
                        cls._token_manager.reload_tokens()
                        cls._token_manager.reset_consecutive_failures()
                        logging.getLogger(__name__).info("强制刷新完成，已重新加载token池")
                    else:
                        logging.getLogger(__name__).error("强制刷新失败")
                except Exception as e:
                    logging.getLogger(__name__).error(f"强制刷新回调执行失败: {e}")
            
            cls._token_manager.set_force_refresh_callback(force_refresh_callback)
            logging.getLogger(__name__).info("已设置连续失效自动强制刷新机制")