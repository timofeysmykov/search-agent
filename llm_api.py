"""
Module for interacting with Claude 3.5 Haiku API.
"""
import os
import requests
import logging
import json

logger = logging.getLogger(__name__)

def generate_test_response(input_text):
    """
    Генерирует тестовый ответ, когда API недоступен или работаем в тестовом режиме.
    
    Args:
        input_text (str): Входной текст запроса
        
    Returns:
        str: Сгенерированный ответ
    """
    input_lower = input_text.lower()
    
    # Базовый ответ для большинства запросов
    default_response = """Это тестовый ответ от AI Agent. В настоящий момент я работаю в тестовом режиме без доступа к API Claude.
Я могу симулировать ответы на типичные запросы. Для полноценной работы потребуется настроить доступ к API Claude."""
    
    # Ответы на приветствия
    if any(greeting in input_lower for greeting in ['привет', 'здравствуй', 'добрый день', 'доброе утро', 'добрый вечер']):
        return """Здравствуйте! Я AI Agent, работающий в тестовом режиме. 
Чем могу помочь вам сегодня? Обратите внимание, что сейчас я функционирую без доступа к API Claude."""
    
    # Ответы на запросы о новостях
    if any(word in input_lower for word in ['новост', 'событи', 'произошло', 'случилось']):
        return """В тестовом режиме я не могу предоставить актуальные новости, так как не имею доступа к интернету.
В реальном режиме работы я бы выполнил поиск последних новостей через Perplexity API и предоставил вам актуальную информацию.
Пожалуйста, настройте API ключи для полноценной работы."""
    
    # Ответы на запросы о погоде
    if any(word in input_lower for word in ['погод', 'температур', 'осадк', 'дожд', 'снег']):
        return """В тестовом режиме я не могу предоставить актуальный прогноз погоды, так как не имею доступа к метеорологическим данным.
В полноценном режиме я бы выполнил поиск через Perplexity API и предоставил вам точную информацию о погоде в указанном регионе.
Для получения реальных данных требуется настройка API ключей."""
    
    # Ответы на запросы о курсах валют и финансах
    if any(word in input_lower for word in ['курс', 'валют', 'доллар', 'евро', 'акци', 'биткоин', 'крипто']):
        return """В тестовом режиме я не могу предоставить актуальные данные о курсах валют или финансовых рынках.
В полноценном режиме работы я бы получил последние котировки через Perplexity API и представил вам актуальную информацию.
Для получения реальных данных требуется настройка API ключей."""
    
    # Ответы на технические и программные запросы
    if any(word in input_lower for word in ['код', 'программ', 'python', 'javascript', 'java', 'разработ']):
        return """В тестовом режиме я могу предоставить общую информацию о программировании, но не могу выполнять сложный анализ кода или создавать оптимальные программные решения.
В полноценном режиме работы я мог бы дать более детальные ответы с использованием возможностей Claude 3.5 Haiku.
Для получения более качественных технических ответов требуется настройка API ключей."""
    
    # Ответы на запросы об AI и машинном обучении
    if any(word in input_lower for word in ['искусств', 'интеллект', 'ai', 'нейросет', 'машинн', 'обучени']):
        return """В тестовом режиме я могу предоставить базовую информацию об искусственном интеллекте и машинном обучении.
Искусственный интеллект - это область компьютерных наук, направленная на создание систем, способных выполнять задачи, требующие человеческого интеллекта.
Для более глубокого и актуального анализа требуется настройка API ключей для доступа к возможностям Claude 3.5 Haiku."""
    
    # Ответы на запросы о помощи или возможностях
    if any(word in input_lower for word in ['помо', 'умеешь', 'можешь', 'способ', 'функци']):
        return """Я - AI Agent, работающий в тестовом режиме. Мои возможности:
1. Имитация ответов на базовые запросы
2. Демонстрация интерфейса взаимодействия
3. Симуляция работы с поисковыми запросами

В полноценном режиме с настроенными API ключами я смогу:
1. Отвечать на сложные вопросы с помощью Claude 3.5 Haiku
2. Выполнять актуальные поисковые запросы через Perplexity
3. Предоставлять точную и актуальную информацию по широкому кругу тем"""
    
    # Для всех остальных запросов
    return default_response

