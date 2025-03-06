"""
Module for interacting with Perplexity API for search functionality.
"""
import os
import requests
import logging
import json

logger = logging.getLogger(__name__)

def search_perplexity(query):
    """
    Search for information using the Perplexity API.
    
    Args:
        query (str): The search query
        
    Returns:
        list: Search results from Perplexity
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            logger.error("PERPLEXITY_API_KEY not found in environment variables")
            return []
        
        # Perplexity API endpoint
        url = "https://api.perplexity.ai/chat/completions"
        
        # Set up headers with API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Оптимизируем запрос для получения актуальной информации
        system_prompt = (
            "Ты - поисковый ассистент, который ищет только фактическую и актуальную информацию в интернете. "
            "Предоставляй только достоверную и актуальную информацию без предположений и прогнозов. "
            "Если информация запрашивается на будущую дату, ищи самые свежие данные и тренды. "
            "Всегда указывай источники и даты их публикации. "
            "ВАЖНО: При запросах о рейтингах, списках и 'топах' компаний, продуктов или людей, "
            "обязательно используй последние доступные данные - НЕ ДЕЛАЙ ПРЕДПОЛОЖЕНИЙ О БУДУЩЕМ. "
            "Структурируй ответ четко в формате: \n\n"
            "1) КРАТКИЙ ФАКТИЧЕСКИЙ ОТВЕТ (без рассуждений)\n\n"
            "2) ПОДРОБНАЯ ИНФОРМАЦИЯ (с цифрами, датами и фактами)\n\n"
            "3) ИСТОЧНИКИ (с указанием дат публикации)\n\n"
            "При отсутствии точной информации на запрашиваемую дату в будущем, "
            "укажи самые последние доступные данные и объясни, что это самая актуальная информация."
        )
        
        # Определяем специфику запроса для более точного поиска
        topics = {
            "компани": "бизнес, рыночная капитализация, финансы",
            "топ": "рейтинг, список, рыночная капитализация",
            "дорог": "стоимость, цена, капитализация, оценка",
            "рейтинг": "список, статистика, оценка",
            "акци": "фондовый рынок, биржа, инвестиции"
        }
        
        # Добавляем ключевые слова для уточнения запроса
        additional_terms = []
        for key, value in topics.items():
            if key.lower() in query.lower():
                additional_terms.append(value)
        
        search_terms = ", ".join(additional_terms)
        
        user_prompt = (
            f"Найди самую актуальную фактическую информацию по запросу: '{query}'. "
            f"Сосредоточься на следующих аспектах: {search_terms}. "
            f"ОЧЕНЬ ВАЖНО: предоставь ТОЛЬКО ФАКТИЧЕСКИЕ ДАННЫЕ из надежных источников, "
            f"без предположений и прогнозов на будущие периоды. "
            f"Если запрос касается будущей даты, укажи самые свежие имеющиеся данные "
            f"и четко отметь, за какой период они актуальны."
        )
        
        logger.info(f"Подготовлен запрос к Perplexity: {user_prompt}")
        
        # Prepare the request data
        data = {
            "model": "pplx-7b-online",  # Используем модель с доступом к интернету
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.2,  # Низкая температура для более точных ответов
            "max_tokens": 1500  # Увеличиваем лимит токенов для более подробных ответов
        }
        
        logger.info(f"Отправка запроса в Perplexity API: {query}")
        
        # Логируем полный запрос (без API ключа)
        log_data = data.copy()
        logger.info(f"Отправляется запрос в Perplexity API: {json.dumps(log_data, ensure_ascii=False)[:500]}...")
        
        # Make the API call
        response = requests.post(url, headers=headers, json=data, timeout=30)  # Добавляем таймаут
        
        # Check for errors
        response.raise_for_status()
        
        # Parse the response
        response_data = response.json()
        
        # Логируем статус ответа
        logger.info(f"Perplexity API вернул статус: {response.status_code}, ID: {response_data.get('id', 'N/A')}")
        
        # Process and format the search results
        if "choices" in response_data and len(response_data["choices"]) > 0:
            # Extract the content from the response
            content = response_data["choices"][0]["message"]["content"]
            logger.info(f"Получен ответ от Perplexity:\n{content[:500]}...")
            
            # Разделяем контент на разделы для лучшей структуры
            sections = []
            
            # Пытаемся разбить контент по маркерам
            if "1)" in content and "2)" in content:
                # Используем регулярные выражения для более надежного извлечения разделов
                import re
                section_patterns = [
                    r'(?:1\)|1\.)[^\n]*((?:.|\n)*?)(?=2\)|2\.)', # Раздел 1
                    r'(?:2\)|2\.)[^\n]*((?:.|\n)*?)(?=3\)|3\.|\.html|http|$)', # Раздел 2
                    r'(?:3\)|3\.)[^\n]*((?:.|\n)*)$' # Раздел 3
                ]
                
                for pattern in section_patterns:
                    match = re.search(pattern, content)
                    if match:
                        section_text = match.group(1).strip()
                        if section_text:
                            sections.append(section_text)
                
                if not sections:  # Если регулярки не сработали
                    sections = [s.strip() for s in content.split('\n\n') if s.strip()]
            else:
                # Если контент не был структурирован по нашему запросу
                sections = [s.strip() for s in content.split('\n\n') if s.strip()]
            
            # Логируем найденные секции
            logger.info(f"Разделено на {len(sections)} секций")
            for i, section in enumerate(sections[:3]):
                logger.info(f"Секция {i+1} (до 100 символов): {section[:100]}...")
            
            # Создаем структурированный результат с дополнительной обработкой
            structured_result = {
                "full_content": content,
                "sections": sections,
                "timestamp": response_data.get("created", 0),
                "model": response_data.get("model", "pplx-7b-online"),
                "has_sources": "источник" in content.lower() or "источники" in content.lower()
            }
            
            # Пытаемся извлечь источники отдельно
            sources = []
            if "источник" in content.lower() or "источники" in content.lower():
                source_section = ""
                if len(sections) >= 3:
                    source_section = sections[-1]
                elif "источник" in content.lower():
                    match = re.search(r'(?:источник|источники)[^\n]*(?:\n.*)*', content, re.IGNORECASE)
                    if match:
                        source_section = match.group(0)
                
                # Извлекаем URL из текста
                urls = re.findall(r'https?://[^\s)"\\]+', source_section)
                if urls:
                    sources = urls
                    structured_result["sources"] = sources
                    logger.info(f"Извлечены источники: {sources}")
            
            # Возвращаем как полный ответ, так и структурированные секции
            results = [
                {"snippet": content},
                {"structured": structured_result}
            ]
            
            logger.info(f"Подготовлены результаты поиска от Perplexity API: {len(sections)} секций и {len(sources)} источников")
            return results
        else:
            logger.warning(f"Результаты поиска не найдены в ответе Perplexity: {response_data}")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса API: {e}")
        # Попробуем еще раз с другой моделью в случае ошибки
        return fallback_search(query)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в search_perplexity: {e}")
        return []


def fallback_search(query):
    """
    Резервный метод поиска в случае ошибки основного метода.
    
    Args:
        query (str): Поисковый запрос
        
    Returns:
        list: Результаты поиска
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            return []
        
        # Используем более простую модель
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3-sonar-small-online",  # Альтернативная модель
            "messages": [
                {
                    "role": "user",
                    "content": f"Найди информацию по запросу: {query}"
                }
            ],
            "temperature": 0.1
        }
        
        logger.info(f"Использование резервного метода поиска для: {query}")
        response = requests.post(url, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        
        response_data = response.json()
        if "choices" in response_data and len(response_data["choices"]) > 0:
            content = response_data["choices"][0]["message"]["content"]
            return [{"snippet": content}]
        
        return []
    except Exception as e:
        logger.error(f"Ошибка в резервном методе поиска: {e}")
        return []
    