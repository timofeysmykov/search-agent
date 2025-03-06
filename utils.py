"""
Utility functions for the AI agent.
"""
import logging
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename="agent.log"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

def process_input(user_input):
    """
    Clean and prepare the user input.
    
    Args:
        user_input (str): Raw input from the user
        
    Returns:
        str: Processed input
    """
    try:
        cleaned_input = user_input.strip()
        logger.info(f"Processed input: {cleaned_input}")
        return cleaned_input
    except Exception as e:
        logger.error(f"Error processing input: {e}")
        return None

def needs_search(processed_input):
    """
    Determine if search is needed based on keywords in the input.
    
    Args:
        processed_input (str): Processed user input
        
    Returns:
        bool: True if search is needed, False otherwise
    """
    try:
        # Convert to lowercase for case-insensitive matching
        lower_input = processed_input.lower()
        
        # Keywords that might indicate a need for up-to-date information
        search_keywords = [
            # Временные маркеры
            "сейчас", "текущий", "актуальный", "свежий", "недавний", 
            "сегодня", "вчера", "последний", "новый", "обновленный",
            "современный", "на данный момент", "в настоящее время",
            "2023", "2024", "2025", "этот год", "этот месяц", "эта неделя",
            "январь", "февраль", "март", "апрель", "май", "июнь",
            "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
            
            # Категории информации, требующие актуальных данных
            "новости", "погода", "цена", "курс", "статистика", "данные", 
            "обновление", "событие", "происшествие", "случилось",
            
            # Запросы о конкретных сущностях
            "компания", "компаний", "организация", "технология", "продукт", 
            "сервис", "приложение", "устройство", "гаджет",
            
            # Списки и рейтинги
            "топ", "рейтинг", "список", "лидер", "самых", "лучших", "богатейших", 
            "известных", "популярных", "дорогих", "крупнейших", "успешных",
            
            # Вопросы, требующие актуальной информации
            "как сейчас", "что нового", "последние изменения", "текущая ситуация",
            "как обстоят дела", "что происходит", "какие новости",
            
            # Финансовые и экономические запросы
            "акции", "биржа", "валюта", "доллар", "евро", "рубль", "биткоин", "криптовалюта",
            "инвестиции", "экономика", "инфляция", "ставка", "банк", "капитализация",
            "рыночная стоимость", "стоимость", "цена акций", "выручка", "доход", "прибыль"
        ]
        
        # Фразы, которые почти всегда требуют поиска
        strong_indicators = [
            "расскажи о", "что такое", "кто такой", "где находится", 
            "как работает", "объясни", "опиши", "найди информацию",
            "поищи", "узнай", "сколько стоит", "какая цена", "как купить",
            "как сделать", "как использовать", "как применять", "инструкция",
            "найди топ", "покажи топ", "рейтинг", "кто самый", "найди список",
            "актуальный список", "текущий рейтинг", "на сегодня", "на текущий момент"
        ]
        
        # Проверяем наличие сильных индикаторов
        for indicator in strong_indicators:
            if indicator in lower_input:
                logger.info(f"Strong search indicator found: '{indicator}' in input: {processed_input}")
                return True
        
        # Проверяем комбинации слов, указывающие на необходимость поиска актуальных данных
        ranking_words = ["топ", "рейтинг", "список", "самых", "лучших"]
        entity_words = ["компания", "компаний", "организация", "банк", "бренд"]
        year_markers = ["2023", "2024", "2025", "год", "года"]
        
        # Ищем комбинации (рейтинг + сущность)
        for rank_word in ranking_words:
            for entity_word in entity_words:
                if rank_word in lower_input and entity_word in lower_input:
                    logger.info(f"Found ranking + entity combination: '{rank_word}' + '{entity_word}' in: {processed_input}")
                    return True
        
        # Ищем комбинации (временной маркер + сущность)
        for year in year_markers:
            for entity_word in entity_words:
                if year in lower_input and entity_word in lower_input:
                    logger.info(f"Found year + entity combination: '{year}' + '{entity_word}' in: {processed_input}")
                    return True
        
        # Проверяем наличие отдельных ключевых слов
        for keyword in search_keywords:
            if keyword in lower_input:
                logger.info(f"Search keyword found: '{keyword}' in input: {processed_input}")
                return True
        
        # Если запрос содержит год (цифры 2023, 2024, 2025 и т.д.), то вероятно нужен поиск
        import re
        if re.search(r'20[2-9][0-9]', lower_input):
            logger.info(f"Year reference detected, enabling search for: {processed_input}")
            return True
        
        # Если запрос длинный (более 50 символов), вероятно, это сложный вопрос, требующий поиска
        if len(processed_input) > 50:
            logger.info(f"Long query detected, enabling search for: {processed_input}")
            return True
        
        # В случае сомнений, лучше выполнить поиск
        if any(word in lower_input for word in ["актуальный", "последний", "текущий", "сейчас"]):
            logger.info(f"Ambiguous query with recency indicators, enabling search: {processed_input}")
            return True
        
        logger.info(f"No search indicators found for input: {processed_input}")
        return False
    except Exception as e:
        logger.error(f"Error determining if search is needed: {e}")
        # В случае ошибки лучше выполнить поиск
        return True

