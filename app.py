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

        # Format the results
        formatted_results = []
        for url, error in result.items():
            formatted_results.append({
                'url': url,
                'error_type': error['error_type'],
                'status_code': error['status_code'],
                'message': error['message']
            })

        return jsonify({
            'success': True,
            'errors_found': len(formatted_results),
            'results': formatted_results
        })

    except Exception as e:
        logging.error(f"Error during crawl: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Start the Flask app
    app.run(debug=True) 