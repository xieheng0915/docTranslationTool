from bs4 import BeautifulSoup as bs
import requests
import json
from utils import *

html_link = "https://solr.apache.org/guide/solr/latest/indexing-guide/indexing-with-update-handlers.html"



headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
page = requests.get(html_link, headers)
soup = bs(page.text, "html.parser")


# page title
page_data = {}
page_data['title'] = soup.title.string

# page preambl
preamble_data = []
preamble = soup.find('div', id='preamble').find('div', class_='sectionbody').find_all('div', recursive=False)
for p in preamble:
  preamble_data.append({'paragraph': p.text})
page_data['preamble'] = preamble_data


## sections
sect1_grp = soup.find_all('div', class_='sect1')
sect_data = []
for sect in sect1_grp:
  sectbody = sect.find('div', class_='sectionbody')
  #sect_data = build_sect1_data(sect_block, 'sect1')
  sect1_data_ = walkthrough_sects(sectbody,'sect1')
  sect_data.append({'sect1': sect1_data_})
page_data['content'] = sect_data



print(json.dumps(page_data, indent=4))
   



  