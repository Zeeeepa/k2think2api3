"""
工具函数模块
提供通用的工具函数
"""
import logging

def safe_log_error(logger: logging.Logger, message: str, exception: Exception = None):
    """
    安全地记录错误日志，避免编码问题
    
    Args:
        logger: 日志记录器
        message: 错误消息
        exception: 异常对象（可选）
    """
    try:
        if exception:
            # 安全地处理异常信息，避免编码问题
            error_msg = str(exception).encode('utf-8', errors='replace').decode('utf-8')
            full_message = f"{message}: {error_msg}"
        else:
            full_message = message
        
        # 确保消息本身也是安全的
        safe_message = full_message.encode('utf-8', errors='replace').decode('utf-8')
        logger.error(safe_message)
        
    except Exception as e:
        # 如果连安全日志都失败了，使用最基本的方式记录
        try:
            logger.error(f"Logging error occurred: {str(e)}")
            logger.error(f"Original message: {repr(message)}")
        except:
            # 最后的保险措施
            print(f"Critical logging failure: {repr(message)}")

def safe_log_info(logger: logging.Logger, message: str):
    """
    安全地记录信息日志，避免编码问题
    
    Args:
        logger: 日志记录器
        message: 信息消息
    """
    try:
        safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
        logger.info(safe_message)
    except Exception as e:
        try:
            logger.info(f"Logging info error: {str(e)}")
        except:
            print(f"Critical info logging failure: {repr(message)}")

def safe_log_warning(logger: logging.Logger, message: str):
    """
    安全地记录警告日志，避免编码问题
    
    Args:
        logger: 日志记录器
        message: 警告消息
    """
    try:
        safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
        logger.warning(safe_message)
    except Exception as e:
        try:
            logger.warning(f"Logging warning error: {str(e)}")
        except:
            print(f"Critical warning logging failure: {repr(message)}")

def safe_str(obj) -> str:
    """
    安全地将对象转换为字符串，避免编码问题
    
    Args:
        obj: 要转换的对象
        
    Returns:
        str: 安全的字符串表示
    """
    try:
        return str(obj).encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return repr(obj)