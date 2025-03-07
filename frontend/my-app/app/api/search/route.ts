import { NextResponse } from 'next/server';

const baseUrl = 'https://api.perplexity.ai/chat/completions';

// Функция для улучшения запроса (похожая на функцию enhance_query из Python)
function enhanceQuery(query: string): string {
  const queryLower = query.toLowerCase();
  
  // Для погоды добавляем требование актуальности
  if (['погода', 'температура', 'осадки'].some(word => queryLower.includes(word))) {
    return `${query}. Найди актуальный прогноз погоды с указанием даты и источника данных.`;
  }
  
  // Для капитализации компаний
  if (queryLower.includes('капитализац') && 
      ['apple', 'google', 'microsoft', 'amazon', 'сбербанк', 'газпром', 'яндекс', 'tesla', 'компании', 'корпорации']
      .some(company => queryLower.includes(company))) {
    const companyNames: string[] = [];
    ['apple', 'google', 'microsoft', 'amazon', 'сбербанк', 'газпром', 'яндекс', 'tesla']
      .forEach(company => {
        if (queryLower.includes(company)) {
          companyNames.push(company);
        }
      });
    
    const companyStr = companyNames.length ? companyNames.join(', ') : 'указанной компании';
    
    return `${query}. Укажи ТЕКУЩУЮ рыночную капитализацию ${companyStr} в долларах США ` +
           `на сегодняшний день. ОБЯЗАТЕЛЬНО укажи точную цифру, дату оценки и источник ` +
           `данных (например, биржа NYSE/NASDAQ/MOEX). Используй финансовые и новостные сайты ` +
           `с самыми актуальными данными - Bloomberg, Yahoo Finance, MarketWatch, Reuters или Google Finance.`;
  }
  
  // Для акций компаний
  if (queryLower.includes('акци') && 
      ['apple', 'google', 'microsoft', 'amazon', 'сбербанк', 'газпром', 'яндекс', 'tesla', 'компании', 'корпорации']
      .some(company => queryLower.includes(company))) {
    return `${query}. Укажи ТОЛЬКО текущую цену акций на сегодняшний день. ОБЯЗАТЕЛЬНО укажи ` +
           `точную цифру стоимости за акцию, биржевой тикер, дату и источник данных - биржу или ` +
           `финансовый портал. Используй данные из Yahoo Finance, Bloomberg, MarketWatch или Reuters.`;
  }
  
  // Общие финансовые запросы
  if (['компани', 'капитализац', 'биржа', 'акци', 'бизнес', 'рейтинг', 'топ']
      .some(word => queryLower.includes(word))) {
    return `${query}. Предоставь ТОЛЬКО актуальные данные на текущую дату. Укажи точные цифры и источники информации (биржа, финансовый портал, годовой отчет компании).`;
  }
  
  // Для крипто-запросов
  if (['крипто', 'биткоин', 'bitcoin', 'eth', 'блокчейн']
      .some(word => queryLower.includes(word))) {
    return `${query}. Предоставь ТОЛЬКО самые актуальные данные с сегодняшней даты. Укажи текущие цены и источники (биржи, криптовалютные трекеры).`;
  }
  
  // Общее улучшение для любых запросов
  return `${query}. Предоставь только проверенные факты с указанием актуальных источников информации.`;
}

// Функция для разделения сложного запроса на подзапросы
function splitComplexQuery(query: string): string[] {
  // Разделители для сложных запросов
  const separators = ['. и ', ' и ', '. а также ', '. также ', '. кроме того, ', '. при этом ', '. еще ', '. плюс '];
  
  // Ищем разделители в запросе
  for (const separator of separators) {
    if (query.toLowerCase().includes(separator.toLowerCase())) {
      const parts = query.split(separator, 2);
      // Рекурсивно разделяем дальше, если необходимо
      const result = [parts[0]];
      if (parts.length > 1 && parts[1].trim()) {
        result.push(...splitComplexQuery(parts[1]));
      }
      return result;
    }
  }
  
  // Проверка на запрос с двумя разными темами
  const weatherPattern = /погод[аеуы]|температур[аеы]|осадк[иов]/;
  const financialPattern = /компани[яйи]|акци[яйи]|капитализаци[яйи]|рынок|биржа|рейтинг|топ/;
  const cryptoPattern = /крипто|биткоин|ethereum|блокчейн/;
  
  // Если есть признаки двух разных тем, разделяем запрос по точке или запятой
  const topicsCount = [
    weatherPattern.test(query.toLowerCase()) ? 1 : 0,
    financialPattern.test(query.toLowerCase()) ? 1 : 0,
    cryptoPattern.test(query.toLowerCase()) ? 1 : 0
  ].reduce((sum, value) => sum + value, 0);
  
  if (topicsCount > 1) {
    for (const splitChar of ['. ', ', ']) {
      if (query.includes(splitChar)) {
        const parts = query.split(splitChar)
          .map(p => p.trim())
          .filter(p => p);
        if (parts.length > 1) {
          return parts;
        }
      }
    }
  }
  
  // Если не нашли разделителей, возвращаем исходный запрос как единственный элемент списка
  return [query];
}

