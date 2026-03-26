#!/bin/bash

# Конфигурация cron-задач для MTS MultAgent System
# Этот скрипт устанавливает автоматические задачи для системы

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/cron.log"

# Создаем директорию для логов если не существует
mkdir -p "$(dirname "$LOG_FILE")"

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Функция запуска агента
run_agent() {
    local agent_name="$1"
    local log_file="$PROJECT_ROOT/logs/${agent_name}_$(date '+%Y%m%d_%H%M%S').log"
    
    log "Запуск агента: $agent_name"
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate 2>/dev/null || source /opt/mts-multagent/venv/bin/activate 2>/dev/null
    
    # Запуск агента с логированием
    python -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from src.core.agent_orchestrator import AgentOrchestrator
from src.agents.${agent_name} import ${agent_name^}

async def run_${agent_name}():
    try:
        orchestrator = AgentOrchestrator()
        agent = ${agent_name^}()
        
        orchestrator.register_agent('${agent_name}', agent, priority=1)
        
        workflow_config = {
            'agents': ['${agent_name}'],
            'execution_constraints': {'sequenced': True}
        }
        
        data_sources = {'${agent_name}': {}}
        
        result = await orchestrator.execute_workflow(workflow_config, data_sources)
        
        print(f'Агент {agent_name} выполнен успешно: {result.status.value}')
        return result.status.value == 'completed'
        
    except Exception as e:
        print(f'Ошибка при выполнении агента {agent_name}: {e}')
        return False

result = asyncio.run(run_${agent_name}())
sys.exit(0 if result else 1)
" >> "$log_file" 2>&1
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        log "Агент $agent_name выполнен успешно"
    else
        log "Ошибка при выполнении агента $agent_name (код: $exit_code)"
    fi
    
    return $exit_code
}

# Функция проверки здоровья системы
health_check() {
    local log_file="$PROJECT_ROOT/logs/health_check_$(date '+%Y%m%d_%H%M%S').log"
    
    log "Запуск проверки здоровья системы"
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate 2>/dev/null || source /opt/mts-multagent/venv/bin/activate 2>/dev/null
    
    python -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from scripts.deploy import ProductionDeployer

async def health_check():
    try:
        deployer = ProductionDeployer()
        health = deployer.run_health_check()
        print(f'Проверка здоровья: {\"УСПЕШНО\" if health else «ПРОБЛЕМЫ»}')
        return health
    except Exception as e:
        print(f'Ошибка при проверке здоровья: {e}')
        return False

result = asyncio.run(health_check())
sys.exit(0 if result else 1)
" >> "$log_file" 2>&1
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        log "Проверка здоровья пройдена успешно"
    else
        log "Проблемы со здоровьем системы (код: $exit_code)"
    fi
    
    return $exit_code
}

# Функция очистки старых логов
cleanup_logs() {
    local retention_days=${1:-30}
    
    log "Очистка логов старше $retention_days дней"
    
    # Удаление старых логов
    find "$PROJECT_ROOT/logs" -name "*.log" -type f -mtime +$retention_days -delete
    find "$PROJECT_ROOT/logs" -name "*.log.*" -type f -mtime +$retention_days -delete
    
    log "Очистка логов завершена"
}

# Функция резервного копирования
backup_data() {
    local backup_dir="$PROJECT_ROOT/backups/backup_$(date '+%Y%m%d_%H%M%S')"
    
    log "Создание резервной копии"
    
    mkdir -p "$backup_dir"
    
    # Копирование важных директорий
    cp -r "$PROJECT_ROOT/data" "$backup_dir/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT/config" "$backup_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/.env" "$backup_dir/" 2>/dev/null || true
    
    # Сжатие бэкапа
    cd "$PROJECT_ROOT/backups"
    tar -czf "$(basename "$backup_dir").tar.gz" "$(basename "$backup_dir")"
    rm -rf "$backup_dir"
    
    log "Резервная копия создана: $(basename "$backup_dir").tar.gz"
}

