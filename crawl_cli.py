#!/usr/bin/env python3
import asyncio
import argparse
import json
import sys
from crawler import run_crawler
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(description='Web Crawler Error Detector CLI')
    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('--depth', type=int, default=2, help='Maximum crawl depth (default: 2)')
    parser.add_argument('--concurrency', type=int, default=5, help='Number of concurrent requests (default: 5)')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('--user-agent', help='Custom user agent string')
    parser.add_argument('--output', help='Output file to save results (JSON format)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    return parser.parse_args()

async def main():
    args = parse_args()
    
    print(f"Starting crawler at {args.url} with depth {args.depth}")
    print("This may take a while depending on the site size and crawl depth...")
    
    try:
        result = await run_crawler(
            start_url=args.url,
            max_depth=args.depth,
            concurrency=args.concurrency,
            timeout=args.timeout,
            user_agent=args.user_agent
        )
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
                print(f"Results saved to {args.output}")
        
        # Print results
        if result:
            print(f"\nFound {len(result)} pages with errors:")
            for url, error in result.items():
                print(f"\n{url}")
                print(f"  Error Type: {error['error_type']}")
                print(f"  Status Code: {error['status_code']}")
                print(f"  Message: {error['message']}")
        else:
            print("\nNo errors found! The website appears to be working properly.")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 