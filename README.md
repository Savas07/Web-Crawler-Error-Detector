# Web Crawler Error Detector

This project is a web crawler that scans websites for errors and displays a report of pages with issues.

## Features

- Crawl websites starting from specified URLs
- Check for HTTP errors, broken links, and other issues
- Display a detailed report of pages with errors
- Configurable crawl depth and concurrency
- Web interface to view results

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the web application:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`
3. Enter the starting URL and crawl configuration
4. View the results on the dashboard

## Configuration Options

- Starting URL: The URL where the crawl will begin
- Crawl Depth: How many links deep to follow (default: 2)
- Concurrency: Number of concurrent requests (default: 5)
- Timeout: Request timeout in seconds (default: 10)
- User Agent: Custom user agent string (optional)
