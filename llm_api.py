"""
Module for interacting with Claude 3.5 Haiku API.
"""
import os
import requests
import logging
import json

logger = logging.getLogger(__name__)

def query_llm(input_text, system_prompt=None, detect_search_needs=False):
    """
    Send a query to Claude 3.5 Haiku and get a response.
    
    Args:
        input_text (str): The input text to send to the LLM
        system_prompt (str, optional): System prompt to guide the model's behavior
        detect_search_needs (bool, optional): If True, the model will analyze if search is needed
        
    Returns:
        str or tuple: The response from the LLM, or a tuple with (response, search_needed, search_query)
                      if detect_search_needs is True
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            logger.error("CLAUDE_API_KEY not found in environment variables")
            return "Ошибка: API ключ Claude не найден. Пожалуйста, установите переменную окружения CLAUDE_API_KEY."
        
        # Короткий системный промпт для уменьшения вероятности ошибок
        if system_prompt is None or len(system_prompt) > 500:
            system_prompt = "Ты - полезный ассистент. Отвечай на русском языке, используя предоставленную информацию."
        
        # Ограничиваем длину пользовательского ввода
        if len(input_text) > 5000:
            logger.warning(f"Input text too long ({len(input_text)} chars), truncating to 5000 chars")
            input_text = input_text[:5000]
        
        # Claude API endpoint
        url = "https://api.anthropic.com/v1/messages"
        
        # Set up headers with API key
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Prepare messages - только сообщения пользователя
        messages = [
            {"role": "user", "content": input_text}
        ]
        
        # Prepare the request data - системный промпт как отдельный параметр
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": messages
        }
        
        # Логируем запрос для отладки
        logger.info(f"Sending request to Claude API with input length: {len(input_text)}")
        
        # Make the API call
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
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
                
                # Если нужно определить необходимость поиска
                if detect_search_needs:
                    # Упрощенный анализ необходимости поиска
                    search_needed = False
                    search_query = ""
                    
                    # Простая эвристика для определения необходимости поиска
                    search_keywords = ["актуальн", "последн", "текущ", "свеж", "нов"]
                    if any(keyword in input_text.lower() for keyword in search_keywords):
                        search_needed = True
                        search_query = input_text
                    
                    return response_text, search_needed, search_query
                
                return response_text
            else:
                logger.error(f"Unexpected response format: {response_data}")
                return "Ошибка: Неожиданный формат ответа от API Claude."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            return f"Ошибка при обращении к API Claude: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return "Ошибка при обработке ответа от API Claude."
            
    except Exception as e:
        logger.error(f"Unexpected error in query_llm: {e}")
        return f"Произошла неожиданная ошибка: {str(e)}"
