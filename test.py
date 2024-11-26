import requests
import wikipedia
import wikipediaapi

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import os
import time
from datetime import datetime


#sort by readinglog or already_read
#web scraper

# OpenAI embedding
# Pinecone Vector DB

# database like Openlibrary for finding fiction books then match to an existing google library book
# match to wikipedia plot description
# segmentation
# add title to text pre embedding
# chatgpt generation of plots that don't exist

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import os
import time
import re

def embed(text, client):
    response = client.embeddings.create(
    input=text,
    model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def init_pinecone():
    pinecone_key = os.getenv("PINECONE_KEY")
    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index("leadtheread")
    time.sleep(1)
    return index 



def init_openai():
    openai_key = os.getenv("OPENAI_KEY")
    client = OpenAI(api_key=openai_key)
    return client

def openlibrary_search(page):
    """
    Fetches a batch of fiction books from the Open Library API.
    Args:
        page (int): The page number to retrieve (default is 1).
    Returns:
        list: A list of fiction books from the specified page, or None if the request fails.
    """
    query = "subject:Fiction"
    base_url = "https://openlibrary.org/search.json"
    params = {
        'q': query,
        'page': page,
        'language':'eng',
        'sort':'readinglog',
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        books = data.get("docs", [])
        result = [
            {"title": book.get("title", "Unknown Title"), "author": book.get("author_name", ["Unknown Author"])}
            for book in books
        ]
        return result
    else:
        print(f"Error: Unable to fetch data. Status code {response.status_code}")
        return None

def clean_title(title):
    # Checks for title (movie) case
    if len(title.split("(")) > 1:
        return title.split("(")[0]
    return title

def get_wiki_plot(title,wiki):
    '''
    return [WIKI:PAGE_NAME,plot_text]
    '''
    title = clean_title(title)
    search_results = wikipedia.search(title + " (book)")
    if not len(search_results):
        search_results = wikipedia.search(title + " (novel)")
        if not len(search_results):
            return None
    for res in search_results:
        page = wiki.page(res)
        for section in page.sections:
            section_words = [word.lower() for word in section.title.split(" ")]
            if "plot" in section_words or "summary" in section_words:
                plot = section.text
                for subsection in section.sections:
                    plot += subsection.text
                if len(plot.split(" ")) > 700:
                    plot = " ".join(plot.split(" ")[:700])
                #get isbn
                print(page.text)

                isbn = extract_isbn(page.text)
                return [f"WIKI:{res}",plot,isbn]
    return None

def extract_isbn(content):
    '''
    Extracts the first ISBN found in the given text content using regex.
    '''
    # Regular expression to match ISBN-10 or ISBN-13
    isbn_pattern = r'\b(?:ISBN(?:-1[03])?:?\s?)?((?:97[89]-?)?\d{1,5}-?\d{1,7}-?\d{1,7}-?\d{1})\b'
    match = re.search(isbn_pattern, content)
    if match:
        return match.group(1).replace("-", "")  # Remove hyphens for a clean ISBN
    return None

def search_wiki(search):
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "opensearch",
        "namespace": "0",
        "search": search,
        "limit": "3",
        "format": "json"
    }
    R = S.get(url=URL, params=PARAMS)
    res = R.json()
    print(res)
    # Data = [query, results[], idk[], links[],]

    time.sleep(1)
    titles = res[1]
    links = res[3]
    for i in range(len(titles)):
        print(titles[i])
        PARAMS = {
            "action": "parse",
            "page": "Harry Potter and the Philosopher's Stone",
            "prop": "text",
            "format": "json"
        }
        R = S.get(url=URL, params=PARAMS)
        DATA = R.json()

        print(DATA["parse"]["text"]["*"])
        break
from bs4 import BeautifulSoup

def get_isbn_wiki(title):
    URL = "https://en.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json"
    }
    
    with requests.Session() as S:
        response = S.get(url=URL, params=PARAMS)
        data = response.json()
    html_content = data["parse"]["text"]["*"]
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text().split(" ")
    for word in text:
        if "isbn" in word.lower():
            return extract_isbn(word)
    return None

def get_raw():
    pass

if __name__=="__main__":
    # print(openlibrary_search(1))
    # get_wiki_plot("Harry Potter and the Philosopher's Stone")
    # upload(1)

    print(get_isbn_wiki())
   
