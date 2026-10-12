#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to remove duplicate entries from JSONL files.
For contents: deduplicates by 'note_id'
For comments: deduplicates by 'comment_id'
"""

import json
import os
from pathlib import Path
from typing import Tuple


def deduplicate_jsonl(file_path: str, unique_key: str) -> Tuple[int, int]:
    """
    Remove duplicate entries from a JSONL file based on a unique key.

    Args:
        file_path: Path to the JSONL file
        unique_key: The key to use for deduplication (e.g., 'note_id', 'comment_id')

    Returns:
        Tuple of (original_count, deduplicated_count)
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return 0, 0

    seen_ids = set()
    unique_records = []
    original_count = 0

    # Read and deduplicate
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            original_count += 1
            try:
                record = json.loads(line)
                record_id = record.get(unique_key)
                if record_id and record_id not in seen_ids:
                    seen_ids.add(record_id)
                    unique_records.append(record)
            except json.JSONDecodeError as e:
                print(f"Error parsing line in {file_path}: {e}")
                continue

    # Write back deduplicated records
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in unique_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    return original_count, len(unique_records)


def main():
    # Define the data directory
    data_dir = Path(__file__).parent / 'data' / 'xhs' / 'jsonl'

    # Files to process with their unique keys
    files_to_process = [
        ('search_contents_2026-04-01.jsonl', 'note_id'),
        ('search_contents_2026-04-02.jsonl', 'note_id'),
        ('search_comments_2026-04-01.jsonl', 'comment_id'),
        ('search_comments_2026-04-02.jsonl', 'comment_id'),
    ]

    print("=" * 60)
    print("JSONL Deduplication Script")
    print("=" * 60)

    total_original = 0
    total_deduplicated = 0

    for filename, unique_key in files_to_process:
        file_path = data_dir / filename
        if file_path.exists():
            original, deduplicated = deduplicate_jsonl(
                str(file_path), unique_key)
            duplicates = original - deduplicated
            print(f"\n{filename}:")
            print(f"  Original count:     {original}")
            print(f"  Deduplicated count: {deduplicated}")
            print(f"  Duplicates removed: {duplicates}")
            total_original += original
            total_deduplicated += deduplicated
        else:
            print(f"\n{filename}: File not found, skipping...")

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total original:     {total_original}")
    print(f"  Total deduplicated: {total_deduplicated}")
    print(f"  Total duplicates:   {total_original - total_deduplicated}")
    print("=" * 60)


if __name__ == '__main__':
    main()
