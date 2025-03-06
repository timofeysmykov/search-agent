"""
Web interface for the AI agent application using Flask.
"""
import os
import logging
from flask import Flask, request, render_template, jsonify
from llm_api import query_llm
from search_api import search_perplexity
from utils import process_input, format_output, needs_search, combine_input

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint to process user queries."""
    try:
        # Get the query from the request
        data = request.json
        user_input = data.get('query', '')
        
        if not user_input:
            return jsonify({'error': 'No query provided'}), 400
        
        # Process the input
        processed_input = process_input(user_input)
        if not processed_input:
            return jsonify({'error': 'Error processing input'}), 500
        
        # Determine if search is needed
        search_performed = False
        search_results = ""
        
        # Всегда выполняем поиск, так как needs_search всегда возвращает True
        if needs_search(processed_input):
            logger.info(f"Выполняю поиск для запроса: {processed_input}")
            search_results = search_perplexity(processed_input)
            search_performed = bool(search_results)
            
            if search_results:
                logger.info(f"Получены результаты поиска длиной {len(search_results)} символов")
            else:
                logger.warning(f"Поиск выполнен, но результаты не получены для запроса: {processed_input}")
        
        # Combine input and search results
        llm_input = combine_input(processed_input, search_results)
        logger.info(f"Подготовлен запрос к LLM длиной {len(llm_input)} символов")
        
        # Query the LLM
        response = query_llm(llm_input)
        
        # Format the response
        formatted_response = format_output(response)
        
        # Return the response
        return jsonify({
            'query': user_input,
            'response': formatted_response,
            'search_performed': search_performed
        })
        
    except Exception as e:
        logger.error(f"Error processing API request: {e}")
        return jsonify({'error': str(e)}), 500

# Проверяем наличие директории templates
def ensure_template_directory():
    """Проверяет наличие директории templates и создает её при необходимости."""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)

if __name__ == '__main__':
    # Проверяем наличие директории templates
    ensure_template_directory()
    
    # Check for API keys
    missing_keys = []
    if not os.getenv('CLAUDE_API_KEY'):
        missing_keys.append('CLAUDE_API_KEY')
    if not os.getenv('PERPLEXITY_API_KEY'):
        missing_keys.append('PERPLEXITY_API_KEY')
    
    if missing_keys:
        print(f"ВНИМАНИЕ: Следующие API ключи не найдены: {', '.join(missing_keys)}")
        print("Пожалуйста, установите их как переменные окружения или в файле .env")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)
