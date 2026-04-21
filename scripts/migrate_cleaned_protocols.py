#!/usr/bin/env python3
"""
Миграция обработанных протоколов в новую структуру и обновление processing tracker.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import hashlib

def calculate_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of file."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {filepath}: {e}")
        return ""

def main():
    """Main migration function."""
    project_root = Path(__file__).parent.parent
    daily_dir = project_root / "reports" / "daily"
    
    # Paths
    processing_tracker_path = daily_dir / ".processing_tracker.json"
    cleaned_protocols_dir = daily_dir / "2026-04-20" / "meeting-analysis" / "cleaned-protocols"
    protocols_dir = project_root / "protocols"
    
    print("🔄 МИГРАЦИЯ ОБРАБОТАННЫХ ПРОТОКОЛОВ")
    print("=" * 60)
    
    # Load existing processing tracker
    if processing_tracker_path.exists():
        with open(processing_tracker_path, 'r', encoding='utf-8') as f:
            tracker_data = json.load(f)
        print(f"✅ Загружен processing tracker с {len(tracker_data)} записями")
    else:
        tracker_data = {}
        print("⚠️  Processing tracker не найден, создаем новый")
    
    # Process each cleaned protocol
    migrated_count = 0
    
    for cleaned_file in cleaned_protocols_dir.glob("cleaned_*.txt"):
        try:
            # Extract original filename from cleaned filename
            original_name = cleaned_file.name
            if original_name.startswith("cleaned_"):
                # Remove "cleaned_" prefix and any timestamp suffix
                original_name = original_name[8:]  # Remove "cleaned_"
                if "_20260420_" in original_name:
                    original_name = original_name.split("_20260420_")[0]
            
            # Find corresponding original protocol file
            original_file = None
            for proto_file in protocols_dir.glob("*.txt"):
                if original_name in proto_file.name:
                    original_file = proto_file
                    break
            
            if not original_file:
                print(f"⚠️  Не найден оригинальный файл для {cleaned_file.name}")
                continue
            
            # Calculate hash of original file
            original_hash = calculate_file_hash(original_file)
            
            # Create processing tracker entry
            file_path_str = str(original_file)
            
            if file_path_str not in tracker_data:
                tracker_data[file_path_str] = []
            
            # Check if already processed
            already_processed = any(
                entry.get("processing_type") == "meeting_clean" 
                for entry in tracker_data[file_path_str]
            )
            
            if already_processed:
                print(f"⚠️  Файл {original_file.name} уже есть в tracker")
                continue
            
            # Add new entry
            tracker_entry = {
                "file_path": file_path_str,
                "file_hash": original_hash,
                "processed_at": datetime.now().isoformat(),
                "processing_type": "meeting_clean",
                "result_path": str(cleaned_file),
                "metadata": {
                    "original_filename": original_file.name,
                    "cleaned_filename": cleaned_file.name,
                    "content_length": len(cleaned_file.read_text(encoding='utf-8')),
                    "processing_timestamp": datetime.now().isoformat(),
                    "migrated": True
                }
            }
            
            tracker_data[file_path_str].append(tracker_entry)
            migrated_count += 1
            
            print(f"✅ Мигрирован: {original_file.name} -> {cleaned_file.name}")
            
        except Exception as e:
            print(f"❌ Ошибка миграции {cleaned_file.name}: {e}")
            continue
    
    # Save updated processing tracker
    with open(processing_tracker_path, 'w', encoding='utf-8') as f:
        json.dump(tracker_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 РЕЗУЛЬТАТЫ МИГРАЦИИ:")
    print(f"✅ Мигрировано файлов: {migrated_count}")
    print(f"📁 Всего записей в tracker: {len(tracker_data)}")
    print(f"💾 Tracker сохранен: {processing_tracker_path}")
    
    # Handle historical comprehensive-analysis files
    print(f"\n🔄 ОБРАБОТКА ИСТОРИЧЕСКИХ ФАЙЛОВ:")
    
    historical_files = [
        daily_dir / "comprehensive-analysis_2026-04-05.txt",
        daily_dir / "comprehensive-analysis_2026-04-10.txt"
    ]
    
    for hist_file in historical_files:
        if hist_file.exists():
            # Move to appropriate meeting-analysis structure
            date_str = hist_file.stem.split("_")[-1]  # Extract date
            target_dir = daily_dir / date_str / "meeting-analysis"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy as stage1 analysis (these are text analyses)
            target_file = target_dir / f"stage1_meeting_analysis_{date_str}.txt"
            
            import shutil
            shutil.copy2(hist_file, target_file)
            
            print(f"✅ Исторический файл перемещен: {hist_file.name} -> {target_file}")
    
    print(f"\n🎉 МИГРАЦИЯ ЗАВЕРШЕНА!")

if __name__ == "__main__":
    main()
