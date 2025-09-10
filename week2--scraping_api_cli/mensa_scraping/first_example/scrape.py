#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "bs4",
#     "requests",
#     "typer",
# ]
# ///


import sys
import csv
import json
from datetime import date as _date
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
import typer


API_URL = "https://api.stw-ma.de/tl1/menuplan"


app = typer.Typer(no_args_is_help=True, add_completion=False, help="""
Fetch and print the Mensa menu for a given date.

Outputs CSV by default (compatible with piping to sqlite-utils with --csv),
or JSON when --json is provided.
""")


def fetch_menu_html(target_date: str) -> str:
    payload = {
        "id": "bc003e93a1e942f45a99dcf8082da289",
        "location": "610",
        "lang": "en",
        "date": target_date,
        "mode": "day",
    }
    response = requests.post(API_URL, data=payload)
    response.raise_for_status()
    return response.json()["content"]


def parse_menu(html_content: str, target_date: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html_content, "html.parser")
    menu_table = soup.find("table", class_="speiseplan-table")
    if not menu_table:
        return []

    rows: List[Dict[str, str]] = []
    for row in menu_table.find_all("tr"):
        title_tag = row.find("td", class_="speiseplan-table-menu-headline")
        desc_tag = row.find("td", class_="speiseplan-table-menu-content")
        price_tag = row.find("i", class_="price")

        title = (
            title_tag.strong.text.strip() if title_tag and title_tag.strong else "N/A"
        )
        desc = desc_tag.text.strip() if desc_tag else "N/A"
        price = price_tag.text.strip() if price_tag else "N/A"

        rows.append(
            {
                "date": target_date,
                "category": title,
                "description": desc,
                "price": price,
            }
        )
    return rows


def print_csv(rows: List[Dict[str, str]]) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["date", "category", "description", "price"])
    for r in rows:
        writer.writerow([r["date"], r["category"], r["description"], r["price"]])


def print_json(rows: List[Dict[str, str]]) -> None:
    # Print as a JSON array for compatibility with sqlite-utils insert
    json.dump(rows, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


@app.command()
def main(
    date: Optional[str] = typer.Argument(
        None,
        help="Date in YYYY-MM-DD. Defaults to today if omitted.",
    ),
    json_: bool = typer.Option(
        False,
        "--json",
        help="Output JSON array of rows.",
    ),
    csv_: bool = typer.Option(
        False,
        "--csv",
        help="Output CSV (default if a date is provided).",
    ),
):
    """Fetch and print the Mensa menu for a date."""
    # Determine the target date
    if date is None:
        # If user provided no args at all, Typer shows help due to no_args_is_help=True.
        # If we're here, user likely passed options only; default date to today.
        target_date = _date.today().isoformat()
    else:
        try:
            _date.fromisoformat(date)
        except ValueError:
            typer.echo(
                f"Error: Invalid date format '{date}'. Please use YYYY-MM-DD.",
                err=True,
            )
            raise typer.Exit(code=1)
        target_date = date

    # Resolve output format: default to CSV if none specified (for backward compatibility)
    if json_ and csv_:
        typer.echo("Error: --json and --csv are mutually exclusive.", err=True)
        raise typer.Exit(code=2)
    output_format = "json" if json_ else "csv"
    if not json_ and not csv_:
        output_format = "csv"

    try:
        html_content = fetch_menu_html(target_date)
        rows = parse_menu(html_content, target_date)
    except requests.exceptions.RequestException as e:
        typer.echo(f"Error fetching data for {target_date}: {e}", err=True)
        raise typer.Exit(code=1)
    except (KeyError, AttributeError) as e:
        typer.echo(f"Error parsing data for {target_date}: {e}", err=True)
        raise typer.Exit(code=1)

    # If no menu rows, exit quietly (useful for piping in scripts)
    if not rows:
        raise typer.Exit(code=0)

    if output_format == "json":
        print_json(rows)
    else:
        print_csv(rows)


if __name__ == "__main__":
    app()