def query_llm(input_text, system_prompt=None, detect_search_needs=False, **kwargs):
    """
    Send a query to Claude 3.5 Haiku and get a response.
    
    Args:
        input_text (str): The input text to send to the LLM
        system_prompt (str, optional): System prompt to guide the model's behavior
        detect_search_needs (bool, optional): If True, the model will analyze if search is needed
        **kwargs: Additional keyword arguments, including test_mode for backwards compatibility
        
    Returns:
        str or tuple: The response from the LLM, or a tuple with (response, search_needed, search_query)
                      if detect_search_needs is True
    """
    # Для совместимости между разными версиями кода
    test_mode = kwargs.get('test_mode', False)
    try:
        # Проверяем тестовый режим
        if test_mode:
            logger.info("Using test mode for LLM query")
            response_text = generate_test_response(input_text)
            # Если проверяем необходимость поиска в тестовом режиме, всегда возвращаем True
            if detect_search_needs:
                return response_text, True, input_text
            return response_text
        
        # Get API key from environment variable
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            logger.error("CLAUDE_API_KEY not found in environment variables")
            if test_mode:
                # В тестовом режиме при отсутствии ключа используем тестовые ответы
                return generate_test_response(input_text)
            return "Ошибка: API ключ Claude не найден. Пожалуйста, установите переменную окружения CLAUDE_API_KEY."
        
        # Системный промпт более информативный, но всё ещё компактный
        if system_prompt is None:
            system_prompt = """Ты - полезный ассистент, отвечающий на русском языке.
Если информация может быть устаревшей или тебе нужны актуальные данные для ответа - явно об этом сообщи.
Отвечай точно, информативно и полезно."""
        elif len(system_prompt) > 800:
            logger.warning(f"System prompt too long ({len(system_prompt)} chars), truncating")
            system_prompt = system_prompt[:800]
        
        # Ограничиваем длину пользовательского ввода
        if len(input_text) > 8000:
            logger.warning(f"Input text too long ({len(input_text)} chars), truncating")
            input_text = input_text[:8000]
        
        # Claude API endpoint
        url = "https://api.anthropic.com/v1/messages"
        
        # Set up headers with API key
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Prepare standard messages
        messages = [
            {"role": "user", "content": input_text}
        ]
        
        # Отдельная логика для определения необходимости поиска
        if detect_search_needs:
            # Особый промпт для определения необходимости поиска
            search_system_prompt = """Ты - полезный ассистент, который анализирует запросы.
Твоя задача - определить, требуется ли для ответа на запрос актуальная информация из интернета.
Если запрос требует актуальные данные о погоде, курсах валют, ценах, новостях, рейтингах или других 
динамически меняющихся данных - ответь "ДА" в первой строке.
Если запрос касается общих знаний, определений, неизменной информации, принципов работы чего-либо или
исторических фактов, ответь "НЕТ" в первой строке.
После этого на новой строке напиши оптимизированный поисковый запрос, если поиск нужен.
Отвечай только в указанном формате."""
            
            # Подготовка данных для определения необходимости поиска
            search_data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 300,
                "system": search_system_prompt,
                "messages": messages
            }
            
            logger.info("Sending request to Claude API to determine search necessity")
            
            try:
                search_response = requests.post(url, headers=headers, json=search_data, timeout=15)
                
                if search_response.status_code == 200:
                    search_response_data = search_response.json()
                    if "content" in search_response_data and len(search_response_data["content"]) > 0:
                        decision_text = search_response_data["content"][0]["text"]
                        
                        # Разбиваем результат на строки для анализа
                        decision_lines = decision_text.strip().split('\n')
                        first_line = decision_lines[0].upper() if decision_lines else ""
                        
                        # Определяем необходимость поиска
                        search_needed = "ДА" in first_line
                        
                        # Определяем поисковый запрос
                        search_query = ""
                        if len(decision_lines) > 1 and search_needed:
                            search_query = decision_lines[1].strip()
                        else:
                            search_query = input_text
                            
                        logger.info(f"Search needed: {search_needed}, Search query: {search_query}")
                    else:
                        # В случае ошибки разбора ответа по умолчанию считаем, что поиск нужен
                        search_needed = True
                        search_query = input_text
                        logger.warning("Unexpected search decision format, defaulting to search=True")
                else:
                    # В случае ошибки API по умолчанию считаем, что поиск нужен
                    search_needed = True
                    search_query = input_text
                    logger.warning(f"Error from Claude API when determining search necessity: {search_response.status_code}")
            
            except Exception as e:
                # В случае исключения при запросе по умолчанию считаем, что поиск нужен
                search_needed = True
                search_query = input_text
                logger.error(f"Exception when determining search necessity: {e}")
        
        # Prepare the request data для основного ответа
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1500,  # Увеличено для более полных ответов
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.2  # Пониженная температура для более точных ответов
        }
        
        # Логируем запрос для отладки
        logger.info(f"Sending main request to Claude API with input length: {len(input_text)}")
        
        # Make the API call
        try:
            response = requests.post(url, headers=headers, json=data, timeout=45)  # Увеличенный таймаут
            
            # Логируем ответ для отладки
            logger.info(f"Claude API response status: {response.status_code}")
            
            # Обрабатываем ошибки
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Claude API error: {response.status_code} - {error_text}")
                return f"Ошибка при обращении к API Claude: {response.status_code}. Проверьте API ключ и формат запроса."
        
            # Успешный ответ - обрабатываем
            response_data = response.json()
            
            # Проверяем формат ответа
            if "content" in response_data and len(response_data["content"]) > 0:
                response_text = response_data["content"][0]["text"]
                logger.info(f"Received response from Claude API with length: {len(response_text)}")
                
                # Если была запущена проверка необходимости поиска, возвращаем кортеж
                if detect_search_needs:
                    return response_text, search_needed, search_query
                
                return response_text
            else:
                logger.error(f"Unexpected response format: {response_data}")
                return "Ошибка: Неожиданный формат ответа от API Claude."
                
        except requests.exceptions.Timeout:
            logger.error("Timeout when querying Claude API")
            return "Ошибка: Превышено время ожидания ответа от API Claude. Пожалуйста, попробуйте позже."
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            return f"Ошибка при обращении к API Claude: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return "Ошибка при обработке ответа от API Claude."
            
    except Exception as e:
        logger.error(f"Unexpected error in query_llm: {e}")
        return f"Произошла неожиданная ошибка: {str(e)}"
