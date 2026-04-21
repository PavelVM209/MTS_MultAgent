"""
Менеджер файлов с таймстемпами для сохранения результатов анализа.

Этот модуль предоставляет функции для сохранения файлов с таймстемпами
и создания символьных ссылок на последние результаты.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class TimestampedFileManager:
    """
    Менеджер для сохранения файлов с таймстемпами и управления ссылками.
    """
    
    def __init__(self, base_dir: Path):
        """
        Инициализация менеджера.
        
        Args:
            base_dir: Базовая директория для сохранения файлов
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_with_timestamp(self, base_name: str, content: Union[str, bytes], 
                          extension: str = "txt", encoding: str = "utf-8",
                          create_latest_link: bool = True) -> Path:
        """
        Сохранить контент в файл с таймстемпом.
        
        Args:
            base_name: Базовое имя файла (без таймстемпа)
            content: Контент для сохранения
            extension: Расширение файла
            encoding: Кодировка (для текстовых файлов)
            create_latest_link: Создавать ли символьную ссылку на latest
            
        Returns:
            Путь к созданному файлу
        """
        # Генерируем имя с таймстемпом
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.{extension}"
        filepath = self.base_dir / filename
        
        try:
            # Сохраняем файл
            if isinstance(content, bytes):
                with open(filepath, 'wb') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding=encoding) as f:
                    f.write(content)
            
            logger.info(f"Saved timestamped file: {filepath}")
            
            # Создаем символьную ссылку на latest если нужно
            if create_latest_link:
                self._create_latest_link(base_name, filename, extension)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save timestamped file {base_name}: {e}")
            raise
    
    def _create_latest_link(self, base_name: str, filename: str, extension: str) -> None:
        """
        Создать символьную ссылку на последний файл.
        
        Args:
            base_name: Базовое имя
            filename: Имя файла с таймстемпом
            extension: Расширение
        """
        latest_path = self.base_dir / f"{base_name}_latest.{extension}"
        
        try:
            # Удаляем старую ссылку если есть
            if latest_path.exists():
                if latest_path.is_symlink():
                    latest_path.unlink()
                else:
                    latest_path.unlink()
            
            # Создаем новую ссылку
            latest_path.symlink_to(filename)
            logger.debug(f"Created latest link: {latest_path} -> {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to create latest link: {e}")
    
    def get_latest_file(self, base_name: str, extension: str = "txt") -> Optional[Path]:
        """
        Получить путь к последнему файлу.
        
        Args:
            base_name: Базовое имя файла
            extension: Расширение файла
            
        Returns:
            Путь к последнему файлу или None
        """
        latest_path = self.base_dir / f"{base_name}_latest.{extension}"
        
        try:
            if latest_path.exists() and latest_path.is_symlink():
                # Получаем реальный путь через символьную ссылку
                real_path = self.base_dir / latest_path.readlink()
                if real_path.exists():
                    return real_path
                else:
                    logger.warning(f"Latest link points to non-existent file: {real_path}")
                    
        except Exception as e:
            logger.warning(f"Failed to read latest link: {e}")
        
        # Ищем последний файл по дате создания
        pattern = f"{base_name}_*.{extension}"
        files = list(self.base_dir.glob(pattern))
        
        if not files:
            return None
        
        # Сортируем по времени модификации (новые последние)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        latest_file = files[0]
        
        # Обновляем ссылку если можно
        try:
            if latest_path.exists():
                latest_path.unlink()
            latest_path.symlink_to(latest_file.name)
        except Exception as e:
            logger.warning(f"Failed to update latest link: {e}")
        
        return latest_file
    
    def get_all_files(self, base_name: str, extension: str = "txt") -> list[Path]:
        """
        Получить все файлы с указанным базовым именем.
        
        Args:
            base_name: Базовое имя файла
            extension: Расширение файла
            
        Returns:
            Список путей к файлам (сортированных по дате)
        """
        pattern = f"{base_name}_*.{extension}"
        files = list(self.base_dir.glob(pattern))
        
        # Сортируем по дате создания (новые последние)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files
    
    def cleanup_old_files(self, base_name: str, extension: str = "txt", 
                         keep_count: int = 10) -> int:
        """
        Очистить старые файлы, оставив только указанное количество.
        
        Args:
            base_name: Базовое имя файла
            extension: Расширение файла
            keep_count: Сколько файлов оставить
            
        Returns:
            Количество удаленных файлов
        """
        files = self.get_all_files(base_name, extension)
        
        if len(files) <= keep_count:
            return 0
        
        # Удаляем самые старые файлы
        files_to_delete = files[keep_count:]
        deleted_count = 0
        
        for file_path in files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {e}")
        
        return deleted_count
    
    def save_json_with_timestamp(self, base_name: str, data: dict, 
                               create_latest_link: bool = True) -> Path:
        """
        Сохранить JSON данные с таймстемпом.
        
        Args:
            base_name: Базовое имя файла
            data: Данные для сохранения
            create_latest_link: Создавать ли символьную ссылку на latest
            
        Returns:
            Путь к созданному файлу
        """
        import json
        
        # Конвертируем в JSON строку
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        
        return self.save_with_timestamp(
            base_name=base_name,
            content=json_content,
            extension="json",
            encoding="utf-8",
            create_latest_link=create_latest_link
        )
    
    def load_latest_json(self, base_name: str) -> Optional[dict]:
        """
        Загрузить последний JSON файл.
        
        Args:
            base_name: Базовое имя файла
            
        Returns:
            Данные из файла или None
        """
        import json
        
        latest_file = self.get_latest_file(base_name, "json")
        
        if not latest_file or not latest_file.exists():
            return None
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load latest JSON {base_name}: {e}")
            return None
    
    def get_file_info(self, base_name: str, extension: str = "txt") -> Optional[dict]:
        """
        Получить информацию о файлах.
        
        Args:
            base_name: Базовое имя файла
            extension: Расширение файла
            
        Returns:
            Словарь с информацией о файлах
        """
        files = self.get_all_files(base_name, extension)
        latest_file = self.get_latest_file(base_name, extension)
        
        if not files:
            return None
        
        # Собираем информацию
        file_infos = []
        for file_path in files:
            stat = file_path.stat()
            file_infos.append({
                'path': str(file_path),
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'is_latest': file_path == latest_file
            })
        
        return {
            'base_name': base_name,
            'extension': extension,
            'total_files': len(files),
            'latest_file': str(latest_file) if latest_file else None,
            'files': file_infos
        }


