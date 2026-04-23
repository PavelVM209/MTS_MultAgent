# -*- coding: utf-8 -*-
"""
QualityOrchestrator - Главный оркестратор с контролем качества на каждом этапе

Этот агент является главным оркестратором всей системы Employee Monitoring.
Он координирует работу всех агентов и контролирует качество результатов на каждом этапе.

Автор: AI Assistant
Дата: 2026-03-27
Версия: 1.0.0
"""

import logging
import asyncio
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from .task_analyzer_agent_improved import ImprovedTaskAnalyzerAgent
from .meeting_analyzer_agent_improved import ImprovedMeetingAnalyzerAgent
from .weekly_reports_agent_complete import WeeklyReportsAgentComplete
from .quality_validator_agent import QualityValidatorAgent
from ..core.config import get_employee_monitoring_config
from ..core.json_memory_store import JSONMemoryStore

logger = logging.getLogger(__name__)


class QualityOrchestrator:
    """
    Главный оркестратор с контролем качества на каждом этапе.
    
    Реализует паттерн "Quality Control Loop" - после каждого агента
    проверяется качество результатов и при необходимости отправляется на доработку.
    """
    
    def __init__(self):
        """Инициализация оркестратора и подчиненных агентов."""
        self.emp_config = get_employee_monitoring_config()
        self.memory_store = JSONMemoryStore()
        
        # Подчиненные агенты
        self.task_analyzer = ImprovedTaskAnalyzerAgent()
        self.meeting_analyzer = ImprovedMeetingAnalyzerAgent()
        self.weekly_reports = WeeklyReportsAgentComplete()
        self.quality_validator = QualityValidatorAgent()
        
        # Параметры качества
        self.quality_threshold = self.emp_config.get('quality', {}).get('threshold', 0.9)
        self.max_revision_attempts = self.emp_config.get('quality', {}).get('max_retries', 3)
        self.auto_improve = self.emp_config.get('quality', {}).get('auto_improve', True)
        
        logger.info(f"QualityOrchestrator initialized: threshold={self.quality_threshold}, max_attempts={self.max_revision_attempts}")

    def _to_plain_data(self, data: Any) -> Dict[str, Any]:
        """Convert dataclass/object analysis results to JSON-friendly dicts."""
        if data is None:
            return {}
        if is_dataclass(data):
            return asdict(data)
        if isinstance(data, dict):
            return data
        if hasattr(data, "__dict__"):
            return dict(data.__dict__)
        return {"data": data}

    def _validation_success(self, validation: Any) -> bool:
        if isinstance(validation, dict):
            return bool(validation.get("success", False))
        return validation is not None

    def _validation_score(self, validation: Any) -> float:
        if isinstance(validation, dict):
            return float(validation.get("overall_score", 0.0) or 0.0)
        return float(getattr(validation, "overall_score", 0.0) or 0.0)

    def _validation_issues(self, validation: Any) -> List[str]:
        if isinstance(validation, dict):
            return validation.get("issues_found", []) or []
        return getattr(validation, "issues_found", getattr(validation, "identified_issues", [])) or []

    def _validation_suggestions(self, validation: Any) -> List[str]:
        if isinstance(validation, dict):
            return validation.get("recommendations", []) or validation.get("recommended_actions", []) or []
        return getattr(validation, "recommendations", getattr(validation, "revision_suggestions", [])) or []
    
    async def execute_daily_task_workflow(self) -> Dict[str, Any]:
        """
        Ежедневный анализ задач с контролем качества.
        
        Returns:
            Dict[str, Any]: Результат выполнения workflow
        """
        workflow_start = datetime.now()
        logger.info("Starting daily task analysis workflow")
        
        for attempt in range(self.max_revision_attempts + 1):
            try:
                logger.info(f"Daily task analysis attempt {attempt + 1}/{self.max_revision_attempts + 1}")
                
                # 1. Получаем задачи из Jira
                jira_tasks = await self.task_analyzer.fetch_jira_tasks()
                if not jira_tasks:
                    logger.warning("No tasks received from Jira")
                    return {
                        'success': False,
                        'error': 'No tasks from Jira',
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }
                
                # 2. Запускаем анализ задач
                task_result = await self.task_analyzer.execute({'jira_tasks': jira_tasks})
                
                if not task_result.success:
                    logger.error(f"Task analysis failed: {task_result.message}")
                    if attempt < self.max_revision_attempts:
                        continue
                    return {
                        'success': False,
                        'error': task_result.message,
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }
                
                # 3. Проверяем качество
                validation = await self.quality_validator.validate_analysis(
                    task_result.data,
                    analysis_type="task_analysis"
                )

                if not self._validation_success(validation):
                    logger.error(f"Task validation failed: {validation.get('error', 'Unknown validation error') if isinstance(validation, dict) else 'Validation failed'}")
                    if attempt < self.max_revision_attempts:
                        continue
                    return {
                        'success': False,
                        'error': validation.get('error', 'Validation failed') if isinstance(validation, dict) else 'Validation failed',
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }

                overall_score = self._validation_score(validation)
                logger.info(f"Quality validation result: {overall_score:.2f}")
                
                # 4. Если качество >= порога - сохраняем и выходим
                if overall_score >= self.quality_threshold:
                    await self._save_approved_report(task_result.data, "task_analysis")
                    
                    workflow_duration = (datetime.now() - workflow_start).total_seconds()
                    logger.info(f"Daily task analysis completed successfully in {workflow_duration:.2f}s")
                    
                    return {
                        'success': True,
                        'quality_score': overall_score,
                        'attempts': attempt + 1,
                        'tasks_analyzed': len(jira_tasks),
                        'workflow_duration': workflow_duration
                    }
                
                # 5. Если качество < порога и есть попытки - запрашиваем доработку
                if attempt < self.max_revision_attempts and self.auto_improve:
                    logger.warning(f"Quality score {overall_score:.2f} < threshold {self.quality_threshold}, requesting improvement")
                    improved_data = await self._request_improvement(task_result.data, validation, "task_analysis")
                    if improved_data:
                        task_result.data = improved_data
                        continue
                
                # 6. Если все попытки исчерпаны или авто-улучшение отключено
                logger.error(f"Task analysis failed after {attempt + 1} attempts")
                await self._save_with_warning(task_result.data, "task_analysis", validation)
                
                return {
                    'success': False,
                    'quality_score': overall_score,
                    'attempts': attempt + 1,
                    'tasks_analyzed': len(jira_tasks),
                    'workflow_duration': (datetime.now() - workflow_start).total_seconds(),
                    'warning': 'Saved with quality issues'
                }
                    
            except Exception as e:
                logger.error(f"Task analysis attempt {attempt + 1} failed with exception: {e}")
                if attempt == self.max_revision_attempts:
                    return {
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }
                await asyncio.sleep(1)  # Небольшая пауза между попытками
                continue
        
        return {
            'success': False,
            'error': 'Max attempts exceeded',
            'attempts': self.max_revision_attempts + 1,
            'workflow_duration': (datetime.now() - workflow_start).total_seconds()
        }
    
    async def execute_daily_meeting_workflow(self) -> Dict[str, Any]:
        """
        Ежедневный анализ протоколов с контролем качества.
        
        Returns:
            Dict[str, Any]: Результат выполнения workflow
        """
        workflow_start = datetime.now()
        logger.info("Starting daily meeting analysis workflow")
        
        for attempt in range(self.max_revision_attempts + 1):
            try:
                logger.info(f"Daily meeting analysis attempt {attempt + 1}/{self.max_revision_attempts + 1}")

                # 1. Проверяем наличие входных протоколов через реальный интерфейс improved-агента
                protocol_files = sorted(self.meeting_analyzer.protocols_dir.glob("*.txt"))
                if not protocol_files:
                    logger.warning("No protocols found in directory")
                    return {
                        'success': False,
                        'error': 'No protocols found',
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }

                # 2. Запускаем анализ протоколов через execute(), который сам выполняет stage1/stage2/stage3
                meeting_result = await self.meeting_analyzer.execute({})
                
                if not meeting_result.success:
                    logger.error(f"Meeting analysis failed: {meeting_result.message}")
                    if attempt < self.max_revision_attempts:
                        continue
                    return {
                        'success': False,
                        'error': meeting_result.message,
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }
                
                # 3. Проверяем качество
                validation = await self.quality_validator.validate_analysis(
                    meeting_result.data,
                    analysis_type="meeting_analysis"
                )

                if not validation.get('success', False):
                    logger.error(f"Meeting validation failed: {validation.get('error', 'Unknown validation error')}")
                    if attempt < self.max_revision_attempts:
                        continue
                    return {
                        'success': False,
                        'error': validation.get('error', 'Validation failed'),
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }

                overall_score = validation.get('overall_score', 0.0)
                
                logger.info(f"Quality validation result: {overall_score:.2f}")
                
                # 4. Если качество >= порога - сохраняем и выходим
                if overall_score >= self.quality_threshold:
                    await self._save_approved_report(meeting_result.data, "meeting_analysis")
                    
                    workflow_duration = (datetime.now() - workflow_start).total_seconds()
                    logger.info(f"Daily meeting analysis completed successfully in {workflow_duration:.2f}s")
                    
                    return {
                        'success': True,
                        'quality_score': overall_score,
                        'attempts': attempt + 1,
                        'protocols_analyzed': len(protocol_files),
                        'workflow_duration': workflow_duration
                    }
                
                # 5. Если качество < порога и есть попытки - запрашиваем доработку
                if attempt < self.max_revision_attempts and self.auto_improve:
                    logger.warning(f"Quality score {overall_score:.2f} < threshold {self.quality_threshold}, requesting improvement")
                    improved_data = await self._request_improvement(meeting_result.data, validation, "meeting_analysis")
                    if improved_data:
                        meeting_result.data = improved_data
                        continue
                
                # 6. Если все попытки исчерпаны
                logger.error(f"Meeting analysis failed after {attempt + 1} attempts")
                await self._save_with_warning(meeting_result.data, "meeting_analysis", validation)
                
                return {
                    'success': False,
                    'quality_score': overall_score,
                    'attempts': attempt + 1,
                    'protocols_analyzed': len(protocol_files),
                    'workflow_duration': (datetime.now() - workflow_start).total_seconds(),
                    'warning': 'Saved with quality issues'
                }
                    
            except Exception as e:
                logger.error(f"Meeting analysis attempt {attempt + 1} failed with exception: {e}")
                if attempt == self.max_revision_attempts:
                    return {
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }
                await asyncio.sleep(1)
                continue
        
        return {
            'success': False,
            'error': 'Max attempts exceeded',
            'attempts': self.max_revision_attempts + 1,
            'workflow_duration': (datetime.now() - workflow_start).total_seconds()
        }
    
    async def execute_weekly_workflow(self) -> Dict[str, Any]:
        """
        Еженедельный отчет с контролем качества и публикацией в Confluence.
        
        Returns:
            Dict[str, Any]: Результат выполнения workflow
        """
        workflow_start = datetime.now()
        logger.info("Starting weekly report workflow")
        
        for attempt in range(self.max_revision_attempts + 1):
            try:
                logger.info(f"Weekly report attempt {attempt + 1}/{self.max_revision_attempts + 1}")
                
                # 1. Собираем данные за неделю
                report_period_end = datetime.now()
                report_period_start = report_period_end - timedelta(days=7)
                
                weekly_data = await self.weekly_reports.collect_weekly_data(
                    report_period_start, report_period_end
                )
                
                # 2. Генерируем отчет
                weekly_result = await self.weekly_reports.execute(weekly_data)
                
                if not weekly_result.success:
                    logger.error(f"Weekly report generation failed: {weekly_result.message}")
                    if attempt < self.max_revision_attempts:
                        continue
                    return {
                        'success': False,
                        'error': weekly_result.message,
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }
                
                # 3. Проверяем качество
                validation = await self.quality_validator.validate_analysis(
                    weekly_result.data,
                    analysis_type="weekly_report"
                )

                if not self._validation_success(validation):
                    logger.error(f"Weekly validation failed: {validation.get('error', 'Unknown validation error') if isinstance(validation, dict) else 'Validation failed'}")
                    if attempt < self.max_revision_attempts:
                        continue
                    return {
                        'success': False,
                        'error': validation.get('error', 'Validation failed') if isinstance(validation, dict) else 'Validation failed',
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }

                overall_score = self._validation_score(validation)
                logger.info(f"Quality validation result: {overall_score:.2f}")
                
                # 4. Если качество >= порога - публикуем в Confluence
                if overall_score >= self.quality_threshold:
                    confluence_result = await self.weekly_reports.publish_to_confluence(weekly_result.data)
                    
                    workflow_duration = (datetime.now() - workflow_start).total_seconds()
                    logger.info(f"Weekly report completed successfully in {workflow_duration:.2f}s")
                    
                    return {
                        'success': True,
                        'quality_score': overall_score,
                        'attempts': attempt + 1,
                        'published_to_confluence': confluence_result.get('success', False),
                        'confluence_url': confluence_result.get('url'),
                        'workflow_duration': workflow_duration
                    }
                
                # 5. Если качество < порога и есть попытки - запрашиваем доработку
                if attempt < self.max_revision_attempts and self.auto_improve:
                    logger.warning(f"Quality score {overall_score:.2f} < threshold {self.quality_threshold}, requesting improvement")
                    improved_data = await self._request_improvement(weekly_result.data, validation, "weekly_report")
                    if improved_data:
                        weekly_result.data = improved_data
                        continue
                
                # 6. Если все попытки исчерпаны - все равно публикуем с предупреждением
                logger.error(f"Weekly report quality issues after {attempt + 1} attempts, publishing anyway")
                confluence_result = await self.weekly_reports.publish_to_confluence(weekly_result.data)
                
                return {
                    'success': False,
                    'quality_score': overall_score,
                    'attempts': attempt + 1,
                    'published_to_confluence': confluence_result.get('success', False),
                    'confluence_url': confluence_result.get('url'),
                    'workflow_duration': (datetime.now() - workflow_start).total_seconds(),
                    'warning': 'Published with quality issues'
                }
                    
            except Exception as e:
                logger.error(f"Weekly report attempt {attempt + 1} failed with exception: {e}")
                if attempt == self.max_revision_attempts:
                    return {
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1,
                        'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                    }
                await asyncio.sleep(1)
                continue
        
        return {
            'success': False,
            'error': 'Max attempts exceeded',
            'attempts': self.max_revision_attempts + 1,
            'workflow_duration': (datetime.now() - workflow_start).total_seconds()
        }
    
    async def _request_improvement(self, data: Dict[str, Any], validation: Any, analysis_type: str) -> Optional[Dict[str, Any]]:
        """
        Запрос улучшения данных через LLM.
        
        Args:
            data: Исходные данные
            validation: Результат валидации
            analysis_type: Тип анализа
            
        Returns:
            Optional[Dict[str, Any]]: Улучшенные данные или None
        """
        try:
            logger.info(f"Requesting improvement for {analysis_type}")
            
            # Формируем промпт для улучшения
            improvement_prompt = self._create_improvement_prompt(data, validation, analysis_type)
            
            # Вызываем LLM для улучшения
            improved_response = await self.quality_validator.llm_client.analyze_async(improvement_prompt)
            
            if improved_response and improved_response.strip():
                # Парсим улучшенные данные
                improved_data = self._parse_improved_response(improved_response, data)
                if improved_data:
                    logger.info(f"Successfully improved {analysis_type} data")
                    return improved_data
            
            logger.warning(f"Failed to improve {analysis_type} data")
            return None
            
        except Exception as e:
            logger.error(f"Error during improvement request: {e}")
            return None
    
    def _create_improvement_prompt(self, data: Dict[str, Any], validation: Any, analysis_type: str) -> str:
        """Создание промпта для улучшения данных."""
        plain_data = self._to_plain_data(data)
        suggestions = self._validation_suggestions(validation)
        issues = self._validation_issues(validation)
        
        prompt = f"""
Проанализируй и улучи следующие данные для {analysis_type}:

ИСХОДНЫЕ ДАННЫЕ:
{json.dumps(plain_data, ensure_ascii=False, indent=2, default=str)}

ПРОБЛЕМЫ КАЧЕСТВА:
{chr(10).join(f"- {issue}" for issue in issues)}

РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:
{chr(10).join(f"- {suggestion}" for suggestion in suggestions)}

ТРЕБОВАНИЯ:
- Сохраняй структуру данных
- Улучши полноту и точность анализа
- Добавь недостающие инсайты
- Исправь выявленные проблемы
- Верни результат в формате JSON

УЛУЧШЕННЫЕ ДАННЫЕ:
"""
        return prompt
    
    def _parse_improved_response(self, response: str, original_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Парсинг ответа LLM с улучшенными данными."""
        try:
            # Пытаемся извлечь JSON из ответа
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            improved_data = json.loads(json_str)
            
            # Проверяем, что структура совпадает
            if isinstance(improved_data, dict) and improved_data:
                # Объединяем с оригинальными данными для сохранения полноты
                merged_data = self._to_plain_data(original_data).copy()
                merged_data.update(improved_data)
                return merged_data
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse improved JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing improved response: {e}")
            return None
    
    async def _save_approved_report(self, data: Dict[str, Any], analysis_type: str):
        """Сохранение утвержденного отчета."""
        try:
            plain_data = self._to_plain_data(data)
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            if analysis_type == "task_analysis":
                filename = f"task-analysis_{timestamp}.json"
                directory = Path("reports/daily")
            elif analysis_type == "meeting_analysis":
                filename = f"meeting-analysis_{timestamp}.json"
                directory = Path("reports/daily")
            else:
                logger.warning(f"Unknown analysis type: {analysis_type}")
                return
            
            directory.mkdir(parents=True, exist_ok=True)
            filepath = directory / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(plain_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Approved report saved: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving approved report: {e}")
    
    async def _save_with_warning(self, data: Dict[str, Any], analysis_type: str, validation: Any):
        """Сохранение отчета с предупреждением о низком качестве."""
        try:
            plain_data = self._to_plain_data(data)
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            if analysis_type == "task_analysis":
                filename = f"task-analysis_{timestamp}_quality_warning.json"
                directory = Path("reports/daily")
            elif analysis_type == "meeting_analysis":
                filename = f"meeting-analysis_{timestamp}_quality_warning.json"
                directory = Path("reports/daily")
            elif analysis_type == "weekly_report":
                week_number = datetime.now().isocalendar()[1]
                filename = f"weekly-report_{week_number}_quality_warning.json"
                directory = Path("reports/weekly")
            else:
                logger.warning(f"Unknown analysis type: {analysis_type}")
                return
            
            directory.mkdir(parents=True, exist_ok=True)
            filepath = directory / filename
            
            # Добавляем информацию о качестве
            warning_data = plain_data.copy()
            warning_data['_quality_warning'] = {
                'quality_score': self._validation_score(validation),
                'identified_issues': self._validation_issues(validation),
                'revision_suggestions': self._validation_suggestions(validation),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(warning_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.warning(f"Report saved with quality warning: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving report with warning: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы и всех компонентов."""
        try:
            status = {
                'orchestrator': {
                    'status': 'active',
                    'quality_threshold': self.quality_threshold,
                    'max_revision_attempts': self.max_revision_attempts,
                    'auto_improve': self.auto_improve
                },
                'agents': {
                    'task_analyzer': 'ready',
                    'meeting_analyzer': 'ready',
                    'weekly_reports': 'ready',
                    'quality_validator': 'ready'
                },
                'last_runs': await self._get_last_run_info(),
                'timestamp': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_last_run_info(self) -> Dict[str, Any]:
        """Получение информации о последних запусках."""
        try:
            last_runs = {}
            
            # Проверяем последние ежедневные отчеты
            daily_dir = Path("reports/daily")
            if daily_dir.exists():
                daily_files = list(daily_dir.glob("*.json"))
                if daily_files:
                    latest_daily = max(daily_files, key=lambda f: f.stat().st_mtime)
                    last_runs['daily_analysis'] = {
                        'last_file': latest_daily.name,
                        'last_run': datetime.fromtimestamp(latest_daily.stat().st_mtime).isoformat()
                    }
            
            # Проверяем последние еженедельные отчеты
            weekly_dir = Path("reports/weekly")
            if weekly_dir.exists():
                weekly_files = list(weekly_dir.glob("*.json"))
                if weekly_files:
                    latest_weekly = max(weekly_files, key=lambda f: f.stat().st_mtime)
                    last_runs['weekly_report'] = {
                        'last_file': latest_weekly.name,
                        'last_run': datetime.fromtimestamp(latest_weekly.stat().st_mtime).isoformat()
                    }
            
            return last_runs
            
        except Exception as e:
            logger.error(f"Error getting last run info: {e}")
            return {}
