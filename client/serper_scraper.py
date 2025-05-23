import asyncio
import json
from typing import Dict, List, Optional, Union, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import re
import concurrent.futures


class GoogleSearchRequest(BaseModel):
    q: str = Field(..., description="Search query string")
    gl: str = Field(..., description="Region code for search results in ISO 3166-1 alpha-2 format (e.g., 'us')")
    hl: str = Field(..., description="Language code for search results in ISO 639-1 format (e.g., 'en')")
    num: Optional[int] = Field(None, description="Number of results to return (default: 10)")
    page: Optional[int] = Field(None, description="Page number of results to return (default: 1)")
    tbs: Optional[str] = Field(None, description="Time-based search filter ('qdr:h' for past hour, 'qdr:d' for past day, 'qdr:w' for past week, 'qdr:m' for past month, 'qdr:y' for past year)")
    location: Optional[str] = Field(None, description="Optional location for search results (e.g., 'SoHo, New York, United States', 'California, United States')")
    autocorrect: Optional[bool] = Field(None, description="Whether to autocorrect spelling in query")


class ScrapeRequest(BaseModel):
    url: str = Field(..., description="The URL of the webpage to scrape.")
    includeMarkdown: Optional[bool] = Field(None, description="Whether to include markdown content.")


class BatchScrapeRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to scrape in parallel.")
    includeMarkdown: Optional[bool] = Field(None, description="Whether to include markdown content.")


class MetaTag(BaseModel):
    name: Optional[str] = None
    property: Optional[str] = None
    content: Optional[str] = None


class JSONLD(BaseModel):
    raw: str
    parsed: Any


class ScrapeResult(BaseModel):
    url: str
    timestamp: str
    title: Optional[str] = None
    html: str
    markdown: Optional[str] = None
    text: Optional[str] = None
    meta_tags: List[MetaTag]
    json_ld: List[JSONLD]
    error: Optional[str] = None


class SerperScraperClient:
    def __init__(self, serper_api_key: Optional[str] = None):
        self.serper_api_key = serper_api_key
        self.serper_api_url = "https://google.serper.dev/search"
        self.headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        } if serper_api_key else {"Content-Type": "application/json"}

    async def google_search(self, request: GoogleSearchRequest) -> Dict:
        """Perform a Google search using the Serper API."""
        if not self.serper_api_key:
            raise ValueError("Serper API key is required for search operations")

        payload = request.model_dump(exclude_none=True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.serper_api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def _extract_meta_tags(self, soup: BeautifulSoup) -> List[MetaTag]:
        """Extract meta tags from the HTML soup."""
        meta_tags = []
        for tag in soup.find_all("meta"):
            meta_tag = {}
            if tag.get("name"):
                meta_tag["name"] = tag.get("name")
            if tag.get("property"):
                meta_tag["property"] = tag.get("property")
            if tag.get("content"):
                meta_tag["content"] = tag.get("content")
            
            if meta_tag:  # Only add if we found at least one attribute
                meta_tags.append(MetaTag(**meta_tag))
        return meta_tags

    async def _extract_json_ld(self, html: str) -> List[JSONLD]:
        """Extract JSON-LD metadata from the HTML."""
        json_ld_list = []
        pattern = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.DOTALL)
        for match in pattern.finditer(html):
            json_str = match.group(1).strip()
            try:
                parsed = json.loads(json_str)
                json_ld_list.append(JSONLD(raw=json_str, parsed=parsed))
            except json.JSONDecodeError:
                # Skip invalid JSON
                pass
        return json_ld_list

    async def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to markdown format."""
        # This is a simple implementation, consider using a dedicated library like html2markdown
        # for a more comprehensive conversion
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text(separator='\n', strip=True)

        # Basic markdown formatting
        # Headers
        for i in range(6, 0, -1):
            for header in soup.find_all(f'h{i}'):
                head_text = header.get_text(strip=True)
                text = text.replace(head_text, f"{'#' * i} {head_text}\n")

        # Bold text
        for bold in soup.find_all(['strong', 'b']):
            bold_text = bold.get_text(strip=True)
            if bold_text:
                text = text.replace(bold_text, f"**{bold_text}**")

        # Italic text
        for italic in soup.find_all(['em', 'i']):
            italic_text = italic.get_text(strip=True)
            if italic_text:
                text = text.replace(italic_text, f"*{italic_text}*")

        # Lists
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                li_text = li.get_text(strip=True)
                if li_text:
                    text = text.replace(li_text, f"* {li_text}")

        # Ordered lists
        counter = 1
        for ol in soup.find_all('ol'):
            for li in ol.find_all('li'):
                li_text = li.get_text(strip=True)
                if li_text:
                    text = text.replace(li_text, f"{counter}. {li_text}")
                    counter += 1

        # Links
        for a in soup.find_all('a', href=True):
            link_text = a.get_text(strip=True)
            if link_text:
                text = text.replace(link_text, f"[{link_text}]({a['href']})")

        return text

    async def _scrape_single_url(self, url: str, include_markdown: bool = False) -> ScrapeResult:
        """Scrape a single URL and return structured data."""
        timestamp = datetime.utcnow().isoformat()
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else None
            meta_tags = await self._extract_meta_tags(soup)
            json_ld = await self._extract_json_ld(html_content)
            text = soup.get_text(separator='\n', strip=True)

            # Generate markdown if requested
            markdown = await self._html_to_markdown(html_content) if include_markdown else None

            return ScrapeResult(
                url=url,
                timestamp=timestamp,
                title=title,
                html=html_content,
                text=text,
                markdown=markdown,
                meta_tags=meta_tags,
                json_ld=json_ld
            )
        except Exception as e:
            return ScrapeResult(
                url=url,
                timestamp=timestamp,
                html="",
                meta_tags=[],
                json_ld=[],
                error=str(e)
            )

    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape a single URL and return structured data."""
        return await self._scrape_single_url(request.url, request.includeMarkdown or False)

    async def batch_scrape(self, request: BatchScrapeRequest) -> List[ScrapeResult]:
        """Scrape multiple URLs in parallel and return a list of results."""
        tasks = []
        for url in request.urls:
            tasks.append(self._scrape_single_url(url, request.includeMarkdown or False))
            
        return await asyncio.gather(*tasks)
