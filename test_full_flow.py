"""
Тестовый скрипт для проверки полного цикла работы AI агента:
1. Получение запроса пользователя
2. Выполнение поиска через Perplexity
3. Формирование ответа с помощью Claude
"""
import os
import sys
import logging
from dotenv import load_dotenv
from llm_api import query_llm
from search_api import search_perplexity
from utils import needs_search

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Проверка наличия API ключей
if not os.getenv('CLAUDE_API_KEY'):
    print("ОШИБКА: API ключ Claude не найден в переменных окружения.")
    sys.exit(1)

if not os.getenv('PERPLEXITY_API_KEY'):
    print("ОШИБКА: API ключ Perplexity не найден в переменных окружения.")
    sys.exit(1)

def process_query(user_query):
    """
    Обработка запроса пользователя с использованием поиска и LLM
    
    Args:
        user_query (str): Запрос пользователя
        
    Returns:
        str: Ответ на запрос
    """
    logger.info(f"Получен запрос: {user_query}")
    
    # Всегда выполняем поиск (согласно измененной функции needs_search)
    search_needed = needs_search(user_query)
    logger.info(f"Нужен ли поиск: {search_needed}")
    
    if search_needed:
        logger.info("Выполняем поиск...")
        search_results = search_perplexity(user_query)
        logger.info(f"Получены результаты поиска длиной: {len(str(search_results))} символов")
        logger.info(f"Начало результатов: {str(search_results)[:100]}...")
        
        # Формируем системный промпт с результатами поиска
        system_prompt = f"""
        Ты - полезный ассистент, который отвечает на вопросы пользователей, опираясь на предоставленную информацию из поиска.
        
        ВАЖНЫЕ ПРАВИЛА:
        1. Используй ТОЛЬКО информацию из результатов поиска для ответа на вопросы о текущих событиях, ценах, рейтингах и других фактических данных.
        2. Не выдумывай факты и не дополняй информацию своими знаниями, когда отвечаешь на вопросы, требующие актуальных данных.
        3. Если в поисковых результатах есть противоречия, укажи это и приведи разные данные с источниками.
        4. Всегда указывай временной период, к которому относятся данные, и приводи источники информации.
        5. Отвечай на русском языке, даже если результаты поиска на английском.
        6. Структурируй ответ четко и логично, выделяя важную информацию.
        
        РЕЗУЛЬТАТЫ ПОИСКА:
        {search_results}
        """
        
        # Отправляем запрос к Claude с результатами поиска
        logger.info("Отправляем запрос к Claude с результатами поиска...")
        response = query_llm(user_query, system_prompt)
    else:
        # Если поиск не нужен, просто отправляем запрос к Claude
        logger.info("Отправляем запрос напрямую к Claude...")
        response = query_llm(user_query)
    
    return response

if __name__ == "__main__":
    # Настройка дополнительного логирования для отладки
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # Тестовый запрос, требующий актуальной информации
    test_query = "Какая сейчас погода в Москве?"
    
    print(f"Тестовый запрос: {test_query}")
    response = process_query(test_query)
    print("\nОтвет AI агента:")
    print("-" * 50)
    print(response)
    print("-" * 50)
