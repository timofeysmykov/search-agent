"""
Тестирование функции поиска с Perplexity API.
"""
import os
import logging
from search_api import search_perplexity
from dotenv import load_dotenv

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Загружаем переменные окружения
load_dotenv()

def test_search():
    """Тестируем функцию поиска с реальным запросом"""
    
    # Проверяем наличие API ключа
    if not os.getenv('PERPLEXITY_API_KEY'):
        print("ОШИБКА: Ключ PERPLEXITY_API_KEY не найден в переменных окружения")
        print("Убедитесь, что файл .env содержит PERPLEXITY_API_KEY=ваш_ключ")
        return
    
    # Тестовый запрос
    query = "Топ 5 крупнейших компаний мира по капитализации на 2024 год"
    
    print(f"\n--- Тестирование поиска с запросом: '{query}' ---\n")
    
    # Выполняем поиск
    try:
        result = search_perplexity(query)
        
        # Выводим результат
        print("\n--- Результат поиска ---\n")
        print(result[:1000] + "..." if len(result) > 1000 else result)
        print(f"\nДлина результата: {len(result)} символов")
        
        # Проверяем наличие фактической информации в ответе
        checks = [
            "Apple" in result,
            "Microsoft" in result,
            "капитализация" in result.lower(),
            "трлн" in result.lower()
        ]
        
        print("\n--- Проверка содержимого результата ---")
        print(f"Содержит 'Apple': {checks[0]}")
        print(f"Содержит 'Microsoft': {checks[1]}")
        print(f"Содержит 'капитализация': {checks[2]}")
        print(f"Содержит 'трлн': {checks[3]}")
        
        if all(checks):
            print("\n✅ Тест УСПЕШЕН: Результат содержит ожидаемую информацию")
        else:
            print("\n⚠️ Тест НЕУСПЕШЕН: Результат не содержит всю ожидаемую информацию")
            
    except Exception as e:
        print(f"\n❌ ОШИБКА при выполнении поиска: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_search()
