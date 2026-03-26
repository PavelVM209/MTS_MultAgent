# Руководство по развертыванию MTS MultAgent System

## 📋 Обзор

MTS MultAgent System - это многоагентная система для автоматического анализа задач JIRA и протоколов совещаний с генерацией отчетов в Confluence.

## 🏗️ Архитектура системы

Комиссия состоит из следующих компонентов:

### 🤖 Агенты
- **DailyJiraAnalyzer** - Анализатор ежедневных задач JIRA
- **DailyMeetingAnalyzer** - Анализатор протоколов совещаний
- **AgentOrchestrator** - Оркестратор для координации работы агентов

### 🔧 Основные компоненты
- **LLMClient** - Клиент для взаимодействия с языковыми моделями (OpenAI GPT-4)
- **JSONMemoryStore** - Система хранения данных
- **ConfigManager** - Управление конфигурацией
- **QualityMetrics** - Система оценки качества анализа

## 🚀 Требования к системе

### Системные требования
- **ОС**: Linux (Ubuntu 20.04+, CentOS 8+) или macOS
- **Python**: 3.8+ 
- **RAM**: Минимум 4GB, рекомендуемо 8GB+
- **Дисковое пространство**: 10GB+ для логов и данных
- **Сеть**: Доступ к API JIRA, Confluence и OpenAI

### Программные зависимости
```bash
# Python пакеты
pip install -r requirements.txt

# Системные пакеты (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3.8 python3.8-venv python3-pip
sudo apt-get install git curl wget

# Системные пакеты (CentOS/RHEL)
sudo yum update
sudo yum install python38 python38-pip git curl wget
```

## 📁 Структура директорий

```
/opt/mts-multagent/
├── src/                    # Исходный код
│   ├── core/              # Основные компоненты
│   ├── agents/            # Агенты анализа
│   ├── schemas/           # Схемы данных
│   └── cli/               # Интерфейс командной строки
├── config/                # Конфигурационные файлы
│   ├── base.yaml         # Базовая конфигурация
│   ├── development.yaml  # Конфигурация для разработки
│   └── production.yaml   # Production конфигурация
├── scripts/               # Скрипты развертывания
│   ├── deploy.py         # Основной скрипт развертывания
│   ├── cron_jobs.sh      # Cron-задачи
│   └── mts-multagent.service # Systemd сервис
├── tests/                 # Тесты
├── logs/                  # Логи системы
├── data/                  # Данные системы
├── backups/              # Резервные копии
├── temp/                 # Временные файлы
└── .env                  # Переменные окружения
```

## 🔧 Установка и настройка

### 1. Подготовка окружения

```bash
# Создание пользователя
sudo useradd -m -s /bin/bash multagent
sudo usermod -aG sudo multagent

# Переключение на пользователя
sudo su - multagent

# Создание директории проекта
sudo mkdir -p /opt/mts-multagent
sudo chown multagent:multagent /opt/mts-multagent
cd /opt/mts-multagent
```

### 2. Клонирование репозитория

```bash
git clone https://github.com/mts/mts-multagent.git .
# или копирование файлов с разработческой машины
```

### 3. Создание виртуального окружения

```bash
python3.8 -m venv venv
source venv/bin/activate
```

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 5. Настройка переменных окружения

```bash
# Копирование шаблона
cp .env.example .env

# Редактирование конфигурации
nano .env
```

Обязательные переменные окружения:
```bash
# API ключи
OPENAI_API_KEY=sk-...
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-api-token
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-api-token

# Опциональные переменные
WEBHOOK_URL=https://hooks.slack.com/...
SMTP_SERVER=smtp.company.com
SMTP_USERNAME=noreply@company.com
SMTP_PASSWORD=your-password
```

## 🚀 Развертывание

### Автоматическое развертывание

```bash
# Запуск скрипта развертывания
python scripts/deploy.py

# Скрипт выполнит:
# - Проверку окружения
# - Создание директорий
# - Валидацию конфигурации
# - Инициализацию базы данных
# - Настройку логирования
# - Проверку работоспособности
```

### Ручное развертывание

```bash
# 1. Создание директорий
mkdir -p logs data temp backups

# 2. Установка прав доступа
chmod 755 logs data temp backups
chown -R multagent:multagent /opt/mts-multagent

# 3. Тестовый запуск
source venv/bin/activate
python -m src.cli.main --help
```

## ⚙️ Настройка автоматизации

### Cron-задачи

```bash
# Установка cron-задач
./scripts/cron_jobs.sh install

# Просмотр текущих задач
./scripts/cron_jobs.sh show

# Тестовый запуск
./scripts/cron_jobs.sh test

# Удаление задач
./scripts/cron_jobs.sh remove
```

### Systemd сервис

```bash
# Копирование файла сервиса
sudo cp scripts/mts-multagent.service /etc/systemd/system/

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable mts-multagent

# Запуск сервиса
sudo systemctl start mts-multagent

# Проверка статуса
sudo systemctl status mts-multagent

# Просмотр логов
sudo journalctl -u mts-multagent -f
```

## 📊 Настройка расписания

### Конфигурация по умолчанию

```yaml
# config/production.yaml
scheduler:
  jobs:
    daily_jira_analysis:
      enabled: true
      cron: "0 8 * * 1-5"  # Будни в 8:00
      agent: "daily_jira_analyzer"
    daily_meeting_analysis:
      enabled: true
      cron: "0 18 * * 1-5"  # Будни в 18:00
      agent: "daily_meeting_analyzer"
    health_check:
      enabled: true
      cron: "*/10 * * * *"  # Каждые 10 минут
      agent: "health_monitor"
```

