import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self, start_url, max_depth=2, concurrency=5, timeout=10, user_agent=None):
        self.start_url = start_url
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.timeout = timeout
        self.user_agent = user_agent or 'WebCrawlerErrorDetector/1.0'
        self.visited_urls = set()
        self.url_errors = {}
        self.session = None
        self.base_domain = urlparse(start_url).netloc

    async def create_session(self):
        headers = {
            'User-Agent': self.user_agent
        }
        return aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout))

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def crawl(self):
        self.session = await self.create_session()
        try:
            tasks = [self.process_url(self.start_url, 0)]
            await asyncio.gather(*tasks)
        finally:
            await self.close_session()
        return self.url_errors

    async def process_url(self, url, depth):
        if url in self.visited_urls or depth > self.max_depth:
            return
        
        self.visited_urls.add(url)
        logger.info(f"Crawling: {url} (Depth: {depth})")
        
        try:
            async with self.session.get(url) as response:
                # Check for HTTP errors
                if response.status >= 400:
                    self.url_errors[url] = {
                        'status_code': response.status,
                        'error_type': 'HTTP Error',
                        'message': f"HTTP {response.status}: {response.reason}"
                    }
                    return
                
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type.lower():
                    return
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check for HTML parsing errors
                if not soup.html:
                    self.url_errors[url] = {
                        'status_code': response.status,
                        'error_type': 'HTML Error',
                        'message': 'Invalid HTML structure'
                    }
                
                # Continue crawling if depth allows
                if depth < self.max_depth:
                    links = soup.find_all('a', href=True)
                    next_urls = []
                    
                    for link in links:
                        next_url = urljoin(url, link['href'])
                        parsed_url = urlparse(next_url)
                        
                        # Skip non-HTTP(S) URLs
                        if parsed_url.scheme not in ('http', 'https'):
                            continue
                        
                        # Only crawl URLs from the same domain
                        if parsed_url.netloc == self.base_domain:
                            next_urls.append(next_url)
                    
                    tasks = [self.process_url(next_url, depth + 1) for next_url in next_urls]
                    await asyncio.gather(*tasks)
        
        except aiohttp.ClientError as e:
            self.url_errors[url] = {
                'status_code': None,
                'error_type': 'Connection Error',
                'message': str(e)
            }
        except asyncio.TimeoutError:
            self.url_errors[url] = {
                'status_code': None,
                'error_type': 'Timeout',
                'message': f'Request timed out after {self.timeout} seconds'
            }
        except Exception as e:
            self.url_errors[url] = {
                'status_code': None,
                'error_type': 'Unknown Error',
                'message': str(e)
            }

async def run_crawler(start_url, max_depth=2, concurrency=5, timeout=10, user_agent=None):
    crawler = WebCrawler(
        start_url=start_url,
        max_depth=max_depth,
        concurrency=concurrency,
        timeout=timeout,
        user_agent=user_agent
    )
    
    return await crawler.crawl()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        start_url = sys.argv[1]
    else:
        start_url = "https://example.com"
    
    result = asyncio.run(run_crawler(start_url))
    
    if result:
        print("\nPages with errors:")
        for url, error in result.items():
            print(f"\n{url}")
            print(f"  Error Type: {error['error_type']}")
            print(f"  Status Code: {error['status_code']}")
            print(f"  Message: {error['message']}")
    else:
        print("No errors found!") 