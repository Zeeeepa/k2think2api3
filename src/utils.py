"""
工具函数模块
提供通用的工具函数
"""
import logging
import sys

def safe_log_error(logger: logging.Logger, message: str, exception: Exception = None):
    """
    安全地记录错误日志，避免编码问题
    
    Args:
        logger: 日志记录器
        message: 错误消息
        exception: 异常对象（可选）
    """
    try:
        # 确保消息是字符串类型
        if not isinstance(message, str):
            message = str(message)
        
        if exception:
            # 安全地处理异常信息，避免编码问题
            try:
                error_msg = str(exception)
                # 处理可能的编码问题
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                else:
                    error_msg = error_msg.encode('utf-8', errors='replace').decode('utf-8')
            except Exception:
                error_msg = repr(exception)
            
            full_message = f"{message}: {error_msg}"
        else:
            full_message = message
        
        # 确保消息本身也是安全的
        try:
            if isinstance(full_message, bytes):
                safe_message = full_message.decode('utf-8', errors='replace')
            else:
                safe_message = full_message.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            safe_message = repr(full_message)
        
        logger.error(safe_message)
        
    except Exception as e:
        # 如果连安全日志都失败了，使用最基本的方式记录
        try:
            fallback_msg = f"Logging error: {repr(e)}, Original: {repr(message)}"
            logger.error(fallback_msg)
        except Exception:
            # 最后的保险措施 - 直接打印到控制台
            try:
                print(f"CRITICAL LOGGING FAILURE: {repr(message)}", file=sys.stderr)
            except Exception:
                pass  # 如果连print都失败了，就放弃

def safe_log_info(logger: logging.Logger, message: str):
    """
    安全地记录信息日志，避免编码问题
    
    Args:
        logger: 日志记录器
        message: 信息消息
    """
    try:
        # 确保消息是字符串类型
        if not isinstance(message, str):
            message = str(message)
        
        # 确保消息是安全的
        try:
            if isinstance(message, bytes):
                safe_message = message.decode('utf-8', errors='replace')
            else:
                safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            safe_message = repr(message)
        
        logger.info(safe_message)
        
    except Exception as e:
        try:
            fallback_msg = f"Logging info error: {repr(e)}, Original: {repr(message)}"
            logger.info(fallback_msg)
        except Exception:
            try:
                print(f"CRITICAL INFO LOGGING FAILURE: {repr(message)}", file=sys.stderr)
            except Exception:
                pass

def safe_log_warning(logger: logging.Logger, message: str):
    """
    安全地记录警告日志，避免编码问题
    
    Args:
        logger: 日志记录器
        message: 警告消息
    """
    try:
        # 确保消息是字符串类型
        if not isinstance(message, str):
            message = str(message)
        
        # 确保消息是安全的
        try:
            if isinstance(message, bytes):
                safe_message = message.decode('utf-8', errors='replace')
            else:
                safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            safe_message = repr(message)
        
        logger.warning(safe_message)
        
    except Exception as e:
        try:
            fallback_msg = f"Logging warning error: {repr(e)}, Original: {repr(message)}"
            logger.warning(fallback_msg)
        except Exception:
            try:
                print(f"CRITICAL WARNING LOGGING FAILURE: {repr(message)}", file=sys.stderr)
            except Exception:
                pass

def safe_str(obj) -> str:
    """
    安全地将对象转换为字符串，避免编码问题
    
    Args:
        obj: 要转换的对象
        
    Returns:
        str: 安全的字符串表示
    """
    try:
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif isinstance(obj, str):
            return obj.encode('utf-8', errors='replace').decode('utf-8')
        else:
            return str(obj).encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return repr(obj)