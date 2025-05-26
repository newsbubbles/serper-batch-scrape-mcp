# Serper Scraper Batch MCP Server

This project enhances the serper-scraper MCP server with a batch scraping capability and optimized content extraction, allowing for simultaneous scraping of multiple URLs while focusing on user-visible content and important links.

## Features

- **Google Search**: Perform Google searches via the Serper API
- **Optimized Single URL Scraping**: Scrape content from a single URL with focus on visible content and links
- **Optimized Batch URL Scraping**: Scrape content from multiple URLs in parallel with content optimization

## Content Optimization

The scraper focuses on extracting only what's relevant to users:

- **User-Visible Content Only**: Filters out scripts, hidden elements, and invisible content
- **Link Extraction**: Identifies and extracts important links with their text
- **Content Structure Preservation**: Organizes content by headings, paragraphs, and lists
- **Duplicate Removal**: Eliminates redundant content
- **Metadata Extraction**: Gets meta description and other important meta tags

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
> I want to scrape these three URLs at the same time and only show me the important content and links: https://example.com, https://google.com, and https://github.com
```

#### Performing a Google Search

```
> Search Google for "python web scraping best practices"
```

#### Scraping a Single URL

```
> Scrape this website and give me the main content and important links: https://news.ycombinator.com
```

## API Details

### BatchScrapeRequest Model

- `urls` (List[str]): List of URLs to scrape in parallel
- `includeMarkdown` (Optional[bool]): Whether to include markdown content in the results

### ScrapeResult Model

- `url` (str): The URL that was scraped
- `timestamp` (str): When the scraping was performed
- `title` (Optional[str]): Title of the webpage, if available
- `main_content` (List[ScrapedContent]): The main visible content structured by type
- `links` (List[Link]): Important links extracted from the page
- `meta_description` (Optional[str]): Meta description of the page if available
- `meta_tags` (List[MetaTag]): Metadata tags extracted from the page
- `json_ld` (List[JSONLD]): JSON-LD structured data from the page
- `error` (Optional[str]): Error message if scraping failed

### ScrapedContent Model

- `type` (str): Type of content (heading, paragraph, list, etc.)
- `text` (str): The actual text content
- `level` (Optional[int]): For headings, the level (1-6)

### Link Model

- `text` (str): The visible text of the link
- `url` (str): The URL the link points to
- `is_external` (bool): Whether the link points to an external domain
