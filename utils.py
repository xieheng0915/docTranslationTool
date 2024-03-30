from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup as bs
import requests
import json
import configparser

client = OpenAI()

def translate_func(text, target_language):
    response = client.completions.create(
    prompt=f"Translate the following English text to {target_language}: {text}\n",
    max_tokens=3000,
    temperature=0.7,
    model = "gpt-3.5-turbo-instruct",
    stop=None)
    return response.choices[0].text.strip()

def process_translation(text):
    config=configparser.ConfigParser()
    config.read('config.ini')
    target_lang = config.get('translation','target.lang')
    source_lang = config.get('translation','source.lang')
    if source_lang == target_lang:
        return text
    elif target_lang == "" or target_lang == "none":
        return text
    else:
        return translate_func(text,target_lang)

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
    elif 'admonitionblock' in element['class']:
      warning_data = get_warning(element)
      sect_data.append({'warning': warning_data})
    elif nextSect in element['class']:
      nextSectData = walkthrough_sects(element, nextSect)
      sect_data.append({nextSect: nextSectData})
      pass
      
  return sect_data
   
#Function to convert html to markdown and json both
def walkthrough_to_json_md(sect, sectLayer, mdFile):
  sect_data = []
  sect_group = sect.findChildren('div', recursive=False)
  nextSect = 'sect' + str(int(sectLayer[-1]) + 1)
  title_tag = 'h' + str(int(nextSect[-1]) + 1)
  mdFileLevel = int(nextSect[-1]) + 1
  for element in sect_group:
    if element.find(title_tag):
      title = element.find(title_tag).text
      mdFile.new_header(level=mdFileLevel, title=title)
      sect_data.append({'title': title})
    if 'paragraph' in element['class']:
      #print(element)
      paragraphs = build_paragraphs(element)
      mdFile.new_paragraph(paragraphs)
      sect_data.append({'paragraph': paragraphs})
    elif 'listingblock' in element['class']:
      code_data = element.find('code').text
      mdFile.write('\n```\n' + code_data + '\n```\n')
      sect_data.append({'code': code_data})
    elif 'dlist' in element['class']:
      dlist_data = insert_dlist(element,mdFile)
      sect_data.append({'dlist': dlist_data})
    elif 'ulist' in element['class']:
      ulist_data = get_ulist(element)
      mdFile.new_list(ulist_data)
      sect_data.append({'ulist': ulist_data})
    elif 'admonitionblock' in element['class']:
      message_data = insert_marks(element.find('tr'),mdFile)
      #sect_data.append({'warning': message_data})
    elif nextSect in element['class']:
      nextSectData = walkthrough_to_json_md(element, nextSect, mdFile)
      sect_data.append({nextSect: nextSectData})
      #pass

  return sect_data

def insert_dlist(dlist,mdFile):
    dl_data = []
    dl_sect = dlist.find('dl')
    children = dl_sect.findChildren(recursive=False)
    for child in children:
        if child.name == 'dt':
            dl_data.append({'dt': child.text})
            mdFile.new_line(child.text, bold_italics_code='b')
        elif child.name == 'dd':
            table = child.find('table')
            if table:
                td = table.find_all('td')
                td_data = []
                for td_ in td:
                    td_data.append(td_.text)
                dl_data.append({'table': td_data})
                mdFile.new_table(len(td_data),1,td_data, 'center')
            paragraph = child.find('div', class_='paragraph')
            if paragraph:
                dl_data[-1].update({'paragraph': paragraph.text})
                mdFile.new_line(paragraph.text.replace('\n',''), bold_italics_code='i')

    return dl_data  

def insert_marks(message_sect,mdFile):
    message_data = []
    children = message_sect.findChildren(recursive=False)
    for child in children:
        if child.name == 'td':
            if child.get('class') == ['icon']:
                info = child.find('i').get('title')
                message_data.append({'icon': info})
                if info == 'Warning':
                    mdFile.new_line(':warning:'+child.find('i').get('title'))
                elif info == 'Important':
                  mdFile.new_line(':exclamation:'+child.find('i').get('title'))
                elif info == 'Note':
                  mdFile.new_line(':information_source:'+child.find('i').get('title'))
            elif child.get('class') == ['content']:
                message_data.append({'content': child.text})
                mdFile.new_line(child.text)
                
    return message_data
                  

# function to convert html to markdown 
def walkthrough_to_md(sect, sectLayer, mdFile):
  sect_group = sect.findChildren('div', recursive=False)
  nextSect = 'sect' + str(int(sectLayer[-1]) + 1)
  title_tag = 'h' + str(int(nextSect[-1]) + 1)
  mdFileLevel = int(nextSect[-1]) + 1
  for element in sect_group:
    if element.find(title_tag):
      title = process_translation(element.find(title_tag).text)
      mdFile.new_header(level=mdFileLevel, title=title)
    if 'paragraph' in element['class']:
      paragraphs = process_translation(build_paragraphs(element))
      mdFile.new_paragraph(paragraphs)
    elif 'listingblock' in element['class']:
      code_data = element.find('code').text
      mdFile.write('\n```\n' + code_data + '\n```\n')
    elif 'dlist' in element['class']:
      dlist_data = insert_dlist(element,mdFile)
    elif 'ulist' in element['class']:
      ulist_data = get_ulist(element)
      mdFile.new_list(ulist_data)
    elif 'admonitionblock' in element['class']:
      insert_marks(element.find('tr'),mdFile)
    elif nextSect in element['class']:
      walkthrough_to_md(element, nextSect, mdFile)
      

def insert_dlist(dlist,mdFile):
    dl_sect = dlist.find('dl')
    children = dl_sect.findChildren(recursive=False)
    for child in children:
        if child.name == 'dt':
            mdFile.new_line(child.text, bold_italics_code='b')
        elif child.name == 'dd':
            table = child.find('table')
            if table:
                td = table.find_all('td')
                td_data = []
                for td_ in td:
                    td_data.append(td_.text)
                mdFile.new_table(len(td_data),1,td_data, 'center')
            paragraph = child.find('div', class_='paragraph')
            if paragraph:
                mdFile.new_line(process_translation(paragraph.text.replace('\n','')), bold_italics_code='i')

    

def insert_marks(message_sect,mdFile):
    children = message_sect.findChildren(recursive=False)
    for child in children:
        if child.name == 'td':
            if child.get('class') == ['icon']:
                info = child.find('i').get('title')
                if info == 'Warning':
                    mdFile.new_line(':warning:'+child.find('i').get('title'))
                elif info == 'Important':
                  mdFile.new_line(':exclamation:'+child.find('i').get('title'))
                elif info == 'Note':
                  mdFile.new_line(':information_source:'+child.find('i').get('title'))
            elif child.get('class') == ['content']:
                mdFile.new_line(process_translation(child.text))
                

    
    
    
        
    
            

  
       
          
    