"""
Simplified FlareProx - Dynamic Cloudflare Worker Proxy
Creates workers on-demand based on request volume
"""
import os
import logging
import random
import json
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

# Cloudflare Worker Script (same as before)
WORKER_SCRIPT = """
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const targetUrl = url.searchParams.get('url');
    if (!targetUrl) {
      return new Response('Missing url parameter', { status: 400 });
    }

    function generateRandomIP() {
      return `${Math.floor(Math.random() * 255) + 1}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`;
    }

    const forwardedFor = generateRandomIP();
    const headers = new Headers(request.headers);
    headers.set('X-Forwarded-For', forwardedFor);
    headers.set('X-Real-IP', forwardedFor);

    try {
      const response = await fetch(targetUrl, {
        method: request.method,
        headers: headers,
        body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      });
      
      const newHeaders = new Headers(response.headers);
      newHeaders.set('X-Proxy-IP', forwardedFor);
      
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    } catch (error) {
      return new Response(`Proxy error: ${error.message}`, { status: 502 });
    }
  }
};
"""


class SimpleFlareProx:
    """Simple on-demand FlareProx worker manager"""
    
    def __init__(self, api_token: str, account_id: str, max_workers: int = 5):
        self.api_token = api_token
        self.account_id = account_id
        self.max_workers = max_workers
        self.workers = []  # List of worker URLs
        self.current_index = 0
        self.enabled = bool(api_token and account_id)
        
        if self.enabled:
            logger.info("FlareProx initialized (workers will be created on-demand)")
        else:
            logger.info("FlareProx disabled (missing credentials)")
    
    def _create_worker(self) -> Optional[str]:
        """Create a new Cloudflare Worker on-demand"""
        try:
            import time
            worker_name = f"k2think-{int(time.time())}-{random.randint(100000, 999999)}"
            
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/workers/scripts/{worker_name}"
            
            # Use multipart/form-data format as required by Cloudflare API
            files = {
                'metadata': (None, json.dumps({
                    "body_part": "script",
                    "main_module": "worker.js"
                })),
                'script': ('worker.js', WORKER_SCRIPT, 'application/javascript')
            }
            
            headers = {"Authorization": f"Bearer {self.api_token}"}
            
            response = httpx.put(url, headers=headers, files=files, timeout=60.0)
            
            if response.status_code in [200, 201]:
                worker_url = f"https://{worker_name}.pixeliumperfecto.workers.dev"
                self.workers.append(worker_url)
                logger.info(f"✅ Created worker: {worker_name}")
                return worker_url
            else:
                error_text = response.text[:500] if response.text else "No error message"
                logger.error(f"Failed to create worker: {response.status_code}")
                logger.error(f"Error details: {error_text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating worker: {e}")
            return None
    
    def get_worker_url(self, target_url: str) -> Optional[str]:
        """Get a worker URL, creating one if needed"""
        if not self.enabled:
            return None
        
        # Create first worker on first request
        if not self.workers:
            worker_url = self._create_worker()
            if not worker_url:
                logger.warning("FlareProx: Failed to create first worker")
                return None
        
        # Create additional workers if needed (dynamic scaling)
        if len(self.workers) < self.max_workers:
            # Simple rule: create new worker every N requests
            # This is where you'd add more sophisticated logic
            pass
        
        # Round-robin selection
        worker_url = self.workers[self.current_index % len(self.workers)]
        self.current_index += 1
        
        # Return proxied URL
        return f"{worker_url}?url={target_url}"


# Global instance
_flareprox_instance: Optional[SimpleFlareProx] = None


def init_flareprox():
    """Initialize FlareProx from environment variables"""
    global _flareprox_instance
    
    if os.getenv("ENABLE_FLAREPROX", "false").lower() == "true":
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        max_workers = int(os.getenv("FLAREPROX_MAX_WORKERS", "5"))
        
        _flareprox_instance = SimpleFlareProx(api_token, account_id, max_workers)
    else:
        logger.info("FlareProx disabled (ENABLE_FLAREPROX=false)")


def get_flareprox_url(target_url: str) -> Optional[str]:
    """Get FlareProx URL for a target, returns None if FlareProx disabled"""
    if _flareprox_instance:
        return _flareprox_instance.get_worker_url(target_url)
    return None


def generate_random_ip() -> str:
    """Generate a random IP address for logging"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
