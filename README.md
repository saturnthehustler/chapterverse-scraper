# ChapterVerse: Web Scraping & EPUB Conversion

A Python project to scrape and create an EPUB from chapters of a novel.

## Features
- Concurrent scraping of chapters
- Error handling with retry logic
- Creation of an EPUB file with a cover image

## Requirements
- Python 3.7+
- `requests`
- `beautifulsoup4`
- `ebooklib`
- `tenacity`
- `concurrent.futures`

## Installation
Clone the repository and install the required packages:
```bash
git clone https://github.com/yourusername/chapterverse-scraper.git
cd chapterverse-scraper
pip install -r requirements.txt

## Usage
python ChapterVerse.py

## Configuration
BASE_URL = 'https://www.bhqtech.com/an-understated-dominance-by-marina-vittori-'
NUM_CHAPTERS = 2239
CONCURRENT_REQUESTS = 5
COVER_IMAGE_PATH = 'An Understated Dominance.png'

## License
This project is licensed under the MIT License - see the LICENSE file for details.

