#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import re
from dotenv import load_dotenv

# 确保使用UTF-8编码
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONLEGACYWINDOWSSTDIO', '0')

# 强制设置UTF-8编码
import locale
try:
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        pass  # 如果设置失败，继续使用默认设置

# 重新配置标准输入输出流
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')

# 加载环境变量
load_dotenv()

class K2ThinkTokenExtractor:
    def __init__(self):
        self.base_url = "https://www.k2think.ai"
        self.login_url = f"{self.base_url}/api/v1/auths/signin"
        
        # 从环境变量读取代理配置
        proxy_url = os.getenv("PROXY_URL", "")
        self.proxies = {}
        if proxy_url:
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            print(f"使用代理: {proxy_url}")
        else:
            print("未配置代理，直接连接")
        
        # 基于f12调试信息的请求头
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://www.k2think.ai',
            'Priority': 'u=1, i',
            'Referer': 'https://www.k2think.ai/auth?mode=signin',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0'
        }
        
        self.lock = threading.Lock()

    def extract_token_from_set_cookie(self, response: requests.Response) -> Optional[str]:
        """从响应的Set-Cookie头中提取token"""
        set_cookie_headers = response.headers.get_list('Set-Cookie') if hasattr(response.headers, 'get_list') else [response.headers.get('Set-Cookie')]
        
        # 处理多个Set-Cookie头
        if set_cookie_headers:
            for cookie_header in set_cookie_headers:
                if cookie_header and 'token=' in cookie_header:
                    # 使用正则提取token值
                    match = re.search(r'token=([^;]+)', cookie_header)
                    if match:
                        return match.group(1)
        
        return None

    def login_and_get_token(self, email: str, password: str, retry_count: int = 3) -> Optional[str]:
        """登录并获取token，带重试机制"""
        login_data = {
            "email": email,
            "password": password
        }
        
        for attempt in range(retry_count):
            try:
                session = requests.Session()
                session.headers.update(self.headers)
                
                response = session.post(
                    self.login_url,
                    json=login_data,
                    proxies=self.proxies if self.proxies else None,
                    timeout=30
                )
                
                if response.status_code == 200:
                    token = self.extract_token_from_set_cookie(response)
                    if token:
                        return token
                
            except Exception as e:
                if attempt == retry_count - 1:
                    return None
                time.sleep(2)  # 重试间隔2秒
                continue
                
        return None

    def load_accounts(self, file_path: str = "./accounts.txt"):
        """从文件加载账户信息"""
        accounts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        account_data = json.loads(line)
                        
                        # Validate required fields
                        if 'email' not in account_data:
                            print(f"⚠️  警告: 账户配置缺少 'email' 字段，已跳过")
                            continue
                        
                        # Support both 'password' (correct) and 'k2_password' (deprecated) for backward compatibility
                        password = None
                        if 'password' in account_data:
                            password = account_data['password']
                        elif 'k2_password' in account_data:
                            print(f"⚠️  警告: 检测到已弃用的 'k2_password' 字段，请使用 'password' 字段")
                            print(f"   账户: {account_data['email']}")
                            print(f"   正确格式: {{\"email\": \"...\", \"password\": \"...\"}}")
                            password = account_data['k2_password']
                        else:
                            print(f"❌ 错误: 账户 {account_data['email']} 缺少 'password' 字段")
                            continue
                        
                        accounts.append({
                            'email': account_data['email'],
                            'password': password
                        })
                    except Exception as e:
                        print(f"⚠️  警告: 解析账户配置失败: {e}")
                        continue
            
            return accounts
            
        except FileNotFoundError:
            return []
        except Exception:
            return []

    def save_token(self, token: str, file_path: str = "./tokens.txt"):
        """保存token到文件"""
        try:
            with self.lock:
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(token + '\n')
        except Exception:
            pass

    def clear_tokens_file(self, file_path: str = "./tokens.txt"):
        """清空tokens文件，准备写入新的tokens"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')  # 清空文件
            print(f"已清空tokens文件: {file_path}")
        except Exception as e:
            print(f"清空tokens文件失败: {e}")

    def process_account(self, account, tokens_file: str = "./tokens.txt"):
        """处理单个账户"""
        token = self.login_and_get_token(account['email'], account['password'])
        if token:
            self.save_token(token, tokens_file)
            return True
        return False

    def process_all_accounts(self, accounts_file: str = "./accounts.txt", tokens_file: str = "./tokens.txt"):
        """使用并发处理所有账户"""
        accounts = self.load_accounts(accounts_file)
        if not accounts:
            print("没有账户需要处理或accounts.txt文件不存在")
            return False
        
        # 清空现有的tokens文件
        self.clear_tokens_file(tokens_file)
        
        print(f"开始处理 {len(accounts)} 个账户，4线程并发...")
        success_count = 0
        failed_count = 0
        
        # 先测试单个账户
        test_account = accounts[0]
        print(f"测试账户: {test_account['email']}")
        
        try:
            token = self.login_and_get_token(test_account['email'], test_account['password'])
            if token:
                print(f"测试成功，获取token: {token[:50]}...")
            else:
                print("测试失败，无法获取token")
        except Exception as e:
            print(f"测试异常: {e}")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有任务
            future_to_account = {executor.submit(self.process_account, account, tokens_file): account for account in accounts}
            
            # 处理结果
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    if future.result():
                        success_count += 1
                        print(f"✓ {account['email']}")
                    else:
                        failed_count += 1
                        print(f"✗ {account['email']}")
                except Exception as e:
                    failed_count += 1
                    print(f"✗ {account['email']} - {e}")
        
        print(f"\n处理完成: 成功 {success_count}, 失败 {failed_count}")
        
        # 返回是否有成功获取的token
        return success_count > 0


def main():
    import sys
    
    # 支持命令行参数
    accounts_file = sys.argv[1] if len(sys.argv) > 1 else "./accounts.txt"
    # 默认使用 data/tokens.txt 以匹配服务器配置
    tokens_file = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TOKENS_FILE", "data/tokens.txt")
    
    extractor = K2ThinkTokenExtractor()
    success = extractor.process_all_accounts(accounts_file, tokens_file)
    
    # 设置退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
