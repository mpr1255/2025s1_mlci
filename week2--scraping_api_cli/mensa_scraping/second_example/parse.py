#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4",
#     "typer",
#     "rich",
# ]
# ///

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
import re

import typer
from bs4 import BeautifulSoup
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


class MensaParser:
    def __init__(self, db_path: str = "mensa_data.db"):
        self.db_path = db_path
        self.data_dir = Path("data")
        self.setup_database()
    
    def setup_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create mensas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensas (
                id INTEGER PRIMARY KEY,
                city TEXT NOT NULL,
                university TEXT,
                mensa_name TEXT NOT NULL,
                scraped_date DATE NOT NULL,
                UNIQUE(city, university, mensa_name, scraped_date)
            )
        """)
        
        # Create menu_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY,
                mensa_id INTEGER NOT NULL,
                date DATE NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                price_students REAL,
                price_staff REAL,
                meal_id TEXT,
                source_html_file TEXT,
                FOREIGN KEY (mensa_id) REFERENCES mensas(id)
            )
        """)
        
        # Create index for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_menu_date ON menu_items(date)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")

    def get_or_create_mensa(self, conn: sqlite3.Connection, city: str, university: str, mensa_name: str, scraped_date: str) -> int:
        """Get existing mensa ID or create new mensa entry"""
        cursor = conn.cursor()
        
        # Try to find existing mensa
        cursor.execute("""
            SELECT id FROM mensas 
            WHERE city = ? AND university = ? AND mensa_name = ? AND scraped_date = ?
        """, (city, university, mensa_name, scraped_date))
        
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Create new mensa entry
        cursor.execute("""
            INSERT INTO mensas (city, university, mensa_name, scraped_date)
            VALUES (?, ?, ?, ?)
        """, (city, university, mensa_name, scraped_date))
        
        return cursor.lastrowid

    def parse_price(self, price_text: str) -> float | None:
        """Parse price string like '1,20 €' to float 1.20"""
        if not price_text:
            return None
        
        # Extract number from price string
        price_match = re.search(r'(\d+[,.]?\d*)', price_text.replace(',', '.'))
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                return None
        return None

    def parse_date(self, date_text: str, year: int | None = None) -> str | None:
        """Parse date string like '08.09.2025' or '08.09.' to YYYY-MM-DD format"""
        if not date_text:
            return None
        
        # Handle full date with year
        date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_text)
        if date_match:
            day, month, year = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Handle date without year (use provided year or current year)
        date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.', date_text)
        if date_match:
            day, month = date_match.groups()
            if not year:
                year = datetime.now().year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return None

    def parse_html_file(self, file_path: Path) -> dict:
        """Parse a single HTML file and extract menu data"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract mensa info from file path
        path_parts = file_path.parts
        city = path_parts[-4] if len(path_parts) >= 4 else ""
        university = path_parts[-3] if len(path_parts) >= 3 else ""
        mensa_name = path_parts[-2] if len(path_parts) >= 2 else ""
        scraped_date = file_path.stem  # YYYY-MM-DD from filename
        
        # Find the weekly menu table
        menu_table = soup.select_one('table.aw-weekly-menu')
        if not menu_table:
            logger.warning(f"No weekly menu table found in {file_path}")
            return {
                'city': city,
                'university': university,
                'mensa_name': mensa_name,
                'scraped_date': scraped_date,
                'menu_items': []
            }
        
        # Extract dates from table header
        date_headers = menu_table.select('thead th p')
        dates = []
        for header in date_headers:
            date_text = header.get_text(strip=True)
            parsed_date = self.parse_date(date_text)
            dates.append(parsed_date)
        
        logger.info(f"Found {len(dates)} dates: {dates}")
        
        # Extract menu items from table body
        menu_items = []
        tbody = menu_table.select_one('tbody')
        
        if tbody:
            current_category = ""
            
            for row in tbody.select('tr'):
                # Check if this row contains a category header
                category_header = row.select_one('th h3')
                if category_header:
                    current_category = category_header.get_text(strip=True)
                    logger.info(f"Found category: {current_category}")
                    continue
                
                # Parse meal data from row
                cells = row.select('td')
                logger.info(f"Processing row with {len(cells)} cells")
                
                for i, cell in enumerate(cells):
                    if i >= len(dates):  # Skip if we don't have a corresponding date
                        continue
                    
                    date = dates[i] if i < len(dates) else None
                    if not date:
                        continue
                    
                    # Extract meals from this cell
                    meals = cell.select('div.meal')
                    logger.info(f"Cell {i} (date {date}): found {len(meals)} meals")
                    
                    for meal in meals:
                        meal_id = meal.get('id', '').replace('m', '') if meal.get('id') else None
                        
                        # Extract meal name from description
                        description_elem = meal.select_one('.description p, .description')
                        meal_name = description_elem.get_text(strip=True) if description_elem else ""
                        
                        if not meal_name:
                            continue
                        
                        # Extract prices
                        price_students = None
                        price_staff = None
                        
                        price_spans = meal.select('span[title]')
                        for span in price_spans:
                            title = span.get('title', '').lower()
                            price_text = span.get_text(strip=True)
                            
                            if 'studierende' in title:
                                price_students = self.parse_price(price_text)
                            elif 'bedienstete' in title:
                                price_staff = self.parse_price(price_text)
                        
                        menu_items.append({
                            'date': date,
                            'category': current_category,
                            'item_name': meal_name,
                            'price_students': price_students,
                            'price_staff': price_staff,
                            'meal_id': meal_id,
                            'source_html_file': str(file_path)
                        })
                        
                        logger.info(f"Added meal: {meal_name} for {date} in category {current_category}")
        
        return {
            'city': city,
            'university': university,
            'mensa_name': mensa_name,
            'scraped_date': scraped_date,
            'menu_items': menu_items
        }

    def save_to_database(self, data: dict):
        """Save parsed data to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get or create mensa entry
            mensa_id = self.get_or_create_mensa(
                conn,
                data['city'],
                data['university'],
                data['mensa_name'],
                data['scraped_date']
            )
            
            cursor = conn.cursor()
            
            # Insert menu items
            for item in data['menu_items']:
                cursor.execute("""
                    INSERT OR REPLACE INTO menu_items 
                    (mensa_id, date, category, item_name, price_students, price_staff, meal_id, source_html_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mensa_id,
                    item['date'],
                    item['category'],
                    item['item_name'],
                    item['price_students'],
                    item['price_staff'],
                    item['meal_id'],
                    item['source_html_file']
                ))
            
            conn.commit()
            logger.info(f"Saved {len(data['menu_items'])} menu items for {data['mensa_name']}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving data to database: {e}")
            raise
        finally:
            conn.close()

    def parse_all_files(self):
        """Parse all HTML files in the data directory"""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return
        
        html_files = list(self.data_dir.rglob("*.html"))
        logger.info(f"Found {len(html_files)} HTML files to parse")
        
        parsed_count = 0
        error_count = 0
        
        for file_path in html_files:
            try:
                logger.info(f"Parsing: {file_path}")
                data = self.parse_html_file(file_path)
                self.save_to_database(data)
                parsed_count += 1
                
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
                error_count += 1
        
        console.print(f"[bold green]Parsing completed: {parsed_count} files processed, {error_count} errors[/bold green]")


@app.command()
def main(
    db_path: str = typer.Option(
        "mensa_data.db",
        "--db-path",
        help="Path to SQLite database file"
    )
):
    """Parse HTML files from data directory and save to SQLite database"""
    console.print("[bold blue]Starting mensa data parser[/bold blue]")
    
    parser = MensaParser(db_path=db_path)
    
    try:
        parser.parse_all_files()
        console.print(f"[bold green]Data saved to database: {db_path}[/bold green]")
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()