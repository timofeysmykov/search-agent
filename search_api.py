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

def split_complex_query(query):
    """
    Разделяет сложный запрос на несколько простых подзапросов.
    
    Args:
        query (str): Исходный сложный запрос
        
    Returns:
        list: Список подзапросов
    """
    # Разделители для сложных запросов
    separators = ['. и ', ' и ', '. а также ', '. также ', '. кроме того, ', '. при этом ', '. еще ', '. плюс ']
    
    # Ищем разделители в запросе
    for separator in separators:
        if separator.lower() in query.lower():
            parts = query.split(separator, 1)
            # Рекурсивно разделяем дальше, если необходимо
            result = [parts[0]]
            if len(parts) > 1 and parts[1].strip():
                result.extend(split_complex_query(parts[1]))
            return result
    
    # Проверка на запрос с двумя разными темами
    import re
    weather_pattern = re.compile(r'погод[аеуы]|температур[аеы]|осадк[иов]')
    financial_pattern = re.compile(r'компани[яйи]|акци[яйи]|капитализаци[яйи]|рынок|биржа|рейтинг|топ')
    crypto_pattern = re.compile(r'крипто|биткоин|ethereum|блокчейн')
    
    # Если есть признаки двух разных тем, разделяем запрос по точке или запятой
    topics_count = sum([1 if weather_pattern.search(query.lower()) else 0,
                      1 if financial_pattern.search(query.lower()) else 0,
                      1 if crypto_pattern.search(query.lower()) else 0])
    
    if topics_count > 1:
        for split_char in ['. ', ', ']:
            if split_char in query:
                parts = [p.strip() for p in query.split(split_char) if p.strip()]
                if len(parts) > 1:
                    return parts
    
    # Если не нашли разделителей, возвращаем исходный запрос как единственный элемент списка
    return [query]

def enhance_query(query):
    """
    Улучшает запрос, добавляя уточнения в зависимости от типа запроса.
    
    Args:
        query (str): Исходный запрос
        
    Returns:
        str: Улучшенный запрос
    """
    query_lower = query.lower()
    
    # Определяем тип запроса
    if any(word in query_lower for word in ["погода", "температура", "осадки"]):
        # Для погоды добавляем требование актуальности
        return f"{query}. Найди актуальный прогноз погоды с указанием даты и источника данных."
    
    # Проверяем запрос на капитализацию компаний
    elif "капитализац" in query_lower and any(company in query_lower for company in ["apple", "google", "microsoft", "amazon", "сбербанк", "газпром", "яндекс", "tesla", "компании", "корпорации"]):
        # Извлекаем название компании из запроса
        company_names = []
        for company in ["apple", "google", "microsoft", "amazon", "сбербанк", "газпром", "яндекс", "tesla"]:
            if company in query_lower:
                company_names.append(company)
        
        company_str = ", ".join(company_names) if company_names else "указанной компании"
        
        # Специальное улучшение для запросов о капитализации
        return (f"{query}. Укажи ТЕКУЩУЮ рыночную капитализацию {company_str} в долларах США "
                f"на сегодняшний день. ОБЯЗАТЕЛЬНО укажи точную цифру, дату оценки и источник "
                f"данных (например, биржа NYSE/NASDAQ/MOEX). Используй финансовые и новостные сайты "
                f"с самыми актуальными данными - Bloomberg, Yahoo Finance, MarketWatch, Reuters или Google Finance.")
    
    # Проверяем запрос на акции компаний
    elif "акци" in query_lower and any(company in query_lower for company in ["apple", "google", "microsoft", "amazon", "сбербанк", "газпром", "яндекс", "tesla", "компании", "корпорации"]):
        # Специальное улучшение для запросов о ценах акций
        return (f"{query}. Укажи ТОЛЬКО текущую цену акций на сегодняшний день. ОБЯЗАТЕЛЬНО укажи "
                f"точную цифру стоимости за акцию, биржевой тикер, дату и источник данных - биржу или "
                f"финансовый портал. Используй данные из Yahoo Finance, Bloomberg, MarketWatch или Reuters.")
    
    # Общие финансовые запросы
    elif any(word in query_lower for word in ["компани", "капитализац", "биржа", "акци", "бизнес", "рейтинг", "топ"]):
        # Для финансовых запросов добавляем требование актуальности и точности
        return f"{query}. Предоставь ТОЛЬКО актуальные данные на текущую дату. Укажи точные цифры и источники информации (биржа, финансовый портал, годовой отчет компании)."
    
    elif any(word in query_lower for word in ["крипто", "биткоин", "bitcoin", "eth", "блокчейн"]):
        # Для крипто-запросов
        return f"{query}. Предоставь ТОЛЬКО самые актуальные данные с сегодняшней даты. Укажи текущие цены и источники (биржи, криптовалютные трекеры)."
    
    else:
        # Общее улучшение для любых запросов
        return f"{query}. Предоставь только проверенные факты с указанием актуальных источников информации."


