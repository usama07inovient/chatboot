import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import os
from django.conf import settings

import logging
import os

def setup_logging(filename):
    """Sets up the error log file based on the path of the provided filename."""
    # Get the directory of the file
    directory_path = os.path.dirname(filename)
    error_file_path = os.path.join(directory_path, 'scraping_errors.txt')
    
    # Ensure the directory exists
    os.makedirs(directory_path, exist_ok=True)
    
    return error_file_path  # Return the path to the error log file

# Custom headers to mimic a browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.google.com",
}

def scrape_url(url, visited_urls, session, main_domain,error_file_path):
    """Scrapes a single URL, extracting headings and paragraphs."""
    if url in visited_urls:
        return None, visited_urls

    try:
        visited_urls.add(url)  # Mark URL as visited before scraping

        # Send a GET request to fetch the page content with headers
        response = session.get(url, headers=HEADERS, timeout=10)  # Set a timeout
        response.raise_for_status()  # Raise an error for bad status codes

        response_content = response.content  # Use .content to get bytes
        print(f"Scraping {url}...")  # Debugging output

        # Check if the response content is valid text
        try:
            response_text = response_content.decode('utf-8')  # Attempt to decode as UTF-8
        except (UnicodeDecodeError, TypeError):
            error_message = f"Invalid text received from {url}. Returning None."
            with open(error_file_path, "a", encoding="utf-8") as error_file:
                error_file.write(error_message)  # Write error message to the text file
            return None, visited_urls  # Return empty string for content

        # Parse the response content with BeautifulSoup
        soup = BeautifulSoup(response_text, "html.parser")
        content = f"\nScraping URL: {url}\n"

        # Extract all headings
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            headings = soup.find_all(tag)
            for heading in headings:
                content += f"{tag.upper()}: {heading.get_text().strip()}\n"

        # Extract all paragraphs
        paragraphs = soup.find_all("p")
        for para in paragraphs:
            content += f"Paragraph: {para.get_text().strip()}\n"

        # Get all links on the page and prepare for recursive scraping
        links = soup.find_all("a")
        new_urls = []
        for link in links:
            href = link.get("href")
            if href:
                full_url = urljoin(url, href)  # Normalize relative URLs
                parsed_url = urlparse(full_url)

                # Only add internal URLs (same domain) and skip external links
                if parsed_url.netloc == main_domain and full_url not in visited_urls:
                    new_urls.append(full_url)

        return content, new_urls

    except (requests.RequestException, requests.Timeout) as e:
        error_message = f"Error fetching {url}: {str(e)}\n"
        with open(error_file_path, "a", encoding="utf-8") as error_file:
            error_file.write(error_message)  # Write error message to the text file
        return None, visited_urls  # Return empty string for content

def scrape_website_recursive(main_url, filename, error_file_path, max_links=None):
    """Recursively scrapes a website and saves the content to a file."""
    visited_urls = set()
    urls_to_scrape = [main_url]
    session = requests.Session()
    scraped_count = 0

    # Extract domain for filtering internal links
    parsed_main_url = urlparse(main_url)
    main_domain = parsed_main_url.netloc

    # Ensure the directory for the file exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:  # Open in write mode to empty the file
            pass  # Just clear the file content
        
    with open(filename, "a", encoding="utf-8") as f:
        while urls_to_scrape:
            if max_links is not None and scraped_count >= max_links:
                break  # Stop if max_links limit is reached

            current_url = urls_to_scrape.pop(0)
            if current_url not in visited_urls:
                page_content, new_urls = scrape_url(current_url, visited_urls, session, main_domain, error_file_path)
                print(page_content,"page_content")
                if page_content:  # Only write if content is not empty
                    f.write(page_content + "\n")
                    scraped_count += 1
                urls_to_scrape.extend(new_urls)

    return scraped_count

def start_scraping(main_url, file_full_path, max_links=None):
    """Entry point to begin the scraping process."""
    # Get the error file path
    error_file_path = setup_logging(file_full_path)

    print(f"Starting scraping for {main_url}")
    scraped_count = scrape_website_recursive(main_url, file_full_path, error_file_path, max_links=max_links)
    print(f"Scraping complete. {scraped_count} links scraped.")