# Функция установки cron-задач
install_cron() {
    log "Установка cron-задач"
    
    # Создаем временный файл с cron-задачами
    local cron_file="/tmp/mts_multagent_cron"
    cat > "$cron_file" << EOF
# MTS MultAgent System Cron Tasks
# ===================================

# Ежедневный анализ JIRA (будни в 8:00)
0 8 * * 1-5 $SCRIPT_DIR/cron_jobs.sh run_daily_jira_analyzer >> $LOG_FILE 2>&1

# Ежедневный анализ совещаний (будни в 18:00)
0 18 * * 1-5 $SCRIPT_DIR/cron_jobs.sh run_daily_meeting_analyzer >> $LOG_FILE 2>&1

# Проверка здоровья системы (каждые 10 минут)
*/10 * * * * $SCRIPT_DIR/cron_jobs.sh health_check >> $LOG_FILE 2>&1

# Очистка старых логов (ежедневно в 2:00)
0 2 * * * $SCRIPT_DIR/cron_jobs.sh cleanup_logs 30 >> $LOG_FILE 2>&1

# Резервное копирование (ежедневно в 3:00)
0 3 * * * $SCRIPT_DIR/cron_jobs.sh backup_data >> $LOG_FILE 2>&1

# Перезапуск сервиса при необходимости (ежечасно)
0 * * * * systemctl restart mts-multagent >> $LOG_FILE 2>&1 || true

# Обновление зависимостей (еженедельно в воскресенье 4:00)
0 4 * * 0 cd $PROJECT_ROOT && git pull && pip install -r requirements.txt >> $LOG_FILE 2>&1 || true
EOF
    
    # Установка cron-задач
    crontab "$cron_file" && rm "$cron_file"
    
    if [ $? -eq 0 ]; then
        log "Cron-задачи установлены успешно"
        echo "✅ Cron-задачи установлены"
    else
        log "Ошибка при установке cron-задач"
        echo "❌ Ошибка при установке cron-задач"
        return 1
    fi
}

# Функция удаления cron-задач
remove_cron() {
    log "Удаление cron-задач"
    
    # Создаем временный файл с исключенными задачами
    local current_cron="/tmp/current_cron"
    crontab -l > "$current_cron" 2>/dev/null || true
    
    # Удаляем строки, связанные с MTS MultAgent
    grep -v "MTS MultAgent System" "$current_cron" 2>/dev/null | grep -v "$SCRIPT_DIR/cron_jobs.sh" > "${current_cron}.new" || true
    
    # Устанавливаем обновленный crontab
    crontab "${current_cron}.new" 2>/dev/null || true
    
    # Очистка
    rm -f "$current_cron" "${current_cron}.new"
    
    log "Cron-задачи удалены"
    echo "✅ Cron-задачи удалены"
}

# Функция вывода текущих cron-задач
show_cron() {
    echo "📅 Текущие cron-задачи:"
    echo "========================="
    crontab -l | grep -E "(MTS MultAgent|$SCRIPT_DIR/cron_jobs.sh)" || echo "Нет активных задач"
    echo "========================="
}

# Функция тестового запуска
test_run() {
    echo "🧪 Тестовый запуск агентов..."
    
    echo "Запуск daily_jira_analyzer:"
    run_agent "daily_jira_analyzer"
    
    echo "Запуск daily_meeting_analyzer:"
    run_agent "daily_meeting_analyzer"
    
    echo "Проверка здоровья:"
    health_check
    
    echo "✅ Тестовый запуск завершен"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "run_daily_jira_analyzer")
        run_agent "daily_jira_analyzer"
        ;;
    "run_daily_meeting_analyzer")
        run_agent "daily_meeting_analyzer"
        ;;
    "health_check")
        health_check
        ;;
    "cleanup_logs")
        cleanup_logs "${2:-30}"
        ;;
    "backup_data")
        backup_data
        ;;
    "install")
        install_cron
        ;;
    "remove")
        remove_cron
        ;;
    "show")
        show_cron
        ;;
    "test")
        test_run
        ;;
    "help"|"-h"|"--help")
        cat << EOF
Использование: $0 [КОМАНДА] [АРГУМЕНТЫ]

Команды:
  run_daily_jira_analyzer     Запуск анализатора JIRA
  run_daily_meeting_analyzer  Запуск анализатора совещаний
  health_check                Проверка здоровья системы
  cleanup_logs [дни]          Очистка старых логов (по умолчанию 30 дней)
  backup_data                  Создание резервной копии
  install                      Установка всех cron-задач
  remove                       Удаление всех cron-задач
  show                         Показать текущие cron-задачи
  test                         Тестовый запуск всех агентов
  help                         Показать эту справку

Примеры:
  $0 install                   # Установить все cron-задачи
  $0 test                      # Тестовый запуск
  $0 health_check              # Проверить здоровье системы
  $0 cleanup_logs 7            # Очистить логи старше 7 дней
EOF
        ;;
    *)
        echo "Неизвестная команда: ${1:-}"
        echo "Используйте '$0 help' для справки"
        exit 1
        ;;
esac
