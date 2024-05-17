import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import concurrent.futures
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration variables
NUM_CHAPTERS = 2239
CONCURRENT_REQUESTS = 5
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
        return (chapter_num, content.prettify().strip() if content else '')
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
def create_epub(chapters, title, author, cover_image_path):
    book = epub.EpubBook()
    book.set_title(title)
    book.add_author(author)
    book.set_identifier('sample123456')  # Set a unique identifier for the EPUB book
    book.set_language('en')

    # Add cover image
    try:
        with open(cover_image_path, 'rb') as file:
            cover_image_content = file.read()

        cover_item_id = "cover_image"
        cover_image = epub.EpubItem(uid=cover_item_id, file_name="cover.png", media_type="image/png",
                                    content=cover_image_content)
        book.set_cover(cover_item_id, cover_image_content)
        book.add_item(cover_image)

        cover_xhtml = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang='en')
        cover_xhtml.content = f'<html><head></head><body><img src="cover.png" alt="Cover" style="width: 100%; height: 100%;" /></body></html>'
        book.add_item(cover_xhtml)
        book.spine = ['cover', 'nav']  # The cover image should be the first item in the spine
    except FileNotFoundError:
        logging.warning(f"Cover image {cover_image_path} not found. Skipping cover image.")

    # Add chapters
    toc = []

    for chapter_title, chapter_content in chapters.items():
        chapter_content_with_header = f'<h1>{chapter_title}</h1>\n{chapter_content}'
        chapter_file_name = f'chapter-{chapter_title.replace(" ", "-")}.xhtml'
        chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='en')
        chapter.content = chapter_content_with_header
        book.add_item(chapter)
        toc.append(epub.Link(chapter_file_name, chapter_title, chapter_file_name))
        book.spine.append(chapter)

    book.toc = tuple(toc)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Add CSS
    style = 'BODY { color: black; }'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Write EPUB file with EPUB 2 version
    epub.write_epub(f'{title}.epub', book, {'version': '2'})
    logging.info(f'{title}.epub created successfully.')

# Main execution
if __name__ == "__main__":
    logging.info("Starting the scraping process")
    base_urls = [
        (1, 'https://www.bhqtech.com/an-understated-dominance-by-marina-vittori-chapter-'),
        (2000, 'https://www.bhqtech.com/novel-an-understated-dominance-by-marina-vittori-chapter-'),
        (2001, 'https://www.bhqtech.com/an-understated-dominance-by-marina-vittori-chapter-'),
        (2010, 'https://www.bhqtech.com/an-understated-dominance-chapter-')
    ]
    chapters = scrape_all_chapters(base_urls, NUM_CHAPTERS)
    if chapters:
        logging.info("Scraping completed successfully. Starting EPUB creation.")
        create_epub(chapters, title='An Understated Dominance', author='Marina Vittori',
                    cover_image_path=COVER_IMAGE_PATH)
    else:
        logging.error("No chapters were scraped. Exiting.")
