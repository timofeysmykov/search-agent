"""
Main entry point for the AI agent application.
"""
import os
import logging
from llm_api import query_llm
from search_api import search_perplexity
from utils import process_input, format_output, needs_search, combine_input

# Set up console logging in addition to file logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

def check_api_keys():
    """Check if the required API keys are set."""
    missing_keys = []
    if not os.getenv('CLAUDE_API_KEY'):
        missing_keys.append('CLAUDE_API_KEY')
    if not os.getenv('PERPLEXITY_API_KEY'):
        missing_keys.append('PERPLEXITY_API_KEY')
    
    return missing_keys

def main():
    """Main function to run the AI agent."""
    print("=" * 50)
    print("AI Agent with Claude 3.5 Haiku and Perplexity")
    print("=" * 50)
    print("Введите 'выход' для завершения программы.")
    print()
    
    # Check for API keys
    missing_keys = check_api_keys()
    if missing_keys:
        print(f"ВНИМАНИЕ: Следующие API ключи не найдены: {', '.join(missing_keys)}")
        print("Пожалуйста, установите их как переменные окружения или в файле .env")
        print("Пример:")
        print("export CLAUDE_API_KEY='ваш_ключ'")
        print("export PERPLEXITY_API_KEY='ваш_ключ'")
        print()
    
    # Системный промпт для Claude
    system_prompt = """
    Ты - полезный ассистент, который отвечает на вопросы пользователя.
    Если для ответа на вопрос требуется актуальная информация, которой нет в твоих знаниях,
    или информация, которая могла измениться с момента твоего обучения, укажи это.
    Отвечай на русском языке, даже если запрос на другом языке.
    Твои ответы должны быть точными, информативными и полезными.
    """
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = input("Ваш запрос: ")
            
            # Check if user wants to exit
            if user_input.lower() in ['выход', 'exit', 'quit', 'q']:
                print("До свидания!")
                break
            
            # Process the input
            processed_input = process_input(user_input)
            if not processed_input:
                print("Ошибка при обработке ввода. Пожалуйста, попробуйте снова.")
                continue
            
            print("Обрабатываю ваш запрос...")
            
            # Первый шаг: Отправляем запрос пользователя в модель Claude с флагом определения необходимости поиска
            print("Анализирую запрос...")
            result = query_llm(processed_input, system_prompt=system_prompt, detect_search_needs=True)
            
            # Проверяем, вернулся ли кортеж (ответ, search_needed, search_query)
            if isinstance(result, tuple) and len(result) == 3:
                initial_response, search_needed, search_query = result
                
                # Если модель определила необходимость поиска
                if search_needed and search_query:
                    print(f"Выполняю поиск информации по запросу: {search_query}")
                    
                    # Выполняем поиск с оптимизированным запросом
                    search_results = search_perplexity(search_query)
                    
                    if search_results:
                        print("Найдена информация. Формирую окончательный ответ...")
                        
                        # Комбинируем исходный запрос пользователя и результаты поиска для финального запроса к модели
                        combined_prompt = combine_input(processed_input, search_results)
                        
                        # Получаем финальный ответ от модели с учетом результатов поиска
                        final_response = query_llm(combined_prompt, system_prompt=system_prompt)
                        formatted_response = format_output(final_response)
                    else:
                        print("Поиск не дал результатов. Использую первоначальный ответ модели...")
                        formatted_response = format_output(initial_response)
                else:
                    # Если поиск не требуется, используем первоначальный ответ
                    print("Модель определила, что поиск не требуется. Использую базовые знания.")
                    formatted_response = format_output(initial_response)
            else:
                # Если произошла ошибка при определении необходимости поиска, используем стандартный подход
                print("Использую стандартный подход для обработки запроса...")
                
                # Проверяем необходимость поиска с помощью функции needs_search
                if needs_search(processed_input):
                    print("Выполняю поиск информации...")
                    search_results = search_perplexity(processed_input)
                    
                    if search_results:
                        print("Найдена информация. Формирую ответ...")
                    else:
                        print("Поиск не дал результатов. Использую только базовые знания...")
                    
                    # Комбинируем запрос и результаты поиска
                    llm_input = combine_input(processed_input, search_results)
                else:
                    print("Использую базовые знания для ответа...")
                    llm_input = f"Запрос пользователя: {processed_input}\n\nПожалуйста, ответь на этот запрос, используя свои знания."
                
                # Получаем ответ от модели
                response = query_llm(llm_input, system_prompt=system_prompt)
                formatted_response = format_output(response)
            
            # Выводим ответ пользователю
            print("\n" + "=" * 50)
            print(formatted_response)
            print("=" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\nПрограмма прервана пользователем. До свидания!")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            print(f"Произошла ошибка: {e}")
            print("Пожалуйста, попробуйте снова или проверьте логи для получения дополнительной информации.")

if __name__ == "__main__":
    main()