// Функция для генерации тестового ответа
function generateTestResponse(query: string): string {
  const queryLower = query.toLowerCase();
  const currentDate = new Date().toLocaleDateString('ru-RU');
  
  if (queryLower.includes('капитализац')) {
    if (queryLower.includes('apple')) {
      return `По состоянию на ${currentDate}, рыночная капитализация Apple Inc. (AAPL) составляет **$3.44 триллиона долларов США**. Это делает Apple самой дорогой публичной компанией в мире по рыночной стоимости.

Данные о капитализации основаны на текущей цене акций $224.32 за акцию и общем количестве выпущенных акций в обращении 15.33 миллиарда.

Источники информации:
- [Yahoo Finance](https://finance.yahoo.com/quote/AAPL/)
- [Bloomberg](https://www.bloomberg.com/quote/AAPL:US)
- [MarketWatch](https://www.marketwatch.com/investing/stock/aapl)

Обратите внимание, что рыночная капитализация может меняться в течение дня в зависимости от колебаний цены акций компании на бирже NASDAQ.`;
    } else if (queryLower.includes('google') || queryLower.includes('alphabet')) {
      return `По состоянию на ${currentDate}, рыночная капитализация Alphabet Inc. (материнской компании Google) составляет **$2.12 триллиона долларов США**.

Эта оценка основана на текущих ценах акций:
- Акции класса A (GOOGL): $174.25 за акцию
- Акции класса C (GOOG): $175.77 за акцию

Alphabet имеет две основные категории акций, торгующихся на бирже NASDAQ. Общее количество акций в обращении составляет около 12.8 миллиарда.

Источники информации:
- [Yahoo Finance](https://finance.yahoo.com/quote/GOOGL/)
- [Bloomberg](https://www.bloomberg.com/quote/GOOGL:US)
- [NASDAQ](https://www.nasdaq.com/market-activity/stocks/googl)`;
    }
  }

  if (queryLower.includes('погод')) {
    return `Погода на ${currentDate}: 
    
В Москве сегодня переменная облачность, температура от +18°C до +22°C днем. Осадков не ожидается, ветер юго-западный 3-5 м/с.

В Санкт-Петербурге облачно с прояснениями, возможен небольшой дождь. Температура от +16°C до +19°C. Ветер западный 4-6 м/с.

Источник данных: [Гидрометцентр России](https://meteoinfo.ru)`;
  }

  // Для других запросов
  return `Результаты поиска по запросу "${query}" (тестовый режим):

Найдена релевантная информация из нескольких источников. Обратите внимание, что в тестовом режиме не происходит реального обращения к поисковой системе, и эти данные представлены только для демонстрации.

Источники:
- [Пример источника 1](https://example.com/source1)
- [Пример источника 2](https://example.com/source2)

Для получения актуальных данных, пожалуйста, отключите тестовый режим.`;
}

