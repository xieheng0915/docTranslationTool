from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup as bs
import requests
import json

client = OpenAI()

def translate_func(text, target_language):
    response = client.completions.create(
    prompt=f"Translate the following English text to {target_language}: {text}\n",
    max_tokens=3000,
    temperature=0.7,
    model = "gpt-3.5-turbo-instruct",
    stop=None)
    return response.choices[0].text.strip()

#Function to split data into smaller chunks
def split_data(docs):
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1500,
    chunk_overlap  = 0,
    length_function = len
    )

    docs_chunks = text_splitter.split_text(docs)
    return docs_chunks

# find titles by layer
def getLayerTitles(layer,soup):
    layer_titles = []
    hlayer = soup.find_all(layer)
    for item in hlayer:
        layer_titles.append(item.get_text())
    return layer_titles
    
def build_paragraphs(soup_element):
    paragraphs = ""
    for p in soup_element.find_all('p'):
        paragraphs +=p.text
    return paragraphs 

def build_code_blocks(code_blocks):
    code_data = []
    for code_block in code_blocks:
        code_content = code_block.find('code').text
        code_data.append(code_content)
    return code_data

def build_paragraph_blocks(paragraphs):
    paragraph_data = []
    for paragraph in paragraphs:
        paragraph_content = paragraph.find('p').text
        paragraph_data.append(paragraph_content)
    return paragraph_data

# build json        
def build_json(sects,layer):
    doc_data = []
    #index = 0
    for sect in sects:
       sect_data = {}
       #index += 1
       #sect_data.update({'id': index})
       sectname = 'sect' + str(int(layer[-1])-1)
       sect_data.update({'sect': sectname})
       # Sect title
       title = sect.find(layer).text
       sect_data.update({'title': title})
       # Sect  paragraph
       if sect.find_all('div', class_='paragraph'):
        paragraph_blocks = sect.find_all('div', class_='paragraph')
        paragraphs = build_paragraph_blocks(paragraph_blocks)
        sect_data.update({'paragraph': paragraphs})
       # Sect code block
       if sect.find_all('div', class_='listingblock'):
        code_blocks = sect.find_all('div', class_='listingblock')
        code_data = build_code_blocks(code_blocks)
        sect_data.update({'code': code_data})
       # Sect table
       # Next Sect
       nextLayer = 'h' + str(int(layer[-1]) + 1)
       nextSect = 'sect' + str(int(layer[-1]))
       if sect.find_all('div', class_=nextSect):
        nextSects = sect.find_all('div', class_=nextSect)
        nextLayerData = build_json(nextSects, nextLayer)
        sect_data.update({nextSect: nextLayerData})
       
       # Add all the elemet into list 
       doc_data.append(sect_data)
 
    return doc_data

# scrape html
def walkthrough_html(html):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    page = requests.get(html, headers)
    soup = bs(page.text, "html.parser")
    # get h1 titles
    # preamble paragraph

    sects = soup.find_all('div', class_='sect1')
    json_=build_json(sects, 'h2')
    print(json.dumps(json_, indent=4))

    #doc_data = find_elements(sect1, 2)
    #print(json.dumps(doc_data, indent=4))
    
   
            
        
        



    
    
    
        
    
            

  
       
          
    