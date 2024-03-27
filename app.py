import openai
from dotenv import load_dotenv
import os
from utils import *

load_dotenv()

text = """Defines the path at which to split the input JSON into multiple Solr documents and is required if you have multiple documents in a single JSON file. If the entire JSON makes a single Solr document, the path must be “/”."""
target_language = "jp"
#docs = split_data(text)

'''
for doc in docs:
    print (doc)
    translation = translate_func(doc, target_language)
    print (translation)
'''


html_link = "https://solr.apache.org/guide/solr/latest/indexing-guide/indexing-with-update-handlers.html"
#extract_html_content(html_link)
#page = requests.get(html_link)
#soup = bs(page.text, "html.parser")
walkthrough_html(html_link)