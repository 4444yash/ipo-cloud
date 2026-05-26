
from bs4 import BeautifulSoup
import sys

# Set stdout to utf-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('page_source.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

table = soup.find('table', id='reportTable')
if not table:
    print("Table not found!")
    sys.exit(1)

rows = table.find_all('tr')
for i, r in enumerate(rows[1:5]):
    cells = [td.text.strip().replace('\n', ' ') for td in r.find_all('td')]
    print(f"Row {i}: {cells}")
