"""
Jira Agent for MTS MultAgent System

This agent handles communication with Jira API to:
- Search for issues by keywords and project
- Extract meeting protocols from issues
- Get comments and attachments
- Build JQL queries dynamically
- Handle rate limiting and authentication
"""

import asyncio
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlencode

import aiohttp
from dateutil.parser import parse as parse_date

from src.core.base_agent import BaseAgent, AgentResult
from src.core.models import (
    JiraTask, JiraResult, JiraIssue, JiraComment, JiraMeetingProtocol
)
from src.core.llm_client import LLMClient, get_llm_client, LLMRequest
from src.core.iterative_engine import IterativeEngine, get_iterative_engine
from src.core.quality_metrics import QualityEvaluator, get_quality_evaluator

import structlog

logger = structlog.get_logger()


class JiraAgent(BaseAgent):
    """
    Agent for integrating with Jira API.
    
    Handles searching issues, extracting meeting protocols,
    and retrieving comments with proper error handling and rate limiting.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize JiraAgent with configuration.
        
        Args:
            config: Configuration dictionary containing Jira settings
        """
        super().__init__(config, "JiraAgent")
        
        # Validate required configuration
        required_keys = ["jira.base_url", "jira.access_token", "jira.username", "jira.timeout"]
        if not self.validate_config(required_keys):
            raise ValueError("Missing required Jira configuration")
        
        self.base_url = self.get_config_value("jira.base_url").rstrip("/")
        self.access_token = self.get_config_value("jira.access_token")
        self.username = self.get_config_value("jira.username")
        self.timeout = self.get_config_value("jira.timeout", 30)
        
        # Prepare authentication headers
        auth_string = f"{self.username}:{self.access_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.auth_headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize LLM components for intelligent enhancements
        self.llm_client = get_llm_client()
        self.iterative_engine = get_iterative_engine()
        self.quality_evaluator = get_quality_evaluator()
        
        # Configuration for LLM features
        self.enable_llm_enhancements = self.get_config_value("jira.enable_llm_enhancements", True)
        self.max_iterations = self.get_config_value("jira.max_iterations", 3)
        
    async def validate(self, task: Dict[str, Any]) -> bool:
        """
        Validate Jira task parameters.
        
        Args:
            task: Task dictionary with JiraTask parameters
            
        Returns:
            True if valid, False otherwise
        """
        try:
            jira_task = JiraTask(**task)
            
            # Additional validation
            if not jira_task.project_key:
                self.logger.error("Project key is required")
                return False
                
            if jira_task.max_results > 100:
                self.logger.warning("Max results limited to 100")
                jira_task.max_results = 100
                
            return True
            
        except Exception as e:
            self.logger.error("Task validation failed", error=str(e))
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute Jira task with search and extraction.
        
        Args:
            task: Task dictionary containing Jira parameters
            
        Returns:
            AgentResult with Jira data
        """
        jira_task = JiraTask(**task)
        
        try:
            # Create aiohttp session if not exists
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self.session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers=self.auth_headers
                )
            
            # Search for issues
            issues = await self.search_issues(
                jira_task.project_key,
                jira_task.search_keywords,
                jira_task.date_range,
                jira_task.jql_query,
                jira_task.max_results
            )
            
            # Extract meeting protocols from issues
            meeting_protocols = []
            comments = []
            
            for issue in issues:
                # Get comments for each issue
                issue_comments = await self.extract_comments(issue.id)
                comments.extend(issue_comments)
                
                # Check if issue looks like meeting protocol
                protocol = await self._extract_meeting_protocol(issue, issue_comments)
                if protocol:
                    meeting_protocols.append(protocol)
            
            # Extract text context
            extracted_context = self._extract_text_context(issues, comments)
            
            # Create result
            result = JiraResult(
                issues=issues,
                meeting_protocols=meeting_protocols,
                comments=comments,
                total_count=len(issues) + len(meeting_protocols) + len(comments),
                extracted_context=extracted_context,
                search_summary={
                    "project_key": jira_task.project_key,
                    "keywords": jira_task.search_keywords,
                    "date_range": jira_task.date_range,
                    "issues_found": len(issues),
                    "protocols_found": len(meeting_protocols),
                    "comments_found": len(comments)
                }
            )
            
            self.logger.info(
                "Jira search completed",
                project_key=jira_task.project_key,
                issues=len(issues),
                protocols=len(meeting_protocols),
                comments=len(comments)
            )
            
            return AgentResult(
                success=True,
                data=result.dict(),
                agent_name=self.name
            )
            
        except Exception as e:
            self.logger.error("Jira execution failed", error=str(e), exc_info=True)
            return AgentResult(
                success=False,
                error=f"Jira execution failed: {str(e)}",
                agent_name=self.name
            )
    
    async def search_issues(
        self,
        project_key: str,
        keywords: List[str],
        date_range: Optional[Dict[str, str]] = None,
        custom_jql: Optional[str] = None,
        max_results: int = 50
    ) -> List[JiraIssue]:
        """
        Search for issues in Jira.
        
        Args:
            project_key: Project key to search in
            keywords: List of keywords to search for
            date_range: Optional date range filter
            custom_jql: Custom JQL query (overrides other search parameters)
            max_results: Maximum number of results
            
        Returns:
            List of JiraIssue objects
        """
        if custom_jql:
            jql = custom_jql
        else:
            jql = self._build_jql_query(project_key, keywords, date_range)
        
        # API endpoint
        endpoint = f"{self.base_url}/rest/api/3/search"
        
        # Query parameters
        params = {
            "jql": jql,
            "fields": "summary,description,status,assignee,reporter,created,updated,issuetype,priority,labels,components,comment",
            "expand": "comment",
            "maxResults": max_results
        }
        
        self.logger.info("Searching Jira issues", jql=jql, max_results=max_results)
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                issues = []
                for issue_data in data.get("issues", []):
                    issue = self._parse_issue(issue_data)
                    if issue:
                        issues.append(issue)
                
                self.logger.info("Issues retrieved", count=len(issues))
                return issues
                
        except aiohttp.ClientError as e:
            self.logger.error("Jira API request failed", error=str(e), endpoint=endpoint)
            raise
    
    async def get_meeting_protocols(self, project_key: str) -> List[JiraMeetingProtocol]:
        """
        Get meeting protocols for a project.
        
        Args:
            project_key: Project key to search in
            
        Returns:
            List of JiraMeetingProtocol objects
        """
        # Search for issues that look like meeting protocols
        keywords = ["протокол", "совещание", "встреча", "meeting", "protocol"]
        issues = await self.search_issues(project_key, keywords)
        
        protocols = []
        for issue in issues:
            comments = await self.extract_comments(issue.id)
            protocol = await self._extract_meeting_protocol(issue, comments)
            if protocol:
                protocols.append(protocol)
        
        return protocols
    
    async def extract_comments(self, issue_id: str) -> List[JiraComment]:
        """
        Extract comments from an issue.
        
        Args:
            issue_id: Issue ID to extract comments from
            
        Returns:
            List of JiraComment objects
        """
        endpoint = f"{self.base_url}/rest/api/3/issue/{issue_id}/comment"
        params = {"expand": "renderedBody"}
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                comments = []
                for comment_data in data.get("comments", []):
                    comment = self._parse_comment(comment_data)
                    if comment:
                        comments.append(comment)
                
                return comments
                
        except aiohttp.ClientError as e:
            self.logger.error("Failed to extract comments", error=str(e), issue_id=issue_id)
            return []
    
    async def build_jql_query(self, task: JiraTask) -> str:
        """
        Build JQL query from task parameters.
        
        Args:
            task: JiraTask with search parameters
            
        Returns:
            JQL query string
        """
        if task.jql_query:
            return task.jql_query
        
        return self._build_jql_query(
            task.project_key,
            task.search_keywords,
            task.date_range
        )
    
    def _build_jql_query(
        self,
        project_key: str,
        keywords: List[str],
        date_range: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build JQL query string.
        
        Args:
            project_key: Project key
            keywords: Search keywords
            date_range: Date range filter
            
        Returns:
            JQL query string
        """
        conditions = [f'project = "{project_key}"']
        
        # Add keyword search
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append(f'text ~ "{keyword}"')
            conditions.append(f'({" OR ".join(keyword_conditions)})')
        
        # Add date range
        if date_range:
            if date_range.get("from"):
                conditions.append(f'created >= "{date_range["from"]}"')
            if date_range.get("to"):
                conditions.append(f'created <= "{date_range["to"]}"')
        
        # Order by creation date
        conditions.append('ORDER BY created DESC')
        
        return ' AND '.join(conditions)
    
    def _parse_issue(self, issue_data: Dict[str, Any]) -> Optional[JiraIssue]:
        """
        Parse issue data from Jira API response.
        
        Args:
            issue_data: Raw issue data from API
            
        Returns:
            JiraIssue object or None if parsing fails
        """
        try:
            fields = issue_data.get("fields", {})
            
            # Handle assignee
            assignee = None
            if fields.get("assignee"):
                assignee = fields["assignee"].get("displayName")
            
            # Handle reporter
            reporter = None
            if fields.get("reporter"):
                reporter = fields["reporter"].get("displayName")
            
            # Handle priority
            priority = None
            if fields.get("priority"):
                priority = fields["priority"].get("name")
            
            # Handle components
            components = []
            for component in fields.get("components", []):
                components.append(component.get("name", ""))
            
            # Handle labels
            labels = fields.get("labels", [])
            
            return JiraIssue(
                id=issue_data["id"],
                key=issue_data["key"],
                summary=fields.get("summary", ""),
                description=fields.get("description"),
                status=fields.get("status", {}).get("name", "Unknown"),
                assignee=assignee,
                reporter=reporter,
                created=parse_date(fields.get("created")),
                updated=parse_date(fields.get("updated")),
                issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
                priority=priority,
                labels=labels,
                components=components
            )
            
        except Exception as e:
            self.logger.error("Failed to parse issue", error=str(e), issue_id=issue_data.get("id"))
            return None
    
    def _parse_comment(self, comment_data: Dict[str, Any]) -> Optional[JiraComment]:
        """
        Parse comment data from Jira API response.
        
        Args:
            comment_data: Raw comment data from API
            
        Returns:
            JiraComment object or None if parsing fails
        """
        try:
            author_data = comment_data.get("author", {})
            
            return JiraComment(
                id=comment_data["id"],
                author=author_data.get("displayName", "Unknown"),
                body=comment_data.get("body", ""),
                created=parse_date(comment_data.get("created")),
                updated=parse_date(comment_data.get("updated")) if comment_data.get("updated") else None
            )
            
        except Exception as e:
            self.logger.error("Failed to parse comment", error=str(e), comment_id=comment_data.get("id"))
            return None
    
    async def _extract_meeting_protocol(
        self,
        issue: JiraIssue,
        comments: List[JiraComment]
    ) -> Optional[JiraMeetingProtocol]:
        """
        Extract meeting protocol from issue and comments.
        
        Args:
            issue: Issue object
            comments: List of comments
            
        Returns:
            JiraMeetingProtocol object or None
        """
        # Check if issue looks like meeting protocol
        title_lower = issue.summary.lower()
        protocol_keywords = ["протокол", "совещание", "встреча", "meeting", "protocol"]
        
        if not any(keyword in title_lower for keyword in protocol_keywords):
            return None
        
        # Extract attendees from description and comments
        attendees = []
        action_items = []
        
        # Extract from description
        if issue.description:
            attendees.extend(self._extract_attendees(issue.description))
            action_items.extend(self._extract_action_items(issue.description))
        
        # Extract from comments
        for comment in comments:
            attendees.extend(self._extract_attendees(comment.body))
            action_items.extend(self._extract_action_items(comment.body))
        
        # Combine description and comments for content
        content_parts = [f"# {issue.summary}"]
        if issue.description:
            content_parts.append(issue.description)
        
        for comment in comments:
            content_parts.append(f"## {comment.author} ({comment.created}):")
            content_parts.append(comment.body)
        
        content = "\n\n".join(content_parts)
        
        return JiraMeetingProtocol(
            issue_id=issue.id,
            title=issue.summary,
            content=content,
            date=issue.created,
            attendees=list(set(attendees)),  # Remove duplicates
            action_items=action_items
        )
    
    def _extract_attendees(self, text: str) -> List[str]:
        """
        Extract attendee names from text.
        
        Args:
            text: Text to search for attendees
            
        Returns:
            List of attendee names
        """
        import re
        
        attendees = []
        
        # Look for patterns like "Присутствовали: Иванов, Петров"
        patterns = [
            r'присутствовали[:\s]*([^.]+)',
            r'участники[:\s]*([^.]+)',
            r'attendees?[:\s]*([^.]+)',
            r'@([A-Za-z0-9_]+)',  # Mentions
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Split by common separators and clean
                names = re.split(r'[,;]\s*', match)
                for name in names:
                    name = name.strip()
                    if len(name) > 1 and len(name) < 50:  # Reasonable name length
                        attendees.append(name)
        
        return list(set(attendees))
    
    def _extract_action_items(self, text: str) -> List[str]:
        """
        Extract action items from text.
        
        Args:
            text: Text to search for action items
            
        Returns:
            List of action items
        """
        import re
        
        action_items = []
        
        # Look for action item patterns
        patterns = [
            r'[-*]\s*(.*?)(?=\n|$)',  # Bullet points
            r'(?:действие|action|задача)[:\s]*([^.]+)',
            r'(?:ответственный|responsible)[:\s]*([^.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                action = match.strip()
                if len(action) > 10:  # Minimum length
                    action_items.append(action)
        
        return list(set(action_items))
    
    def _extract_text_context(self, issues: List[JiraIssue], comments: List[JiraComment]) -> str:
        """
        Extract combined text context from issues and comments.
        
        Args:
            issues: List of issues
            comments: List of comments
            
        Returns:
            Combined text context
        """
        context_parts = []
        
        # Add issue summaries and descriptions
        for issue in issues:
            context_parts.append(f"Issue: {issue.summary}")
            if issue.description:
                context_parts.append(issue.description)
        
        # Add comments
        for comment in comments:
            context_parts.append(f"Comment by {comment.author}: {comment.body}")
        
        return "\n\n".join(context_parts)
    
    async def enhance_search_with_llm(
        self, 
        keywords: List[str], 
        project_context: Optional[str] = None
    ) -> List[str]:
        """
        Enhance search keywords using LLM for better results.
        
        Args:
            keywords: Original search keywords
            project_context: Optional context about the project
            
        Returns:
            Enhanced keywords list
        """
        if not self.enable_llm_enhancements:
            return keywords
        
        prompt = f"""
        Улучши поисковые ключевые слова для Jira поиска.
        
        ИСХОДНЫЕ КЛЮЧЕВЫЕ СЛОВА:
        {', '.join(keywords)}
        
        КОНТЕКСТ ПРОЕКТА:
        {project_context or 'Не указан'}
        
        ВЕРНИ УЛУЧШЕННЫЕ КЛЮЧЕВЫЕ СЛОВА В ФОРМАТЕ JSON МАССИВА:
        ["ключевое1", "ключевое2", "ключевое3"]
        
        ТРЕБОВАНИЯ:
        - Добавь синонимы и связанные термины
        - Включи варианты написания (если применимо)
        - Добавь технические термины связанные с проектом
        - Ограничься 5-7 наиболее релевантными ключевыми словами
        - Сохраняй язык оригинала (русский)
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.2,
                max_tokens=300,
                cache_key=f"jira_keyword_enhancement_{hash(str(keywords) + str(project_context))}"
            ))
            
            enhanced_keywords = json.loads(response.content)
            self.logger.info(f"Enhanced {len(keywords)} keywords to {len(enhanced_keywords)}")
            return enhanced_keywords
            
        except Exception as e:
            self.logger.error(f"LLM keyword enhancement failed: {e}")
            return keywords
    
    async def optimize_jql_query(self, jql: str, search_results_count: int) -> str:
        """
        Optimize JQL query based on results using LLM.
        
        Args:
            jql: Original JQL query
            search_results_count: Number of results from the query
            
        Returns:
            Optimized JQL query
        """
        if not self.enable_llm_enhancements or search_results_count > 10:
            return jql
        
        prompt = f"""
        Оптимизируй JQL запрос для получения более релевантных результатов.
        
        ТЕКУЩИЙ JQL ЗАПРОС:
        {jql}
        
        РЕЗУЛЬТАТОВ НАЙДЕНО:
        {search_results_count} (слишком мало)
        
        ВЕРНИ ОПТИМИЗИРОВАННЫЙ JQL ЗАПРОС.
        
        ТРЕБОВАНИЯ:
        - Расширь критерии поиска для получения большего количества результатов
        - Используй более гибкие условия поиска
        - Добавь альтернативные поля для поиска
        - Сохрани основную логику фильтрации
        - Верни только JQL запрос без дополнительного текста
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500,
                cache_key=f"jql_optimization_{hash(jql + str(search_results_count))}"
            ))
            
            optimized_jql = response.content.strip()
            
            # Validate that it looks like a JQL query
            if any(keyword in optimized_jql.upper() for keyword in ['PROJECT', 'ORDER BY', 'AND', 'OR']):
                self.logger.info(f"Optimized JQL query: {optimized_jql}")
                return optimized_jql
            else:
                self.logger.warning("LLM optimization didn't return valid JQL")
                return jql
                
        except Exception as e:
            self.logger.error(f"JQL optimization failed: {e}")
            return jql
    
    async def intelligent_protocol_detection(
        self, 
        issues: List[JiraIssue]
    ) -> List[JiraMeetingProtocol]:
        """
        Use LLM to intelligently detect meeting protocols from issues.
        
        Args:
            issues: List of Jira issues to analyze
            
        Returns:
            List of detected meeting protocols
        """
        if not self.enable_llm_enhancements:
            return []
        
        protocols = []
        
        for issue in issues:
            try:
                # Get comments for the issue
                comments = await self.extract_comments(issue.id)
                
                # Prepare data for LLM analysis
                issue_data = {
                    "summary": issue.summary,
                    "description": issue.description,
                    "comments": [comment.body for comment in comments],
                    "issue_type": issue.issue_type,
                    "labels": issue.labels
                }
                
                protocol = await self._llm_detect_meeting_protocol(issue, issue_data, comments)
                if protocol:
                    protocols.append(protocol)
                    
            except Exception as e:
                self.logger.error(f"Failed to analyze issue {issue.key} for protocol detection: {e}")
                continue
        
        return protocols
    
    async def _llm_detect_meeting_protocol(
        self, 
        issue: JiraIssue, 
        issue_data: Dict[str, Any], 
        comments: List[JiraComment]
    ) -> Optional[JiraMeetingProtocol]:
        """
        Use LLM to detect if issue is a meeting protocol.
        
        Args:
            issue: Jira issue object
            issue_data: Structured issue data
            comments: Issue comments
            
        Returns:
            Meeting protocol if detected, None otherwise
        """
        prompt = f"""
        Проанализируй данные Jira задачи и определи, является ли она протоколом совещания.
        
        ДАННЫЕ ЗАДАЧИ:
        {json.dumps(issue_data, ensure_ascii=False, indent=2)}
        
        ВЕРНИ РЕЗУЛЬТАТ В ФОРМАТЕ JSON:
        {{
            "is_meeting_protocol": true/false,
            "confidence_score": 0.85,
            "protocol_title": "заголовок протокола",
            "attendees": ["участник1", "участник2"],
            "action_items": ["действие1", "действие2"],
            "key_decisions": ["решение1", "решение2"],
            "date_discussed": "обсуждаемая дата или null"
        }}
        
        ТРЕБОВАНИЯ:
        - Используй семантический анализ для определения типа документа
        - Извлекай конкретные данные если это протокол
        - Оцени уверенность в определении (0.0 - 1.0)
        - Используй только информацию из предоставленных данных
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=1000,
                cache_key=f"protocol_detection_{hash(str(issue_data))}"
            ))
            
            result = json.loads(response.content)
            
            if result.get("is_meeting_protocol") and result.get("confidence_score", 0) > 0.7:
                # Create meeting protocol
                content_parts = [f"# {result.get('protocol_title', issue.summary)}"]
                if issue.description:
                    content_parts.append(issue.description)
                
                for comment in comments:
                    content_parts.append(f"## {comment.author} ({comment.created}):")
                    content_parts.append(comment.body)
                
                if result.get("key_decisions"):
                    content_parts.append("## Ключевые решения:")
                    for decision in result["key_decisions"]:
                        content_parts.append(f"- {decision}")
                
                content = "\n\n".join(content_parts)
                
                return JiraMeetingProtocol(
                    issue_id=issue.id,
                    title=result.get("protocol_title", issue.summary),
                    content=content,
                    date=result.get("date_discussed") or issue.created,
                    attendees=result.get("attendees", []),
                    action_items=result.get("action_items", [])
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"LLM protocol detection failed: {e}")
            return None
    
    async def enhance_context_extraction(
        self, 
        issues: List[JiraIssue], 
        comments: List[JiraComment]
    ) -> str:
        """
        Enhance context extraction using LLM analysis.
        
        Args:
            issues: List of Jira issues
            comments: List of comments
            
        Returns:
            Enhanced context string
        """
        if not self.enable_llm_enhancements:
            return self._extract_text_context(issues, comments)
        
        # Prepare structured data for LLM
        structured_data = {
            "issues": [
                {
                    "summary": issue.summary,
                    "description": issue.description,
                    "status": issue.status,
                    "priority": issue.priority,
                    "assignee": issue.assignee,
                    "labels": issue.labels,
                    "components": issue.components
                }
                for issue in issues[:10]  # Limit to avoid token limits
            ],
            "comments": [
                {
                    "author": comment.author,
                    "body": comment.body,
                    "created": comment.created.isoformat() if comment.created else None
                }
                for comment in comments[:20]  # Limit comments
            ]
        }
        
        prompt = f"""
        Проанализируй данные из Jira и создай улучшенный контекст для дальнейшего анализа.
        
        ДАННЫЕ JIRA:
        {json.dumps(structured_data, ensure_ascii=False, indent=2)}
        
        ВЕРНИ УЛУЧШЕННЫЙ КОНТЕКСТ В ФОРМАТЕ JSON:
        {{
            "enhanced_context": "структурированный контекст с ключевыми инсайтами",
            "key_topics": ["тема1", "тема2"],
            "actionable_items": ["действие1", "действие2"],
            "stakeholders": ["заинтересованное1", "заинтересованное2"],
            "timeline_summary": "сводка по времени и этапам"
        }}
        
        ТРЕБОВАНИЯ:
        - Синхронизируй информацию из разных источников
        - Выдели ключевые темы и тренды
        - Определи заинтересованных стороны
        - Создай структурированный контекст для анализа
        - Используй естественный язык для описания
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000,
                cache_key=f"context_enhancement_{hash(str(structured_data))}"
            ))
            
            result = json.loads(response.content)
            
            # Combine enhanced context with structured summary
            enhanced_parts = [
                result.get("enhanced_context", ""),
                "\n\n## Ключевые темы:",
                "\n".join(f"- {topic}" for topic in result.get("key_topics", [])[:10]),
                "\n\n## Заинтересованные стороны:",
                "\n".join(f"- {stakeholder}" for stakeholder in result.get("stakeholders", [])[:10]),
                "\n\n## Временная сводка:",
                result.get("timeline_summary", "")
            ]
            
            return "\n".join(filter(None, enhanced_parts))
            
        except Exception as e:
            self.logger.error(f"Context enhancement failed: {e}")
            return self._extract_text_context(issues, comments)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for Jira agent.
        
        Returns:
            Health check result
        """
        base_health = await super().health_check()
        
        try:
            # Test API connectivity
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=5)
                self.session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers=self.auth_headers
                )
            
            # Make a simple API call to test connectivity
            endpoint = f"{self.base_url}/rest/api/3/serverInfo"
            async with self.session.get(endpoint) as response:
                if response.status == 200:
                    jira_health = {"status": "healthy", "api_connected": True}
                else:
                    jira_health = {"status": "unhealthy", "api_connected": False}
                    
        except Exception as e:
            jira_health = {"status": "error", "api_connected": False, "error": str(e)}
        
        base_health.update({
            "jira_configured": bool(self.base_url and self.access_token),
            "jira_health": jira_health
        })
        
        return base_health
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
