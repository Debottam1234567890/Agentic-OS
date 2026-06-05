import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
def fetch_category(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            root = ET.fromstring(response.read())
            items = root.findall('.//item')[:3]
            return [item.find('title').text for item in items]
    except Exception as e:
        return [f'Unavailable: {e}']
print('WORLD:')
print(fetch_category('https://news.google.com/rss/headlines/section/topic/WORLD'))
print('LOCAL:')
country = 'India'
print(fetch_category(f'https://news.google.com/rss/headlines/section/geo/{urllib.parse.quote(country)}'))
print('SPORTS:')
print(fetch_category('https://news.google.com/rss/headlines/section/topic/SPORTS'))
