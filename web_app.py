"""
Web interface for the AI agent application using Flask.
"""
import os
import logging
import sqlite3
import json
import uuid
import datetime
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from llm_api import query_llm
from search_api import search_perplexity
from utils import process_input, format_output, needs_search, combine_input
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/my-app/build', static_url_path='')

# Включаем CORS для всех маршрутов, чтобы React-приложение могло обращаться к API
CORS(app)

# Добавляем catch-all маршрут для любых путей, чтобы React-Router мог работать корректно
@app.route('/<path:path>')
def static_file(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, 'index.html')

# Глобальная переменная для контроля тестового режима
TEST_MODE = False

# Конфигурация базы данных
# Путь к базе данных будет браться из переменной окружения, если она установлена,
# иначе база будет размещена в том же каталоге, что и приложение
# При деплое на VPS установите переменную DB_PATH в каталог с постоянным хранилищем
DB_PATH = os.getenv('DB_PATH', os.path.dirname(__file__))
DATABASE = os.path.join(DB_PATH, 'chat_history.db')

# Примечание: SQLite подходит для небольших приложений, но для продакшена на VPS
# рекомендуется использовать более надежные решения, такие как PostgreSQL или MySQL

def get_db():
    """Соединение с базой данных на протяжении запроса."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Закрываем соединение с базой данных в конце запроса."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Инициализация базы данных."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    """Выполнение запроса к базе данных."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def save_chat(user_input, response, search_performed, test_mode):
    """Сохранение сообщения чата в базу данных."""
    db = get_db()
    chat_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    db.execute(
        'INSERT INTO chats (id, timestamp, user_input, response, search_performed, test_mode) VALUES (?, ?, ?, ?, ?, ?)',
        (chat_id, timestamp, user_input, response, 1 if search_performed else 0, 1 if test_mode else 0)
    )
    db.commit()
    return chat_id

def get_chat_history():
    """Получение истории чатов."""
    chats = query_db('SELECT * FROM chats ORDER BY timestamp DESC')
    return [dict(chat) for chat in chats]

def get_chat_by_id(chat_id):
    """Получение чата по ID."""
    chat = query_db('SELECT * FROM chats WHERE id = ?', [chat_id], one=True)
    return dict(chat) if chat else None

