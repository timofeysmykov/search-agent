// Дождемся полной загрузки DOM перед выполнением скрипта
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM полностью загружен');
    
    // Получаем элементы DOM
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const statusDiv = document.getElementById('status');
    const sendButton = document.getElementById('send-button');
    const themeToggle = document.getElementById('theme-toggle');
    
    // Проверяем наличие элементов
    if (!chatContainer) console.error('Ошибка: chatContainer не найден!');
    if (!userInput) console.error('Ошибка: userInput не найден!');
    if (!statusDiv) console.error('Ошибка: statusDiv не найден!');
    if (!sendButton) console.error('Ошибка: sendButton не найден!');
    
    // Инициализация высоты textarea
    function initTextarea() {
        if (userInput) {
            userInput.focus();
            userInput.style.height = 'auto';
            userInput.style.height = (userInput.scrollHeight) + 'px';
        }
    }
    
    // Инициализируем textarea
    initTextarea();
    
    // Обработка нажатия Enter в textarea
    if (userInput) {
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter нажат, отправляем сообщение');
                sendQuery();
            }
        });
        
        // Автоизменение высоты textarea при вводе
        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    // Обработчик нажатия кнопки отправки
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Кнопка отправки нажата');
            sendQuery();
        });
    }
    
    // Обработчик переключения темы
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('light-theme');
            console.log('Тема переключена');
        });
    }
    
    // Форматирование текста с поддержкой markdown
    function formatText(text) {
        text = text.replace(/\n/g, '<br>');
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/_(.*?)_/g, '<em>$1</em>');
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');
        return text;
    }
    
    // Добавление сообщения в чат
    function addMessage(text, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message agent-message';
        
        if (!isUser) {
            messageDiv.innerHTML = formatText(text);
        } else {
            messageDiv.textContent = text;
        }
        
        chatContainer.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 100);
    }
    
    // Индикаторы статуса
    function showLoading() {
        statusDiv.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Обрабатываю ваш запрос...</p>
            </div>
        `;
        statusDiv.style.display = 'block';
    }
    
    function clearStatus() {
        statusDiv.innerHTML = '';
        statusDiv.style.display = 'none';
    }
    
    function showError(message) {
        statusDiv.innerHTML = `
            <div class="error">
                <span class="material-symbols-rounded">error</span>
                <p>${message}</p>
            </div>
        `;
        statusDiv.style.display = 'block';
        
        // Автоматически скрываем ошибку через 5 секунд
        setTimeout(() => {
            clearStatus();
        }, 5000);
    }
    
    function addSearchIndicator() {
        const searchIndicator = document.createElement('div');
        searchIndicator.className = 'search-indicator';
        searchIndicator.innerHTML = `
            <span class="material-symbols-rounded" style="font-size: 14px;">search</span>
            <span>Для ответа использовалась информация из поиска</span>
        `;
        chatContainer.appendChild(searchIndicator);
    }
    
    // Функция отправки запроса
    async function sendQuery() {
        // Проверка на пустой запрос
        const query = userInput.value.trim();
        if (!query) {
            console.log('Пустой запрос, отмена отправки');
            userInput.focus();
            return;
        }
        
        // Проверка, не отправляется ли уже запрос
        if (sendButton.disabled) {
            console.log('Запрос уже отправляется, отмена');
            return;
        }
        
        // Блокируем кнопку отправки и поле ввода
        sendButton.disabled = true;
        sendButton.classList.add('disabled');
        
        // Добавляем сообщение пользователя в чат
        addMessage(query, true);
        
        // Очищаем поле ввода и возвращаем ему фокус
        userInput.value = '';
        userInput.style.height = 'auto';
        userInput.focus();
        
        // Показываем индикатор загрузки
        showLoading();
        
        try {
            // Отправляем запрос к API
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            // Проверяем успешность ответа
            if (!response.ok) {
                throw new Error(`Ошибка HTTP: ${response.status}`);
            }
            
            // Парсим JSON-ответ
            const data = await response.json();
            
            // Проверяем на ошибки в ответе
            if (data.error) {
                showError(`Ошибка: ${data.error}`);
                return;
            }
            
            // Добавляем ответ в чат
            addMessage(data.response, false);
            
            // Если был использован поиск, показываем индикатор
            if (data.search_performed) {
                addSearchIndicator();
            }
            
            // Скрываем индикатор загрузки
            clearStatus();
            
        } catch (error) {
            console.error('Ошибка:', error);
            showError(`Произошла ошибка при обработке запроса: ${error.message}`);
        } finally {
            // Разблокируем кнопку отправки
            sendButton.disabled = false;
            sendButton.classList.remove('disabled');
        }
    }
    
    // Экспортируем функцию sendQuery в глобальную область видимости
    window.sendQuery = sendQuery;
});