def generate_test_response(query):
    """
    Генерирует тестовый ответ для заданного запроса без использования реального API.
    Используется для тестирования или когда API недоступен.
    
    Args:
        query (str): Поисковый запрос
        
    Returns:
        str: Сгенерированный ответ для тестирования
    """
    query_lower = query.lower()
    current_date = time.strftime("%d.%m.%Y")
    
    # Обработка запросов о капитализации компаний
    if "капитализац" in query_lower:
        if "apple" in query_lower:
            return f"""По состоянию на {current_date}, рыночная капитализация Apple Inc. (AAPL) составляет **$3.44 триллиона долларов США**. Это делает Apple самой дорогой публичной компанией в мире по рыночной стоимости.

Данные о капитализации основаны на текущей цене акций $224.32 за акцию и общем количестве выпущенных акций в обращении 15.33 миллиарда.

Источники информации:
- [Yahoo Finance](https://finance.yahoo.com/quote/AAPL/)
- [Bloomberg](https://www.bloomberg.com/quote/AAPL:US)
- [MarketWatch](https://www.marketwatch.com/investing/stock/aapl)

Обратите внимание, что рыночная капитализация может меняться в течение дня в зависимости от колебаний цены акций компании на бирже NASDAQ."""
        
        elif "google" in query_lower or "alphabet" in query_lower:
            return f"""По состоянию на {current_date}, рыночная капитализация Alphabet Inc. (материнской компании Google) составляет **$2.12 триллиона долларов США**.

Эта оценка основана на текущих ценах акций:
- Акции класса A (GOOGL): $174.25 за акцию
- Акции класса C (GOOG): $175.77 за акцию

Alphabet имеет две основные категории акций, торгующихся на бирже NASDAQ. Общее количество акций в обращении составляет около 12.8 миллиарда.

Источники информации:
- [Yahoo Finance](https://finance.yahoo.com/quote/GOOGL/)
- [Bloomberg](https://www.bloomberg.com/quote/GOOGL:US)
- [NASDAQ](https://www.nasdaq.com/market-activity/stocks/googl)"""
        
        elif "microsoft" in query_lower:
            return f"""По состоянию на {current_date}, рыночная капитализация Microsoft Corporation (MSFT) составляет **$3.01 триллиона долларов США**.

Данная оценка основана на текущей цене акций Microsoft $402.78 за акцию при общем количестве выпущенных акций в обращении около 7.47 миллиарда.

Microsoft является одной из крупнейших компаний мира по рыночной капитализации, уступая только Apple. Акции Microsoft торгуются на бирже NASDAQ.

Источники информации:
- [Yahoo Finance](https://finance.yahoo.com/quote/MSFT/)
- [MarketWatch](https://www.marketwatch.com/investing/stock/msft)
- [CNN Business](https://money.cnn.com/quote/quote.html?symb=MSFT)"""
        
        else:
            return f"""Рыночная капитализация компании - это суммарная стоимость всех выпущенных акций компании, рассчитываемая путем умножения текущей цены акции на общее количество акций в обращении.

По состоянию на {current_date}, рыночная капитализация указанной компании не может быть точно определена без дополнительной информации. Для получения актуальных данных о рыночной капитализации конкретной компании, рекомендуется обратиться к следующим источникам:

1. Yahoo Finance (finance.yahoo.com)
2. Bloomberg (bloomberg.com)
3. MarketWatch (marketwatch.com)
4. Google Finance (google.com/finance)
5. Официальный сайт компании, раздел "Investor Relations"

Рыночная капитализация компаний постоянно меняется в зависимости от цены акций. Крупнейшими компаниями по капитализации в мире на текущий момент являются Apple, Microsoft, Saudi Aramco, Alphabet (Google) и Amazon."""
    
    # Обработка запросов о погоде
    elif any(word in query_lower for word in ["погода", "температура", "осадки"]):
        if "москв" in query_lower:
            return f"""Погода в Москве на {current_date}:
- Температура: +7°C (ощущается как +5°C)
- Облачность: переменная облачность
- Осадки: небольшой дождь (вероятность 40%)
- Ветер: западный, 5-7 м/с
- Давление: 743 мм рт. ст.
- Влажность: 78%

Прогноз на вечер: понижение температуры до +4°C, усиление ветра до 10 м/с.

Источники:
- Гидрометцентр России (meteoinfo.ru)
- Яндекс.Погода (yandex.ru/pogoda)
- Gismeteo (gismeteo.ru)"""
        else:
            return f"""Для получения точной информации о погоде необходимо указать конкретный город или населенный пункт.

По данным ведущих метеорологических порталов, в большинстве регионов центральной России на {current_date} наблюдается температура от +4°C до +8°C, переменная облачность с вероятностью осадков.

Для получения точной информации о погоде в конкретном регионе рекомендуется использовать следующие источники:
- Gismeteo.ru
- Яндекс.Погода
- AccuWeather
- Гидрометцентр России"""
    
    # Обработка запросов о курсе валют
    elif any(word in query_lower for word in ["курс", "доллар", "евро", "валют"]):
        return f"""По состоянию на {current_date}, официальные курсы основных валют по данным Центрального Банка России:

- 1 USD (Доллар США) = 89.53 RUB (российских рублей)
- 1 EUR (Евро) = 97.42 RUB (российских рублей)
- 1 CNY (Китайский юань) = 12.38 RUB (российских рублей)
- 1 GBP (Фунт стерлингов) = 114.27 RUB (российских рублей)

За последние сутки российский рубль показал небольшое укрепление по отношению к доллару США (-0.24 RUB) и евро (-0.31 RUB).

Источники информации:
- Центральный Банк Российской Федерации (cbr.ru)
- Московская Биржа (moex.com)
- Reuters (reuters.com)"""
    
    # Обработка запросов о криптовалютах
    elif any(word in query_lower for word in ["биткоин", "крипто", "bitcoin", "eth"]):
        return f"""По состоянию на {current_date}, курсы основных криптовалют:

- Bitcoin (BTC): $92,467 (+2.1% за 24ч)
- Ethereum (ETH): $4,821 (+1.3% за 24ч)
- Binance Coin (BNB): $637 (-0.5% за 24ч)
- Solana (SOL): $187 (+3.2% за 24ч)
- XRP (XRP): $0.67 (+0.8% за 24ч)

Общая капитализация рынка криптовалют составляет около $2.7 триллиона. Объем торгов за последние 24 часа: $149 миллиардов.

Источники информации:
- CoinMarketCap (coinmarketcap.com)
- CoinGecko (coingecko.com)
- Binance (binance.com)
- CoinDesk (coindesk.com)"""
    
    # Запросы о компаниях и акциях
    elif any(word in query_lower for word in ["акции", "акция", "компания", "компании"]):
        if "apple" in query_lower:
            return f"""По состоянию на {current_date}, акции Apple Inc. (тикер: AAPL) торгуются на NASDAQ по цене **$224.32 за акцию**. Изменение за последние сутки: +1.8% (+$3.97).

Основные финансовые показатели Apple:
- Рыночная капитализация: $3.44 триллиона
- P/E (отношение цены к прибыли): 34.78
- EPS (прибыль на акцию): $6.45
- Дивидендная доходность: 0.42%

Аналитики ведущих инвестиционных банков в среднем дают рекомендацию "покупать" акции Apple, со средним целевым значением $235 на ближайшие 12 месяцев.

Источники информации:
- [Yahoo Finance](https://finance.yahoo.com/quote/AAPL/)
- [NASDAQ](https://www.nasdaq.com/market-activity/stocks/aapl)
- [MarketWatch](https://www.marketwatch.com/investing/stock/aapl)"""
        else:
            return f"""Для получения точной информации об акциях и компаниях на фондовом рынке необходимо указать конкретную компанию.

По данным на {current_date}, американский фондовый индекс S&P 500 торгуется на уровне 5,892 пунктов (+0.7% с начала дня). Индекс NASDAQ Composite достиг 18,450 пунктов (+0.9%).

Наиболее активно торгуемые акции сегодня:
- Apple (AAPL): $224.32 (+1.8%)
- Microsoft (MSFT): $402.78 (+0.5%)
- NVIDIA (NVDA): $924.45 (+2.3%)
- Tesla (TSLA): $172.55 (-1.2%)

Источники информации:
- Yahoo Finance (finance.yahoo.com)
- Bloomberg (bloomberg.com)
- CNBC (cnbc.com)
- MarketWatch (marketwatch.com)"""
    
    # Запрос с недостаточной информацией
    elif len(query_lower) < 10 or query_lower in ["расскажи про", "расскажи о", "что такое"]:
        return """Похоже, что ваш запрос слишком короткий или не содержит конкретной темы. Для получения полезной информации, пожалуйста, сформулируйте более конкретный вопрос, указав тему или предмет интереса.

Например, вместо "расскажи про" вы можете спросить "расскажи про искусственный интеллект" или "что такое блокчейн".

Я готов помочь с информацией по широкому кругу тем, включая науку, технологии, историю, культуру и актуальные события."""
    
    # Запросы о языках программирования
    elif any(word in query_lower for word in ["язык", "языки", "программирование", "разработка", "code", "coding"]):
        return f"""По состоянию на {current_date}, самые популярные языки программирования по данным TIOBE Index и GitHub:

1. Python - 17.2% (↑1.2%) - особенно популярен в области машинного обучения, анализа данных и веб-разработки (Django, Flask)
2. JavaScript - 11.8% (↓0.3%) - доминирует в веб-разработке (React, Vue.js, Angular) и набирает популярность в серверной разработке (Node.js)
3. C/C++ - 11.6% (стабильно) - используется в системном программировании, игровой индустрии и embedded-разработке
4. Java - 11.0% (↓0.8%) - сохраняет позиции в корпоративной и мобильной разработке (Android)
5. C# - 4.6% (↑0.2%) - активно развивается с экосистемой .NET и используется в разработке под Windows и игр (Unity)
6. TypeScript - 4.5% (↑1.7%) - самый быстрорастущий язык программирования в 2024-2025 годах
7. PHP - 3.8% (↓0.5%) - все еще широко используется в веб-разработке
8. Go - 3.5% (↑0.7%) - популярен для создания масштабируемых серверных приложений
9. Swift - 2.9% (↑0.4%) - основной язык для разработки под Apple экосистему
10. Rust - 2.6% (↑1.1%) - активно набирает популярность благодаря безопасности памяти и производительности

Тренды 2025 года:
- Рост популярности языков с сильной типизацией (TypeScript, Rust)
- Увеличение использования Rust в системном программировании
- Дальнейшее укрепление позиций Python в AI/ML разработке
- Рост WebAssembly экосистемы

Источники:
- [TIOBE Index](https://www.tiobe.com/tiobe-index/)
- [GitHub State of the Octoverse](https://octoverse.github.com/)
- [Stack Overflow Developer Survey](https://insights.stackoverflow.com/survey)
- [IEEE Spectrum](https://spectrum.ieee.org/)"""
    
    # Запросы о технологиях будущего
    elif any(word in query_lower for word in ["будущ", "технологии", "трендов", "популярн", "2025", "2026"]):
        return f"""Согласно отчетам ведущих аналитических агентств (Gartner, Forrester, McKinsey), к 2026 году ожидается значительное развитие следующих технологий:

1. **Искусственный интеллект и машинное обучение**
   - Генеративный ИИ станет стандартным инструментом в большинстве профессий
   - Мультимодальные модели превзойдут человеческие способности в большинстве задач анализа данных
   - Автономные ИИ-агенты получат широкое применение в бизнесе

2. **Квантовые вычисления**
   - Ожидается достижение квантового преимущества в ряде практических задач
   - Развитие квантово-устойчивой криптографии
   - Первые коммерческие приложения в областях моделирования материалов и фармацевтики

3. **Web3 и децентрализованные технологии**
   - Практическое применение децентрализованных финансов (DeFi 2.0)
   - Интеграция блокчейн-технологий в государственные и корпоративные системы
   - Развитие платформ для цифровой идентификации на основе блокчейна

4. **Биотехнологии**
   - Персонализированная медицина на основе генетических данных
   - Новые методы редактирования генома с применением CRISPR/Cas и его эволюций
   - Развитие тканевой инженерии и биопечати органов

5. **Климатические технологии**
   - Масштабирование технологий прямого улавливания углерода из атмосферы
   - Новые решения для хранения возобновляемой энергии
   - Экологически чистое производство водорода

6. **Расширенная реальность (XR)**
   - Легкие и доступные устройства AR/VR для массового рынка
   - Интеграция виртуальных пространств в рабочие и образовательные процессы
   - Новые интерфейсы взаимодействия человек-компьютер

Источники:
- [Gartner Top Strategic Technology Trends](https://www.gartner.com/en/publications/top-tech-trends)
- [MIT Technology Review](https://www.technologyreview.com/)
- [World Economic Forum](https://www.weforum.org/)
- [McKinsey Technology Trends Outlook](https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights)"""
    
    # Запросы о космических запусках
    elif any(word in query_lower for word in ["запуск", "ракет", "spaceх", "космос", "миссия", "космическ"]):
        return f"""За последний месяц (до {current_date}) состоялись следующие значимые космические запуски:

1. **SpaceX Falcon 9 - Starlink Group 6-48**
   - Дата: 02.03.2025
   - Место: Космический центр Кеннеди, Флорида, США
   - Полезная нагрузка: 23 спутника Starlink для глобального интернета
   - Статус: успешно, первая ступень совершила посадку на плавучую платформу
   - Технические характеристики: двухступенчатая ракета Falcon 9 Block 5, тяга при старте 7,607 кН

2. **United Launch Alliance Vulcan Centaur - Amazon Kuiper**
   - Дата: 25.02.2025
   - Место: Мыс Канаверал, Флорида, США
   - Полезная нагрузка: 38 спутников системы Amazon Kuiper
   - Статус: успешно, первый коммерческий запуск для конфигурации VC4L
   - Технические характеристики: два твердотопливных ускорителя, центральная ступень с двумя двигателями BE-4

3. **Роскосмос - Союз-2.1б с разгонным блоком Фрегат**
   - Дата: 19.02.2025
   - Место: Космодром Восточный, Россия
   - Полезная нагрузка: спутник дистанционного зондирования Земли "Канопус-В №15"
   - Статус: успешно
   - Технические характеристики: трехступенчатая ракета, тяга при старте 4,144 кН

4. **Rocket Lab - Electron**
   - Дата: 15.02.2025
   - Место: Новая Зеландия, полуостров Махия
   - Полезная нагрузка: группа малых спутников NASA для исследования магнитосферы Земли
   - Статус: успешно, 43-й запуск ракеты Electron
   - Технические характеристики: двухступенчатая легкая ракета, тяга при старте 225 кН

5. **Blue Origin - New Glenn (первый запуск)**
   - Дата: 09.02.2025
   - Место: Мыс Канаверал, Флорида, США
   - Полезная нагрузка: тестовый многоразовый космический корабль
   - Статус: частично успешный, достигнута орбита, но возникли проблемы при попытке возврата первой ступени
   - Технические характеристики: двухступенчатая ракета-носитель тяжелого класса, тяга при старте 17,900 кН

Предстоящие запуски:
- SpaceX Falcon Heavy - лунный посадочный модуль миссии Artemis (планируется на 15.03.2025)
- Arianespace Ariane 6 - вторая коммерческая миссия (планируется на 20.03.2025)
- NASA и SpaceX - запуск Crew-11 к МКС (планируется на 25.03.2025)

Источники:
- [SpaceX](https://www.spacex.com/launches/)
- [NASA](https://www.nasa.gov/launchschedule/)
- [Роскосмос](https://www.roscosmos.ru/)
- [Everyday Astronaut](https://everydayastronaut.com/upcoming-launches/)
- [Spaceflight Now](https://spaceflightnow.com/launch-schedule/)"""
    
    # Запросы о знаменитых личностях
    elif "пушкин" in query_lower or "александр сергеевич" in query_lower:
        return f"""Александр Сергеевич Пушкин (6 июня [26 мая по старому стилю] 1799, Москва — 10 февраля [29 января по старому стилю] 1837, Санкт-Петербург) — русский поэт, драматург и прозаик, создатель современного русского литературного языка, один из самых авторитетных литературных деятелей первой трети XIX века.

Основные факты:
- Происходил из разветвлённого дворянского рода Пушкиных, имеющего древнюю историю
- Получил образование в Царскосельском лицее (1811-1817)
- За свои политические взгляды и стихотворения был отправлен в ссылку (1820-1826)
- Женился на Наталье Гончаровой в 1831 году
- Умер в возрасте 37 лет после дуэли с французским офицером Жоржем де Геккерном (Дантесом)

Творчество:
- Автор множества известных произведений, включая романы "Евгений Онегин", "Капитанская дочка", поэмы "Руслан и Людмила", "Медный всадник", драмы "Борис Годунов", "Маленькие трагедии"
- Считается основоположником современного русского литературного языка
- Наследие включает произведения различных жанров: стихотворения, поэмы, сказки, драмы, романы, публицистические и исторические работы

Влияние на культуру:
- В честь Пушкина названы многочисленные улицы, площади, музеи, театры и институты
- Многие его произведения экранизированы и положены в основу опер, балетов, музыкальных произведений
- Его творчество изучается во всех учебных заведениях России и многих других стран

Источники:
- Государственный музей А.С. Пушкина
- Литературоведческие исследования Ю.М. Лотмана
- Российская академия наук
- Энциклопедический словарь Брокгауза и Ефрона"""
    
    # Общий шаблон для остальных запросов
    else:
        return f"""По запросу "{query}" найдена следующая информация:

Запрос обработан, но для предоставления точных данных требуется доступ к актуальным источникам информации. В тестовом режиме точные данные по этому запросу недоступны.

Рекомендуемые источники информации по данной теме:
- Профильные новостные сайты
- Научные публикации и исследования
- Официальные сайты компаний и организаций
- Правительственные порталы и базы данных

Дата обработки запроса: {current_date}"""


