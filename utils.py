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

def get_ulist(ulist):
    ulist_data = []
    ul = ulist.find('ul').find_all('li')
    for li in ul:
        content = li.find('p').text
        ulist_data.append(content)
    
    return ulist_data
    
def get_dlist(dlist):
    dl_data = []
    dl_sect = dlist.find('dl')
    children = dl_sect.findChildren(recursive=False)
    for child in children:
        if child.name == 'dt':
            dl_data.append({'dt': child.text})
        elif child.name == 'dd':
            table = child.find('table')
            if table:
                td = table.find_all('td')
                td_data = []
                for td_ in td:
                    td_data.append({'td':td_.text})
                dl_data.append({'table': td_data})
            paragraph = child.find('div', class_='paragraph')
            if paragraph:
                dl_data[-1].update({'paragraph': paragraph.text})

    return dl_data  

# get warning message
def get_warning(warning_sect):
    warning_data = []
    warning = warning_sect.find('table').find('tbody').find('tr')
    children = warning.findChildren(recursive=False)
    for child in children:
        if child.name == 'td':
            if child.get('class') == ['icon']:
                warning_data.append({'icon': child.find('i').get('title')})
            elif child.get('class') == ['content']:
                warning_data.append({'content': child.text})
    return warning_data


def walkthrough_sects(sect, sectLayer):
  sect_data = []
  sect_group = sect.findChildren('div', recursive=False)
  nextSect = 'sect' + str(int(sectLayer[-1]) + 1)
  for element in sect_group:
    if 'paragraph' in element['class']:
      #print(element)
      paragraphs = build_paragraphs(element)
      sect_data.append({'paragraph': paragraphs})
    elif 'listingblock' in element['class']:
      code_data = element.find('code').text
      sect_data.append({'code': code_data})
    elif 'dlist' in element['class']:
      dlist_data = get_dlist(element)
      sect_data.append({'dlist': dlist_data})
    elif 'ulist' in element['class']:
      ulist_data = get_ulist(element)
      sect_data.append({'ulist': ulist_data})
    elif 'admonitionblock warning' in element['class']:
      warning_data = get_warning(element)
      sect_data.append({'warning': warning_data})
    elif nextSect in element['class']:
      nextSectData = walkthrough_sects(element, nextSect)
      sect_data.append({nextSect: nextSectData})
      pass
      
  return sect_data
   
            
        
        



    
    
    
        
    
            

  
       
          
    