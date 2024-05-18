import requests
from bs4 import BeautifulSoup
import concurrent.futures
import logging
from ebooklib import epub
from tenacity import retry, stop_after_attempt, wait_exponential
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration variables
NUM_CHAPTERS = 2240
CONCURRENT_REQUESTS = 200
COVER_IMAGE_PATH = 'An Understated Dominance.png'

# Retry configuration
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_response_with_retry(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response

# Function to scrape the content of a single chapter
def scrape_chapter(chapter_num, chapter_url):
    try:
        response = get_response_with_retry(chapter_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('div', class_='entry-content')
        if content:
            # Remove the "Back to Category" link
            back_to_category = content.find('a', string='Back to Category')
            if back_to_category:
                back_to_category.decompose()
            return (chapter_num, content.prettify().strip())
        else:
            return (chapter_num, '')
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve {chapter_url}: {e}")
        return (chapter_num, '')

# Function to scrape all chapters and organize them
def scrape_all_chapters(base_urls, num_chapters):
    chapters = []
    chapter_urls = []

    for start_chapter, base_url in base_urls:
        for i in range(start_chapter, num_chapters + 1):
            if i < start_chapter:
                continue
            # Infer the URL for each chapter based on the pattern
            if i <= 2009:
                chapter_urls.append((i, f"{base_url}{i}/"))
            else:
                # Calculate the second part of the URL
                second_part = 4018 + 2 * (i - 2010) + 1
                chapter_urls.append((i, f"{base_url}{i}-{second_part}-{second_part + 1}/"))

    # Use ThreadPoolExecutor to scrape chapters concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = {executor.submit(scrape_chapter, num, url): num for num, url in chapter_urls}
        for future in concurrent.futures.as_completed(futures):
            chapter_num = futures[future]
            try:
                chapter_num, chapter_content = future.result()
                if chapter_content:
                    chapters.append((chapter_num, chapter_content))
                    logging.info(f"Scraped Chapter {chapter_num}")
            except Exception as e:
                logging.error(f"Error processing Chapter {chapter_num}: {e}")

    # Sort chapters by chapter number
    chapters.sort(key=lambda x: x[0])
    return {f"Chapter {num}": content for num, content in chapters}

# Function to create EPUB file


def create_epub(title, author, chapters, cover_image_path):
    # Create an EPUB book
    book = epub.EpubBook()

    # Set the metadata
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)

    # Add cover image
    if os.path.exists(cover_image_path):
        book.set_cover("cover.jpg", open(cover_image_path, 'rb').read())

    # Create chapters and add them to the book
    epub_chapters = []
    for i, (chapter_title, content) in enumerate(chapters.items(), start=1):
        # Add chapter headers
        content = f'<h1>Chapter {i}</h1>' + content
        c = epub.EpubHtml(title=chapter_title, file_name=f'{chapter_title}.xhtml', lang='en')
        c.content = content
        book.add_item(c)
        epub_chapters.append(c)

    # Define Table Of Contents
    book.toc = (epub_chapters)

    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Arial, sans-serif;
    }
    h1 {
        text-align: center;
        text-transform: uppercase;
        font-weight: bold;
    }
    h2 {
        text-align: center;
        text-transform: uppercase;
        font-weight: bold;
    }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Add spine (order of the book contents)
    book.spine = ['nav'] + epub_chapters

    # Write to the file
    epub.write_epub(f'{title}.epub', book, {})

# Main execution
if __name__ == "__main__":
    logging.info("Starting the scraping process")
    base_urls = [
        (1, 'https://www.bhqtech.com/an-understated-dominance-by-marina-vittori-chapter-'),
        (2000, 'https://www.bhqtech.com/novel-an-understated-dominance-by-marina-vittori-chapter-'),
        (2001, 'https://www.bhqtech.com/an-understated-dominance-by-marina-vittori-chapter-'),
        (2010, 'https://www.bhqtech.com/an-understated-dominance-chapter-')
    ]
    # Scrape all chapters
    chapters = scrape_all_chapters(base_urls, NUM_CHAPTERS)

    # Create the EPUB book
    create_epub('An Understated Dominance', 'Marina Vittori', chapters, COVER_IMAGE_PATH)

    logging.info("EPUB creation complete")
