#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "crawlee[beautifulsoup]",
#     "typer",
#     "rich",
# ]
# ///

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import re

import typer
from bs4 import BeautifulSoup
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
from rich.console import Console
from rich.logging import RichHandler

console = Console()
app = typer.Typer()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
)
logger = logging.getLogger(__name__)


class MensaScraper:
    def __init__(self, overwrite: bool = False):
        self.overwrite = overwrite
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.base_url = "https://www.mensaplan.de"
        self.data_dir = Path("data")
        self.scraped_urls = set()
        
    def get_file_path(self, city: str, university: str, mensa: str) -> Path:
        """Generate file path for storing HTML content"""
        # If no university, use city as the middle directory
        uni_dir = university if university else city
        return self.data_dir / city / uni_dir / mensa / f"{self.today}.html"
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped based on overwrite flag"""
        if not self.overwrite and file_path.exists():
            logger.info(f"Skipping {file_path} (already exists)")
            return True
        return False
    
    def save_html(self, file_path: Path, content: str):
        """Save HTML content to file"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved: {file_path}")

    async def scrape_cities(self, limit: int | None = None):
        """Main scraping function"""
        crawler = BeautifulSoupCrawler(
            max_requests_per_crawl=limit if limit else None
        )
        
        @crawler.router.default_handler
        async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
            url = context.request.url
            logger.info(f"Processing: {url}")
            
            if url in self.scraped_urls:
                return
            self.scraped_urls.add(url)
            
            soup = context.soup
            
            # Handle landing page - extract cities
            if "index.html" in url and "mensaplan.de/index.html" in url:
                await self.handle_landing_page(context, soup)
            
            # Handle all other pages - check for mensa content or extract links
            else:
                await self.handle_city_or_mensa_page(context, soup, url)
    
        # Start with the landing page
        await crawler.run(["https://www.mensaplan.de/index.html"])

    def get_city_names_from_url(self, url: str) -> list[str]:
        """Extract possible city names from URL for identification"""
        # This is a simple heuristic - in practice you might need more sophisticated parsing
        path_parts = urlparse(url).path.split('/')
        return [part for part in path_parts if part and not part.endswith('.html')]

    async def handle_landing_page(self, context: BeautifulSoupCrawlingContext, soup: BeautifulSoup):
        """Process the landing page to find all city links"""
        # Find all city groups (li elements containing letter groups)
        city_groups = soup.select('ul li')
        
        for group in city_groups:
            # Find all city links within each group
            city_links = group.select('a[href]')
            
            for link in city_links:
                href = link.get('href')
                if href and not href.startswith('http'):
                    full_url = urljoin(self.base_url, href)
                    await context.add_requests([full_url])

    async def handle_city_or_mensa_page(self, context: BeautifulSoupCrawlingContext, soup: BeautifulSoup, url: str):
        """Handle city pages that might contain universities or direct mensa links"""
        
        # Check if this is a direct mensa page (has the weekly menu table)
        weekly_menu = soup.select('table.aw-weekly-menu')
        if weekly_menu:
            logger.info(f"Found mensa page with weekly menu: {url}")
            await self.save_mensa_page(soup, url)
            return  # Don't process links on mensa pages to avoid infinite loops
        
        # If not a mensa page, look for links to follow
        logger.info(f"Checking page for links: {url}")
        
        # Look for university sections (h2 tags) with mensa links
        h2_sections = soup.select('h2')
        new_urls = []
        
        if h2_sections:
            for h2 in h2_sections:
                university = h2.get_text(strip=True)
                logger.info(f"Found university section: {university}")
                
                # Find mensa links following this h2
                next_element = h2.find_next_sibling()
                while next_element and next_element.name != 'h2':
                    mensa_links = next_element.select('a[href*="mensa-"]') if next_element else []
                    
                    for link in mensa_links:
                        href = link.get('href')
                        if href:
                            mensa_url = urljoin(self.base_url, href)
                            new_urls.append(mensa_url)
                            logger.info(f"Found mensa link in university section: {mensa_url}")
                    
                    next_element = next_element.find_next_sibling()
        
        # Also look for any direct mensa links on the page
        mensa_links = soup.select('a[href*="mensa-"]')
        for link in mensa_links:
            href = link.get('href')
            if href:
                mensa_url = urljoin(self.base_url, href)
                new_urls.append(mensa_url)
                logger.info(f"Found direct mensa link: {mensa_url}")
        
        # Also look for general links to other city pages
        city_links = soup.select('a[href*="/index.html"], a[href$="/"]')
        for link in city_links:
            href = link.get('href')
            if href and 'mensaplan.de' in urljoin(self.base_url, href):
                city_url = urljoin(self.base_url, href)
                new_urls.append(city_url)
                logger.info(f"Found city link: {city_url}")
        
        # Add all found URLs to the queue
        if new_urls:
            logger.info(f"Adding {len(new_urls)} new URLs to queue")
            await context.add_requests(new_urls)

    async def save_mensa_page(self, soup: BeautifulSoup, url: str):
        """Save a mensa page if it contains menu data"""
        # Extract city, university, and mensa name from URL and page content
        city, university, mensa = self.parse_mensa_info(soup, url)
        
        logger.info(f"Parsed mensa info - City: {city}, University: {university}, Mensa: {mensa}")
        
        if city and mensa:
            file_path = self.get_file_path(city, university or city, mensa)
            
            if not self.should_skip_file(file_path):
                self.save_html(file_path, str(soup))
        else:
            logger.warning(f"Could not extract mensa info from {url} - City: {city}, Mensa: {mensa}")

    def parse_mensa_info(self, soup: BeautifulSoup, url: str) -> tuple[str, str, str]:
        """Parse city, university, and mensa information from page"""
        # Extract from URL path
        url_parts = [part for part in urlparse(url).path.split('/') if part]
        logger.info(f"URL parts: {url_parts}")
        
        # Default values
        city = ""
        university = ""
        mensa_name = ""
        
        # Extract city and mensa from URL structure
        if len(url_parts) >= 1:
            city = url_parts[0].replace('-', ' ').title()
            
            # Determine structure based on URL path
            if len(url_parts) == 3 and url_parts[1].startswith('mensa-') and url_parts[2] == 'index.html':
                # Direct city/mensa structure (e.g., amberg/mensa-amberg/index.html)
                # In this case, there's no separate university - the city IS the location
                mensa_name = url_parts[1].replace('mensa-', '').replace('-', ' ').title()
                university = ""  # No university, just city
            elif len(url_parts) >= 3 and not url_parts[1].startswith('mensa-'):
                # city/university/mensa or city/university/index.html structure
                university = url_parts[1].replace('-', ' ').title()
                if len(url_parts) >= 4 and url_parts[2].startswith('mensa-'):
                    # city/university/mensa/index.html
                    mensa_name = url_parts[2].replace('mensa-', '').replace('-', ' ').title()
                elif url_parts[2] != 'index.html':
                    # city/university/mensa_name/index.html (mensa name is not prefixed)
                    mensa_name = url_parts[2].replace('-', ' ').title()
                else:
                    # city/university/index.html - use university as mensa name
                    mensa_name = university
        
        # Try to get better names from page content
        title = soup.select_one('title')
        h1 = soup.select_one('h1')
        
        if title:
            title_text = title.get_text(strip=True)
            if title_text and not mensa_name:
                mensa_name = title_text
        
        if h1:
            h1_text = h1.get_text(strip=True)
            if h1_text and not mensa_name:
                mensa_name = h1_text
        
        # Fallback: use URL parts if we still don't have a mensa name
        if not mensa_name:
            for part in url_parts:
                if part.startswith('mensa-'):
                    mensa_name = part.replace('mensa-', '').replace('-', ' ').title()
                    break
        
        # If still no mensa name, use the last meaningful URL part
        if not mensa_name and url_parts:
            mensa_name = url_parts[-1].replace('-', ' ').title() if url_parts[-1] != 'index.html' else url_parts[-2].replace('-', ' ').title()
        
        return city, university, mensa_name


@app.command()
def main(
    overwrite: bool = typer.Option(
        False, 
        "--overwrite", 
        help="Overwrite existing files for today's date"
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Limit the number of requests to process (useful for testing)"
    )
):
    """Scrape mensaplan.de and save HTML files to data directory"""
    console.print(f"[bold blue]Starting mensa scraper for {datetime.now().strftime('%Y-%m-%d')}[/bold blue]")
    
    if overwrite:
        console.print("[yellow]Overwrite mode enabled - will replace existing files[/yellow]")
    
    if limit:
        console.print(f"[yellow]Request limit set to {limit}[/yellow]")
    
    scraper = MensaScraper(overwrite=overwrite)
    
    try:
        asyncio.run(scraper.scrape_cities(limit=limit))
        console.print("[bold green]Scraping completed successfully![/bold green]")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()