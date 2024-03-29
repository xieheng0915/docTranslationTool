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

# find html elements, build json by sequence
def build_json_sequence(sects,layer):
    sect_docs = {}
    doc_data = []
    for sect in sects:
       #call sect process
        sect_data = build_json_sect1(sect)
        doc_data.append(sect_data)
    
    sect_docs.update({'sect1': doc_data})
    return sect_docs

# build json for sect1 layer
def build_json_sect1(sect):
    sect_data = []
    # Sect definition
    nextLayer = 'h3'
    nextSect = 'sect2'
    
    # Sect title
    title = sect.find('h2').text
    sect_data.append({'title': title})
    #first element under sectionbody 
    sect_body = sect.find('div', class_='sectionbody').find_all('div', recursive=False)
    for element in sect_body:
        if 'paragraph' in element['class']:
            paragraphs = build_paragraphs(element)
            sect_data.append({'paragraph': paragraphs})
        elif 'listingblock' in element['class']:
            code_data = element.find('code').text
            sect_data.append({'code': code_data})
        elif 'sect2' in element['class']:
            sect2_data = build_json_after_sect2(element,'h3')            
            sect_data.append({'sect2': sect2_data})
    
   
    #return data
    return sect_data

# build json for sect2 and after
def build_json_after_sect2(sect, layer):
    sect_data = []
    # sect2, h3; sect3, h4; sect4, h5...
    nextSect = 'sect' + str(int(layer[-1]))
    nextLayer = 'h' + str(int(layer[-1]) + 1)

    curr_element = sect.find(layer)
    sect_data.append({'title': curr_element.text})
    nextSiblings = curr_element.find_next_siblings('div', recursive=False)
    for element in nextSiblings:
        if 'paragraph' in element['class']:
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
        elif nextSect in element['class']:
            nextSectData = build_json_after_sect2(element, nextLayer)
            sect_data.append({nextSect: nextSectData})
        


    return sect_data


# scrape html
def walkthrough_html(html):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    page = requests.get(html, headers)
    soup = bs(page.text, "html.parser")
    # get h1 titles
    # preamble paragraph

    sects = soup.find_all('div', class_='sect1')
    #json_=build_json(sects, 'h2')
    json_=build_json_sequence(sects, 'h2')
    #json_=build_json_for_elements(soup)
    print(json.dumps(json_, indent=4))

    
    
   
            
        
        



    
    
    
        
    
            

  
       
          
    