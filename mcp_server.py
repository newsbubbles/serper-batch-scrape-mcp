import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP, Context
from client.serper_scraper import (GoogleSearchRequest, ScrapeRequest, BatchScrapeRequest, 
                                 ScrapeResult, SerperScraperClient)

# Create the FastMCP server
mcp = FastMCP("SerperScraperMCP")


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Initialize SerperScraperClient on server startup."""
    client = SerperScraperClient(serper_api_key=os.getenv("SERPER_API_KEY"))
    try:
        yield {"client": client}
    finally:
        # No cleanup needed for this client
        pass


# Set the lifespan manager
mcp.lifespan = server_lifespan


@mcp.tool()
async def google_search(request: GoogleSearchRequest, ctx: Context) -> Dict:
    """Perform a Google search using the Serper API.
    
    Args:
        request: The search parameters including query, region, language, etc.
        ctx: The MCP server context.
        
    Returns:
        Dictionary containing search results from Serper API.
    """
    client = ctx.request_context.lifespan_context["client"]
    try:
        return await client.google_search(request)
    except Exception as e:
        ctx.error(f"Error during Google search: {str(e)}")
        raise ValueError(f"Failed to perform Google search: {str(e)}")


@mcp.tool()
async def scrape(request: ScrapeRequest, ctx: Context) -> ScrapeResult:
    """Scrape a single URL and return structured data.
    
    Args:
        request: The scrape parameters including URL and markdown option.
        ctx: The MCP server context.
        
    Returns:
        Structured data extracted from the webpage including HTML, text, metadata, etc.
    """
    client = ctx.request_context.lifespan_context["client"]
    try:
        return await client.scrape(request)
    except Exception as e:
        ctx.error(f"Error during web scraping: {str(e)}")
        raise ValueError(f"Failed to scrape URL: {str(e)}")


@mcp.tool()
async def batch_scrape(request: BatchScrapeRequest, ctx: Context) -> List[ScrapeResult]:
    """Scrape multiple URLs in parallel and return a list of results.
    
    Args:
        request: The batch scrape parameters including list of URLs and markdown option.
        ctx: The MCP server context.
        
    Returns:
        List of structured data results extracted from each webpage.
    """
    client = ctx.request_context.lifespan_context["client"]
    try:
        total_urls = len(request.urls)
        ctx.info(f"Starting batch scrape of {total_urls} URLs")
        
        # Start the scraping operation
        results = await client.batch_scrape(request)
        
        # Count successful and failed results
        success_count = sum(1 for r in results if not r.error)
        error_count = sum(1 for r in results if r.error)
        
        ctx.info(f"Completed batch scrape: {success_count} successful, {error_count} failed")
        return results
    except Exception as e:
        ctx.error(f"Error during batch web scraping: {str(e)}")
        raise ValueError(f"Failed to execute batch scrape: {str(e)}")


def main():
    mcp.run()
    

if __name__ == "__main__":
    main()