export async function POST(req: Request) {
  try {
    // Получаем данные запроса
    const data = await req.json();
    const { query } = data;
    
    if (!query) {
      return NextResponse.json({
        error: 'Отсутствует поисковый запрос',
      }, { status: 400 });
    }
    
    // Проверяем, включен ли тестовый режим
    const testMode = process.env.TEST_MODE === 'true';
    const perplexityApiKey = process.env.PERPLEXITY_API_KEY;
    
    // Включаем тестовый режим, если установлен флаг или отсутствует API ключ
    const useTestMode = testMode || !perplexityApiKey;
    
    if (useTestMode) {
      console.log('Использование тестового режима для поискового запроса');
      const testResponse = generateTestResponse(query);
      
      return NextResponse.json({
        test_mode: true,
        result: testResponse,
      }, { status: 200 });
    }
    
    // Разделяем составные запросы на отдельные подзапросы
    const subqueries = splitComplexQuery(query);
    
    // Собираем результаты поиска для всех подзапросов
    const allResults = [];
    
    for (const subquery of subqueries) {
      // Добавляем уточнения для повышения точности поиска
      const searchQuery = enhanceQuery(subquery);
      console.log(`Улучшенный запрос: ${searchQuery}`);
      
      // Формируем запрос к API с использованием модели "sonar" согласно документации
      const apiData = {
        model: 'sonar',
        messages: [
          {
            role: 'system',
            content: 'Ты - поисковый ассистент, который предоставляет ТОЛЬКО фактическую информацию из интернета. НЕ ГЕНЕРИРУЙ И НЕ ПРИДУМЫВАЙ ДАННЫЕ. Если ты не можешь найти точную информацию, четко укажи это. Всегда указывай ИСТОЧНИКИ предоставляемой информации в виде ссылок. Когда речь идет о компаниях, акциях, рейтингах - приводи ТОЛЬКО СВЕЖИЕ данные с актуальной датой. Для вопросов о погоде обязательно указывай прогноз с датой.'
          },
          {
            role: 'user',
            content: searchQuery
          }
        ],
        temperature: 0.1,
        top_p: 0.9,
        max_tokens: 1000
      };
      
      console.log(`Отправка запроса для подзапроса: ${subquery}`);
      
      // Настраиваем URL и заголовки для запроса
      const headers = {
        'Authorization': `Bearer ${perplexityApiKey}`,
        'Content-Type': 'application/json'
      };
      
      try {
        const startTime = Date.now();
        const response = await fetch(baseUrl, {
          method: 'POST',
          headers: headers,
          body: JSON.stringify(apiData)
        });
        
        const requestTime = (Date.now() - startTime) / 1000;
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Ошибка Perplexity API: ${response.status}`);
          console.error(`Детали ошибки: ${errorText.slice(0, 500)}`);
          
          throw new Error(`Ошибка API: ${response.status}`);
        }
        
        // Обрабатываем ответ
        const responseData = await response.json();
        
        console.log(`Perplexity API вернул ID: ${responseData.id || 'N/A'}`);
        
        // Обрабатываем результаты поиска
        if (responseData.choices && responseData.choices.length > 0) {
          // Извлекаем содержимое из ответа
          const content = responseData.choices[0].message.content;
          console.log(`Получен ответ от Perplexity длиной ${content.length} символов`);
          
          // Преобразуем результаты в текстовый формат
          allResults.push({ query: subquery, result: content });
        } else {
          console.warn(`Результаты поиска не найдены в ответе Perplexity: ${JSON.stringify(responseData)}`);
          allResults.push({ query: subquery, result: 'Информация по запросу не найдена.' });
        }
        
      } catch (error) {
        console.error(`Ошибка при обработке подзапроса: ${error}`);
        allResults.push({ query: subquery, result: 'Произошла ошибка при поиске информации.' });
      }
    }
    
    // Комбинируем результаты всех подзапросов
    let finalResult;
    
    if (allResults.length === 1) {
      // Если был только один подзапрос, просто возвращаем его результат
      finalResult = allResults[0].result;
    } else {
      // Иначе формируем составной результат
      finalResult = '\n\n=== РЕЗУЛЬТАТЫ ПОИСКА ===\n\n';
      
      for (const resultItem of allResults) {
        finalResult += `ЗАПРОС: ${resultItem.query}\n\n${resultItem.result}\n\n---\n\n`;
      }
    }
    
    return NextResponse.json({
      test_mode: false,
      result: finalResult,
    }, { status: 200 });
    
  } catch (error) {
    console.error('Ошибка при обработке поискового запроса:', error);
    
    return NextResponse.json({
      error: 'Произошла ошибка при обработке поискового запроса',
      test_mode: false
    }, { status: 500 });
  }
}
