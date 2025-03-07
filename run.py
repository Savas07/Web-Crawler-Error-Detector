#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description='Web Crawler Error Detector')
    parser.add_argument('--mode', choices=['web', 'cli'], default='web', 
                      help='Run mode: web interface or command-line (default: web)')
    
    # CLI mode arguments
    parser.add_argument('--url', help='Starting URL to crawl (required for CLI mode)')
    parser.add_argument('--depth', type=int, default=2, help='Maximum crawl depth (default: 2)')
    parser.add_argument('--concurrency', type=int, default=5, help='Number of concurrent requests (default: 5)')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('--user-agent', help='Custom user agent string')
    parser.add_argument('--output', help='Output file to save results (JSON format)')
    
    # Web mode arguments
    parser.add_argument('--port', type=int, default=5000, help='Port for web interface (default: 5000)')
    parser.add_argument('--host', default='127.0.0.1', help='Host for web interface (default: 127.0.0.1)')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.mode == 'cli':
        # Ensure URL is provided for CLI mode
        if not args.url:
            print("Error: --url is required for CLI mode", file=sys.stderr)
            return 1
        
        # Build command for CLI mode
        cmd = [
            sys.executable, 'crawl_cli.py', 
            args.url,
            '--depth', str(args.depth),
            '--concurrency', str(args.concurrency),
            '--timeout', str(args.timeout)
        ]
        
        if args.user_agent:
            cmd.extend(['--user-agent', args.user_agent])
        
        if args.output:
            cmd.extend(['--output', args.output])
        
        # Run CLI mode
        return subprocess.call(cmd)
    
    else:  # Web mode
        # Modify app.py to use specified host and port
        import app
        print(f"Starting web interface at http://{args.host}:{args.port}")
        print("Press Ctrl+C to exit")
        
        # Run web mode
        app.app.run(host=args.host, port=args.port, debug=True)
        return 0

if __name__ == "__main__":
    sys.exit(main()) 