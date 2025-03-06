#!/bin/bash

# Параметры сервера
SERVER_USER="root"
SERVER_IP="88.218.93.213"
REMOTE_DIR="/opt/ai_agent"
SSH_KEY="~/.ssh/ai_agent_key_nopass"
GIT_REPO="https://github.com/timofeysmykov/search-agent.git"

echo "Начинаю деплой AI агента на сервер..."

# Установка необходимых пакетов на сервере
echo "Устанавливаю необходимые пакеты на сервере..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "apt-get update && apt-get install -y python3 python3-pip python3-venv git nginx"

# Клонирование репозитория с GitHub
echo "Клонирую репозиторий с GitHub..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "if [ ! -d $REMOTE_DIR ]; then
    mkdir -p $REMOTE_DIR
    git clone $GIT_REPO $REMOTE_DIR
else
    cd $REMOTE_DIR && git pull
fi"

# Создание виртуального окружения и установка зависимостей на сервере
echo "Создаю виртуальное окружение и устанавливаю зависимости на сервере..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $REMOTE_DIR && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt"

# Создаем файл .env на сервере, если он не существует
echo "Проверяю наличие файла .env на сервере..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "if [ ! -f $REMOTE_DIR/.env ]; then
    echo 'Создаю файл .env на сервере...'
    echo 'CLAUDE_API_KEY=your_claude_api_key' > $REMOTE_DIR/.env
    echo 'PERPLEXITY_API_KEY=your_perplexity_api_key' >> $REMOTE_DIR/.env
    echo 'Файл .env создан. Не забудьте заменить значения API ключей!'
else
    echo 'Файл .env уже существует на сервере.'
fi"

# Настройка запуска приложения через systemd
echo "Настраиваю автозапуск приложения через systemd..."
cat > /tmp/ai_agent.service << EOF
[Unit]
Description=AI Agent with Claude and Perplexity
After=network.target

[Service]
User=root
WorkingDirectory=$REMOTE_DIR
ExecStart=$REMOTE_DIR/venv/bin/python $REMOTE_DIR/web_app.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Копируем файл службы на сервер и включаем её
scp -i $SSH_KEY /tmp/ai_agent.service $SERVER_USER@$SERVER_IP:/etc/systemd/system/
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "systemctl daemon-reload && systemctl enable ai_agent.service && systemctl restart ai_agent.service"

# Настройка Nginx для веб-доступа
echo "Настраиваю Nginx для веб-доступа..."
cat > /tmp/ai_agent_nginx << EOF
server {
    listen 80;
    server_name $SERVER_IP;

    location / {
        proxy_pass http://localhost:5007;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Копируем конфигурацию Nginx на сервер и включаем её
scp -i $SSH_KEY /tmp/ai_agent_nginx $SERVER_USER@$SERVER_IP:/etc/nginx/sites-available/ai_agent
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "ln -sf /etc/nginx/sites-available/ai_agent /etc/nginx/sites-enabled/ && nginx -t && systemctl restart nginx"

echo "Деплой завершен успешно!"
echo "Приложение доступно по адресу: http://$SERVER_IP"