### Изменение расписания

```bash
# Редактирование конфигурации
nano config/production.yaml

# Перезагрузка сервиса для применения изменений
sudo systemctl restart mts-multagent
```

## 🔍 Мониторинг и логирование

### Структура логов

```
logs/
├── app.log              # Основной лог приложения
├── error.log            # Лог ошибок
├── performance.log      # Лог производительности
├── security.log         # Лог безопасности
├── deployment_*.log     # Логи развертывания
├── cron.log             # Лог cron-задач
└── metrics/             # Метрики мониторинга
    ├── health/
    └── alerts/
```

### Просмотр логов

```bash
# Основной лог
tail -f logs/app.log

# Лог ошибок
tail -f logs/error.log

# Лог производительности
tail -f logs/performance.log

# Cron-логи
tail -f logs/cron.log

# Systemd логи
sudo journalctl -u mts-multagent -f
```

### Проверка здоровья системы

```bash
# Автоматическая проверка
python scripts/deploy.py --health-check

# Ручная проверка
./scripts/cron_jobs.sh health_check

# Детальная диагностика
python -c "
import asyncio
from scripts.deploy import ProductionDeployer
deployer = ProductionDeployer()
health = asyncio.run(deployer.run_health_check())
print('System Healthy:', health)
"
```

## 🔄 Обслуживание

### Резервное копирование

```bash
# Автоматическое резервное копирование (настроено в cron)
# Ежедневно в 3:00

# Ручное резервное копирование
./scripts/cron_jobs.sh backup_data

# Просмотр бэкапов
ls -la backups/
```

### Очистка логов

```bash
# Автоматическая очистка (настроено в cron)
# Удаляются логи старше 30 дней

# Ручная очистка
./scripts/cron_jobs.sh cleanup_logs 7  # Очистка логов старше 7 дней
```

### Обновление системы

```bash
# Автоматическое обновление (настроено в cron)
# Еженедельно в воскресенье 4:00

# Ручное обновление
git pull origin main
pip install -r requirements.txt
sudo systemctl restart mts-multagent
```

## 🚨 Устранение неисправностей

### Частые проблемы

#### 1. Ошибка подключения к JIRA
```
Решение: Проверьте JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN в .env файле
```

#### 2. Проблемы с OpenAI API
```
Решение: Проверьте OPENAI_API_KEY и баланс счета OpenAI
```

#### 3. Ошибки доступа к файлам
```bash
# Проверка прав доступа
ls -la /opt/mts-multagent/
sudo chown -R multagent:multagent /opt/mts-multagent
chmod -R 755 /opt/mts-multagent
```

#### 4. Проблемы с сервисом systemd
```bash
# Проверка статуса
sudo systemctl status mts-multagent

# Перезапуск
sudo systemctl restart mts-multagent

# Просмотр логов
sudo journalctl -u mts-multagent --since "1 hour ago"
```

### Диагностика

```bash
# Полная диагностика системы
python scripts/deploy.py --full-diagnostic

# Проверка конфигурации
python -c "
from src.core.config import get_config
config = get_config()
print('Configuration:', config)
"

# Тест запуска агентов
./scripts/cron_jobs.sh test
```

## 📈 Оптимизация производительности

### Настройки производительности

```yaml
# config/production.yaml
performance:
  caching:
    enabled: true
    ttl: 3600
    max_size: "100MB"
  async_workers: 4
  batch_processing:
    enabled: true
    batch_size: 20
    timeout: 60

orchestrator:
  workflow:
    max_parallel_agents: 4
    agent_timeout: 300
    enable_data_sharing: true
```

### Мониторинг производительности

```bash
# Просмотр метрик
tail -f logs/performance.log

# Анализ времени выполнения
grep "execution_time" logs/app.log | tail -20
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Переменные окружения**: Храните секретные ключи в `.env` файле с ограниченными правами доступа
   ```bash
   chmod 600 .env
   ```

2. **Права доступа**: Ограничьте права на запись в конфигурационные файлы
   ```bash
   chmod 644 config/*.yaml
   ```

3. **Сетевой доступ**: Ограничьте доступ к API с помощью IP-фильтрации
4. **Логирование безопасности**: Включите логирование безопасности в production
5. **Регулярные обновления**: Обновляйте зависимости и системные пакеты

### Аудит безопасности

```bash
# Проверка прав доступа
find /opt/mts-multagent -type f -perm /o+w

# Проверка наличия секретов в коде
grep -r "sk-" src/ || echo "No secrets found in code"

# Проверка открытых портов
netstat -tlnp | grep python
```

## 📞 Поддержка

### Контактная информация

- **Техническая поддержка**: support@mts.ru
- **Документация**: https://github.com/mts/mts-multagent/docs
- **Issues**: https://github.com/mts/mts-multagent/issues

### Сбор информации для поддержки

```bash
# Создание архива для поддержки
tar -czf mts-multagent-support-$(date +%Y%m%d).tar.gz \
    logs/ \
    config/ \
    --exclude=logs/*.log \
    --exclude=config/.env

# Отправка архива в поддержку
```

---

## 📚 Дополнительная документация

- [Архитектура системы](ARCHITECTURE.md)
- [API документация](API.md)
- [Руководство разработчика](DEVELOPER.md)
- [FAQ](FAQ.md)

---

**Версия документации**: 1.0.0  
**Последнее обновление**: 26 марта 2026 г.
