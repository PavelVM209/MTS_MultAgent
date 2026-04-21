# -*- coding: utf-8 -*-
"""
Confluence Publisher Agent - Employee Monitoring System

Специализированный агент для публикации аналитических файлов в Confluence.
Наследует всю Confluence логику от WeeklyReportsAgentComplete.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from agents.weekly_reports_agent_complete import WeeklyReportsAgentComplete
from core.base_agent import AgentConfig, AgentResult

logger = logging.getLogger(__name__)


class ConfluencePublisherAgent(WeeklyReportsAgentComplete):
    """
    Специализированный агент для публикации аналитических файлов в Confluence.
    
    Публикует файлы:
    - comprehensive-analysis_YYYY-MM-DD.txt
    - stage1_text_analysis.txt
    
    В дочерние страницы от CONFLUENCE_PARENT_PAGE_ID=2282162313
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            config or AgentConfig(
                name="ConfluencePublisherAgent",
                description="Publishes analysis files to Confluence",
                version="1.0.0"
            )
        )
        
        # Пути к файлам для публикации
        self.project_root = Path(__file__).resolve().parents[2]
        
        # Файлы для публикации
        self.files_to_publish = {
            "comprehensive-analysis": self.project_root / "reports/daily/comprehensive-analysis_2026-04-05.txt",
            "task-analysis": self.project_root / "stage1_text_analysis.txt"
        }
        
        logger.info("ConfluencePublisherAgent initialized")
    
    async def publish_analysis_files(self, files_config: Dict[str, str] = None) -> AgentResult:
        """
        Основной método публикации аналитических файлов в Confluence.
        
        Args:
            files_config: Опциональная конфигурация файлов для публикации
            
        Returns:
            AgentResult с результатами публикации
        """
        try:
            logger.info("Starting publication of analysis files to Confluence")
            
            # Используем переданную конфигурацию или дефолтную
            files_to_process = files_config if files_config else self.files_to_publish
            
            if not files_to_process:
                return AgentResult(
                    success=False,
                    message="No files configured for publication",
                    data={}
                )
            
            # Проверяем конфигурацию Confluence
            if not self.confluence_url or not self.confluence_api_token:
                return AgentResult(
                    success=False,
                    message="Confluence configuration incomplete. Check CONFLUENCE_BASE_URL and CONFLUENCE_ACCESS_TOKEN",
                    data={}
                )
            
            if not self.confluence_parent_page_id:
                return AgentResult(
                    success=False,
                    message="CONFLUENCE_PARENT_PAGE_ID not configured",
                    data={}
                )
            
            logger.info(f"Publishing to parent page ID: {self.confluence_parent_page_id}")
            
            # Результаты публикации
            publication_results = {}
            successful_publications = 0
            
            # Обрабатываем каждый файл
            for file_key, file_path in files_to_process.items():
                try:
                    logger.info(f"Processing file: {file_key} -> {file_path}")
                    
                    # Читаем содержимое файла
                    content = await self._read_analysis_file(file_path)
                    if not content:
                        logger.error(f"Failed to read file: {file_path}")
                        publication_results[file_key] = {
                            "success": False,
                            "error": f"Failed to read file: {file_path}",
                            "url": None
                        }
                        continue
                    
                    # Форматируем контент для Confluence
                    formatted_content = await self._format_file_content(content, file_key)
                    
                    # Создаем заголовок страницы
                    page_title = await self._generate_page_title(file_key)
                    
                    # Публикуем в Confluence (обновляем основную страницу)
                    page_url = await self._update_main_page(content, file_key)
                    
                    if page_url:
                        publication_results[file_key] = {
                            "success": True,
                            "url": page_url,
                            "title": page_title,
                            "file_path": str(file_path)
                        }
                        successful_publications += 1
                        logger.info(f"✅ Successfully published {file_key} to Confluence: {page_url}")
                    else:
                        publication_results[file_key] = {
                            "success": False,
                            "error": "Failed to create Confluence page",
                            "url": None
                        }
                        logger.error(f"❌ Failed to publish {file_key} to Confluence")
                
                except Exception as e:
                    logger.error(f"Error processing file {file_key}: {e}")
                    publication_results[file_key] = {
                        "success": False,
                        "error": str(e),
                        "url": None
                    }
            
            # Формируем результат
            total_files = len(files_to_process)
            success_rate = (successful_publications / total_files) * 100 if total_files > 0 else 0
            
            result_message = f"Published {successful_publications}/{total_files} files to Confluence ({success_rate:.1f}% success rate)"
            
            if successful_publications == total_files:
                logger.info(f"🎉 All files published successfully!")
                return AgentResult(
                    success=True,
                    message=result_message,
                    data={
                        "publication_results": publication_results,
                        "successful_publications": successful_publications,
                        "total_files": total_files,
                        "success_rate": success_rate,
                        "parent_page_id": self.confluence_parent_page_id
                    }
                )
            elif successful_publications > 0:
                logger.warning(f"⚠️ Partial success: {successful_publications}/{total_files} files published")
                return AgentResult(
                    success=False,
                    message=f"Partial success: {result_message}",
                    data={
                        "publication_results": publication_results,
                        "successful_publications": successful_publications,
                        "total_files": total_files,
                        "success_rate": success_rate
                    }
                )
            else:
                logger.error(f"❌ All publications failed")
                return AgentResult(
                    success=False,
                    message="All file publications failed",
                    data=publication_results
                )
        
        except Exception as e:
            logger.error(f"ConfluencePublisherAgent execution failed: {e}")
            return AgentResult(
                success=False,
                message=f"Publication failed: {str(e)}",
                data={"error": str(e)}
            )
    
    async def _read_analysis_file(self, file_path: Path) -> Optional[str]:
        """
        Чтение содержимого аналитического файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Содержимое файла или None в случае ошибки
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            if not file_path.is_file():
                logger.error(f"Path is not a file: {file_path}")
                return None
            
            # Читаем содержимое с UTF-8 кодировкой
            content = file_path.read_text(encoding='utf-8')
            
            if not content.strip():
                logger.warning(f"File is empty: {file_path}")
                return ""
            
            logger.info(f"Successfully read file: {file_path} ({len(content)} chars)")
            return content
        
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    async def _format_file_content(self, content: str, file_key: str) -> str:
        """
        Форматирование содержимого файла для Confluence.
        
        Args:
            content: Исходное содержимое файла
            file_key: Ключ файла для определения типа форматирования
            
        Returns:
            Отформатированный контент для Confluence
        """
        try:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if file_key == "comprehensive-analysis":
                # Форматирование для comprehensive analysis
                formatted_parts = [
                    f"h1. Комплексный анализ команды",
                    "",
                    f"*Генерирован:* {current_date}",
                    f"*Источник:* Meeting Analyzer Agent",
                    "",
                    "h2. Анализ собраний и задач",
                    "",
                    # Сохраняем исходное форматирование с преобразованием markdown
                    self._convert_markdown_to_confluence(content)
                ]
            
            elif file_key == "task-analysis":
                # Форматирование для task analysis
                formatted_parts = [
                    f"h1. Анализ задач Jira",
                    "",
                    f"*Генерирован:* {current_date}",
                    f"*Источник:* Task Analyzer Agent",
                    "",
                    "h2. Производительность команды по задачам",
                    "",
                    # Сохраняем исходное форматирование с преобразованием markdown
                    self._convert_markdown_to_confluence(content)
                ]
            
            else:
                # Универсальное форматирование
                formatted_parts = [
                    f"h1. {file_key.replace('-', ' ').title()}",
                    "",
                    f"*Генерирован:* {current_date}",
                    "",
                    "h2. Содержимое",
                    "",
                    self._convert_markdown_to_confluence(content)
                ]
            
            return "\n".join(formatted_parts)
        
        except Exception as e:
            logger.error(f"Error formatting content for {file_key}: {e}")
            # Возвращаем базовое форматирование в случае ошибки
            return f"h1. {file_key}\n\n*Генерирован:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}"
    
    def _convert_markdown_to_confluence(self, markdown_content: str) -> str:
        """
        Преобразование Markdown в Confluence Wiki markup.
        
        Args:
            markdown_content: Содержимое в Markdown формате
            
        Returns:
            Содержимое в Confluence Wiki формате
        """
        try:
            # Базовые преобразования Markdown -> Confluence
            content = markdown_content
            
            # Заголовки
            content = content.replace('### ', 'h3. ')
            content = content.replace('## ', 'h2. ')
            content = content.replace('# ', 'h1. ')
            
            # Жирный текст
            content = content.replace('**', '*')
            
            # Курсив
            content = content.replace('*', '_')
            content = content.replace('_', '*')
            
            # Списки
            lines = content.split('\n')
            converted_lines = []
            
            for line in lines:
                stripped = line.lstrip()
                if stripped.startswith('- '):
                    # Маркированный список
                    indent = len(line) - len(stripped)
                    converted_lines.append(' ' * indent + stripped)
                elif stripped.strip().isdigit() and '.' in stripped[:10]:
                    # Нумерованный список
                    converted_lines.append(stripped)
                else:
                    converted_lines.append(line)
            
            # Кодовые блоки
            content = '\n'.join(converted_lines)
            content = content.replace('```', '{code}')
            
            # Горизонтальные линии
            content = content.replace('---', '----')
            
            return content
        
        except Exception as e:
            logger.error(f"Error converting markdown to confluence markup: {e}")
            return markdown_content
    
    async def _generate_page_title(self, file_key: str) -> str:
        """
        Генерация заголовка страницы в Confluence.
        
        Args:
            file_key: Ключ файла
            
        Returns:
            Заголовок страницы
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        titles = {
            "comprehensive-analysis": f"Комплексный анализ команды - {current_date}",
            "task-analysis": f"Анализ задач Jira - {current_date}",
        }
        
        return titles.get(file_key, f"{file_key.replace('-', ' ').title()} - {current_date}")
    
    async def _update_main_page(self, file_content: str, file_key: str) -> Optional[str]:
        """
        Обновление основной страницы 2282162313 новым содержимым.
        
        Args:
            file_content: Содержимое файла для добавления
            file_key: Ключ файла для заголовка
            
        Returns:
            URL обновленной страницы или None в случае ошибки
        """
        try:
            # Получаем текущую страницу
            current_url = f"{self.confluence_url}/rest/api/content/{self.confluence_parent_page_id}"
            
            import aiohttp
            headers = {
                "Authorization": f"Bearer {self.confluence_api_token}",
                "Content-Type": "application/json"
            }
            
            # Сначала получаем текущую версию страницы
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(current_url + "?expand=version,body.storage") as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get current page: {response.status} - {error_text}")
                        return None
                    
                    page_data = await response.json()
                    current_version = page_data['version']['number']
                    current_content = page_data['body']['storage']['value']
            
            # Форматируем новое содержимое
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if file_key == "comprehensive-analysis":
                section_title = f"h2. Комплексный анализ команды - {current_date}"
                section_content = f"{section_title}\n\n{self._convert_markdown_to_confluence(file_content)}"
            elif file_key == "task-analysis":
                section_title = f"h2. Анализ задач Jira - {current_date}"
                section_content = f"{section_title}\n\n{self._convert_markdown_to_confluence(file_content)}"
            else:
                section_title = f"h2. {file_key.replace('-', ' ').title()} - {current_date}"
                section_content = f"{section_title}\n\n{self._convert_markdown_to_confluence(file_content)}"
            
            # Добавляем новый контент в начало страницы
            updated_content = f"{section_content}\n\n----\n\n{current_content}"
            
            # Обновляем страницу
            update_data = {
                "id": self.confluence_parent_page_id,
                "type": "page",
                "title": page_data['title'],
                "version": {"number": current_version + 1},
                "body": {
                    "storage": {
                        "value": updated_content,
                        "representation": "wiki"
                    }
                }
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.put(current_url, json=update_data) as response:
                    if response.status == 200:
                        logger.info(f"Successfully updated page with {file_key}")
                        page_url = f"{self.confluence_url}/pages/viewpage.action?pageId={self.confluence_parent_page_id}"
                        return page_url
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to update page: {response.status} - {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Failed to update main page with '{file_key}': {e}")
            return None
    
    async def execute(self, input_data: Dict[str, Any] = None, **kwargs) -> AgentResult:
        """
        Основной метод выполнения агента.
        
        Args:
            input_data: Опциональные входные данные
            **kwargs: Дополнительные параметры
            
        Returns:
            AgentResult с результатами публикации
        """
        return await self.publish_analysis_files()
    
    async def get_publication_status(self) -> Dict[str, Any]:
        """
        Проверка статусaaaaaaaaагента и готовности к публикации.
        
        Returns:
            Словарь со статусом проверки
        """
        try:
            # Проверка файлов
            file_status = {}
            for file_key, file_path in self.files_to_publish.items():
                file_status[file_key] = {
                    "path": str(file_path),
                    "exists": file_path.exists(),
                    "readable": file_path.exists() and os.access(file_path, os.R_OK),
                    "size": file_path.stat().st_size if file_path.exists() else 0
                }
            
            # Проверка Confluence конфигурации
            confluence_status = {
                "url_configured": bool(self.confluence_url),
                "token_configured": bool(self.confluence_api_token),
                "parent_page_id": self.confluence_parent_page_id,
                "space_key": self.confluence_space_key or None  # Может быть None для child pages
            }
            
            # Проверка доступности LLM (для форматирования)
            llm_available = await self.llm_client.is_available()
            
            # Общий статус - space key не обязателен для child pages
            all_files_exist = all(status["exists"] for status in file_status.values())
            required_confluence_config = [
                confluence_status["url_configured"],
                confluence_status["token_configured"],
                confluence_status["parent_page_id"]
            ]
            confluence_ready = all(required_confluence_config)
            
            return {
                "agent_name": self.config.name,
                "status": "ready" if all_files_exist and confluence_ready else "not_ready",
                "files": file_status,
                "confluence": confluence_status,
                "llm_available": llm_available,
                "ready_for_publication": all_files_exist and confluence_ready
            }
        
        except Exception as e:
            logger.error(f"Error checking publication status: {e}")
            return {
                "agent_name": self.config.name,
                "status": "error",
                "error": str(e),
                "ready_for_publication": False
            }


if __name__ == "__main__":
    """
    Тестирование ConfluencePublisherAgent
    """
    import asyncio
    import logging
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def main():
        print("🚀 ЗАПУСК CONFLUENCE PUBLISHER AGENT")
        print("=" * 60)
        
        try:
            # Создаем агент
            agent = ConfluencePublisherAgent()
            print("✅ Agent created")
            
            # Проверяем статус
            status = await agent.get_publication_status()
            print(f"📊 Agent Status: {status['status']}")
            print(f"📁 Files Ready: {status.get('ready_for_publication', False)}")
            
            if not status.get('ready_for_publication', False):
                print("❌ Agent not ready for publication")
                print("Files status:")
                for file_key, file_info in status.get('files', {}).items():
                    print(f"  {file_key}: {'✅' if file_info['exists'] else '❌'} {file_info['path']}")
                print("Confluence status:")
                for key, value in status.get('confluence', {}).items():
                    print(f"  {key}: {'✅' if value else '❌'}")
                return
            
            # Выполняем публикацию
            print("\n📤 ПУБЛИКАЦИЯ ФАЙЛОВ В CONFLUENCE")
            print("=" * 60)
            
            result = await agent.execute()
            
            if result.success:
                print("✅ Публикация выполнена успешно!")
                print(f"📋 Сообщение: {result.message}")
                
                results = result.data.get('publication_results', {})
                for file_key, file_result in results.items():
                    if file_result.get('success'):
                        print(f"  ✅ {file_key}: {file_result.get('url')}")
                    else:
                        print(f"  ❌ {file_key}: {file_result.get('error')}")
                
                print(f"\n🎉 УСПЕХ: {result.data.get('successful_publications', 0)}/{result.data.get('total_files', 0)} файлов опубликовано")
                print(f"📊 Success Rate: {result.data.get('success_rate', 0):.1f}%")
                
            else:
                print("❌ Публикация не выполнена!")
                print(f"📋 Ошибка: {result.message}")
                
                if result.data and 'publication_results' in result.data:
                    results = result.data['publication_results']
                    for file_key, file_result in results.items():
                        print(f"  ❌ {file_key}: {file_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
