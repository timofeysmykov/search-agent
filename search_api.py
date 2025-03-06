"""
Module for interacting with Perplexity API for search functionality.
"""
import os
import requests
import logging
import json
import time
import re

logger = logging.getLogger(__name__)

def search_perplexity(query):
    """
    Поиск информации с использованием Perplexity API.
    
    Args:
        query (str): Поисковый запрос
        
    Returns:
        str: Результаты поиска в текстовом формате
    """
    logger.info(f"Запуск поиска для запроса: '{query}'")
    
    try:
        # Получаем API ключ из переменных окружения
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            logger.error("PERPLEXITY_API_KEY не найден в переменных окружения")
            return "Ошибка: API ключ Perplexity не настроен."
        
        # Настраиваем URL и заголовки для запроса
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
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
        
        # Формируем запрос к API с использованием модели "sonar" согласно документации
        data = {
            "model": "sonar",  # Официальная модель Perplexity из документации
            "messages": [
                {
                    "role": "system",
                    "content": "Найди актуальную информацию по запросу пользователя. Предоставь только проверенные факты."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.2,     # Значение по умолчанию из документации
            "top_p": 0.9,           # Значение по умолчанию из документации
            "max_tokens": 1000      # Ограничение длины ответа
        }
        
        logger.info(f"Отправка запроса к Perplexity API с использованием модели 'sonar'")
        
        # Отправляем запрос с замером времени
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=60)
        request_time = time.time() - start_time
        
        # Логируем информацию о запросе
        logger.info(f"Получен ответ от API за {request_time:.2f} сек. Статус: {response.status_code}")
        
        # Обрабатываем ошибочные статусы
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_detail = json.dumps(error_data, ensure_ascii=False)
            except:
                error_detail = response.text[:500] if response.text else "Нет деталей ошибки"
            
            logger.error(f"Ошибка Perplexity API: {response.status_code}")
            logger.error(f"Детали ошибки: {error_detail}")
            
            # Пробуем использовать резервный метод поиска
            logger.info("Переключение на резервный метод поиска...")
            return fallback_search(query)
        
        # Parse the response
        response_data = response.json()
        
        # Логируем статус ответа
        logger.info(f"Perplexity API вернул ID: {response_data.get('id', 'N/A')}")
        
        # Process and format the search results
        if "choices" in response_data and len(response_data["choices"]) > 0:
            # Extract the content from the response
            content = response_data["choices"][0]["message"]["content"]
            logger.info(f"Получен ответ от Perplexity длиной {len(content)} символов")
            logger.info(f"Начало ответа: {content[:200]}...")
            
            # Разделяем контент на разделы для лучшей структуры
            sections = []
            
            # Пытаемся разбить контент по маркерам
            if "1)" in content and "2)" in content:
                # Используем регулярные выражения для более надежного извлечения разделов
                section_patterns = [
                    r'(?:1\)|1\.)[^\n]*((?:.|\n)*?)(?=2\)|2\.)', # Раздел 1
                    r'(?:2\)|2\.)[^\n]*((?:.|\n)*?)(?=3\)|3\.|ИСТОЧНИКИ|Источники|источники|$)', # Раздел 2
                    r'(?:3\)|3\.)[^\n]*((?:.|\n)*?)(?=ИСТОЧНИКИ|Источники|источники|$)', # Раздел 3
                    r'(?:ИСТОЧНИКИ|Источники|источники)[^\n]*((?:.|\n)*)$' # Раздел источников
                ]
                
                for pattern in section_patterns:
                    match = re.search(pattern, content)
                    if match:
                        section_text = match.group(1).strip()
                        if section_text:
                            sections.append(section_text)
                            logger.info(f"Найден раздел по шаблону: {pattern[:30]}... длиной {len(section_text)} символов")
                
                if not sections:  # Если регулярки не сработали
                    logger.warning("Регулярные выражения не смогли извлечь разделы, использую разделение по параграфам")
                    sections = [s.strip() for s in content.split('\n\n') if s.strip()]
            else:
                # Если контент не был структурирован по нашему запросу
                logger.info("Контент не содержит маркеров разделов, использую разделение по параграфам")
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
            
            # Преобразуем результаты в текстовый формат для использования в системном промпте
            text_result = content
            
            # Добавляем форматирование для лучшей читаемости
            if len(sources) > 0:
                text_result += "\n\nИСТОЧНИКИ:\n" + "\n".join(sources)
            
            logger.info(f"Подготовлены результаты поиска от Perplexity API: {len(sections)} секций и {len(sources)} источников")
            return text_result
        else:
            logger.warning(f"Результаты поиска не найдены в ответе Perplexity: {response_data}")
            return "Результаты поиска не найдены."
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса API: {e}")
        # Попробуем еще раз с другой моделью в случае ошибки
        logger.info("Используем резервный метод поиска после ошибки основного метода")
        fallback_result = fallback_search(query)
        return fallback_result
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        return "Ошибка при обработке результатов поиска."
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в search_perplexity: {e}")
        return "Произошла непредвиденная ошибка при поиске."


def fallback_search(query):
    """
    Резервный метод поиска с использованием наиболее стабильной модели.
    Применяется, когда основной метод поиска не работает.
    
    Args:
        query (str): Поисковый запрос от пользователя
        
    Returns:
        str: Результаты поиска в текстовом формате или сообщение об ошибке
    """
    logger.info(f"Запуск резервного метода поиска для запроса: '{query}'")
    
    try:
        # Получаем API ключ из переменных окружения
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            logger.error("PERPLEXITY_API_KEY не найден в переменных окружения")
            return "К сожалению, невозможно выполнить поиск. API ключ не настроен."
        
        # URL и заголовки для API Perplexity
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Максимально простой и стабильный запрос с моделью sonar
        data = {
            "model": "sonar",  # Используем модель sonar из документации
            "messages": [
                {
                    "role": "user",
                    "content": query  # Используем прямой запрос пользователя
                }
            ],
            "temperature": 0.2,  # Значение по умолчанию
            "top_p": 0.9,  # Значение по умолчанию
            "max_tokens": 500  # Ограниченное количество токенов для стабильности
        }
        
        # Отладочное логирование
        logger.info(f"Резервный метод: запрос в Perplexity API с моделью {data['model']}")
        logger.info(f"Параметры запроса: температура={data['temperature']}, max_tokens={data['max_tokens']}")
        
        try:
            # Отправляем запрос с увеличенным таймаутом для стабильности
            start_time = time.time()
            response = requests.post(url, headers=headers, json=data, timeout=60)
            request_time = time.time() - start_time
            
            # Подробное логирование ответа
            logger.info(f"Получен ответ от Perplexity API за {request_time:.2f} сек. Статус: {response.status_code}")
            
            # Детальная обработка кодов статуса
            if response.status_code != 200:
                error_text = response.text[:200] if response.text else "Нет текста ошибки"
                logger.error(f"Ошибка Perplexity API: {response.status_code} - {error_text}")
                
                # Генерируем информативный ответ на основе типа ошибки
                if response.status_code == 400:
                    return "К сожалению, запрос был некорректным. Попробуйте изменить формулировку."
                elif response.status_code == 401:
                    return "Проблема с авторизацией API. Пожалуйста, проверьте настройки API ключа."
                elif response.status_code == 429:
                    return "Превышен лимит запросов к API. Пожалуйста, попробуйте позже."
                else:
                    return f"Не удалось получить информацию. Ошибка сервиса: {response.status_code}."
            
            # Обработка успешного ответа с дополнительными проверками
            try:
                response_data = response.json()
                
                # Проверяем все необходимые поля в ответе
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                        content = response_data["choices"][0]["message"]["content"]
                        content_length = len(content)
                        
                        # Проверяем качество ответа
                        if content_length < 10:
                            logger.warning(f"Слишком короткий ответ от API: '{content}'")
                            return "Не удалось найти достаточно информации по вашему запросу."
                        
                        logger.info(f"Успешно получен ответ от Perplexity длиной {content_length} символов")
                        return content
                
                # Лог неожиданного формата ответа
                logger.warning(f"Неожиданный формат ответа API: {json.dumps(response_data, ensure_ascii=False)[:300]}...")
                return "Не удалось корректно обработать результаты поиска."
        
            except json.JSONDecodeError as json_err:
                logger.error(f"Ошибка декодирования JSON в резервном методе: {json_err}")
                logger.error(f"Содержимое ответа: {response.text[:200]}...")
                return "Не удалось обработать ответ поисковой системы. Технические проблемы."
                
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Таймаут запроса к Perplexity API: {timeout_err}")
            return "Поисковый запрос занял слишком много времени. Пожалуйста, попробуйте позже."
            
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Ошибка соединения с Perplexity API: {conn_err}")
            return "Не удалось установить соединение с поисковой системой. Проверьте подключение к интернету."
            
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Общая ошибка запроса к Perplexity API: {req_err}")
            return "Произошла ошибка при обработке поискового запроса. Пожалуйста, попробуйте позже."
    
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в резервном методе поиска: {repr(e)}")
        # Добавляем stack trace для больших ошибок
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return "К сожалению, произошла непредвиденная ошибка при поиске информации."
    