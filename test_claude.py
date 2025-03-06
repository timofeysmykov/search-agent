import os
import sys
import logging
from dotenv import load_dotenv
from llm_api import query_llm

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Проверка наличия API ключа
if not os.getenv('CLAUDE_API_KEY'):
    print("ОШИБКА: API ключ Claude не найден в переменных окружения.")
    print("Создайте файл .env с содержимым: CLAUDE_API_KEY=ваш_ключ")
    sys.exit(1)

# Тестовый запрос
test_query = "Привет, как дела?"

print(f"Отправка запроса: {test_query}")
response = query_llm(test_query)
print(f"Ответ от Claude API:\n{response}")
