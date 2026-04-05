# -*- coding: utf-8 -*-
"""
Jira Client - Интеграция с Jira API для Employee Monitoring System

Предоставляет интерфейс для работы с Jira API:
- Получение задач
- Извлечение метрик коммитов и PR
- Обработка результатов
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Клиент для работы с Jira API.
    
    Получает задачи из Jira и извлекает метрики для анализа.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация Jira клиента.
        
        Args:
            config: Конфигурация Jira
        """
        self.config = config or {}
        self._session = None
        
        # Load configuration from environment variables if not provided
        if not self.config:
            import os
            self.config = {
                'base_url': os.getenv('JIRA_BASE_URL', ''),
                'username': os.getenv('JIRA_USERNAME', ''),
                'api_token': os.getenv('JIRA_ACCESS_TOKEN', ''),  # Маппинг с .env
                'project_key': os.getenv('JIRA_PROJECT_KEYS', '').split(',')[0] if os.getenv('JIRA_PROJECT_KEYS') else ''
            }
            
        # Debug: Print configuration loading
        logger.info(f"Loading Jira config: base_url={self.config.get('base_url')}, username={self.config.get('username')}, token_configured={'Yes' if self.config.get('api_token') else 'No'}")
        
        # Jira configuration
        self.base_url = self.config.get('base_url', '')
        self.username = self.config.get('username', '')
        self.api_token = self.config.get('api_token', '')
        self.project_key = self.config.get('project_key', '')
        
        # Test configuration
        if not all([self.base_url, self.username, self.api_token]):
            logger.warning("Jira configuration incomplete")
        else:
            logger.info(f"Jira client initialized for {self.base_url}")
    
    async def test_connection(self) -> bool:
        """
        Тест соединения с Jira API.
        
        Returns:
            bool: True если соединение успешно
        """
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not available")
            return False
        
        if not all([self.base_url, self.api_token]):
            logger.error(f"Jira configuration incomplete - base_url: {bool(self.base_url)}, api_token: {bool(self.api_token)}")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                # Тестовый запрос к myself endpoint - используем API v2 как в примере
                url = f"{self.base_url}/rest/api/2/myself"
                
                logger.info(f"Testing connection to: {url}")
                
                async with session.get(url) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        logger.info(f"Jira API connection successful. User: {user_data.get('displayName', 'Unknown')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Jira API connection failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to test Jira connection: {e}")
            return False
    
    async def search_issues(
        self, 
        jql: str, 
        fields: List[str] = None, 
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Поиск задач в Jira.
        
        Args:
            jql: JQL запрос
            fields: Список полей для получения
            max_results: Максимальное количество результатов
            
        Returns:
            List[Dict[str, Any]]: Список задач
        """
        logger.info(f"Searching Jira issues with JQL: {jql}")
        
        if not await self.test_connection():
            logger.error("Cannot search issues - connection test failed")
            return []
        
        if not fields:
            fields = [
                'summary', 'status', 'assignee', 'priority', 'created', 'updated', 
                'project', 'reporter', 'resolution', 'issuetype', 'description'
            ]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Формируем URL запроса - используем API v2
            url = f"{self.base_url}/rest/api/2/search"
            
            params = {
                'jql': jql,
                'fields': ','.join(fields),
                'maxResults': max_results
            }
            
            logger.info(f"Making request to: {url}")
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        issues = data.get('issues', [])
                        
                        logger.info(f"Successfully retrieved {len(issues)} issues from Jira")
                        logger.info(f"Total available: {data.get('total', 0)} issues")
                        
                        return issues
                    else:
                        error_text = await response.text()
                        logger.error(f"Jira API error: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to search Jira issues: {e}")
            return []
    
    async def get_issue_details(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации о задаче.
        
        Args:
            issue_key: Ключ задачи
            
        Returns:
            Optional[Dict[str, Any]]: Детальная информация о задаче
        """
        if not await self.test_connection():
            return None
        
        try:
            auth = aiohttp.BasicAuth(self.username, self.api_token)
            
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            params = {
                'expand': 'names,schema,renderedFields,versionedRepresentations'
            }
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        issue_data = await response.json()
                        logger.info(f"Retrieved details for issue {issue_key}")
                        return issue_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get issue details: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to get issue details: {e}")
            return None
    
    async def get_development_info(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о разработке для задачи (commits, PRs).
        
        Args:
            issue_key: Ключ задачи
            
        Returns:
            Optional[Dict[str, Any]]: Информация о разработке
        """
        if not await self.test_connection():
            return None
        
        try:
            auth = aiohttp.BasicAuth(self.username, self.api_token)
            
            # Development panel endpoint
            url = f"{self.base_url}/rest/dev-status/latest/issue/detail"
            params = {
                'issueId': issue_key,
                'applicationType': 'github',  # или другие VCS
                'dataType': 'pullrequest,branch,commit,build,deployment'
            }
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        dev_data = await response.json()
                        return self._process_development_data(dev_data)
                    else:
                        # Development panel может быть недоступен
                        logger.debug(f"Development info not available for {issue_key}")
                        return self._get_default_development_info()
                        
        except Exception as e:
            logger.debug(f"Failed to get development info for {issue_key}: {e}")
            return self._get_default_development_info()
    
    def _process_development_data(self, dev_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка данных о разработке."""
        try:
            commits_count = 0
            prs_count = 0
            
            # Извлекаем информацию из development panel
            for category in dev_data.get('detail', []):
                for detail in category.get('data', []):
                    if detail.get('type') == 'commit':
                        commits_count += 1
                    elif detail.get('type') == 'pullrequest':
                        prs_count += 1
            
            return {
                'commits_count': commits_count,
                'pull_requests_count': prs_count,
                'has_development_data': True
            }
            
        except Exception as e:
            logger.debug(f"Failed to process development data: {e}")
            return self._get_default_development_info()
    
    def _get_default_development_info(self) -> Dict[str, Any]:
        """Информация о разработке по умолчанию."""
        return {
            'commits_count': 0,
            'pull_requests_count': 0,
            'has_development_data': False
        }
    
    async def get_project_issues(
        self, 
        project_key: str = None, 
        status_category: str = None,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Получение задач проекта.
        
        Args:
            project_key: Ключ проекта
            status_category: Категория статуса
            days_back: Количество дней для поиска
            
        Returns:
            List[Dict[str, Any]]: Список задач
        """
        project_key = project_key or self.project_key
        
        if not project_key:
            logger.error("Project key not specified")
            return []
        
        # Формируем JQL запрос
        jql_parts = [f'project = "{project_key}"']
        
        if status_category:
            jql_parts.append(f'statusCategory = "{status_category}"')
        
        if days_back > 0:
            from datetime import datetime, timedelta
            date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            jql_parts.append(f'updated >= "{date_from}"')
        
        jql = ' AND '.join(jql_parts)
        
        return await self.search_issues(jql)
    
    async def get_user_issues(
        self, 
        username: str = None, 
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Получение задач пользователя.
        
        Args:
            username: Имя пользователя
            days_back: Количество дней для поиска
            
        Returns:
            List[Dict[str, Any]]: Список задач
        """
        username = username or self.username
        
        if not username:
            logger.error("Username not specified")
            return []
        
        # Формируем JQL запрос
        jql_parts = [f'assignee = "{username}"']
        
        if days_back > 0:
            from datetime import datetime, timedelta
            date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            jql_parts.append(f'updated >= "{date_from}"')
        
        jql = ' AND '.join(jql_parts)
        
        return await self.search_issues(jql)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Получение текущей конфигурации Jira клиента.
        
        Returns:
            Dict[str, Any]: Текущая конфигурация
        """
        return {
            'base_url': self.base_url,
            'username': self.username,
            'api_token': '***configured***' if self.api_token else None,
            'project_key': self.project_key,
            'aiohttp_available': AIOHTTP_AVAILABLE,
            'configured': bool(self.base_url and self.username and self.api_token)
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Валидация конфигурации Jira клиента.
        
        Returns:
            Dict[str, Any]: Результат валидации
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'configured_fields': []
        }
        
        # Check required fields
        if not self.base_url:
            validation_result['valid'] = False
            validation_result['errors'].append('base_url is required')
        elif not self.base_url.startswith(('http://', 'https://')):
            validation_result['valid'] = False
            validation_result['errors'].append('base_url must start with http:// or https://')
        else:
            validation_result['configured_fields'].append('base_url')
        
        if not self.username:
            validation_result['valid'] = False
            validation_result['errors'].append('username is required')
        else:
            validation_result['configured_fields'].append('username')
        
        if not self.api_token:
            validation_result['valid'] = False
            validation_result['errors'].append('api_token is required')
        else:
            validation_result['configured_fields'].append('api_token')
        
        # Check optional fields
        if self.project_key:
            validation_result['configured_fields'].append('project_key')
        else:
            validation_result['warnings'].append('project_key not configured')
        
        # Check aiohttp availability
        if not AIOHTTP_AVAILABLE:
            validation_result['valid'] = False
            validation_result['errors'].append('aiohttp library is required but not available')
        
        validation_result['status'] = 'valid' if validation_result['valid'] else 'invalid'
        
        return validation_result
    
    async def close(self):
        """Закрытие сессии."""
        if self._session:
            await self._session.close()
            self._session = None


# Утилиты для работы с Jira
async def create_jira_client(config: Dict[str, Any] = None) -> JiraClient:
    """
    Создание Jira клиента.
    
    Args:
        config: Конфигурация
        
    Returns:
        JiraClient: Экземпляр клиента
    """
    return JiraClient(config)


def jql_date_range(days_back: int) -> str:
    """
    Формирование диапазона дат для JQL.
    
    Args:
        days_back: Количество дней назад
        
    Returns:
        str: Диапазон дат в формате JQL
    """
    from datetime import datetime, timedelta
    
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    return f'"{start_date}" .. "{end_date}"'


def parse_jira_datetime(date_str: str) -> Optional[datetime]:
    """
    Парсинг даты из Jira формата.
    
    Args:
        date_str: Строка с датой
        
    Returns:
        Optional[datetime]: Распарсенная дата
    """
    try:
        # Jira формат: 2023-03-26T10:30:00.000+0000
        if date_str.endswith('+0000'):
            date_str = date_str[:-5] + '+00:00'
        
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
    except Exception as e:
        logger.debug(f"Failed to parse Jira datetime '{date_str}': {e}")
        return None
