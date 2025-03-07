import { anthropic } from "@ai-sdk/anthropic";
import { jsonSchema, streamText, type Message } from "ai";
import { search_perplexity } from "../../../lib/search_api";

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages, system, tools } = await req.json();
  
  // Получаем последнее сообщение пользователя для возможного поиска
  const lastUserMessage = messages.filter((m: Message) => m.role === 'user').pop();
  
  // Флаг тестового режима
  const testMode = process.env.TEST_MODE === 'true' || !process.env.CLAUDE_API_KEY;
  
  // Проверяем, нужен ли поиск
  let searchResults = "";
  let systemPromptWithSearch = system || "";
  
  if (lastUserMessage && !testMode) {
    try {
      // Выполняем поиск через Perplexity
      searchResults = await search_perplexity(lastUserMessage.content);
      
      if (searchResults) {
        // Добавляем результаты поиска к системному промпту
        systemPromptWithSearch = `${system || ""}\n\n# Результаты поиска по запросу пользователя:\n${searchResults}`;
      }
    } catch (error) {
      console.error("Ошибка при выполнении поиска:", error);
    }
  }
  
  // Тестовый режим для работы без API ключа
  if (testMode) {
    // Возвращаем заглушку для тестового режима
    const testResponse = `Это тестовый ответ на ваш запрос: "${lastUserMessage?.content || 'Запрос отсутствует'}".\n\nЯ работаю в тестовом режиме без использования API ключей.`;
    
    return new Response(JSON.stringify({ content: testResponse }), {
      headers: { "Content-Type": "application/json" }
    });
  }

  // Используем Claude 3.5 Haiku для получения ответа
  const result = streamText({
    model: anthropic("claude-3-haiku-20240307"),
    messages,
    system: systemPromptWithSearch,
    tools: tools ? Object.fromEntries(
      Object.keys(tools).map((name) => [
        name,
        { ...tools[name], parameters: jsonSchema(tools[name].parameters) },
      ])
    ) : undefined,
  });

  return result.toDataStreamResponse();
}
