"""
Тестовый скрипт для проверки AI-агента на различных сценариях запросов.
"""
import logging
import os
import json
import time
import argparse
from dotenv import load_dotenv
from search_api import search_perplexity
from llm_api import query_llm
from utils import process_input, needs_search, combine_input, format_output

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("test_agent")

# Загрузка переменных окружения
load_dotenv()

def run_test_scenario(scenario_id, query, test_mode=False):
    """
    Запускает тестовый сценарий для указанного запроса.
    
    Args:
        scenario_id (int): Идентификатор тестового сценария
        query (str): Запрос для тестирования
    """
    logger.info(f"Тестовый сценарий {scenario_id}: '{query}'")
    print(f"\n{'='*80}\nТЕСТОВЫЙ СЦЕНАРИЙ {scenario_id}: '{query}'\n{'='*80}")
    
    try:
        # Шаг 1: Обработка входного запроса
        processed_query = process_input(query)
        print(f"Обработанный запрос: {processed_query}")
        
        # Шаг 2: Определение необходимости поиска
        search_needed = needs_search(processed_query)
        print(f"Необходимость поиска: {search_needed}")
        
        # Шаг 3: Выполнение поиска, если необходимо
        search_results = None
        if search_needed:
            start_time = time.time()
            print("Выполняется поиск информации...")
            search_results = search_perplexity(processed_query, test_mode=test_mode)
            search_time = time.time() - start_time
            print(f"Поиск выполнен за {search_time:.2f} секунд")
            print(f"Результаты поиска (первые 200 символов): {search_results[:200]}...")
        
        # Шаг 4: Комбинирование запроса и результатов поиска
        combined_input = combine_input(processed_query, search_results)
        print(f"Комбинированный ввод подготовлен (длина: {len(combined_input)} символов)")
        
        # Шаг 5: Отправка запроса к LLM для получения ответа
        print("Отправка запроса к Claude 3.5 Haiku...")
        start_time = time.time()
        
        if test_mode:
            # В тестовом режиме генерируем примерный ответ LLM без реального запроса к API
            llm_response = f"Тестовый ответ на запрос '{query}'. " \
                          f"Информация основана на данных поиска: {search_results[:100]}..."
        else:
            # Реальный запрос к LLM API
            llm_response = query_llm(combined_input)
            
        llm_time = time.time() - start_time
        print(f"Ответ получен за {llm_time:.2f} секунд")
        
        # Шаг 6: Форматирование ответа для вывода
        formatted_output = format_output(llm_response)
        
        # Вывод результата
        print("\nРЕЗУЛЬТАТ ТЕСТА:")
        print(f"{'='*40}")
        print(formatted_output)
        print(f"{'='*40}")
        
        # Записываем результат в файл для анализа
        with open(f"test_result_{scenario_id}.txt", "w", encoding="utf-8") as f:
            f.write(f"Тестовый сценарий {scenario_id}: {query}\n\n")
            f.write(f"Результаты поиска:\n{search_results}\n\n")
            f.write(f"Ответ LLM:\n{formatted_output}\n")
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка в тестовом сценарии {scenario_id}: {e}")
        print(f"ОШИБКА: {e}")
        return False

def run_all_tests(test_mode=False):
    """
    Запускает все тестовые сценарии.
    """
    test_scenarios = [
        # 1. Простой фактический запрос
        "Кто такой Александр Пушкин?",
        
        # 2. Запрос, требующий актуальной информации
        "Какой сейчас курс доллара к рублю?",
        
        # 3. Погодный запрос
        "Какая погода сегодня в Москве?",
        
        # 4. Составной запрос с несколькими темами
        "Расскажи о курсе биткоина и последних новостях SpaceX",
        
        # 5. Запрос, ориентированный на будущее
        "Какие технологии будут популярны в 2026 году?",
        
        # 6. Запрос о компании/финансах
        "Какая капитализация у компании Apple?",
        
        # 7. Сложный запрос для проверки обработки ошибок
        "Составь подробный список всех запусков ракет за последний месяц с техническими характеристиками каждой миссии",
        
        # 8. Запрос с нестандартным форматированием
        "какие   самые  популярные   языки  программирования   в  2025  году???",
        
        # 9. Запрос на другом языке
        "What is the current stock price of Google?",
        
        # 10. Неполный запрос
        "расскажи про"
    ]
    
    results = {}
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nЗапуск тестового сценария {i}/{len(test_scenarios)}")
        success = run_test_scenario(i, scenario, test_mode=test_mode)
        results[i] = {
            "query": scenario,
            "success": success
        }
    
    # Выводим итоговый отчет
    print("\n\nИТОГОВЫЙ ОТЧЕТ:")
    print(f"{'='*50}")
    for scenario_id, result in results.items():
        status = "✅ УСПЕХ" if result["success"] else "❌ СБОЙ"
        print(f"Сценарий {scenario_id}: {status} - '{result['query']}'")
    
    success_count = sum(1 for r in results.values() if r["success"])
    print(f"{'='*50}")
    print(f"Всего выполнено: {len(results)} сценариев")
    print(f"Успешно: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"Сбоев: {len(results) - success_count} ({(len(results) - success_count)/len(results)*100:.1f}%)")
    print(f"{'='*50}")

if __name__ == "__main__":
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Тестирование AI-агента")
    parser.add_argument(
        "--test-mode", 
        action="store_true", 
        help="Запустить в тестовом режиме без использования реальных API-запросов"
    )
    parser.add_argument(
        "--scenario", 
        type=int, 
        help="Запустить только указанный сценарий (номер от 1 до 10)"
    )
    args = parser.parse_args()
    
    # Проверяем наличие API ключей, если не в тестовом режиме
    if not args.test_mode:
        if not os.getenv("CLAUDE_API_KEY"):
            print("ОШИБКА: Отсутствует CLAUDE_API_KEY в переменных окружения (.env)")
            print("Запустите с флагом --test-mode для использования тестового режима без API-ключей")
            exit(1)
        
        if not os.getenv("PERPLEXITY_API_KEY"):
            print("ОШИБКА: Отсутствует PERPLEXITY_API_KEY в переменных окружения (.env)")
            print("Запустите с флагом --test-mode для использования тестового режима без API-ключей")
            exit(1)
    
    print(f"Запуск тестирования AI-агента{' в тестовом режиме' if args.test_mode else ''}...")
    
    # Запуск определенного сценария или всех сценариев
    if args.scenario:
        if 1 <= args.scenario <= 10:
            test_scenarios = [
                "Кто такой Александр Пушкин?",
                "Какой сейчас курс доллара к рублю?",
                "Какая погода сегодня в Москве?",
                "Расскажи о курсе биткоина и последних новостях SpaceX",
                "Какие технологии будут популярны в 2026 году?",
                "Какая капитализация у компании Apple?",
                "Составь подробный список всех запусков ракет за последний месяц с техническими характеристиками каждой миссии",
                "какие   самые  популярные   языки  программирования   в  2025  году???",
                "What is the current stock price of Google?",
                "расскажи про"
            ]
            scenario_idx = args.scenario - 1
            run_test_scenario(args.scenario, test_scenarios[scenario_idx], test_mode=args.test_mode)
        else:
            print(f"ОШИБКА: Недопустимый номер сценария {args.scenario}. Выберите от 1 до 10.")
            exit(1)
    else:
        # Запуск всех тестовых сценариев
        run_all_tests(test_mode=args.test_mode)
