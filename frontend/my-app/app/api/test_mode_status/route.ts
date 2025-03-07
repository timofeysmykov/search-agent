import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Проверяем наличие API ключей для определения тестового режима
    const claudeApiKey = process.env.CLAUDE_API_KEY;
    const perplexityApiKey = process.env.PERPLEXITY_API_KEY;
    
    // Если отсутствует хотя бы один ключ, включаем принудительный тестовый режим
    const forcedTestMode = !claudeApiKey || !perplexityApiKey;
    
    // Получаем текущее значение тестового режима из env или используем принудительный
    const testMode = process.env.TEST_MODE === 'true' || forcedTestMode;
    
    return NextResponse.json({
      test_mode: testMode,
      forced_test_mode: forcedTestMode,
      message: `Тестовый режим ${testMode ? 'включен' : 'выключен'}`
    }, { status: 200 });
  } catch (error) {
    console.error('Ошибка при получении статуса тестового режима:', error);
    
    return NextResponse.json({ 
      error: 'Ошибка при получении статуса тестового режима',
      test_mode: false,
      forced_test_mode: false
    }, { status: 500 });
  }
}
