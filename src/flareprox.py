"""
FlareProx Integration for K2Think API
Provides rotating Cloudflare Workers for IP masking and load distribution
"""
import os
import json
import time
import random
import string
import logging
import requests
from typing import Dict, List, Optional
from threading import Lock
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FlareProxError(Exception):
    """Custom exception for FlareProx errors."""
    pass


class CloudflareWorker:
    """Represents a single Cloudflare Worker endpoint."""
    
    def __init__(self, name: str, url: str, created_at: str):
        self.name = name
        self.url = url
        self.created_at = created_at
        self.last_used = None
        self.success_count = 0
        self.failure_count = 0
        self.is_healthy = True
    
    def mark_success(self):
        """Mark this worker as successfully used."""
        self.last_used = datetime.now()
        self.success_count += 1
        self.is_healthy = True
    
    def mark_failure(self):
        """Mark this worker as failed."""
        self.last_used = datetime.now()
        self.failure_count += 1
        
        # Mark unhealthy if failure rate is too high
        if self.failure_count > 5 and self.success_count < self.failure_count:
            self.is_healthy = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "created_at": self.created_at,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "is_healthy": self.is_healthy
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CloudflareWorker':
        """Create from dictionary."""
        worker = cls(
            name=data["name"],
            url=data["url"],
            created_at=data["created_at"]
        )
        worker.success_count = data.get("success_count", 0)
        worker.failure_count = data.get("failure_count", 0)
        worker.is_healthy = data.get("is_healthy", True)
        
        if data.get("last_used"):
            try:
                worker.last_used = datetime.fromisoformat(data["last_used"])
            except:
                pass
        
        return worker


