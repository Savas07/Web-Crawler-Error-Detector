# Web Crawler Error Detector

This project is a web crawler that scans websites for errors and displays a report of pages with issues.

## Features

- Crawl websites starting from specified URLs
- Check for HTTP errors, broken links, and other issues
- Display a detailed report of pages with errors
- Configurable crawl depth and concurrency
- Web interface to view results

## Installation

### Option 1: Using a Virtual Environment (Recommended)

1. Clone this repository
2. Create a virtual environment:
   ```
   python3 -m venv venv
   ```
3. Activate the virtual environment:
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```
   - On Windows:
     ```
     venv\Scripts\activate
     ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Option 2: Global Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Activate your virtual environment (if using one)
2. Run the web application:
   ```
   python app.py
   ```
   Or use the unified run script:
   ```
   python run.py
   ```
3. Open your browser and navigate to `http://localhost:5000`
4. Enter the starting URL and crawl configuration
5. View the results on the dashboard

### Command Line Interface

The project also includes a command-line interface:

```
# Using the unified script
python run.py --mode cli --url https://example.com

# Or directly
python crawl_cli.py https://example.com
```

## Configuration Options

- Starting URL: The URL where the crawl will begin
- Crawl Depth: How many links deep to follow (default: 2)
- Concurrency: Number of concurrent requests (default: 5)
- Timeout: Request timeout in seconds (default: 10)
- User Agent: Custom user agent string (optional)

## Requirements

- Python 3.8+ (Python 3.12 recommended)
- Dependencies listed in requirements.txt
