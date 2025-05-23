# Serper Scraper Batch MCP Server

This project enhances the serper-scraper MCP server with a batch scraping capability, allowing for simultaneous scraping of multiple URLs.

## Features

- **Google Search**: Perform Google searches via the Serper API
- **Single URL Scraping**: Scrape content from a single URL
- **Batch URL Scraping**: Scrape content from multiple URLs in parallel

## Project Structure

- `client/serper_scraper.py` - Core client implementation with both single and batch scraping functionality
- `mcp_server.py` - MCP server that wraps the client and exposes its functionality
- `agent.py` - Test agent for interacting with the MCP server
- `agents/SerperScraperAgent.md` - System prompt for the test agent

## Requirements

- Python 3.8+
- httpx
- BeautifulSoup4
- Pydantic
- MCP SDK (FastMCP)
- PydanticAI (for the test agent)

## Environment Variables

- `SERPER_API_KEY` - API key for the Serper service (required for Google search functionality)
- `OPENROUTER_API_KEY` - API key for OpenRouter (optional, for the test agent)

## Usage

### Running the Agent

```bash
python agent.py
```

### Using the MCP Server Directly

```bash
python mcp_server.py
```

### Examples

#### Batch Scraping Multiple URLs

```
> I want to scrape these three URLs at the same time: https://example.com, https://google.com, and https://github.com
```

#### Performing a Google Search

```
> Search Google for "python web scraping best practices"
```

#### Scraping a Single URL

```
> Scrape this website and give me a summary: https://news.ycombinator.com
```

## API Details

### BatchScrapeRequest Model

- `urls` (List[str]): List of URLs to scrape in parallel
- `includeMarkdown` (Optional[bool]): Whether to include markdown content in the results

### ScrapeResult Model

- `url` (str): The URL that was scraped
- `timestamp` (str): When the scraping was performed
- `title` (Optional[str]): Title of the webpage, if available
- `html` (str): Raw HTML content
- `markdown` (Optional[str]): Markdown representation of the content (if requested)
- `text` (Optional[str]): Plain text content
- `meta_tags` (List[MetaTag]): Metadata tags extracted from the page
- `json_ld` (List[JSONLD]): JSON-LD structured data from the page
- `error` (Optional[str]): Error message if scraping failed