class CloudflareManager:
    """Manages Cloudflare Worker deployments."""
    
    WORKER_SCRIPT = '''/**
 * FlareProx - Cloudflare Worker for K2Think API
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  try {
    const url = new URL(request.url)
    const targetUrl = getTargetUrl(url, request.headers)

    if (!targetUrl) {
      return createErrorResponse('No target URL specified', 400)
    }

    let targetURL
    try {
      targetURL = new URL(targetUrl)
    } catch (e) {
      return createErrorResponse('Invalid target URL', 400)
    }

    // Build target URL with filtered query parameters
    const targetParams = new URLSearchParams()
    for (const [key, value] of url.searchParams) {
      if (!['url', '_cb', '_t'].includes(key)) {
        targetParams.append(key, value)
      }
    }
    if (targetParams.toString()) {
      targetURL.search = targetParams.toString()
    }

    // Create proxied request
    const proxyRequest = createProxyRequest(request, targetURL)
    const response = await fetch(proxyRequest)

    // Process and return response
    return createProxyResponse(response, request.method)

  } catch (error) {
    return createErrorResponse('Proxy request failed: ' + error.message, 500)
  }
}

function getTargetUrl(url, headers) {
  let targetUrl = url.searchParams.get('url')
  if (!targetUrl) {
    targetUrl = headers.get('X-Target-URL')
  }
  if (!targetUrl && url.pathname !== '/') {
    const pathUrl = url.pathname.slice(1)
    if (pathUrl.startsWith('http')) {
      targetUrl = pathUrl
    }
  }
  return targetUrl
}

function createProxyRequest(request, targetURL) {
  const proxyHeaders = new Headers()
  const allowedHeaders = [
    'accept', 'accept-language', 'accept-encoding', 'authorization',
    'cache-control', 'content-type', 'origin', 'referer', 'user-agent'
  ]

  for (const [key, value] of request.headers) {
    if (allowedHeaders.includes(key.toLowerCase())) {
      proxyHeaders.set(key, value)
    }
  }

  proxyHeaders.set('Host', targetURL.hostname)

  const customXForwardedFor = request.headers.get('X-My-X-Forwarded-For')
  if (customXForwardedFor) {
    proxyHeaders.set('X-Forwarded-For', customXForwardedFor)
  } else {
    proxyHeaders.set('X-Forwarded-For', generateRandomIP())
  }

  return new Request(targetURL.toString(), {
    method: request.method,
    headers: proxyHeaders,
    body: ['GET', 'HEAD'].includes(request.method) ? null : request.body
  })
}

function createProxyResponse(response, requestMethod) {
  const responseHeaders = new Headers()

  for (const [key, value] of response.headers) {
    if (!['content-encoding', 'content-length', 'transfer-encoding'].includes(key.toLowerCase())) {
      responseHeaders.set(key, value)
    }
  }

  responseHeaders.set('Access-Control-Allow-Origin', '*')
  responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD')
  responseHeaders.set('Access-Control-Allow-Headers', '*')

  if (requestMethod === 'OPTIONS') {
    return new Response(null, { status: 204, headers: responseHeaders })
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders
  })
}

function createErrorResponse(error, status) {
  return new Response(JSON.stringify({ error }), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

function generateRandomIP() {
  return [1, 2, 3, 4].map(() => Math.floor(Math.random() * 255) + 1).join('.')
}'''
    
    def __init__(self, api_token: str, account_id: str):
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self._account_subdomain = None
    
    @property
    def worker_subdomain(self) -> str:
        """Get the worker subdomain for workers.dev URLs."""
        if self._account_subdomain:
            return self._account_subdomain
        
        url = f"{self.base_url}/accounts/{self.account_id}/workers/subdomain"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                subdomain = data.get("result", {}).get("subdomain")
                if subdomain:
                    self._account_subdomain = subdomain
                    return subdomain
        except requests.RequestException:
            pass
        
        self._account_subdomain = self.account_id.lower()
        return self._account_subdomain
    
    def create_worker(self, name: Optional[str] = None) -> CloudflareWorker:
        """Deploy a new Cloudflare Worker."""
        if not name:
            timestamp = str(int(time.time()))
            random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
            name = f"k2think-{timestamp}-{random_suffix}"
        
        url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts/{name}"
        
        files = {
            'metadata': (None, json.dumps({
                "body_part": "script",
                "main_module": "worker.js"
            })),
            'script': ('worker.js', self.WORKER_SCRIPT, 'application/javascript')
        }
        
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            response = requests.put(url, headers=headers, files=files, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            raise FlareProxError(f"Failed to create worker: {e}")
        
        # Enable subdomain
        subdomain_url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts/{name}/subdomain"
        try:
            requests.post(subdomain_url, headers=self.headers, json={"enabled": True}, timeout=30)
        except requests.RequestException:
            pass
        
        worker_url = f"https://{name}.{self.worker_subdomain}.workers.dev"
        created_at = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return CloudflareWorker(name=name, url=worker_url, created_at=created_at)
    
    def delete_worker(self, worker_name: str) -> bool:
        """Delete a Cloudflare Worker."""
        url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts/{worker_name}"
        
        try:
            response = requests.delete(url, headers=self.headers, timeout=30)
            return response.status_code in [200, 404]
        except requests.RequestException as e:
            logger.error(f"Failed to delete worker {worker_name}: {e}")
            return False
    
    def list_workers(self) -> List[Dict]:
        """List all K2Think workers."""
        url = f"{self.base_url}/accounts/{self.account_id}/workers/scripts"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise FlareProxError(f"Failed to list workers: {e}")
        
        data = response.json()
        workers = []
        
        for script in data.get("result", []):
            name = script.get("id", "")
            if name.startswith("k2think-"):
                workers.append({
                    "name": name,
                    "url": f"https://{name}.{self.worker_subdomain}.workers.dev",
                    "created_at": script.get("created_on", "unknown")
                })
        
        return workers


class FlareProxPool:
    """Manages a pool of FlareProx workers with load balancing and rotation."""
    
    def __init__(self, api_token: str, account_id: str, pool_size: int = 3):
        self.manager = CloudflareManager(api_token, account_id)
        self.pool_size = pool_size
        self.workers: List[CloudflareWorker] = []
        self.current_index = 0
        self.lock = Lock()
        self.workers_file = "data/flareprox_workers.json"
        self.enabled = True
        
        # Load existing workers
        self._load_workers()
    
    def _load_workers(self):
        """Load workers from local cache."""
        if os.path.exists(self.workers_file):
            try:
                with open(self.workers_file, 'r') as f:
                    data = json.load(f)
                    self.workers = [CloudflareWorker.from_dict(w) for w in data.get("workers", [])]
                    logger.info(f"Loaded {len(self.workers)} FlareProx workers from cache")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load workers from cache: {e}")
    
    def _save_workers(self):
        """Save workers to local cache."""
        try:
            os.makedirs(os.path.dirname(self.workers_file), exist_ok=True)
            with open(self.workers_file, 'w') as f:
                data = {
                    "workers": [w.to_dict() for w in self.workers],
                    "updated_at": datetime.now().isoformat()
                }
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Could not save workers to cache: {e}")
    
    def initialize(self):
        """Initialize the worker pool."""
        if not self.enabled:
            logger.info("FlareProx is disabled")
            return
        
        # Remove unhealthy workers
        healthy_workers = [w for w in self.workers if w.is_healthy]
        
        # Create new workers if needed
        workers_needed = self.pool_size - len(healthy_workers)
        
        if workers_needed > 0:
            logger.info(f"Creating {workers_needed} new FlareProx workers...")
            for i in range(workers_needed):
                try:
                    worker = self.manager.create_worker()
                    healthy_workers.append(worker)
                    logger.info(f"Created worker: {worker.name}")
                except FlareProxError as e:
                    logger.error(f"Failed to create worker {i+1}: {e}")
        
        self.workers = healthy_workers
        self._save_workers()
        
        logger.info(f"FlareProx pool initialized with {len(self.workers)} workers")
    
    def get_next_worker(self) -> Optional[CloudflareWorker]:
        """Get the next worker using round-robin with health checks."""
        if not self.enabled or not self.workers:
            return None
        
        with self.lock:
            # Try to find a healthy worker
            attempts = 0
            while attempts < len(self.workers):
                worker = self.workers[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.workers)
                
                if worker.is_healthy:
                    return worker
                
                attempts += 1
            
            # No healthy workers found
            return None
    
    def mark_worker_success(self, worker: CloudflareWorker):
        """Mark a worker as successfully used."""
        worker.mark_success()
        self._save_workers()
    
    def mark_worker_failure(self, worker: CloudflareWorker):
        """Mark a worker as failed."""
        worker.mark_failure()
        self._save_workers()
        
        # If too many workers are unhealthy, trigger recreation
        healthy_count = sum(1 for w in self.workers if w.is_healthy)
        if healthy_count < self.pool_size // 2:
            logger.warning("Too many unhealthy workers, triggering pool refresh...")
            self.refresh_pool()
    
    def refresh_pool(self):
        """Refresh the worker pool by removing unhealthy workers and creating new ones."""
        if not self.enabled:
            return
        
        # Remove unhealthy workers from Cloudflare
        unhealthy_workers = [w for w in self.workers if not w.is_healthy]
        for worker in unhealthy_workers:
            try:
                self.manager.delete_worker(worker.name)
                logger.info(f"Deleted unhealthy worker: {worker.name}")
            except Exception as e:
                logger.error(f"Failed to delete worker {worker.name}: {e}")
        
        # Keep only healthy workers
        self.workers = [w for w in self.workers if w.is_healthy]
        
        # Create new workers
        self.initialize()
    
    def cleanup(self):
        """Delete all workers."""
        for worker in self.workers:
            try:
                self.manager.delete_worker(worker.name)
                logger.info(f"Deleted worker: {worker.name}")
            except Exception as e:
                logger.error(f"Failed to delete worker {worker.name}: {e}")
        
        self.workers = []
        self._save_workers()
    
    def get_stats(self) -> Dict:
        """Get pool statistics."""
        healthy_count = sum(1 for w in self.workers if w.is_healthy)
        total_success = sum(w.success_count for w in self.workers)
        total_failure = sum(w.failure_count for w in self.workers)
        
        return {
            "enabled": self.enabled,
            "total_workers": len(self.workers),
            "healthy_workers": healthy_count,
            "unhealthy_workers": len(self.workers) - healthy_count,
            "total_requests_success": total_success,
            "total_requests_failure": total_failure,
            "success_rate": total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0,
            "workers": [w.to_dict() for w in self.workers]
        }


# Global FlareProx pool instance
_flareprox_pool: Optional[FlareProxPool] = None


def init_flareprox():
    """Initialize the global FlareProx pool."""
    global _flareprox_pool
    
    # Check if FlareProx is enabled
    enabled = os.getenv("ENABLE_FLAREPROX", "false").lower() == "true"
    
    if not enabled:
        logger.info("FlareProx is disabled (ENABLE_FLAREPROX=false)")
        return
    
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    pool_size = int(os.getenv("FLAREPROX_POOL_SIZE", "3"))
    
    if not api_token or not account_id:
        logger.warning("FlareProx enabled but missing credentials (CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID)")
        return
    
    try:
        _flareprox_pool = FlareProxPool(api_token, account_id, pool_size)
        _flareprox_pool.initialize()
        logger.info("FlareProx initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize FlareProx: {e}")


def get_flareprox_pool() -> Optional[FlareProxPool]:
    """Get the global FlareProx pool."""
    return _flareprox_pool


def proxy_request_via_flareprox(target_url: str, method: str = "POST", 
                                 headers: Optional[Dict] = None, 
                                 data: Optional[bytes] = None,
                                 timeout: int = 30) -> requests.Response:
    """Proxy a request through FlareProx with automatic worker rotation."""
    pool = get_flareprox_pool()
    
    if not pool or not pool.enabled:
        # Fallback to direct request
        return requests.request(method, target_url, headers=headers, data=data, timeout=timeout)
    
    # Get next worker
    worker = pool.get_next_worker()
    
    if not worker:
        logger.warning("No healthy FlareProx workers available, using direct connection")
        return requests.request(method, target_url, headers=headers, data=data, timeout=timeout)
    
    # Build proxy URL
    proxy_url = f"{worker.url}?url={target_url}"
    
    try:
        # Make request through worker
        response = requests.request(method, proxy_url, headers=headers, data=data, timeout=timeout)
        
        # Mark success
        pool.mark_worker_success(worker)
        
        return response
        
    except Exception as e:
        logger.warning(f"FlareProx worker {worker.name} failed: {e}, falling back to direct connection")
        
        # Mark failure
        pool.mark_worker_failure(worker)
        
        # Fallback to direct request
        return requests.request(method, target_url, headers=headers, data=data, timeout=timeout)


def get_flareprox_worker_url(target_url: str) -> Optional[str]:
    """
    Get a FlareProx worker URL for the given target URL.
    Returns None if FlareProx is disabled or no workers available.
    This is meant to be used by async HTTP clients that will handle the request themselves.
    """
    pool = get_flareprox_pool()
    
    if not pool or not pool.enabled:
        return None
    
    worker = pool.get_next_worker()
    
    if not worker:
        logger.warning("No healthy FlareProx workers available")
        return None
    
    # Return the proxy URL with target URL as query parameter
    return f"{worker.url}?url={target_url}"


def mark_flareprox_request_result(target_url: str, success: bool):
    """
    Mark the result of a FlareProx request (success or failure).
    This helps track worker health.
    """
    pool = get_flareprox_pool()
    
    if not pool or not pool.enabled:
        return
    
    # Find the worker that was used (based on current index - 1)
    with pool.lock:
        index = (pool.current_index - 1) % len(pool.workers) if pool.workers else 0
        if 0 <= index < len(pool.workers):
            worker = pool.workers[index]
            if success:
                pool.mark_worker_success(worker)
            else:
                pool.mark_worker_failure(worker)
