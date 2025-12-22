"""
Configuration Loader for K2Think API Proxy
Supports YAML config files with environment variable overrides
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage configuration from YAML files and environment variables"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to config file. Defaults to config.yaml
        """
        self.config_path = config_path or os.getenv('K2THINK_CONFIG', 'config.yaml')
        self.config: Dict[str, Any] = {}
        self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            # Try example config
            example_config = Path('config.example.yaml')
            if example_config.exists():
                logger.warning(f"Config file {self.config_path} not found. Using example config.")
                config_file = example_config
            else:
                logger.warning(f"No config file found. Using defaults.")
                self.config = self._get_default_config()
                return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"Configuration loaded from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
            self.config = self._get_default_config()
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration"""
        # Server configuration
        if os.getenv('HOST'):
            self.config.setdefault('server', {})['host'] = os.getenv('HOST')
        if os.getenv('PORT'):
            self.config.setdefault('server', {})['port'] = int(os.getenv('PORT'))
        
        # K2Think configuration
        if os.getenv('K2THINK_BASE_URL'):
            self.config.setdefault('k2think', {})['base_url'] = os.getenv('K2THINK_BASE_URL')
        if os.getenv('K2THINK_API_ENDPOINT'):
            self.config.setdefault('k2think', {})['api_endpoint'] = os.getenv('K2THINK_API_ENDPOINT')
        
        # Proxy configuration
        if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY'):
            self.config.setdefault('network', {}).setdefault('proxy', {})
            self.config['network']['proxy']['enabled'] = True
            if os.getenv('HTTP_PROXY'):
                self.config['network']['proxy']['http_proxy'] = os.getenv('HTTP_PROXY')
            if os.getenv('HTTPS_PROXY'):
                self.config['network']['proxy']['https_proxy'] = os.getenv('HTTPS_PROXY')
        
        # Logging configuration
        if os.getenv('LOG_LEVEL'):
            self.config.setdefault('server', {})['log_level'] = os.getenv('LOG_LEVEL')
        
        # Debug mode
        if os.getenv('DEBUG'):
            self.config.setdefault('development', {})['debug_mode'] = os.getenv('DEBUG').lower() in ('true', '1', 'yes')
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 8001,
                'workers': 4,
                'timeout': 300,
                'log_level': 'info'
            },
            'api': {
                'api_prefix': '/v1',
                'enable_cors': True,
                'cors_origins': ['*']
            },
            'k2think': {
                'base_url': 'https://www.k2think.ai',
                'api_endpoint': 'https://www.k2think.ai/api/inference/v1/chat/completions',
                'tokens': {
                    'auto_refresh': True,
                    'refresh_interval': 3600,
                    'min_valid_tokens': 2,
                    'max_retries': 3
                },
                'requests': {
                    'timeout': 120,
                    'max_retries': 3,
                    'retry_delay': 1
                }
            },
            'error_handling': {
                'enable_fallback': True,
                'circuit_breaker': {
                    'enabled': True,
                    'failure_threshold': 5,
                    'success_threshold': 2,
                    'timeout': 60
                },
                'retry_policy': {
                    'max_attempts': 3,
                    'backoff_multiplier': 2,
                    'max_backoff': 60
                }
            },
            'logging': {
                'file': {
                    'enabled': True,
                    'path': 'logs/k2think.log'
                },
                'requests': {
                    'enabled': True,
                    'log_request_body': True,
                    'log_response_body': False
                }
            },
            'monitoring': {
                'prometheus': {
                    'enabled': True,
                    'endpoint': '/metrics'
                },
                'health': {
                    'enabled': True,
                    'liveness_endpoint': '/health/live',
                    'readiness_endpoint': '/health/ready'
                }
            },
            'features': {
                'streaming': {'enabled': True},
                'function_calling': {'enabled': True},
                'vision': {'enabled': True},
                'embeddings': {'enabled': True}
            },
            'models': {
                'default': 'k2-think',
                'available': [
                    {
                        'id': 'k2-think',
                        'name': 'K2-Think',
                        'description': 'MBZUAI K2-Think reasoning model',
                        'max_tokens': 32768,
                        'supports_streaming': True,
                        'supports_functions': True,
                        'supports_vision': True
                    }
                ]
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key path
        
        Args:
            key_path: Dot-separated path (e.g., 'server.port')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value by dot-separated key path
        
        Args:
            key_path: Dot-separated path (e.g., 'server.port')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
        self._apply_env_overrides()
        logger.info("Configuration reloaded")
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary"""
        return self.config.copy()
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if configuration is valid
        """
        required_keys = [
            'server.host',
            'server.port',
            'k2think.api_endpoint'
        ]
        
        for key_path in required_keys:
            if self.get(key_path) is None:
                logger.error(f"Missing required configuration: {key_path}")
                return False
        
        # Validate port range
        port = self.get('server.port')
        if not (1 <= port <= 65535):
            logger.error(f"Invalid port number: {port}")
            return False
        
        return True


# Global configuration instance
_config: Optional[ConfigLoader] = None


def get_config(reload: bool = False) -> ConfigLoader:
    """
    Get global configuration instance
    
    Args:
        reload: Force reload configuration
        
    Returns:
        ConfigLoader instance
    """
    global _config
    
    if _config is None or reload:
        _config = ConfigLoader()
        
        if not _config.validate():
            logger.warning("Configuration validation failed. Using defaults.")
    
    return _config


def reload_config():
    """Reload global configuration"""
    global _config
    if _config:
        _config.reload()
    else:
        _config = ConfigLoader()


if __name__ == '__main__':
    # Test configuration loading
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    
    print("=== Configuration Loaded ===")
    print(f"Server: {config.get('server.host')}:{config.get('server.port')}")
    print(f"K2Think API: {config.get('k2think.api_endpoint')}")
    print(f"Log Level: {config.get('server.log_level')}")
    print(f"Circuit Breaker: {config.get('error_handling.circuit_breaker.enabled')}")
    print(f"Retry Max Attempts: {config.get('error_handling.retry_policy.max_attempts')}")
    print(f"Available Models: {len(config.get('models.available', []))}")

