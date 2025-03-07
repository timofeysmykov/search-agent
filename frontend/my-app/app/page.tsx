"use client";
import { useState, useEffect } from "react";
import { Thread } from "@/components/assistant-ui/thread";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { ThreadList } from "@/components/assistant-ui/thread-list";

export default function Home() {
  const [testMode, setTestMode] = useState(false);
  const [darkTheme, setDarkTheme] = useState(true);
  
  // Инициализация темы при загрузке страницы
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setDarkTheme(savedTheme === 'dark');
    document.body.classList.toggle('light-theme', savedTheme !== 'dark');
    
    // Проверка статуса тестового режима
    checkTestModeStatus();
  }, []);
  
  // Функция для проверки статуса тестового режима
  const checkTestModeStatus = async () => {
    try {
      const response = await fetch('/api/test_mode_status');
      const data = await response.json();
      setTestMode(data.test_mode);
      
      if (data.test_mode && data.forced_test_mode) {
        showNotification('Приложение запущено в тестовом режиме из-за отсутствия API ключей');
      }
    } catch (error) {
      console.error('Ошибка при получении статуса тестового режима:', error);
      setTestMode(false);
    }
  };
  
  // Показ временного уведомления
  const showNotification = (message: string) => {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow-lg z-50';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transition = 'opacity 0.5s';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 500);
    }, 5000);
  };
  
  // Переключение темы
  const toggleTheme = () => {
    const newTheme = darkTheme ? 'light' : 'dark';
    setDarkTheme(!darkTheme);
    localStorage.setItem('theme', newTheme);
    document.body.classList.toggle('light-theme', newTheme === 'light');
  };
  
  // Переключение тестового режима
  const toggleTestMode = async (enabled: boolean) => {
    try {
      const response = await fetch('/api/test_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
      
      const data = await response.json();
      setTestMode(data.test_mode);
      showNotification(data.message);
    } catch (error) {
      console.error('Ошибка при переключении тестового режима:', error);
    }
  };
  
  // Инициализация runtime для assistant-ui
  const runtime = useChatRuntime({
    api: "/api/chat",
    // Передаем тестовый режим как параметр запроса
    body: () => ({ test_mode: testMode }),
    // Добавляем функцию для поискового запроса
    search: async (query) => {
      try {
        const response = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, test_mode: testMode })
        });
        
        if (!response.ok) {
          throw new Error(`Ошибка поиска: ${response.status}`);
        }
        
        const data = await response.json();
        return data.result;
      } catch (error) {
        console.error('Ошибка при выполнении поискового запроса:', error);
        return `Ошибка при выполнении поиска: ${error.message}`;
      }
    }
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className={`min-h-dvh flex flex-col bg-gray-100 ${darkTheme ? 'dark' : 'light'}`}>
        {/* Шапка приложения */}
        <header className="bg-white dark:bg-gray-800 shadow-sm p-3 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-bold dark:text-white flex items-center">
              <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path fillRule="evenodd" d="M.458 10a9.557 9.557 0 0019.084 0A9.557 9.557 0 00.458 10zM10 2.018a8 8 0 100 15.964 8 8 0 000-15.964z" clipRule="evenodd" />
              </svg>
              AI Agent
              {testMode && <span className="ml-2 text-xs px-2 py-1 bg-yellow-500 text-black rounded-full">Тестовый режим</span>}
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Переключатель тестового режима */}
            <div className="flex items-center">
              <label className="inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={testMode}
                  onChange={(e) => toggleTestMode(e.target.checked)}
                />
                <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                <span className="ms-3 text-sm font-medium text-gray-900 dark:text-gray-300">Тестовый режим</span>
              </label>
            </div>
            
            {/* Кнопка переключения темы */}
            <button 
              onClick={toggleTheme}
              className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none"
              aria-label="Переключить тему"
            >
              {darkTheme ? (
                <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              )}
            </button>
          </div>
        </header>
      
        {/* Основной контент */}
        <main className="flex-1 grid grid-cols-[250px_1fr] gap-x-4 p-4">
          <aside className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="mb-4 flex justify-between items-center">
              <h3 className="text-lg font-medium dark:text-white">История чатов</h3>
              <button 
                className="text-blue-600 dark:text-blue-400 flex items-center text-sm hover:underline focus:outline-none"
                onClick={() => window.location.reload()}
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Новый чат
              </button>
            </div>
            <ThreadList />
          </aside>
          
          <div className="flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <Thread className="flex-1 p-4 overflow-auto" />
          </div>
        </main>
        
        <footer className="bg-white dark:bg-gray-800 shadow-sm p-2 text-center text-xs text-gray-500 dark:text-gray-400">
          Claude 3.5 Haiku + Perplexity • {new Date().getFullYear()}
        </footer>
      </div>
    </AssistantRuntimeProvider>
  );
}