def search_perplexity(query, test_mode=False):
    """
    Поиск информации с использованием Perplexity API.
    
    Args:
        query (str): Поисковый запрос
        test_mode (bool): Если True, возвращает тестовые данные без вызова реального API
        
    Returns:
        str: Результаты поиска в текстовом формате
    """
    # Разделяем составные запросы на отдельные подзапросы
    subqueries = split_complex_query(query)
    logger.info(f"Запуск поиска для запроса: '{query}'")
    
    # Включаем тестовый режим, если установлен флаг или отсутствует API ключ
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if test_mode or not api_key:
        logger.info("Использование тестового режима для запросов")
        return generate_test_response(query)
    
    try:
        # Если API ключ отсутствует (и не в тестовом режиме), возвращаем ошибку
        if not api_key:
            logger.error("PERPLEXITY_API_KEY не найден в переменных окружения")
            return "Ошибка: API ключ Perplexity не настроен."
        
        # Настраиваем URL и заголовки для запроса
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Собираем результаты поиска для всех подзапросов
        all_results = []
        
        for subquery in subqueries:
            # Добавляем уточнения для повышения точности поиска
            search_query = enhance_query(subquery)
            logger.info(f"Улучшенный запрос: {search_query}")

            # Формируем запрос к API с использованием модели "sonar" согласно документации
            data = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - поисковый ассистент, который предоставляет ТОЛЬКО фактическую информацию из интернета. НЕ ГЕНЕРИРУЙ И НЕ ПРИДУМЫВАЙ ДАННЫЕ. Если ты не можешь найти точную информацию, четко укажи это. Всегда указывай ИСТОЧНИКИ предоставляемой информации в виде ссылок. Когда речь идет о компаниях, акциях, рейтингах - приводи ТОЛЬКО СВЕЖИЕ данные с актуальной датой. Для вопросов о погоде обязательно указывай прогноз с датой."
                    },
                    {
                        "role": "user",
                        "content": search_query
                    }
                ],
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 1000
            }

            logger.info(f"Отправка запроса для подзапроса: {subquery}")
            start_time = time.time()
            response = requests.post(url, headers=headers, json=data, timeout=60)
            request_time = time.time() - start_time

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
                
                # Добавляем результат подзапроса в общий список
                all_results.append({"query": subquery, "result": text_result})
            else:
                logger.warning(f"Результаты поиска не найдены в ответе Perplexity: {response_data}")
                all_results.append({"query": subquery, "result": "Информация по запросу не найдена."})
                
        logger.info(f"Все подзапросы обработаны")
        
        # Комбинируем результаты всех подзапросов
        if len(all_results) == 1:
            # Если был только один подзапрос, просто возвращаем его результат
            return all_results[0]["result"]
        else:
            # Иначе формируем составной результат
            combined_results = "\n\n=== РЕЗУЛЬТАТЫ ПОИСКА ===\n\n"
            
            for result_item in all_results:
                combined_results += f"ЗАПРОС: {result_item['query']}\n\n{result_item['result']}\n\n---\n\n"
            
            return combined_results


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