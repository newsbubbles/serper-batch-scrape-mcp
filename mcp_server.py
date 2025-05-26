import os
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Add the project root to the path so we can import the client module
# This ensures the imports work regardless of where the script is run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP, Context
from client.serper_scraper import (GoogleSearchRequest, ScrapeRequest, BatchScrapeRequest, 
                                 ScrapeResult, SerperScraperClient)


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Initialize SerperScraperClient on server startup."""
    api_key = os.getenv("SERPER_API_KEY")
    # if not api_key:
        # server.log.warning("SERPER_API_KEY environment variable not set. Google search functionality might not work correctly.")
    
    client = SerperScraperClient(serper_api_key=api_key)
    # server.log.info("SerperScraperClient initialized successfully")
    
    try:
        yield {"client": client}
    finally:
        # No cleanup needed for this client
        # server.log.info("Shutting down SerperScraperClient")
        pass


# Create the FastMCP server
mcp = FastMCP("SerperScraperMCP", lifespan=server_lifespan)


@mcp.tool()
async def google_search(request: GoogleSearchRequest, ctx: Context) -> Dict:
    """Perform a Google search using the Serper API.
    
    Args:
        request: The search parameters including query, region, language, etc.
        ctx: The MCP server context.
        
    Returns:
        Dictionary containing search results from Serper API.
    """
    if "client" not in ctx.request_context.lifespan_context:
        raise ValueError("SerperScraperClient not properly initialized")
        
    client = ctx.request_context.lifespan_context["client"]
    try:
        return await client.google_search(request)
    except Exception as e:
        ctx.error(f"Error during Google search: {str(e)}")
        raise ValueError(f"Failed to perform Google search: {str(e)}")


@mcp.tool()
async def scrape(request: ScrapeRequest, ctx: Context) -> ScrapeResult:
    """Scrape a single URL and return structured data focused on visible content.
    
    Args:
        request: The scrape parameters including URL and markdown option.
        ctx: The MCP server context.
        
    Returns:
        Structured data extracted from the webpage with focus on visible content and important links.
    """
    if "client" not in ctx.request_context.lifespan_context:
        raise ValueError("SerperScraperClient not properly initialized")
        
    client = ctx.request_context.lifespan_context["client"]
    try:
        await ctx.info(f"Scraping URL: {request.url}")
        return await client.scrape(request)
    except Exception as e:
        ctx.error(f"Error during web scraping: {str(e)}")
        raise ValueError(f"Failed to scrape URL: {str(e)}")


@mcp.tool()
async def batch_scrape(request: BatchScrapeRequest, ctx: Context) -> List[ScrapeResult]:
    """Scrape multiple URLs in parallel and return a list of results with focused content.
    
    Args:
        request: The batch scrape parameters including list of URLs and markdown option.
        ctx: The MCP server context.
        
    Returns:
        List of structured data results with visible content and links extracted from each webpage.
    """
    if "client" not in ctx.request_context.lifespan_context:
        raise ValueError("SerperScraperClient not properly initialized")
        
    client = ctx.request_context.lifespan_context["client"]
    try:
        total_urls = len(request.urls)
        await ctx.info(f"Starting batch scrape of {total_urls} URLs with optimized content extraction")
        
        # Start the scraping operation
        results = await client.batch_scrape(request)
        
        # Count successful and failed results
        success_count = sum(1 for r in results if not r.error)
        error_count = sum(1 for r in results if r.error)
        
        await ctx.info(f"Completed batch scrape: {success_count} successful, {error_count} failed")
        return results
    except Exception as e:
        ctx.error(f"Error during batch web scraping: {str(e)}")
        raise ValueError(f"Failed to execute batch scrape: {str(e)}")


def main():
    mcp.run()
    

if __name__ == "__main__":
    main()