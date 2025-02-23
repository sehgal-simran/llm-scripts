import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import time
import logging
from observo_llm import log_response, log_request  # Assuming this is the observability package

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = OpenAI()

links = ["https://www.bio.iitb.ac.in/people/faculty/"]

def scrape_website(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            logging.info(f"Successfully scraped {url} in {elapsed_time:.2f} seconds.")
            soup = BeautifulSoup(response.text, 'html.parser')
            extractProfInfo(soup)
        else:
            logging.error(f"Failed to retrieve {url}. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")

def extractProfInfo(soup):
    try:
        start_time = time.time()
        prompt = f"Take this beautiful soup object and extract the professor's name, designation, department, and research interests. {soup}"
        model = "gpt-4o-mini"
        log_request(prompt, model)
        response = log_response(client.chat.completions.create, 
                                model=model, 
                                messages=[
                                    {"role": "system", "content": "You are a helpful assistant."},
                                    {"role": "user", "content": prompt}
                                ])
        
        elapsed_time = time.time() - start_time
        logging.info(f"LLM call completed in {elapsed_time:.2f} seconds.")
        print(response.choices[0].message)
    except Exception as e:
        logging.error(f"Error in LLM processing: {e}")

for link in links:
    logging.info(f"Starting scrape for {link}")
    scrape_website(link)
