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

def find_elements(sects, layer):
    #set json 
    doc_data = {}
    #Title
    layerStr = str('h' + str(layer))
    print("layer: " + layerStr)
    doc_data['layer'] = layerStr
    for sect in sects:
      title = sect.find(layerStr).text
      print(title)
      doc_data['title'] = title
      sectionbody = sect.find_all('div', class_='sectionbody')
      for section in sectionbody:
        #Paragraph
        paragraph = build_paragraphs(section.find('div', class_='paragraph'))
        print(paragraph)
        doc_data['paragraph'] = paragraph
        #Code Block
        if section.find('div', class_='listingblock'):
          code_block = section.find('div', class_='listingblock').find('code').text
          print(code_block)
        #list
        if section.find('ul'):
          ulist = section.find_all('ul')
          for ul in ulist:
            litem = ul.find_all('li')
            for li in litem:
              print(li.find('p').text)  
        #table
        if section.find('table'):
          pass
        #attention marks  
        #find next layer and call regressionly
        nextSectStr = 'sect' + str(layer)
        #print("nextSect: " + nextSectStr)
        if section.find_all('div', class_=nextSectStr):
          sect_next = section.find_all('div', class_=nextSectStr)
          find_elements(sect_next, layer +1)
    return doc_data
        
                        
# scrape html
def walkthrough_html(html):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    page = requests.get(html, headers)
    soup = bs(page.text, "html.parser")
    #find titles by layer
    h2_titles = getLayerTitles("h2",soup)
    #print(h2_titles)
    h3_titles = getLayerTitles("h3",soup)
    #print(h3_titles)

    sect1 = soup.find_all('div', class_='sect1')
    doc_data = find_elements(sect1, 2)
    print(doc_data)
    
   
            
        
        



    
    
    
        
    
            

  
       
          
    