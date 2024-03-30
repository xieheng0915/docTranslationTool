import openai
from dotenv import load_dotenv
import os
from utils import *
import json
from mdutils.mdutils import MdUtils

load_dotenv()

html_link = "https://solr.apache.org/guide/solr/latest/indexing-guide/indexing-with-update-handlers.html"

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
page = requests.get(html_link, headers)
soup = bs(page.text, "html.parser")

# page title
page_title = soup.find('h1').text
mdFile = MdUtils(file_name='output/' + page_title)
mdFile.new_header(level=1, title=process_translation(page_title))

# page preambl
preamble = soup.find('div', id='preamble').find('div', class_='sectionbody').find_all('div', recursive=False)
for p in preamble:
  mdFile.new_paragraph(process_translation(p.text))


## sections
sect1_grp = soup.find_all('div', class_='sect1')
for sect in sect1_grp:
  mdFile.new_header(level=2, title=process_translation(sect.find('h2').text))
  sectbody = sect.find('div', class_='sectionbody')
  walkthrough_to_md(sectbody,'sect1',mdFile)

#create markdown file
mdFile.create_md_file()





