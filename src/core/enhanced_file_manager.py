"""
Улучшенный менеджер файлов с правильной структурой папок для результатов анализа.

Структура папок:
reports/
├── daily/
│   ├── {YYYY-MM-DD}/
│   │   ├── task-analysis/
│   │   │   ├── stage1/
│   │   │   │   ├── stage1_task_analysis_YYYYMMDD_HHMMSS.txt
│   │   │   │   └── stage1_task_analysis_latest.txt -> ...
│   │   │   ├── stage2/
│   │   │   │   ├── stage2_task_result_YYYYMMDD_HHMMSS.json
│   │   │   │   └── stage2_task_result_latest.txt -> ...
│   │   │   └── final/
│   │   │       ├── task-analysis_YYYYMMDD.json
│   │   │       └── task-analysis_latest.json -> ...
│   │   ├── meeting-analysis/
│   │   │   ├── cleaned-protocols/
│   │   │   │   ├── cleaned_protocol1_YYYYMMDD_HHMMSS.txt
│   │   │   ├── stage1/
│   │   │   │   ├── stage1_meeting_analysis_YYYYMMDD_HHMMSS.txt
│   │   │   ├── stage2/
│   │   │   │   ├── stage2_comprehensive_YYYYMMDD_HHMMSS.json
│   │   │   └── final/
│   │   │       ├── meeting-analysis_YYYYMMDD.json
│   │   │       └── meeting-analysis_latest.json -> ...
│   │   ├── employee-progression/
│   │   │   ├── employee1_YYYYMMDD.json
│   │   │   └── employee1_latest.json -> ...
│   │   └── .processing_tracker.json
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class EnhancedFileManager:
    """
    Улучшенный менеджер файлов с правильной структурой папок.
    """
    
    def __init__(self, base_reports_dir: Optional[Path] = None):
        """
        Инициализация менеджера файлов.
        
        Args:
            base_reports_dir: Базовая директория отчетов (по умолчанию reports/daily)
        """
        if base_reports_dir is None:
            project_root = Path(__file__).parent.parent.parent
            base_reports_dir = project_root / "reports" / "daily"
        
        self.base_dir = Path(base_reports_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Дата для текущего анализа
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.today_dir = self.base_dir / self.today
        self.today_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем структуру папок
        self._create_directory_structure()
        
        logger.info(f"Enhanced file manager initialized with base dir: {self.base_dir}")
    
    def _create_directory_structure(self) -> None:
        """Создать структуру директорий."""
        directories = [
            self.today_dir / "task-analysis" / "stage1",
            self.today_dir / "task-analysis" / "stage2", 
            self.today_dir / "task-analysis" / "final",
            self.today_dir / "meeting-analysis" / "cleaned-protocols",
            self.today_dir / "meeting-analysis" / "stage1",
            self.today_dir / "meeting-analysis" / "stage2",
            self.today_dir / "meeting-analysis" / "final",
            self.today_dir / "employee_progression"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    # TASK ANALYSIS METHODS
    
    def save_task_stage1(self, content: str) -> Path:
        """Сохранить stage1 анализ задач."""
        stage1_dir = self.today_dir / "task-analysis" / "stage1"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage1_task_analysis_{timestamp}.txt"
        filepath = stage1_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Создаем символьную ссылку на latest
        self._create_symlink(stage1_dir / filename, stage1_dir / "stage1_task_analysis_latest.txt")
        
        logger.info(f"Task stage1 saved: {filepath}")
        return filepath
    
    def save_task_stage2(self, data: Dict[str, Any]) -> Path:
        """Сохранить stage2 анализ задач."""
        stage2_dir = self.today_dir / "task-analysis" / "stage2"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage2_task_result_{timestamp}.json"
        filepath = stage2_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Создаем символьную ссылку на latest
        self._create_symlink(stage2_dir / filename, stage2_dir / "stage2_task_result_latest.json")
        
        logger.info(f"Task stage2 saved: {filepath}")
        return filepath
    
    def save_task_final(self, data: Dict[str, Any]) -> Path:
        """Сохранить финальный анализ задач."""
        final_dir = self.today_dir / "task-analysis" / "final"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"task-analysis_{timestamp}.json"
        filepath = final_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Создаем символьную ссылку на latest
        self._create_symlink(final_dir / filename, final_dir / "task-analysis_latest.json")
        
        # Also create date-specific version
        date_filename = f"task-analysis_{self.today}.json"
        self._create_symlink(final_dir / filename, final_dir / date_filename)
        
        logger.info(f"Task final saved: {filepath}")
        return filepath
    
    # MEETING ANALYSIS METHODS
    
    def save_cleaned_protocol(self, protocol_name: str, content: str) -> Path:
        """Сохранить очищенный протокол."""
        cleaned_dir = self.today_dir / "meeting-analysis" / "cleaned-protocols"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self._sanitize_filename(protocol_name)
        filename = f"cleaned_{safe_name}_{timestamp}.txt"
        filepath = cleaned_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Cleaned protocol saved: {filepath}")
        return filepath
    
    def save_meeting_stage1(self, content: str) -> Path:
        """Сохранить stage1 анализ встреч."""
        stage1_dir = self.today_dir / "meeting-analysis" / "stage1"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage1_meeting_analysis_{timestamp}.txt"
        filepath = stage1_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Создаем символьную ссылку на latest
        self._create_symlink(stage1_dir / filename, stage1_dir / "stage1_meeting_analysis_latest.txt")
        
        logger.info(f"Meeting stage1 saved: {filepath}")
        return filepath
    
    def save_meeting_stage2(self, data: Dict[str, Any]) -> Path:
        """Сохранить stage2 анализ встреч."""
        stage2_dir = self.today_dir / "meeting-analysis" / "stage2"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage2_comprehensive_{timestamp}.json"
        filepath = stage2_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Создаем символьную ссылку на latest
        self._create_symlink(stage2_dir / filename, stage2_dir / "stage2_comprehensive_latest.json")
        
        logger.info(f"Meeting stage2 saved: {filepath}")
        return filepath
    
    def save_meeting_final(self, data: Dict[str, Any]) -> Path:
        """Сохранить финальный анализ встреч."""
        final_dir = self.today_dir / "meeting-analysis" / "final"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting-analysis_{timestamp}.json"
        filepath = final_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Создаем символьную ссылку на latest
        self._create_symlink(final_dir / filename, final_dir / "meeting-analysis_latest.json")
        
        # Also create date-specific version
        date_filename = f"meeting-analysis_{self.today}.json"
        self._create_symlink(final_dir / filename, final_dir / date_filename)
        
        logger.info(f"Meeting final saved: {filepath}")
        return filepath
    
    # EMPLOYEE PROGRESSION METHODS
    
    def save_employee_progression(self, employee_name: str, data: Dict[str, Any]) -> Path:
        """Сохранить прогресс сотрудника."""
        progression_dir = self.today_dir / "employee_progression"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self._sanitize_filename(employee_name)
        filename = f"{safe_name}_{timestamp}.json"
        filepath = progression_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Создаем символьную ссылку на latest
        self._create_symlink(progression_dir / filename, progression_dir / f"{safe_name}_latest.json")
        
        logger.info(f"Employee progression saved: {filepath}")
        return filepath
    
    # TRACKER METHODS
    
    def get_tracker_path(self) -> Path:
        """Получить путь к файлу трекера."""
        return self.base_dir / ".processing_tracker.json"
    
    # UTILITY METHODS
    
    def _sanitize_filename(self, filename: str) -> str:
        """Очистить имя файла для безопасного использования."""
        import re
        # Удаляем расширение
        name = Path(filename).stem
        # Заменяем недопустимые символы
        name = re.sub(r'[^\w\s-]', '', name)
        # Заменяем пробелы на подчеркивания
        name = re.sub(r'[-\s]+', '_', name)
        return name[:50]  # Ограничиваем длину
    
    def _create_symlink(self, target: Path, link_path: Path) -> None:
        """Создать символьную ссылку."""
        try:
            if link_path.exists():
                if link_path.is_symlink():
                    link_path.unlink()
                else:
                    link_path.unlink()
            
            # Создаем относительную ссылку
            relative_target = Path(os.path.relpath(target, link_path.parent))
            link_path.symlink_to(relative_target)
            
        except Exception as e:
            logger.warning(f"Failed to create symlink {link_path} -> {target}: {e}")
    
    # GETTER METHODS
    
    def get_latest_task_stage1(self) -> Optional[Path]:
        """Получить последний stage1 анализ задач."""
        stage1_dir = self.today_dir / "task-analysis" / "stage1"
        latest_link = stage1_dir / "stage1_task_analysis_latest.txt"
        
        if latest_link.exists() and latest_link.is_symlink():
            return stage1_dir / latest_link.readlink()
        
        # Ищем последний файл по дате
        files = list(stage1_dir.glob("stage1_task_analysis_*.txt"))
        if files:
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return files[0]
        
        return None
    
    def get_latest_task_stage2(self) -> Optional[Dict[str, Any]]:
        """Получить последний stage2 анализ задач."""
        stage2_dir = self.today_dir / "task-analysis" / "stage2"
        latest_link = stage2_dir / "stage2_task_result_latest.json"
        
        filepath = None
        if latest_link.exists() and latest_link.is_symlink():
            filepath = stage2_dir / latest_link.readlink()
        else:
            # Ищем последний файл по дате
            files = list(stage2_dir.glob("stage2_task_result_*.json"))
            if files:
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                filepath = files[0]
        
        if filepath and filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load latest task stage2: {e}")
        
        return None
    
    def get_latest_meeting_final(self) -> Optional[Dict[str, Any]]:
        """Получить последний финальный анализ встреч."""
        final_dir = self.today_dir / "meeting-analysis" / "final"
        latest_link = final_dir / "meeting-analysis_latest.json"
        
        filepath = None
        if latest_link.exists() and latest_link.is_symlink():
            filepath = final_dir / latest_link.readlink()
        else:
            # Ищем последний файл по дате
            files = list(final_dir.glob("meeting-analysis_*.json"))
            if files:
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                filepath = files[0]
        
        if filepath and filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load latest meeting final: {e}")
        
        return None
    
    def get_directory_info(self) -> Dict[str, Any]:
        """Получить информацию о директориях."""
        return {
            "base_dir": str(self.base_dir),
            "today": self.today,
            "today_dir": str(self.today_dir),
            "task_dirs": {
                "stage1": str(self.today_dir / "task-analysis" / "stage1"),
                "stage2": str(self.today_dir / "task-analysis" / "stage2"),
                "final": str(self.today_dir / "task-analysis" / "final")
            },
            "meeting_dirs": {
                "cleaned": str(self.today_dir / "meeting-analysis" / "cleaned-protocols"),
                "stage1": str(self.today_dir / "meeting-analysis" / "stage1"),
                "stage2": str(self.today_dir / "meeting-analysis" / "stage2"),
                "final": str(self.today_dir / "meeting-analysis" / "final")
            },
            "progression_dir": str(self.today_dir / "employee_progression"),
            "tracker_path": str(self.get_tracker_path())
        }
    
    # BACKWARD COMPATIBILITY
    
    def create_backward_compatibility_links(self) -> None:
        """Создать символьные ссылки для обратной совместимости."""
        project_root = self.base_dir.parent.parent
        
        # Task analyzer links
        task_stage1 = self.get_latest_task_stage1()
        if task_stage1:
            try:
                target = project_root / "stage1_text_analysis.txt"
                if target.exists():
                    target.unlink()
                target.symlink_to(task_stage1.relative_to(project_root))
                logger.info("Created backward compatibility link: stage1_text_analysis.txt")
            except Exception as e:
                logger.warning(f"Failed to create stage1 compatibility link: {e}")
        
        task_stage2 = self.get_latest_task_stage2()
        if task_stage2:
            try:
                # Get the actual file path
                stage2_dir = self.today_dir / "task-analysis" / "stage2"
                files = list(stage2_dir.glob("stage2_task_result_*.json"))
                if files:
                    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    target = project_root / "stage2_final_json.json"
                    if target.exists():
                        target.unlink()
                    target.symlink_to(files[0].relative_to(project_root))
                    logger.info("Created backward compatibility link: stage2_final_json.json")
            except Exception as e:
                logger.warning(f"Failed to create stage2 compatibility link: {e}")
    
    def create_unified_txt_reports(self) -> Dict[str, Path]:
        """
        Создать единые TXT отчеты после завершения всех этапов анализа.
        
        Returns:
            Dict[str, Path]: Словарь с путями к созданным TXT файлам
        """
        created_files = {}
        
        try:
            # 1. Единый отчет по анализу задач
            task_report = self._create_unified_task_report()
            if task_report:
                created_files['task_analysis'] = task_report
            
            # 2. Единый отчет по анализу встреч
            meeting_report = self._create_unified_meeting_report()
            if meeting_report:
                created_files['meeting_analysis'] = meeting_report
            
            # 3. Комбинированный отчет по всем анализам
            combined_report = self._create_combined_analysis_report()
            if combined_report:
                created_files['combined_analysis'] = combined_report
            
            # 4. Отчет по прогрессу сотрудников
            employee_report = self._create_employee_progression_report()
            if employee_report:
                created_files['employee_progression'] = employee_report
            
            logger.info(f"Created {len(created_files)} unified TXT reports")
            return created_files
            
        except Exception as e:
            logger.error(f"Failed to create unified TXT reports: {e}")
            return created_files
    
    def _create_unified_task_report(self) -> Optional[Path]:
        """Создать единый TXT отчет по анализу задач."""
        try:
            # Получаем данные из всех этапов
            stage1_content = self._get_latest_stage1_content()
            stage2_data = self.get_latest_task_stage2()
            
            if not stage1_content and not stage2_data:
                logger.warning("No task analysis data available for unified report")
                return None
            
            # Создаем unified отчет
            report_lines = []
            report_lines.append("КОМПЛЕКСНЫЙ АНАЛИЗ ЗАДАЧ КОМАНДЫ")
            report_lines.append("=" * 80)
            report_lines.append(f"Дата анализа: {self.today}")
            report_lines.append(f"Время генерации: {datetime.now().strftime('%H:%M:%S')}")
            report_lines.append("")
            
            # Stage 1: Текстовый анализ
            if stage1_content:
                report_lines.append("ЭТАП 1: ТЕКСТОВЫЙ АНАЛИЗ ЗАДАЧ")
                report_lines.append("-" * 60)
                report_lines.append(stage1_content)
                report_lines.append("")
            
            # Stage 2: Структурированные данные
            if stage2_data:
                report_lines.append("ЭТАП 2: СТРУКТУРИРОВАННЫЕ ДАННЫЕ")
                report_lines.append("-" * 60)
                report_lines.append(json.dumps(stage2_data, indent=2, ensure_ascii=False))
                report_lines.append("")
            
            # Сохраняем отчет
            reports_dir = self.today_dir / "unified-reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unified-task-analysis_{timestamp}.txt"
            filepath = reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            # Создаем ссылку на последнюю версию
            latest_link = reports_dir / "unified-task-analysis_latest.txt"
            self._create_symlink(filepath, latest_link)
            
            logger.info(f"Unified task report created: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to create unified task report: {e}")
            return None
    
    def _create_unified_meeting_report(self) -> Optional[Path]:
        """Создать единый TXT отчет по анализу встреч."""
        try:
            # Получаем данные анализа встреч
            meeting_data = self.get_latest_meeting_final()
            
            if not meeting_data:
                logger.warning("No meeting analysis data available for unified report")
                return None
            
            # Создаем unified отчет
            report_lines = []
            report_lines.append("КОМПЛЕКСНЫЙ АНАЛИЗ ВСТРЕЧ КОМАНДЫ")
            report_lines.append("=" * 80)
            report_lines.append(f"Дата анализа: {self.today}")
            report_lines.append(f"Время генерации: {datetime.now().strftime('%H:%M:%S')}")
            report_lines.append("")
            
            # Основные метрики
            if 'team_collaboration_score' in meeting_data:
                report_lines.append("ОСНОВНЫЕ МЕТРИКИ")
                report_lines.append("-" * 40)
                report_lines.append(f"Оценка командной коллаборации: {meeting_data['team_collaboration_score']:.2f}/10")
                report_lines.append(f"Согласованность задач и встреч: {meeting_data.get('task_meeting_alignment', 0):.2f}")
                report_lines.append(f"Общее здоровье команды: {meeting_data.get('overall_team_health', 0):.2f}/10")
                report_lines.append("")
            
            # Инсайты по команде
            if 'team_insights' in meeting_data:
                report_lines.append("КОМАНДНЫЕ ИНСАЙТЫ")
                report_lines.append("-" * 40)
                for insight in meeting_data['team_insights']:
                    report_lines.append(f"• {insight}")
                report_lines.append("")
            
            # Персональные инсайты
            if 'personal_insights' in meeting_data:
                report_lines.append("ИНСАЙТЫ СОТРУДНИКОВ")
                report_lines.append("-" * 40)
                for employee, insights in meeting_data['personal_insights'].items():
                    report_lines.append(f"{employee}:")
                    if isinstance(insights, dict):
                        for key, value in insights.items():
                            report_lines.append(f"  {key}: {value}")
                    else:
                        report_lines.append(f"  {insights}")
                    report_lines.append("")
            
            # Рекомендации
            if 'recommendations' in meeting_data:
                report_lines.append("РЕКОМЕНДАЦИИ")
                report_lines.append("-" * 40)
                for i, rec in enumerate(meeting_data['recommendations'], 1):
                    report_lines.append(f"{i}. {rec}")
                report_lines.append("")
            
            # Сохраняем отчет
            reports_dir = self.today_dir / "unified-reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unified-meeting-analysis_{timestamp}.txt"
            filepath = reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            # Создаем ссылку на последнюю версию
            latest_link = reports_dir / "unified-meeting-analysis_latest.txt"
            self._create_symlink(filepath, latest_link)
            
            logger.info(f"Unified meeting report created: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to create unified meeting report: {e}")
            return None
    
    def _create_combined_analysis_report(self) -> Optional[Path]:
        """Создать комбинированный отчет по всем анализам."""
        try:
            # Получаем данные из всех источников
            task_data = self.get_latest_task_stage2()
            meeting_data = self.get_latest_meeting_final()
            
            if not task_data and not meeting_data:
                logger.warning("No analysis data available for combined report")
                return None
            
            # Создаем комбинированный отчет
            report_lines = []
            report_lines.append("КОМБИНИРОВАННЫЙ АНАЛИЗ КОМАНДЫ")
            report_lines.append("=" * 80)
            report_lines.append(f"Дата анализа: {self.today}")
            report_lines.append(f"Время генерации: {datetime.now().strftime('%H:%M:%S')}")
            report_lines.append("")
            
            # Сводная информация
            report_lines.append("СВОДНАЯ ИНФОРМАЦИЯ")
            report_lines.append("-" * 40)
            report_lines.append(f"Доступные источники данных:")
            if task_data:
                report_lines.append("  ✅ Анализ задач")
            if meeting_data:
                report_lines.append("  ✅ Анализ встреч")
            report_lines.append("")
            
            # Комбинированные метрики
            task_score = 0
            meeting_score = 0
            
            if task_data and 'employee_performance' in task_data:
                scores = []
                for emp_data in task_data['employee_performance'].values():
                    if 'task_performance' in emp_data and 'score' in emp_data['task_performance']:
                        scores.append(emp_data['task_performance']['score'])
                if scores:
                    task_score = sum(scores) / len(scores)
            
            if meeting_data and 'team_collaboration_score' in meeting_data:
                meeting_score = meeting_data['team_collaboration_score']
            
            report_lines.append("КОМБИНИРОВАННЫЕ МЕТРИКИ")
            report_lines.append("-" * 40)
            report_lines.append(f"Средняя оценка задач: {task_score:.2f}/10")
            report_lines.append(f"Оценка коллаборации: {meeting_score:.2f}/10")
            
            if task_score > 0 and meeting_score > 0:
                combined_score = (task_score + meeting_score) / 2
                report_lines.append(f"Общая производительность: {combined_score:.2f}/10")
            
            report_lines.append("")
            
            # Объединенные рекомендации
            all_recommendations = []
            
            if meeting_data and 'recommendations' in meeting_data:
                all_recommendations.extend(meeting_data['recommendations'])
            
            if task_data and 'recommendations' in task_data:
                all_recommendations.extend(task_data['recommendations'])
            
            if all_recommendations:
                report_lines.append("ОБЪЕДИНЕННЫЕ РЕКОМЕНДАЦИИ")
                report_lines.append("-" * 40)
                for i, rec in enumerate(all_recommendations[:10], 1):  # Ограничиваем до 10
                    report_lines.append(f"{i}. {rec}")
                report_lines.append("")
            
            # Сохраняем отчет
            reports_dir = self.today_dir / "unified-reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined-analysis-{timestamp}.txt"
            filepath = reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            # Создаем ссылку на последнюю версию
            latest_link = reports_dir / "combined-analysis_latest.txt"
            self._create_symlink(filepath, latest_link)
            
            logger.info(f"Combined analysis report created: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to create combined analysis report: {e}")
            return None
    
    def _create_employee_progression_report(self) -> Optional[Path]:
        """Создать отчет по прогрессу сотрудников."""
        try:
            # Получаем файлы прогресса сотрудников
            progression_dir = self.today_dir / "employee_progression"
            progression_files = list(progression_dir.glob("*.json"))
            
            if not progression_files:
                logger.warning("No employee progression data available")
                return None
            
            # Собираем данные всех сотрудников
            employees_data = {}
            for file_path in progression_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        employee_name = data.get('employee_name', file_path.stem)
                        employees_data[employee_name] = data
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
            
            if not employees_data:
                logger.warning("No valid employee progression data")
                return None
            
            # Создаем отчет
            report_lines = []
            report_lines.append("ОТЧЕТ ПО ПРОГРЕССУ СОТРУДНИКОВ")
            report_lines.append("=" * 80)
            report_lines.append(f"Дата анализа: {self.today}")
            report_lines.append(f"Всего сотрудников: {len(employees_data)}")
            report_lines.append("")
            
            # Сортируем сотрудников по имени
            sorted_employees = sorted(employees_data.items())
            
            for employee_name, emp_data in sorted_employees:
                report_lines.append(f"СОТРУДНИК: {employee_name}")
                report_lines.append("-" * 60)
                
                # Основные метрики
                if 'performance_rating' in emp_data:
                    report_lines.append(f"Общая оценка: {emp_data['performance_rating']:.2f}/10")
                
                if 'engagement_level' in emp_data:
                    report_lines.append(f"Уровень вовлеченности: {emp_data['engagement_level']}")
                
                if 'communication_effectiveness' in emp_data:
                    report_lines.append(f"Эффективность коммуникации: {emp_data['communication_effectiveness']:.2f}/10")
                
                if 'task_to_meeting_correlation' in emp_data:
                    report_lines.append(f"Корреляция задач и встреч: {emp_data['task_to_meeting_correlation']:.2f}")
                
                # Детальные инсайты
                if 'detailed_insights' in emp_data:
                    report_lines.append("")
                    report_lines.append("Детальные инсайты:")
                    insights = emp_data['detailed_insights']
                    if isinstance(insights, str):
                        report_lines.append(insights)
                    elif isinstance(insights, list):
                        for insight in insights:
                            report_lines.append(f"  • {insight}")
                
                report_lines.append("")
                report_lines.append("=" * 80)
                report_lines.append("")
            
            # Сохраняем отчет
            reports_dir = self.today_dir / "unified-reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"employee-progression-{timestamp}.txt"
            filepath = reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            # Создаем ссылку на последнюю версию
            latest_link = reports_dir / "employee-progression_latest.txt"
            self._create_symlink(filepath, latest_link)
            
            logger.info(f"Employee progression report created: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to create employee progression report: {e}")
            return None
    
    def _get_latest_stage1_content(self) -> Optional[str]:
        """Получить содержимое последнего stage1 файла."""
        try:
            stage1_path = self.get_latest_task_stage1()
            if stage1_path and stage1_path.exists():
                with open(stage1_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Failed to read stage1 content: {e}")
        return None


if __name__ == "__main__":
    """
    Тестирование улучшенного файлового менеджера
    """
    import tempfile
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    # Создаем временную директорию для тестов
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = EnhancedFileManager(Path(temp_dir))
        
        print("=== Directory Structure ===")
        info = manager.get_directory_info()
        for key, value in info.items():
            print(f"{key}: {value}")
        
        print("\n=== Testing Task Analysis Saving ===")
        # Тест сохранения stage1
        task_stage1_content = "Task analysis stage 1 content"
        stage1_path = manager.save_task_stage1(task_stage1_content)
        print(f"Stage1 saved: {stage1_path}")
        
        # Тест сохранения stage2
        task_stage2_data = {"employees": {"test": {"rating": 8}}}
        stage2_path = manager.save_task_stage2(task_stage2_data)
        print(f"Stage2 saved: {stage2_path}")
        
        # Тест сохранения final
        task_final_data = {"analysis": "complete", "date": manager.today}
        final_path = manager.save_task_final(task_final_data)
        print(f"Final saved: {final_path}")
        
        print("\n=== Testing Meeting Analysis Saving ===")
        # Тест сохранения очищенного протокола
        cleaned_content = "Cleaned protocol content"
        protocol_path = manager.save_cleaned_protocol("test_protocol.txt", cleaned_content)
        print(f"Protocol saved: {protocol_path}")
        
        print("\n=== Testing Getter Methods ===")
        # Тест получения последних файлов
        latest_stage1 = manager.get_latest_task_stage1()
        print(f"Latest stage1: {latest_stage1}")
        
        latest_stage2 = manager.get_latest_task_stage2()
        print(f"Latest stage2 data: {latest_stage2}")
        
        print("\n=== Testing Backward Compatibility ===")
        manager.create_backward_compatibility_links()
        
        print("\n✅ All tests completed successfully!")
