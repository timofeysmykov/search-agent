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
        
        # Claude API endpoint
        url = "https://api.anthropic.com/v1/messages"
        
        # Set up headers with API key
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Prepare messages
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user message
        messages.append({"role": "user", "content": input_text})
        
        # Prepare the request data
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1000,
            "messages": messages
        }
        
        logger.info(f"Sending request to Claude API with input length: {len(input_text)}")
        
        # Make the API call
        response = requests.post(url, headers=headers, json=data)
        
        # Check for errors
        response.raise_for_status()
        
        # Parse the response
        response_data = response.json()
        
        # Extract the text from the response
        if "content" in response_data and len(response_data["content"]) > 0:
            response_text = response_data["content"][0]["text"]
            logger.info(f"Received response from Claude API with length: {len(response_text)}")
            
            # If we need to detect search needs
            if detect_search_needs:
                # Send another request to analyze if search is needed
                search_analysis_prompt = f"""
                Проанализируй следующий запрос пользователя и определи:
                1. Требуется ли для ответа на этот запрос поиск актуальной информации в интернете?
                2. Если да, сформулируй оптимальный поисковый запрос для получения нужной информации.
                
                Запрос пользователя: "{input_text}"
                
                Ответь в формате JSON:
                {{
                    "search_needed": true/false,
                    "search_query": "оптимизированный поисковый запрос"
                }}
                
                Верни только JSON без дополнительного текста.
                """
                
                search_analysis = query_llm(search_analysis_prompt)
                
                try:
                    # Попытка извлечь JSON из ответа
                    import re
                    json_match = re.search(r'({.*})', search_analysis, re.DOTALL)
                    if json_match:
                        search_data = json.loads(json_match.group(1))
                        search_needed = search_data.get("search_needed", False)
                        search_query = search_data.get("search_query", "")
                        
                        logger.info(f"Search analysis: needed={search_needed}, query='{search_query}'" if search_query else "Search not needed")
                        
                        return response_text, search_needed, search_query
                except Exception as e:
                    logger.error(f"Error parsing search analysis: {e}")
            
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
