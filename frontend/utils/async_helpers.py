"""
Async helpers for frontend performance optimization
"""
import asyncio
import aiohttp
import streamlit as st
from typing import Dict, List, Optional, Any
import time
from functools import lru_cache
import json

# Cache for API responses
API_CACHE = {}
CACHE_DURATION = 300  # 5 minutes

class AsyncAPIClient:
    """Async HTTP client for API calls with caching and retry logic"""
    
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_cache_key(self, method: str, url: str, data: Any = None) -> str:
        """Generate cache key for request"""
        cache_data = {
            'method': method,
            'url': url,
            'data': data,
            'token': self.token
        }
        return json.dumps(cache_data, sort_keys=True)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in API_CACHE:
            return False
        cache_time, _ = API_CACHE[cache_key]
        return time.time() - cache_time < CACHE_DURATION
    
    async def request(self, method: str, endpoint: str, data: Any = None, 
                     use_cache: bool = True, cache_duration: int = None) -> Dict:
        """Make async HTTP request with caching"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cache_key = self._get_cache_key(method, url, data)
        
        # Check cache for GET requests
        if use_cache and method.upper() == 'GET' and self._is_cache_valid(cache_key):
            _, cached_data = API_CACHE[cache_key]
            return cached_data
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url) as response:
                    result = await response.json()
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
            elif method.upper() == 'PUT':
                async with self.session.put(url, json=data) as response:
                    result = await response.json()
            elif method.upper() == 'DELETE':
                async with self.session.delete(url) as response:
                    result = await response.json()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Cache successful GET responses
            if use_cache and method.upper() == 'GET':
                API_CACHE[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            st.error(f"API request failed: {str(e)}")
            return None
    
    async def get(self, endpoint: str, use_cache: bool = True) -> Dict:
        """Async GET request"""
        return await self.request('GET', endpoint, use_cache=use_cache)
    
    async def post(self, endpoint: str, data: Any) -> Dict:
        """Async POST request"""
        return await self.request('POST', endpoint, data=data, use_cache=False)
    
    async def put(self, endpoint: str, data: Any) -> Dict:
        """Async PUT request"""
        return await self.request('PUT', endpoint, data=data, use_cache=False)
    
    async def delete(self, endpoint: str) -> Dict:
        """Async DELETE request"""
        return await self.request('DELETE', endpoint, use_cache=False)

def clear_cache():
    """Clear API cache"""
    global API_CACHE
    API_CACHE.clear()

def get_cached_data(key: str) -> Optional[Any]:
    """Get data from Streamlit session state cache"""
    if key in st.session_state:
        cache_time, data = st.session_state[key]
        if time.time() - cache_time < CACHE_DURATION:
            return data
        else:
            del st.session_state[key]
    return None

def set_cached_data(key: str, data: Any):
    """Set data in Streamlit session state cache"""
    st.session_state[key] = (time.time(), data)

async def fetch_data_concurrently(api_client: AsyncAPIClient, endpoints: List[str]) -> List[Dict]:
    """Fetch multiple endpoints concurrently"""
    tasks = [api_client.get(endpoint) for endpoint in endpoints]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results (failed requests)
    return [result for result in results if result is not None]

def run_async(coro):
    """Run async coroutine in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.operation_name = None
    
    def start(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = time.time()
    
    def end(self):
        if self.start_time:
            duration = time.time() - self.start_time
            st.sidebar.metric(f"{self.operation_name} Time", f"{duration:.2f}s")
            self.start_time = None
            self.operation_name = None

# Global performance monitor
perf_monitor = PerformanceMonitor() 