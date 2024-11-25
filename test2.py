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

def get_wiki_plot(title,wiki):
    '''
    return [WIKI:PAGE_NAME,plot_text]
    '''
    title = clean_title(title)
    search_results = wikipedia.search(title + "(book)")
    if not len(search_results):
        return None
    for res in search_results:
        page = wiki.page(res)  
        for section in page.sections:
            section_words = [word.lower() for word in section.title.split(" ")]
            if "plot" in section_words or "summary" in section_words:
                return [f"WIKI:{res}",section.text]
    return None

def web_scrape():
    pass

def generate_summary(title,client):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You summarize books, if you don't know the book say only 'Unknown'"},  # System role
            {"role": "user", "content": f"Please summarize the book {title}, in a way that spoils the plot and reveals key moments and characters"}  
        ],
        temperature=0.7,  
        max_tokens=400,  
    )
    return response.choices[0].message.content

def upload(page_index,client):
    page_batches = 100
    wiki = wikipediaapi.Wikipedia(user_agent="LeadTheRead/0.0 (http://leadtheread.com; leadtheread@gmail.com)")
    for i in range(page_index,page_index+page_batches):
        res = openlibrary_search(i)
        if not res:
            print(i)
            break
        for title,author in res:
            if title != "Unknown Title":
                plot = get_wiki_plot(title,wiki)
                if not plot:
                    query = title + " by " + author
                    plot = generate_summary(query,client)
            print("----------------")
            print(title)
            print(plot)
            time.sleep(5)
            #embed
            #upsert
    print(f"Last Page Index: {i}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("last_page_index.txt", "w") as file:
        file.write(f"{timestamp}, {str(i)}\n")

if __name__=="__main__":
    # print(openlibrary_search(1))
    get_wiki_plot("Harry Potter and the Philosopher's Stone")