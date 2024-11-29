import requests
import wikipedia
import wikipediaapi

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

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

def upsert(index,embedding,title,ISBN,id):
    if ISBN == None:
        ISBN = "None"
    meta = {'title':title,'ISBN':ISBN}
    vector = [{
        'id':str(id),
        'values':embedding,
        'metadata': meta
    }]
    index.upsert(vectors=vector)

def query(index,q):
    client = init_openai()
    embedding = embed(q,client)
    resp = index.query(
        vector = embedding,
        top_k = 2,
        include_metadata=True
    )
    return resp


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

def search_books_isbn(isbn):
    base_url = "https://www.googleapis.com/books/v1/volumes" 
    params = {'q': f'Subject:{isbn}'}
    response = requests.get(base_url, params=params)   
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        return data
    elif response.status_code == 403:
        print("Error 403: Forbidden. Please check your API key and its restrictions.")
        return None
    else:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
        return None

def clean_title(title):
    # Checks for title (movie) case
    if len(title.split("(")) > 1:
        return title.split("(")[0]
    return title

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
            match = extract_isbn(word)
            if len(str(match)) < 9 or len(str(match)) > 13:
                continue
            return extract_isbn(word)
    return None

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
                time.sleep(.2)
                isbn = get_isbn_wiki(res)
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

def contains_illegal_char(s):
    legal_pattern = re.compile(
        r"[\u3000-\u303F\u4E00-\u9FFF\uAC00-\uD7AF\uFF00-\uFFEF"
        r"\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF"  
        r"\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF"  
        r"\u0D00-\u0D7F\u0D80-\u0DFF\u0E00-\u0E7F]"              
    )

    return bool(legal_pattern.search(s))

def web_scrape():
    pass

def generate_summary(title,client):
    #error
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You summarize and spoil books with key details, plot points, and character names. You do not have any biases nor thoughts about the books, you simply explain them in 500 words or less."},  # System role
            {"role": "user", "content": f"Summarize the book: {title}"}  
        ],
        temperature=0.7,  
        max_tokens=400,  
    )
    return response.choices[0].message.content

def upload(page_batches):
    openai_client = init_openai()
    index = init_pinecone()
    wiki = wikipediaapi.Wikipedia(user_agent="LeadTheRead/0.0 (http://leadtheread.com; leadtheread@gmail.com)")
    with open("last_page_index.txt", "r", encoding="utf-8") as file:
        lines = file.readlines()
        if lines: 
            last_line = lines[-1]
    file.close()
    page_index = int(last_line.split(",")[1].strip().split(":")[1])
    id_num = int(last_line.split(",")[3].strip().split(":")[1])
    for i in range(page_index,page_index+page_batches):
        res = openlibrary_search(i)
        if not res:
            print("Error in openlibrary")
            print(i)
            return None
        AI_used = 0
        for book in res:
            title, author = book.get("title"), book.get("author")
            print(title)
            if contains_illegal_char(title):
                print(f"{title}------------------------")
                continue
            if title != "Unknown Title":
                wiki_res = get_wiki_plot(title,wiki)
                if not wiki_res:
                    AI_used +=1
                    authors = ", ".join(author)
                    query = title + " by " + authors
                    print(query)
                    plot = generate_summary(query,openai_client)
                    if plot == "Unknown":
                        continue
                    isbn = None
                else:
                    plot = wiki_res[1]
                    isbn = wiki_res[2]

            plot = plot.encode("utf-8", errors="ignore").decode("utf-8")
            emb = embed(text=plot,client=openai_client)
            upsert(index,emb,title,isbn,id_num)
            id_num += 1


    print(f"Last Page Index: {i}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("last_page_index.txt", "a") as file:
        # timestamp, last_completed_search_page_index, times AI was used to generate summary, last_id uploaded to vector db
        file.write(f"{timestamp}, page_index:{str(i+1)}, AI:{AI_used}, id:{id_num}\n")
    file.close()

if __name__=="__main__":
    # print(openlibrary_search(1))
    # get_wiki_plot("Harry Potter and the Philosopher's Stone")

    # upload(1)
    
    index = init_pinecone()
    res = query(index,"Misha and Ryen, who are both in high school. They are also pen pals, although they have never met face to face before. Misha is punk and in a band and has piercings. Ryen is a cheerleader and preppy ")
    print(res)
    # wiki = wikipediaapi.Wikipedia(user_agent="LeadTheRead/0.0 (http://leadtheread.com; leadtheread@gmail.com)")
    
    # print(get_wiki_plot("Harry Potter and the Philosopher's Stone",wiki))
   
