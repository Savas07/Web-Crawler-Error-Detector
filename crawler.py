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
        self.successful_urls = {}  # Track successfully crawled pages
        self.session = None
        self.base_domain = urlparse(start_url).netloc
        self.stats = {
            "total_crawled": 0,
            "successful": 0,
            "errors": 0,
            "by_error_type": {}
        }

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
        
        # Compile final statistics
        self.stats["total_crawled"] = len(self.visited_urls)
        self.stats["successful"] = len(self.successful_urls)
        self.stats["errors"] = len(self.url_errors)
        
        # Count errors by type
        error_types = {}
        for url, error in self.url_errors.items():
            error_type = error['error_type']
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        self.stats["by_error_type"] = error_types
        
        return {
            "stats": self.stats,
            "errors": self.url_errors,
            "successful": self.successful_urls
        }

    async def process_url(self, url, depth, referring_page=None):
        if url in self.visited_urls or depth > self.max_depth:
            return
        
        self.visited_urls.add(url)
        logger.info(f"Crawling: {url} (Depth: {depth})")
        
        try:
            async with self.session.get(url) as response:
                # Check for HTTP errors
                if response.status >= 400:
                    error_content = None
                    try:
                        # Attempt to get error page content
                        error_content = await response.text()
                        # Extract useful parts from the error page
                        soup = BeautifulSoup(error_content, 'html.parser')
                        # Try to find error details in common error page elements
                        error_details = None
                        error_elements = soup.select('div.error, .error-message, #error, .exception, .message')
                        if error_elements:
                            error_details = error_elements[0].get_text(strip=True)
                        
                        # If we couldn't find specific error elements, look for title or h1
                        if not error_details:
                            if soup.title:
                                error_details = soup.title.get_text(strip=True)
                            elif soup.h1:
                                error_details = soup.h1.get_text(strip=True)
                    except Exception as e:
                        error_details = f"Could not parse error page: {str(e)}"

                    self.url_errors[url] = {
                        'status_code': response.status,
                        'error_type': 'HTTP Error',
                        'message': f"HTTP {response.status}: {response.reason}",
                        'details': error_details if error_details else "No additional details available",
                        'headers': dict(response.headers),
                        'referring_page': referring_page
                    }
                    return
                
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type.lower():
                    # Track as successful, but no further crawling for non-HTML content
                    self.successful_urls[url] = {
                        'status_code': response.status,
                        'content_type': content_type,
                        'depth': depth,
                        'referring_page': referring_page
                    }
                    return
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check for HTML parsing errors
                if not soup.html:
                    self.url_errors[url] = {
                        'status_code': response.status,
                        'error_type': 'HTML Error',
                        'message': 'Invalid HTML structure',
                        'details': 'The page does not have a valid HTML structure',
                        'headers': dict(response.headers),
                        'referring_page': referring_page
                    }
                    return

                # Check for other common page issues
                if soup.find('body') and len(soup.find('body').get_text(strip=True)) < 50:
                    # Suspiciously little content
                    self.url_errors[url] = {
                        'status_code': response.status,
                        'error_type': 'Content Warning',
                        'message': 'Page has minimal content',
                        'details': f"Content length: {len(soup.find('body').get_text(strip=True))} characters",
                        'headers': dict(response.headers),
                        'referring_page': referring_page
                    }
                    return
                
                # If we got here, the page was successfully crawled
                self.successful_urls[url] = {
                    'status_code': response.status,
                    'content_type': content_type,
                    'title': soup.title.get_text() if soup.title else 'No title',
                    'depth': depth,
                    'links_count': len(soup.find_all('a', href=True)),
                    'referring_page': referring_page
                }
                
                # Continue crawling if depth allows
                if depth < self.max_depth:
                    links = soup.find_all('a', href=True)
                    next_urls = []
                    
                    # Check for broken internal links
                    for link in links:
                        next_url = urljoin(url, link['href'])
                        parsed_url = urlparse(next_url)
                        
                        # Skip non-HTTP(S) URLs
                        if parsed_url.scheme not in ('http', 'https'):
                            continue
                        
                        # Only crawl URLs from the same domain
                        if parsed_url.netloc == self.base_domain:
                            next_urls.append(next_url)
                    
                    tasks = [self.process_url(next_url, depth + 1, url) for next_url in next_urls]
                    await asyncio.gather(*tasks)
        
        except aiohttp.ClientError as e:
            self.url_errors[url] = {
                'status_code': None,
                'error_type': 'Connection Error',
                'message': str(e),
                'details': f"Client error when connecting to {url}",
                'referring_page': referring_page
            }
        except asyncio.TimeoutError:
            self.url_errors[url] = {
                'status_code': None,
                'error_type': 'Timeout',
                'message': f'Request timed out after {self.timeout} seconds',
                'details': 'The server took too long to respond',
                'referring_page': referring_page
            }
        except Exception as e:
            self.url_errors[url] = {
                'status_code': None,
                'error_type': 'Unknown Error',
                'message': str(e),
                'details': f"Exception type: {type(e).__name__}",
                'referring_page': referring_page
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
    
    # Print statistics
    print("\nCrawl Statistics:")
    print(f"Total Pages Crawled: {result['stats']['total_crawled']}")
    print(f"Successfully Crawled: {result['stats']['successful']}")
    print(f"Pages with Errors: {result['stats']['errors']}")
    
    if result['stats']['by_error_type']:
        print("\nErrors by Type:")
        for error_type, count in result['stats']['by_error_type'].items():
            print(f"  {error_type}: {count}")
    
    # Print errors
    if result['errors']:
        print("\nPages with errors:")
        for url, error in result['errors'].items():
            print(f"\n{url}")
            print(f"  Error Type: {error['error_type']}")
            print(f"  Status Code: {error['status_code']}")
            print(f"  Message: {error['message']}")
            if 'details' in error:
                print(f"  Details: {error['details']}")
    else:
        print("\nNo errors found!") 