class AnalysisFileManager:
    """
    Специализированный менеджер для файлов анализа.
    """
    
    def __init__(self, reports_dir: Optional[Path] = None):
        """
        Инициализация менеджера анализа.
        
        Args:
            reports_dir: Директория отчетов (по умолчанию reports/daily)
        """
        if reports_dir is None:
            project_root = Path(__file__).parent.parent.parent
            reports_dir = project_root / "reports" / "daily"
        
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем поддиректории для разных типов файлов
        self.stages_dir = self.reports_dir / "stages"
        self.stages_dir.mkdir(exist_ok=True)
        
        # Менеджеры для разных типов файлов
        self.stage1_manager = TimestampedFileManager(self.stages_dir)
        self.stage2_manager = TimestampedFileManager(self.stages_dir)
        self.daily_manager = TimestampedFileManager(self.reports_dir)
    
    def save_stage1_analysis(self, content: str, analysis_type: str = "task") -> Path:
        """
        Сохранить анализ этапа 1.
        
        Args:
            content: Содержимое анализа
            analysis_type: Тип анализа (task/meeting)
            
        Returns:
            Путь к созданному файлу
        """
        base_name = f"stage1_{analysis_type}_analysis"
        return self.stage1_manager.save_with_timestamp(base_name, content, "txt")
    
    def save_stage2_json(self, data: dict, analysis_type: str = "task") -> Path:
        """
        Сохранить JSON этапа 2.
        
        Args:
            data: Данные для сохранения
            analysis_type: Тип анализа (task/meeting)
            
        Returns:
            Путь к созданному файлу
        """
        base_name = f"stage2_{analysis_type}_result"
        return self.stage2_manager.save_json_with_timestamp(base_name, data)
    
    def save_daily_report(self, data: dict, report_type: str) -> Path:
        """
        Сохранить ежедневный отчет.
        
        Args:
            data: Данные отчета
            report_type: Тип отчета (task-analysis/meeting-analysis)
            
        Returns:
            Путь к созданному файлу
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        base_name = f"{report_type}_{date_str}"
        return self.daily_manager.save_json_with_timestamp(base_name, data)
    
    def get_latest_stage1(self, analysis_type: str = "task") -> Optional[Path]:
        """Получить последний анализ этапа 1."""
        base_name = f"stage1_{analysis_type}_analysis"
        return self.stage1_manager.get_latest_file(base_name, "txt")
    
    def get_latest_stage2(self, analysis_type: str = "task") -> Optional[dict]:
        """Получить последний JSON этапа 2."""
        base_name = f"stage2_{analysis_type}_result"
        return self.stage2_manager.load_latest_json(base_name)
    
    def cleanup_old_analyses(self, keep_count: int = 10) -> dict:
        """
        Очистить старые анализы.
        
        Args:
            keep_count: Сколько файлов оставить
            
        Returns:
            Статистика очистки
        """
        stats = {}
        
        # Очищаем stage1 файлы
        task_deleted = self.stage1_manager.cleanup_old_files("stage1_task_analysis", "txt", keep_count)
        meeting_deleted = self.stage1_manager.cleanup_old_files("stage1_meeting_analysis", "txt", keep_count)
        stats['stage1_deleted'] = task_deleted + meeting_deleted
        
        # Очищаем stage2 файлы
        task_json_deleted = self.stage2_manager.cleanup_old_files("stage2_task_result", "json", keep_count)
        meeting_json_deleted = self.stage2_manager.cleanup_old_files("stage2_meeting_result", "json", keep_count)
        stats['stage2_deleted'] = task_json_deleted + meeting_json_deleted
        
        stats['total_deleted'] = stats['stage1_deleted'] + stats['stage2_deleted']
        
        return stats


def create_analysis_file_manager(reports_dir: Optional[Path] = None) -> AnalysisFileManager:
    """Создать менеджер файлов анализа."""
    return AnalysisFileManager(reports_dir)


if __name__ == "__main__":
    """
    Тестирование менеджера файлов
    """
    import tempfile
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TimestampedFileManager(Path(temp_dir))
        
        # Тест сохранения файлов
        content = "Test content for timestamped file"
        file1 = manager.save_with_timestamp("test_file", content)
        print(f"Saved file: {file1}")
        
        # Тест сохранения JSON
        data = {"test": True, "timestamp": datetime.now().isoformat()}
        json_file = manager.save_json_with_timestamp("test_json", data)
        print(f"Saved JSON: {json_file}")
        
        # Тест получения последнего файла
        latest = manager.get_latest_file("test_file")
        print(f"Latest file: {latest}")
        
        # Тест загрузки JSON
        loaded_data = manager.load_latest_json("test_json")
        print(f"Loaded data: {loaded_data}")
        
        # Тест AnalysisFileManager
        analysis_manager = AnalysisFileManager(Path(temp_dir))
        stage1_file = analysis_manager.save_stage1_analysis("Test stage1 content", "task")
        stage2_file = analysis_manager.save_stage2_json({"result": "success"}, "task")
        
        print(f"Stage1 file: {stage1_file}")
        print(f"Stage2 file: {stage2_file}")
        
        # Тест получения последних файлов
        latest_stage1 = analysis_manager.get_latest_stage1("task")
        latest_stage2 = analysis_manager.get_latest_stage2("task")
        
        print(f"Latest stage1: {latest_stage1}")
        print(f"Latest stage2: {latest_stage2}")
