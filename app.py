from flask import Flask, render_template, request, jsonify
import asyncio
import logging
from crawler import run_crawler
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.json
    start_url = data.get('start_url')
    max_depth = int(data.get('max_depth', 2))
    concurrency = int(data.get('concurrency', 5))
    timeout = int(data.get('timeout', 10))
    user_agent = data.get('user_agent')

    if not start_url:
        return jsonify({'error': 'Start URL is required'}), 400

    try:
        # Run the crawler (need to handle asyncio in Flask)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_crawler(
            start_url=start_url,
            max_depth=max_depth,
            concurrency=concurrency,
            timeout=timeout,
            user_agent=user_agent
        ))
        loop.close()

        # Format the error results
        formatted_errors = []
        for url, error in result['errors'].items():
            error_data = {
                'url': url,
                'error_type': error['error_type'],
                'status_code': error['status_code'],
                'message': error['message']
            }
            
            # Include additional details if available
            if 'details' in error:
                error_data['details'] = error['details']
            
            # Include headers if available
            if 'headers' in error:
                error_data['headers'] = error['headers']
                
            # Include referring page if available
            if 'referring_page' in error and error['referring_page']:
                error_data['referring_page'] = error['referring_page']
                
            formatted_errors.append(error_data)
        
        # Format the successful results
        formatted_success = []
        for url, success in result['successful'].items():
            success_data = {
                'url': url,
                'status_code': success['status_code'],
                'content_type': success.get('content_type', 'Unknown'),
                'title': success.get('title', 'No title'),
                'depth': success.get('depth', 0),
                'links_count': success.get('links_count', 0)
            }
            
            # Include referring page if available
            if 'referring_page' in success and success['referring_page']:
                success_data['referring_page'] = success['referring_page']
                
            formatted_success.append(success_data)

        return jsonify({
            'success': True,
            'stats': result['stats'],
            'errors': formatted_errors,
            'successful': formatted_success,
        })

    except Exception as e:
        logging.error(f"Error during crawl: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/recrawl', methods=['POST'])
def recrawl_single_url():
    data = request.json
    url = data.get('url')
    timeout = int(data.get('timeout', 10))
    user_agent = data.get('user_agent')
    previous_data = data.get('previous_data', {})

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        # Run a single URL crawl with max_depth=0 to just check this URL
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_crawler(
            start_url=url,
            max_depth=0,  # Only crawl the specified URL
            concurrency=1,  # Single request
            timeout=timeout,
            user_agent=user_agent
        ))
        loop.close()

        # Format the result for this single URL
        response_data = {
            'success': True,
            'url': url,
            'previous': previous_data,
            'current': None,
            'has_changed': False,
            'changes': {}
        }

        # Check if URL is in errors or successful results
        if url in result['errors']:
            error = result['errors'][url]
            current_data = {
                'url': url,
                'error_type': error['error_type'],
                'status_code': error['status_code'],
                'message': error['message'],
                'is_error': True
            }
            
            # Include additional details if available
            if 'details' in error:
                current_data['details'] = error['details']
            
            # Include headers if available
            if 'headers' in error:
                current_data['headers'] = error['headers']
            
            response_data['current'] = current_data
            
        elif url in result['successful']:
            success = result['successful'][url]
            current_data = {
                'url': url,
                'status_code': success['status_code'],
                'content_type': success.get('content_type', 'Unknown'),
                'title': success.get('title', 'No title'),
                'is_error': False
            }
            
            if 'links_count' in success:
                current_data['links_count'] = success['links_count']
                
            response_data['current'] = current_data

        # Determine if anything has changed
        if previous_data and response_data['current']:
            changes = {}
            current = response_data['current']
            
            # Check if error status changed
            if previous_data.get('is_error') != current.get('is_error'):
                changes['status_changed'] = {
                    'from': 'error' if previous_data.get('is_error') else 'success',
                    'to': 'error' if current.get('is_error') else 'success'
                }
            
            # Check for specific field changes
            if previous_data.get('status_code') != current.get('status_code'):
                changes['status_code'] = {
                    'from': previous_data.get('status_code'),
                    'to': current.get('status_code')
                }
                
            if previous_data.get('error_type') != current.get('error_type'):
                changes['error_type'] = {
                    'from': previous_data.get('error_type'),
                    'to': current.get('error_type')
                }
                
            if previous_data.get('message') != current.get('message'):
                changes['message'] = {
                    'from': previous_data.get('message'),
                    'to': current.get('message')
                }
                
            if previous_data.get('title') != current.get('title'):
                changes['title'] = {
                    'from': previous_data.get('title'),
                    'to': current.get('title')
                }
                
            response_data['has_changed'] = len(changes) > 0
            response_data['changes'] = changes

        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error during recrawl: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Start the Flask app
    app.run(debug=True) 