def combine_input(processed_input, search_results):
    """
    Combine user input and search results for the LLM.
    
    Args:
        processed_input (str): Processed user input
        search_results (list): Results from the search API
        
    Returns:
        str: Combined input for the LLM
    """
    try:
        if not search_results:
            logger.warning("No search results to combine")
            return f"Запрос пользователя: {processed_input}\n\nПожалуйста, ответь на этот запрос, используя свои знания."
        
        # Подготовка информации из поиска
        search_text = ""
        sources_text = ""
        has_sources = False
        search_model = "неизвестно"
        
        # Проверяем наличие структурированных результатов
        has_structured_results = any("structured" in result for result in search_results)
        
        # Анализируем запрос на предмет наличия временных маркеров будущего времени
        future_date_request = False
        import re
        future_year_match = re.search(r'20(2[5-9]|[3-9][0-9])', processed_input.lower())
        if future_year_match or any(word in processed_input.lower() for word in ["будущ", "следующ", "прогноз"]):
            future_date_request = True
            logger.info(f"Запрос содержит указание на будущую дату: {processed_input}")
        
        if has_structured_results:
            # Обрабатываем структурированные результаты
            for result in search_results:
                if "structured" in result:
                    structured_data = result["structured"]
                    search_model = structured_data.get('model', 'неизвестно')
                    
                    # Проверяем наличие источников
                    if structured_data.get("has_sources", False) or "sources" in structured_data:
                        has_sources = True
                        if "sources" in structured_data:
                            sources = structured_data["sources"]
                            sources_text = "\nИсточники информации:\n"
                            for i, source in enumerate(sources[:5]):
                                sources_text += f"- {source}\n"
                    
                    # Добавляем разделы структурированного результата
                    sections = structured_data.get("sections", [])
                    
                    # Проверяем наличие ответа с разделами
                    if len(sections) >= 2:
                        # Используем только первые 2 секции для краткого и подробного ответа
                        search_text += f"КРАТКИЙ ОТВЕТ:\n{sections[0]}\n\n"
                        search_text += f"ПОДРОБНАЯ ИНФОРМАЦИЯ:\n{sections[1]}\n\n"
                        
                        # Добавляем секцию с источниками, если есть третья секция и нет отдельных источников
                        if len(sections) >= 3 and not has_sources:
                            search_text += f"ИСТОЧНИКИ:\n{sections[2]}\n\n"
                    else:
                        # Если нет структурированных разделов, добавляем весь контент
                        full_content = structured_data.get("full_content", "")
                        if full_content:
                            search_text += f"{full_content}\n\n"
                        else:
                            # Если и этого нет, добавляем все имеющиеся секции
                            for section in sections:
                                search_text += f"{section}\n\n"
        else:
            # Обрабатываем обычные сниппеты
            for i, result in enumerate(search_results[:2]):  # Ограничиваем до 2 результатов
                if "snippet" in result:
                    search_text += f"Результат поиска {i+1}:\n{result['snippet']}\n\n"
                elif "text" in result:
                    search_text += f"Результат поиска {i+1}:\n{result['text']}\n\n"
        
        # Добавляем информацию об источниках, если она есть
        if has_sources and sources_text:
            search_text += sources_text
        
        # Указываем модель поиска и дату
        from datetime import datetime
        current_date = datetime.now().strftime("%d.%m.%Y")
        search_info = f"[Информация получена с помощью поисковой модели {search_model} по состоянию на {current_date}]"
        
        # Определяем ключевые индикаторы запроса для более точных инструкций LLM
        contains_ranking = any(word in processed_input.lower() for word in ["топ", "рейтинг", "список", "самый", "лучший"])
        contains_factual = any(word in processed_input.lower() for word in ["сколько", "где", "когда", "кто", "факт", "статистика"])
        
        # Создаем специальные инструкции в зависимости от типа запроса
        special_instructions = ""
        if future_date_request:
            special_instructions = (
                "ВАЖНО: Запрос касается будущего периода. Не делай предположений о будущем. "
                "Используй ТОЛЬКО самые актуальные данные из поиска и явно укажи, что это последние доступные данные, "
                "а не прогноз на запрашиваемый период. Чётко обозначь дату актуальности информации."
            )
        elif contains_ranking:
            special_instructions = (
                "ВАЖНО: Запрос касается рейтинга или списка. Приведи точный список из поисковых результатов. "
                "Не изменяй порядок элементов и сохрани все числовые показатели. "
                "Обязательно укажи источник данных и дату их актуальности."
            )
        elif contains_factual:
            special_instructions = (
                "ВАЖНО: Запрос требует фактической информации. Приведи точные данные из поисковых результатов. "
                "Включи все релевантные числа, даты и факты. Избегай обобщений."
            )
        
        # Создаем улучшенный промпт для LLM
        combined_text = (
            f"Запрос пользователя: {processed_input}\n\n"
            f"АКТУАЛЬНАЯ ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА:\n{search_text}\n"
            f"{search_info}\n\n"
            f"ИНСТРУКЦИИ:\n"
            f"1. Для ответа на запрос пользователя СТРОГО ИСПОЛЬЗУЙ предоставленную информацию из поиска.\n"
            f"2. НИКОГДА не выдумывай факты и не дополняй информацию своими знаниями, когда отвечаешь на вопросы "
            f"о текущих данных, рейтингах, ценах или событиях.\n"
            f"3. Если в поисковых результатах есть противоречия, укажи это и приведи разные данные с источниками.\n"
            f"4. Четко укажи временной период, к которому относятся данные, и приведи источники информации.\n"
            f"5. Для запросов о будущих периодах всегда опирайся на последние известные данные и явно "
            f"указывай, что это актуальная информация на текущий момент, а не прогноз.\n"
        )
        
        # Добавляем специальные инструкции, если они есть
        if special_instructions:
            combined_text += f"\n{special_instructions}\n"
        
        # Завершаем промпт
        combined_text += "\nОтвет для пользователя:"
        
        logger.info("Successfully combined input and search results with enhanced structure and specific instructions")
        return combined_text
    except Exception as e:
        logger.error(f"Error combining input and search results: {e}")
        return processed_input

def format_output(response):
    """
    Format the LLM response for display to the user.
    
    Args:
        response (str): Raw response from the LLM
        
    Returns:
        str: Formatted response
    """
    try:
        # Simple formatting for now, can be expanded later
        formatted = response.strip()
        logger.info("Response formatted successfully")
        return formatted
    except Exception as e:
        logger.error(f"Error formatting output: {e}")
        return response if response else "Произошла ошибка при форматировании ответа."