@app.route('/', methods=['GET'])
def home():
    """Serve the React app - only in production.
    In development, React app is served by its own dev server."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint to process user queries."""
    try:
        # Get the query from the request
        data = request.json
        user_input = data.get('query', '')
        
        # Получаем флаг тестового режима из запроса, если он есть
        test_mode = data.get('test_mode', TEST_MODE)
        
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
            search_results = search_perplexity(processed_input, test_mode=test_mode)
            search_performed = bool(search_results)
            
            if search_results:
                logger.info(f"Получены результаты поиска длиной {len(search_results)} символов")
            else:
                logger.warning(f"Поиск выполнен, но результаты не получены для запроса: {processed_input}")
        
        # Combine input and search results
        llm_input = combine_input(processed_input, search_results)
        logger.info(f"Подготовлен запрос к LLM длиной {len(llm_input)} символов")
        
        # Query the LLM - не используем параметр test_mode для совместимости с серверной версией
        # Если нужен тестовый режим, обрабатываем его отдельно
        if test_mode:
            # Генерируем тестовый ответ без прямого использования test_mode в query_llm
            from llm_api import generate_test_response
            response = generate_test_response(processed_input)
        else:
            response = query_llm(llm_input, detect_search_needs=False)
        
        # Format the response
        formatted_response = format_output(response)
        
        # Сохраняем диалог в базу данных
        chat_id = save_chat(user_input, formatted_response, search_performed, test_mode)
        
        # Return the response
        return jsonify({
            'id': chat_id,
            'query': user_input,
            'response': formatted_response,
            'search_performed': search_performed,
            'test_mode': test_mode,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing API request: {e}")
        return jsonify({'error': str(e)}), 500

# Функция для обеспечения наличия build директории для React-приложения
def ensure_react_build_directory():
    """Проверяет наличие build директории для React-приложения и создает её при необходимости."""
    build_dir = os.path.join(os.path.dirname(__file__), 'frontend/my-app/build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir, exist_ok=True)

def ensure_schema_file():
    """Проверяет наличие файла schema.sql и создает его при необходимости."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    schema_content = '''
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_input TEXT NOT NULL,
    response TEXT NOT NULL,
    search_performed INTEGER NOT NULL,
    test_mode INTEGER NOT NULL
);
'''
    
    # Проверяем, существует ли файл схемы
    if not os.path.exists(schema_path):
        # Создаем директорию для файла схемы, если её нет
        schema_dir = os.path.dirname(schema_path)
        if not os.path.exists(schema_dir):
            os.makedirs(schema_dir, exist_ok=True)
            
        # Создаем файл схемы
        with open(schema_path, 'w') as f:
            f.write(schema_content)
            
    # Проверяем права доступа к базе данных
    db_dir = os.path.dirname(DATABASE)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            print(f"Создана директория для базы данных: {db_dir}")
        except Exception as e:
            print(f"Ошибка при создании директории для базы данных: {e}")
            print("Проверьте права доступа или установите переменную окружения DB_PATH")

# Статус тестового режима без создания нового чата
@app.route('/api/test_mode_status', methods=['GET'])
def test_mode_status():
    """Получить текущий статус тестового режима без создания чата"""
    global TEST_MODE
    
    # Также проверяем наличие API ключей для метки принудительного тестового режима
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
    forced_test_mode = not (claude_api_key and perplexity_api_key)
    
    # Если отсутствуют API ключи, принудительно включаем тестовый режим
    current_test_mode = TEST_MODE or forced_test_mode
    
    return jsonify({
        'test_mode': current_test_mode,
        'forced_test_mode': forced_test_mode,
        'message': f"Тестовый режим {'включен' if current_test_mode else 'выключен'}"
    })

# Новый маршрут для переключения тестового режима
@app.route('/api/test_mode', methods=['POST'])
def toggle_test_mode():
    """Включить или отключить тестовый режим"""
    global TEST_MODE
    data = request.json
    enabled = data.get('enabled', False)
    TEST_MODE = bool(enabled)
    return jsonify({
        'test_mode': TEST_MODE,
        'message': f"Тестовый режим {'включен' if TEST_MODE else 'выключен'}"
    })

# Маршруты для работы с историей чатов
@app.route('/api/history', methods=['GET'])
def get_history():
    """Получить историю чатов"""
    try:
        history = get_chat_history()
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        logger.error(f"Ошибка при получении истории чатов: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Получить конкретный чат по ID"""
    try:
        chat = get_chat_by_id(chat_id)
        if chat:
            return jsonify({
                'success': True,
                'chat': chat
            })
        else:
            return jsonify({'error': 'Чат не найден'}), 404
    except Exception as e:
        logger.error(f"Ошибка при получении чата: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Удалить чат по ID"""
    try:
        db = get_db()
        db.execute('DELETE FROM chats WHERE id = ?', [chat_id])
        db.commit()
        return jsonify({
            'success': True,
            'message': 'Чат успешно удален'
        })
    except Exception as e:
        logger.error(f"Ошибка при удалении чата: {e}")
        return jsonify({'error': str(e)}), 500

# Функция для сборки React-приложения
def build_react_app():
    """Собирает React-приложение для production"""
    try:
        import subprocess
        import os
        frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend/my-app')
        if os.path.exists(frontend_dir):
            print(f"Сборка React-приложения из директории {frontend_dir}...")
            subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir, check=True)
            print("React-приложение успешно собрано.")
            return True
        else:
            print(f"Директория React-приложения не найдена: {frontend_dir}")
            return False
    except Exception as e:
        print(f"Ошибка при сборке React-приложения: {e}")
        return False

if __name__ == '__main__':
    # Выводим информацию о расположении базы данных
    print(f"База данных будет размещена по пути: {DATABASE}")
    if os.getenv('DB_PATH'):
        print(f"Используется кастомный путь из DB_PATH: {os.getenv('DB_PATH')}")
    else:
        print("Используется путь по умолчанию. Для размещения на VPS рекомендуется")
        print("установить переменную окружения DB_PATH=/путь/к/постоянной/директории")
    
    # Проверяем наличие и создаем файл схемы базы данных
    ensure_schema_file()
    
    # Инициализируем базу данных
    try:
        init_db()
        print("База данных успешно инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        print("Проверьте права доступа к директории базы данных и переменную DB_PATH")
    
    # Check for API keys
    missing_keys = []
    if not os.getenv('CLAUDE_API_KEY'):
        missing_keys.append('CLAUDE_API_KEY')
    if not os.getenv('PERPLEXITY_API_KEY'):
        missing_keys.append('PERPLEXITY_API_KEY')
    
    # Если API ключи отсутствуют, включаем тестовый режим автоматически
    if missing_keys:
        TEST_MODE = True
        print(f"ВНИМАНИЕ: Следующие API ключи не найдены: {', '.join(missing_keys)}")
        print("Автоматически включен тестовый режим. Для полноценной работы установите API ключи.")
    else:
        print("API ключи найдены. Приложение работает в обычном режиме.")
    
        # Создаем директорию для React-сборки, если она не существует
    ensure_react_build_directory()
    
    # Проверяем наличие собранного React-приложения
    build_dir = os.path.join(os.path.dirname(__file__), 'frontend/my-app/build')
    index_html = os.path.join(build_dir, 'index.html')
    if not os.path.exists(index_html):
        print("\n\033[33mВнимание: React-приложение не собрано!\033[0m")
        print("\033[33mДля сборки React-приложения выполните следующие команды:\033[0m")
        print("\033[33mcd frontend/my-app && npm run build\033[0m")
        print("\033[33mИли запустите функцию build_react_app() в коде.\033[0m")
        print("\033[33mПока React-приложение не собрано, вы можете запустить его в режиме разработки:\033[0m")
        print("\033[33mcd frontend/my-app && npm run dev\033[0m")
    else:
        print("React-приложение собрано и доступно по адресу http://localhost:5001")
    
    # Для сборки React-приложения раскомментируйте эту строку
    # build_react_app()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)
