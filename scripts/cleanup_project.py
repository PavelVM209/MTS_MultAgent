#!/usr/bin/env python3
"""
Скрипт для очистки проекта от временных и устаревших файлов

Анализирует проект и предлагает удалить:
- Временные файлы в корне проекта (stage1_*, stage2_*)
- Дублирующиеся отчеты в reports/
- Старые версии протоколов
- Временные файлы тестирования
- Логи тестов
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

class ProjectCleaner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dry_run = True  # По умолчанию только показываем что будет удалено
        
        # Категории файлов для удаления
        self.categories = {
            'temporary_root_files': {
                'description': 'Временные файлы в корне проекта',
                'patterns': ['stage1_*.txt', 'stage2_*.json', 'test_*.json', 'debug_*.py'],
                'paths': []
            },
            'duplicate_reports': {
                'description': 'Дублирующиеся отчеты',
                'patterns': ['reports/baseline_agent_test_*', 'reports/validation_report_*'],
                'paths': []
            },
            'test_logs': {
                'description': 'Логи тестов',
                'patterns': ['tests/logs/', 'tests/test_results/'],
                'paths': []
            },
            'old_protocols': {
                'description': 'Старые версии протоколов (если есть newer версии)',
                'patterns': ['protocols/*_old.txt', 'protocols/*_backup.txt'],
                'paths': []
            },
            'temporary_cleaned_protocols': {
                'description': 'Временные cleaned протоколы в корне reports/daily/',
                'patterns': ['reports/daily/cleaned_*.txt'],
                'paths': []
            },
            'old_stages': {
                'description': 'Старые файлы этапов analysis',
                'patterns': ['reports/daily/stages/'],
                'paths': []
            }
        }
        
        # Файлы которые НЕ удалять
        self.protected_files = {
            '.env.example', '.gitignore', 'README.md', 'requirements.txt', 
            'pyproject.toml', 'setup.py', '.env', 'config/', 'src/', 
            'tests/', 'docs/', 'memory-bank/', 'scripts/', 'data/'
        }
        
    def scan_files(self) -> Dict[str, List[Path]]:
        """Сканирует проект и находит файлы для удаления"""
        found_files = {}
        
        for category, config in self.categories.items():
            found_files[category] = []
            
            for pattern in config['patterns']:
                # Обрабатываем директории
                if pattern.endswith('/'):
                    dir_path = self.project_root / pattern.rstrip('/')
                    if dir_path.exists() and dir_path.is_dir():
                        found_files[category].append(dir_path)
                else:
                    # Обрабатываем файлы по паттернам
                    matches = self.project_root.glob(pattern)
                    for match in matches:
                        if match.exists():
                            found_files[category].append(match)
        
        return found_files
    
    def calculate_sizes(self, files: List[Path]) -> int:
        """Подсчитывает общий размер файлов"""
        total_size = 0
        for item in files:
            if item.is_file():
                total_size += item.stat().st_size
            elif item.is_dir():
                total_size += sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
        return total_size
    
    def is_safe_to_delete(self, path: Path) -> bool:
        """Проверяет что файл безопасен для удаления"""
        # Проверяем что нет в защищенных
        for protected in self.protected_files:
            if path.match(protected) or path.is_relative_to(self.project_root / protected):
                return False
        
        # Проверяем что файл старше 7 дней
        if path.is_file():
            file_time = datetime.fromtimestamp(path.stat().st_mtime)
            if datetime.now() - file_time < timedelta(days=7):
                return False
        
        return True
    
    def filter_safe_files(self, found_files: Dict[str, List[Path]]) -> Dict[str, List[Path]]:
        """Фильтрует только безопасные для удаления файлы"""
        safe_files = {}
        
        for category, files in found_files.items():
            safe_files[category] = [f for f in files if self.is_safe_to_delete(f)]
        
        return safe_files
    
    def format_size(self, size_bytes: int) -> str:
        """Форматирует размер в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def scan_and_report(self) -> Dict[str, Any]:
        """Сканирует и формирует отчет"""
        print("🔍 СКАНИРОВАНИЕ ПРОЕКТА НА УДАЛЕНИЕ ФАЙЛОВ")
        print("=" * 60)
        
        # Находим все файлы
        all_found = self.scan_files()
        
        # Фильтруем безопасные
        safe_files = self.filter_safe_files(all_found)
        
        # Считаем статистику
        total_files = 0
        total_size = 0
        category_stats = {}
        
        for category, files in safe_files.items():
            files_count = len([f for f in files if f.is_file()])
            dirs_count = len([f for f in files if f.is_dir()])
            size = self.calculate_sizes(files)
            
            category_stats[category] = {
                'files_count': files_count,
                'dirs_count': dirs_count,
                'size': size,
                'size_formatted': self.format_size(size),
                'description': self.categories[category]['description']
            }
            
            total_files += files_count + dirs_count
            total_size += size
        
        report = {
            'categories': category_stats,
            'total_files': total_files,
            'total_size': total_size,
            'total_size_formatted': self.format_size(total_size),
            'dry_run': self.dry_run
        }
        
        # Выводим отчет
        self.print_report(report)
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Выводит отчет на экран"""
        print(f"\n📊 ОТЧЕТ О ФАЙЛАХ ДЛЯ УДАЛЕНИЯ")
        print("=" * 60)
        print(f"Режим: {'ПРЕДПРОСМОТР (не удаляем)' if report['dry_run'] else 'УДАЛЕНИЕ'}")
        print(f"Всего файлов/директорий: {report['total_files']}")
        print(f"Общий размер: {report['total_size_formatted']}")
        print()
        
        for category, stats in report['categories'].items():
            if stats['files_count'] > 0 or stats['dirs_count'] > 0:
                print(f"📁 {stats['description']}")
                print(f"   Файлы: {stats['files_count']}, Директории: {stats['dirs_count']}")
                print(f"   Размер: {stats['size_formatted']}")
                print()
        
        if report['total_files'] == 0:
            print("✅ Файлы для удаления не найдены")
        else:
            print("⚠️  Для выполнения удаления используйте --execute")
    
    def execute_cleanup(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет очистку"""
        if report['total_files'] == 0:
            return {'success': True, 'deleted_count': 0, 'freed_space': 0}
        
        print("\n🗑️  ВЫПОЛНЕНИЕ ОЧИСТКИ")
        print("=" * 60)
        
        deleted_count = 0
        freed_space = 0
        errors = []
        
        # Создаем backup информации
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'deleted_files': [],
            'total_size_freed': 0
        }
        
        for category, stats in report['categories'].items():
            if stats['files_count'] == 0 and stats['dirs_count'] == 0:
                continue
                
            print(f"\n📁 Удаление: {stats['description']}")
            
            # Получаем список файлов для этой категории
            files_to_delete = []
            for pattern in self.categories[category]['patterns']:
                if pattern.endswith('/'):
                    dir_path = self.project_root / pattern.rstrip('/')
                    if dir_path.exists():
                        files_to_delete.append(dir_path)
                else:
                    files_to_delete.extend(self.project_root.glob(pattern))
            
            # Фильтруем безопасные
            files_to_delete = [f for f in files_to_delete if self.is_safe_to_delete(f)]
            
            for item in files_to_delete:
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        freed_space += size
                        
                        backup_info['deleted_files'].append({
                            'path': str(item.relative_to(self.project_root)),
                            'type': 'file',
                            'size': size
                        })
                        
                        print(f"  ✅ Удален файл: {item.name}")
                        
                    elif item.is_dir():
                        # Удаляем директорию рекурсивно
                        size = self.calculate_sizes([item])
                        shutil.rmtree(item)
                        deleted_count += 1
                        freed_space += size
                        
                        backup_info['deleted_files'].append({
                            'path': str(item.relative_to(self.project_root)),
                            'type': 'directory',
                            'size': size
                        })
                        
                        print(f"  ✅ Удалена директория: {item.name}")
                        
                except Exception as e:
                    error_msg = f"Ошибка удаления {item}: {e}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
        
        backup_info['total_size_freed'] = freed_space
        
        # Сохраняем backup информацию
        backup_file = self.project_root / f"cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 ИНформация сохранена: {backup_file}")
        
        # Итоги
        print(f"\n✅ ОЧИСТКА ЗАВЕРШЕНА")
        print(f"Удалено файлов/директорий: {deleted_count}")
        print(f"Освобождено места: {self.format_size(freed_space)}")
        print(f"Ошибок: {len(errors)}")
        
        if errors:
            print(f"\n❌ ОШИБКИ:")
            for error in errors:
                print(f"  • {error}")
        
        return {
            'success': len(errors) == 0,
            'deleted_count': deleted_count,
            'freed_space': freed_space,
            'backup_file': backup_file
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Очистка проекта от временных файлов')
    parser.add_argument('--execute', action='store_true', help='Выполнить удаление (без этого флага только предпросмотр)')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), help='Корень проекта')
    
    args = parser.parse_args()
    
    # Создаем очиститель
    cleaner = ProjectCleaner(args.project_root)
    
    if args.execute:
        cleaner.dry_run = False
    
    # Сканируем и показываем отчет
    report = cleaner.scan_and_report()
    
    # Если это реальное выполнение и есть файлы для удаления
    if not cleaner.dry_run and report['total_files'] > 0:
        response = input("\n⚠️  Вы уверены что хотите удалить эти файлы? (y/N): ")
        if response.lower() in ['y', 'yes']:
            result = cleaner.execute_cleanup(report)
            
            if result['success']:
                print(f"\n🎉 Очистка успешно завершена!")
                print(f"Освобождено: {cleaner.format_size(result['freed_space'])}")
            else:
                print(f"\n❌ Очистка завершена с ошибками")
        else:
            print("❌ Отменено пользователем")


if __name__ == "__main__":
    main()
