menu.db and test.py were just examples for trying to scrape the mensa menu and show some things in jq and curl. 

steps were:

go to the mensa page on the internet

https://www.stw-ma.de/en/food-drink/menus/mensa-am-schloss-en/

open netwrok requests

inspect them, figure out where the actual data for the menu plan is coming from

try a few things in curl, dump some stuff, see what's what. 

 curl 'https://api.stw-ma.de/tl1/menuplan' -s \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  --data-raw "id=bc003e93a1e942f45a99dcf8082da289&location=610&lang=en&date=2025-08-27&mode=day" \
  | jq -r .content \
  | pup 'table.speiseplan-table tr json{}'



and this is the one to insert htem into the table: 

uv run test.py 2025-08-26 | sqlite-utils insert menu.db menu - --csv --pk=date --pk=category



