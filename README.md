# ChapterVerse: Web Scraping & EPUB Conversion

ChapterVerse is a Python project designed to scrape online novels and create EPUB files from their chapters. It provides concurrent scraping capabilities, error handling with retry logic, and the ability to add a cover image to the generated EPUB.

## Features
- Concurrent scraping of chapters to improve efficiency.
- Error handling with automatic retry logic to handle transient network errors.
- Creation of EPUB files with customizable cover images.

## Requirements
- Python 3.7 or higher
- `requests`
- `beautifulsoup4`
- `ebooklib`
- `tenacity`
- `concurrent.futures`

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/saturnthehustler/chapterverse-scraper.git
   cd chapterverse-scraper
