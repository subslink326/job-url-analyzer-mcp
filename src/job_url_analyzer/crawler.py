"""Web crawler for fetching job posting and company pages."""

import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from aiohttp_robotparser import AsyncRobotFileParser
from opentelemetry import trace

from .config import get_settings
from .database import AsyncSession, CrawlLogDB
from .metrics import (
    CRAWL_REQUEST_COUNT,
    CRAWL_DURATION,
    ROBOTS_TXT_BLOCKS,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class WebCrawler:
    """Async web crawler with robots.txt respect and rate limiting."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.robots_cache: Dict[str, AsyncRobotFileParser] = {}
        self.last_request_times: Dict[str, float] = {}
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        
        # Configure HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.REQUEST_TIMEOUT),
            headers={
                "User-Agent": "JobAnalyzer/1.0 (+https://yourcompany.com/bot)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
            },
            follow_redirects=True,
            max_redirects=5,
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc.lower()
    
    async def _get_robots_parser(self, url: str) -> Optional[AsyncRobotFileParser]:
        """Get robots.txt parser for domain."""
        if not settings.RESPECT_ROBOTS_TXT:
            return None
        
        domain = self._get_domain(url)
        
        if domain not in self.robots_cache:
            try:
                base_url = f"{urlparse(url).scheme}://{domain}"
                robots_url = urljoin(base_url, "/robots.txt")
                
                logger.debug("Fetching robots.txt", url=robots_url)
                
                parser = AsyncRobotFileParser()
                await parser.read(robots_url)
                self.robots_cache[domain] = parser
                
                logger.info("Loaded robots.txt", domain=domain)
                
            except Exception as e:
                logger.warning("Failed to load robots.txt", domain=domain, error=str(e))
                # Create permissive parser as fallback
                parser = AsyncRobotFileParser()
                parser.disallow_all = False
                self.robots_cache[domain] = parser
        
        return self.robots_cache[domain]
    
    async def _is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        robots_parser = await self._get_robots_parser(url)
        
        if robots_parser is None:
            return True
        
        user_agent = "JobAnalyzer"
        allowed = robots_parser.can_fetch(user_agent, url)
        
        if not allowed:
            logger.info("URL blocked by robots.txt", url=url)
            ROBOTS_TXT_BLOCKS.inc()
        
        return allowed
    
    async def _respect_crawl_delay(self, url: str) -> None:
        """Respect crawl delay for domain."""
        domain = self._get_domain(url)
        now = time.time()
        
        if domain in self.last_request_times:
            elapsed = now - self.last_request_times[domain]
            if elapsed < settings.CRAWL_DELAY:
                delay = settings.CRAWL_DELAY - elapsed
                logger.debug("Applying crawl delay", domain=domain, delay=delay)
                await asyncio.sleep(delay)
        
        self.last_request_times[domain] = time.time()
    
    def _should_follow_link(self, url: str, base_url: str) -> bool:
        """Determine if a link should be followed for additional content."""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)
        
        # Only follow links on the same domain
        if parsed_url.netloc != parsed_base.netloc:
            return False
        
        # Avoid common non-content paths
        avoid_patterns = [
            "/api/", "/ajax/", "/static/", "/assets/",
            "/css/", "/js/", "/images/", "/img/",
            "/admin/", "/dashboard/", "/login/",
            ".json", ".xml", ".pdf", ".doc",
        ]
        
        path = parsed_url.path.lower()
        return not any(pattern in path for pattern in avoid_patterns)
    
    async def _log_crawl_result(
        self,
        profile_id: str,
        url: str,
        response: Optional[httpx.Response] = None,
        error: Optional[Exception] = None,
        robots_allowed: bool = True,
        response_time_ms: Optional[int] = None,
    ) -> None:
        """Log crawl result to database."""
        try:
            crawl_log = CrawlLogDB(
                profile_id=profile_id,
                url=url,
                status_code=response.status_code if response else None,
                success=response is not None and response.is_success,
                error_message=str(error) if error else None,
                response_time_ms=response_time_ms,
                content_length=len(response.content) if response else None,
                robots_txt_allowed=robots_allowed,
            )
            
            self.db_session.add(crawl_log)
            await self.db_session.flush()
            
        except Exception as log_error:
            logger.error("Failed to log crawl result", error=str(log_error))
    
    async def fetch_page(self, url: str, profile_id: str) -> Optional[str]:
        """Fetch a single page with full error handling and logging."""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("fetch_page") as span:
            span.set_attribute("url", url)
            span.set_attribute("profile_id", profile_id)
            
            start_time = time.time()
            
            async with self._semaphore:
                try:
                    # Check robots.txt
                    robots_allowed = await self._is_allowed_by_robots(url)
                    if not robots_allowed:
                        await self._log_crawl_result(
                            profile_id=profile_id,
                            url=url,
                            robots_allowed=False,
                        )
                        return None
                    
                    # Respect crawl delay
                    await self._respect_crawl_delay(url)
                    
                    # Make request
                    logger.debug("Fetching page", url=url)
                    
                    response = await self.client.get(url)
                    response_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Record metrics
                    CRAWL_REQUEST_COUNT.labels(status_code=str(response.status_code)).inc()
                    CRAWL_DURATION.observe(time.time() - start_time)
                    
                    # Log result
                    await self._log_crawl_result(
                        profile_id=profile_id,
                        url=url,
                        response=response,
                        response_time_ms=response_time_ms,
                    )
                    
                    if response.is_success:
                        span.set_attribute("success", True)
                        span.set_attribute("status_code", response.status_code)
                        span.set_attribute("content_length", len(response.content))
                        
                        logger.info(
                            "Successfully fetched page",
                            url=url,
                            status_code=response.status_code,
                            content_length=len(response.content),
                            response_time_ms=response_time_ms,
                        )
                        
                        return response.text
                    else:
                        response.raise_for_status()
                
                except Exception as e:
                    response_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Log error
                    await self._log_crawl_result(
                        profile_id=profile_id,
                        url=url,
                        error=e,
                        response_time_ms=response_time_ms,
                    )
                    
                    span.set_attribute("success", False)
                    span.set_attribute("error", str(e))
                    
                    logger.error(
                        "Failed to fetch page",
                        url=url,
                        error=str(e),
                        response_time_ms=response_time_ms,
                    )
                    
                    return None
    
    async def crawl_site(
        self,
        start_url: str,
        profile_id: str,
        max_pages: int = 5,
    ) -> List[str]:
        """Crawl multiple pages from a site."""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("crawl_site") as span:
            span.set_attribute("start_url", start_url)
            span.set_attribute("max_pages", max_pages)
            
            pages_content = []
            crawled_urls: Set[str] = set()
            
            # Start with the main page
            main_content = await self.fetch_page(start_url, profile_id)
            if main_content:
                pages_content.append(main_content)
                crawled_urls.add(start_url)
            
            # Extract additional URLs to crawl (if needed)
            if len(pages_content) < max_pages and main_content:
                additional_urls = self._extract_additional_urls(main_content, start_url)
                
                for url in additional_urls:
                    if len(pages_content) >= max_pages:
                        break
                    
                    if url not in crawled_urls:
                        content = await self.fetch_page(url, profile_id)
                        if content:
                            pages_content.append(content)
                            crawled_urls.add(url)
            
            span.set_attribute("pages_crawled", len(pages_content))
            
            logger.info(
                "Site crawl completed",
                start_url=start_url,
                pages_crawled=len(pages_content),
                total_urls=len(crawled_urls),
            )
            
            return pages_content
    
    def _extract_additional_urls(self, html_content: str, base_url: str) -> List[str]:
        """Extract additional URLs to crawl from HTML content."""
        from selectolax.parser import HTMLParser
        
        parser = HTMLParser(html_content)
        urls = []
        
        # Look for company/about pages
        for link in parser.css("a[href]"):
            href = link.attributes.get("href", "")
            if not href:
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Check if this is a useful link to follow
            if self._should_follow_link(full_url, base_url):
                # Look for about/company related pages
                link_text = (link.text() or "").lower()
                href_lower = href.lower()
                
                if any(keyword in link_text or keyword in href_lower for keyword in [
                    "about", "company", "team", "culture", "careers",
                    "jobs", "mission", "values", "story"
                ]):
                    urls.append(full_url)
        
        # Limit to avoid too many requests
        return urls[:3]