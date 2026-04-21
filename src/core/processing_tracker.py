"""
Трекер обработанных файлов для инкрементальной обработки.

Этот модуль предоставляет систему отслеживания обработанных файлов,
позволяя избежать повторной обработки и обеспечивать инкрементальный анализ.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProcessingRecord:
    """Запись об обработке файла."""
    file_path: str
    file_hash: str
    processed_at: datetime
    processing_type: str  # 'meeting_clean' | 'task_analysis' | 'comprehensive_analysis'
    result_path: str
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, any]:
        """Конвертировать в словарь для сериализации."""
        return {
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'processed_at': self.processed_at.isoformat(),
            'processing_type': self.processing_type,
            'result_path': self.result_path,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'ProcessingRecord':
        """Создать из словаря."""
        return cls(
            file_path=data['file_path'],
            file_hash=data['file_hash'],
            processed_at=datetime.fromisoformat(data['processed_at']),
            processing_type=data['processing_type'],
            result_path=data['result_path'],
            metadata=data.get('metadata', {})
        )


class ProcessingTracker:
    """
    Трекер обработанных файлов с поддержкой различных типов обработки.
    """
    
    def __init__(self, tracker_file: Optional[Path] = None):
        """
        Инициализация трекера.
        
        Args:
            tracker_file: Путь к файлу трекера (по умолчанию в reports/daily/.processing_tracker.json)
        """
        if tracker_file is None:
            # По умолчанию в reports/daily/
            project_root = Path(__file__).parent.parent.parent
            tracker_file = project_root / "reports" / "daily" / ".processing_tracker.json"
        
        self.tracker_file = tracker_file
        self.records: Dict[str, List[ProcessingRecord]] = {}
        self._load_tracker()
    
    def _load_tracker(self) -> None:
        """Загрузить данные трекера из файла."""
        try:
            if self.tracker_file.exists():
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for file_path, records_data in data.items():
                    self.records[file_path] = [
                        ProcessingRecord.from_dict(record_data) 
                        for record_data in records_data
                    ]
                
                logger.info(f"Loaded {self._get_total_records()} processing records")
            else:
                logger.info("No existing tracker file, starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load tracker: {e}")
            self.records = {}
    
    def _save_tracker(self) -> None:
        """Сохранить данные трекера в файл."""
        try:
            # Убеждаемся что директория существует
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Конвертируем в сериализуемый формат
            data = {}
            for file_path, records in self.records.items():
                data[file_path] = [record.to_dict() for record in records]
            
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Saved tracker with {self._get_total_records()} records")
            
        except Exception as e:
            logger.error(f"Failed to save tracker: {e}")
    
    def _get_total_records(self) -> int:
        """Получить общее количество записей."""
        return sum(len(records) for records in self.records.values())
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Рассчитать хэш файла для detecting изменений."""
        try:
            with open(file_path, 'rb') as f:
                # Читаем файл блоками для больших файлов
                hash_md5 = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
                return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def is_processed(self, file_path: Path, processing_type: str) -> bool:
        """
        Проверить был ли файл уже обработан указанным типом обработки.
        
        Args:
            file_path: Путь к файлу
            processing_type: Тип обработки
            
        Returns:
            True если файл был обработан и не изменялся
        """
        file_path_str = str(file_path)
        
        if file_path_str not in self.records:
            return False
        
        # Ищем записи нужного типа
        for record in self.records[file_path_str]:
            if record.processing_type == processing_type:
                # Проверяем что файл не изменился (только для реальных файлов)
                if file_path.exists():
                    current_hash = self._calculate_file_hash(file_path)
                    if current_hash == record.file_hash:
                        return True
                    else:
                        logger.info(f"File {file_path} changed, needs reprocessing")
                        return False
                else:
                    # Для виртуальных或不 существующих файлов считаем что не обработан
                    logger.debug(f"Virtual/non-existent file {file_path}, skipping hash check")
                    return False
        
        return False
    
    def get_processing_record(self, file_path: Path, processing_type: str) -> Optional[ProcessingRecord]:
        """
        Получить запись об обработке файла.
        
        Args:
            file_path: Путь к файлу
            processing_type: Тип обработки
            
        Returns:
            Запись об обработке или None
        """
        file_path_str = str(file_path)
        
        if file_path_str not in self.records:
            return None
        
        for record in self.records[file_path_str]:
            if record.processing_type == processing_type:
                # Проверяем что файл не изменился
                current_hash = self._calculate_file_hash(file_path)
                if current_hash == record.file_hash:
                    return record
        
        return None
    
    def mark_processed(self, file_path: Path, processing_type: str, result_path: Path, 
                      metadata: Optional[Dict[str, any]] = None) -> None:
        """
        Отметить файл как обработанный.
        
        Args:
            file_path: Путь к исходному файлу
            processing_type: Тип обработки
            result_path: Путь к результату
            metadata: Дополнительные метаданные
        """
        file_path_str = str(file_path)
        file_hash = self._calculate_file_hash(file_path)
        
        # Создаем новую запись
        record = ProcessingRecord(
            file_path=file_path_str,
            file_hash=file_hash,
            processed_at=datetime.now(),
            processing_type=processing_type,
            result_path=str(result_path),
            metadata=metadata or {}
        )
        
        # Удаляем старые записи этого же типа (если есть)
        if file_path_str not in self.records:
            self.records[file_path_str] = []
        
        self.records[file_path_str] = [
            r for r in self.records[file_path_str] 
            if r.processing_type != processing_type
        ]
        
        # Добавляем новую запись
        self.records[file_path_str].append(record)
        
        # Сохраняем трекер
        self._save_tracker()
        
        logger.info(f"Marked {file_path} as processed ({processing_type}) -> {result_path}")
    
    def get_unprocessed_files(self, directory: Path, pattern: str = "*", 
                            processing_type: Optional[str] = None) -> List[Path]:
        """
        Получить список необработанных файлов в директории.
        
        Args:
            directory: Директория для поиска
            pattern: Паттерн имен файлов
            processing_type: Конкретный тип обработки для проверки
            
        Returns:
            Список необработанных файлов
        """
        if not directory.exists():
            return []
        
        all_files = list(directory.glob(pattern))
        unprocessed = []
        
        for file_path in all_files:
            if file_path.is_file():
                if processing_type:
                    if not self.is_processed(file_path, processing_type):
                        unprocessed.append(file_path)
                else:
                    # Проверяем любой тип обработки
                    is_any_processed = any(
                        self.is_processed(file_path, pt) 
                        for pt in ['meeting_clean', 'task_analysis', 'comprehensive_analysis']
                    )
                    if not is_any_processed:
                        unprocessed.append(file_path)
        
        return unprocessed
    
    def get_processed_files(self, processing_type: Optional[str] = None) -> List[ProcessingRecord]:
        """
        Получить список всех обработанных файлов.
        
        Args:
            processing_type: Фильтр по типу обработки
            
        Returns:
            Список записей об обработке
        """
        records = []
        
        for file_records in self.records.values():
            for record in file_records:
                if processing_type is None or record.processing_type == processing_type:
                    records.append(record)
        
        # Сортируем по дате обработки
        records.sort(key=lambda r: r.processed_at, reverse=True)
        return records
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Получить статистику обработки.
        
        Returns:
            Словарь со статистикой
        """
        stats = {
            'total_files': len(self.records),
            'total_records': self._get_total_records(),
            'by_type': {},
            'by_date': {},
            'last_processing': None
        }
        
        for file_records in self.records.values():
            for record in file_records:
                # Статистика по типу
                ptype = record.processing_type
                stats['by_type'][ptype] = stats['by_type'].get(ptype, 0) + 1
                
                # Статистика по дате
                date_str = record.processed_at.strftime('%Y-%m-%d')
                stats['by_date'][date_str] = stats['by_date'].get(date_str, 0) + 1
                
                # Последняя обработка
                if (stats['last_processing'] is None or 
                    record.processed_at > stats['last_processing']):
                    stats['last_processing'] = record.processed_at
        
        return stats
    
    def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """
        Очистить старые записи.
        
        Args:
            days_to_keep: Сколько дней хранить записи
            
        Returns:
            Количество удаленных записей
        """
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        removed_count = 0
        
        for file_path in list(self.records.keys()):
            original_count = len(self.records[file_path])
            
            # Фильтруем старые записи
            self.records[file_path] = [
                record for record in self.records[file_path]
                if record.processed_at.timestamp() > cutoff_date
            ]
            
            removed_count += original_count - len(self.records[file_path])
            
            # Удаляем пустые записи
            if not self.records[file_path]:
                del self.records[file_path]
        
        if removed_count > 0:
            self._save_tracker()
            logger.info(f"Cleaned up {removed_count} old processing records")
        
        return removed_count
    
    def force_reprocess(self, file_path: Path, processing_type: str) -> bool:
        """
        Принудительно отметить файл как необработанный.
        
        Args:
            file_path: Путь к файлу
            processing_type: Тип обработки
            
        Returns:
            True если запись была удалена
        """
        file_path_str = str(file_path)
        
        if file_path_str not in self.records:
            return False
        
        original_count = len(self.records[file_path_str])
        self.records[file_path_str] = [
            record for record in self.records[file_path_str]
            if record.processing_type != processing_type
        ]
        
        if len(self.records[file_path_str]) == 0:
            del self.records[file_path_str]
        
        removed = original_count - len(self.records.get(file_path_str, []))
        if removed > 0:
            self._save_tracker()
            logger.info(f"Force reprocess: removed {removed} records for {file_path}")
            return True
        
        return False


def create_global_tracker() -> ProcessingTracker:
    """Создать глобальный трекер для стандартного расположения."""
    return ProcessingTracker()


if __name__ == "__main__":
    """
    Тестирование трекера
    """
    import tempfile
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO)
    
    # Создаем временный трекер
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        tracker = ProcessingTracker(Path(tmp.name))
        
        # Тестовый файл
        test_file = Path(__file__).parent.parent / "README.md"
        
        print(f"Testing tracker with {test_file}")
        
        # Проверяем статус
        is_processed = tracker.is_processed(test_file, 'test_type')
        print(f"Is processed: {is_processed}")
        
        # Отмечаем как обработанный
        result_path = Path("/tmp/test_result.txt")
        tracker.mark_processed(test_file, 'test_type', result_path, {'test': True})
        
        # Проверяем снова
        is_processed = tracker.is_processed(test_file, 'test_type')
        print(f"Is processed after marking: {is_processed}")
        
        # Получаем статистику
        stats = tracker.get_statistics()
        print(f"Statistics: {stats}")
        
        # Очищаем
        Path(tmp.name).unlink()
