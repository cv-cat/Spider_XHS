#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to classify XHS posts and comments by HKBU professor names.
Searches for English names, Simplified Chinese names, and Traditional Chinese names.
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class Professor:
    """Represents a professor with various name formats."""
    faculty: str
    department: str
    name_raw: str
    title: str
    english_names: List[str] = field(default_factory=list)
    chinese_names: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'faculty': self.faculty,
            'department': self.department,
            'name': self.name_raw,
            'title': self.title,
            'english_names': self.english_names,
            'chinese_names': self.chinese_names
        }


def parse_name(name_raw: str) -> Tuple[List[str], List[str]]:
    """
    Parse a name field to extract English and Chinese names.
    Handles various formats:
    - "Leevan LING"
    - "ZHONG, Bu 鍾布"
    - "Prof. XU, Jianliang"
    - "CHAN, Kara. K. W. 陳家華"
    """
    english_names = []
    chinese_names = []
    
    # Remove leading titles like "Prof.", "Dr."
    cleaned = re.sub(r'^(Prof\.|Dr\.|Professor)\s*', '', name_raw.strip())
    
    # Extract Chinese characters (both simplified and traditional)
    chinese_pattern = r'[\u4e00-\u9fff]+'
    chinese_matches = re.findall(chinese_pattern, cleaned)
    for match in chinese_matches:
        if len(match) >= 2:  # At least 2 Chinese characters for a name
            chinese_names.append(match)
    
    # Remove Chinese part for English name extraction
    english_part = re.sub(chinese_pattern, '', cleaned).strip()
    
    # Parse English name
    if english_part:
        # Handle format "LASTNAME, Firstname"
        if ',' in english_part:
            parts = english_part.split(',', 1)
            if len(parts) == 2:
                lastname = parts[0].strip()
                firstname = parts[1].strip()
                # Full name
                full_name = f"{firstname} {lastname}"
                english_names.append(full_name)
                # Last name only (for searching)
                english_names.append(lastname)
                # First name only if long enough
                if len(firstname) >= 3:
                    english_names.append(firstname)
        else:
            # Format "Firstname Lastname" or single name
            english_names.append(english_part)
            # Also add individual parts
            parts = english_part.split()
            for part in parts:
                if len(part) >= 3:  # Skip very short parts
                    english_names.append(part)
    
    # Deduplicate and clean
    english_names = list(set(n.strip() for n in english_names if n.strip() and len(n.strip()) >= 2))
    chinese_names = list(set(n.strip() for n in chinese_names if n.strip()))
    
    return english_names, chinese_names


def load_professors_from_csv(csv_file: str) -> List[Professor]:
    """Load professors from a CSV file."""
    professors = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name_raw = row.get('Name', '').strip()
            if not name_raw:
                continue
            
            english_names, chinese_names = parse_name(name_raw)
            
            # Skip if no usable names
            if not english_names and not chinese_names:
                continue
            
            prof = Professor(
                faculty=row.get('Faculty', ''),
                department=row.get('Department', ''),
                name_raw=name_raw,
                title=row.get('Title', ''),
                english_names=english_names,
                chinese_names=chinese_names
            )
            professors.append(prof)
    
    return professors


def load_all_professors(data_dir: str) -> List[Professor]:
    """Load professors from all CSV files."""
    data_path = Path(data_dir)
    
    csv_files = [
        'hkbu_teachers_v2.csv',
        'hkbu_comm_faculty_parsed_v2.csv',
        'hkbu_cs_faculty_parsed_v2.csv'
    ]
    
    all_professors = []
    seen_names = set()
    
    for csv_file in csv_files:
        file_path = data_path / csv_file
        if file_path.exists():
            professors = load_professors_from_csv(str(file_path))
            for prof in professors:
                # Deduplicate by raw name
                if prof.name_raw not in seen_names:
                    seen_names.add(prof.name_raw)
                    all_professors.append(prof)
    
    return all_professors


def build_search_index(professors: List[Professor]) -> Dict[str, Professor]:
    """Build a search index mapping name variants to professors."""
    index = {}
    
    for prof in professors:
        # Index English names - only if long enough to avoid false positives
        for name in prof.english_names:
            # Skip very short names (less than 4 chars) as they cause too many false positives
            # Names like "LI", "MA", "SO", "HU" are too common
            if len(name) < 4:
                continue
            key = name.upper()
            if key not in index:
                index[key] = prof
        
        # Index Chinese names (more reliable, shorter is OK)
        for name in prof.chinese_names:
            if name not in index:
                index[name] = prof
    
    return index


def find_matching_professors(text: str, search_index: Dict[str, Professor]) -> List[dict]:
    """
    Find all professors mentioned in the text.
    Returns a list of matched professor info dicts.
    """
    if not text:
        return []
    
    matched = {}
    text_upper = text.upper()
    
    # Search for English names (longer names first for better matching)
    english_items = [(k, v) for k, v in search_index.items() if k.isalpha() or k.replace(' ', '').isalpha()]
    english_items.sort(key=lambda x: len(x[0]), reverse=True)
    
    for name_key, prof in english_items:
        if name_key in text_upper:
            if prof.name_raw not in matched:
                matched[prof.name_raw] = prof
    
    # Search for Chinese names (longer names first)
    chinese_items = [(k, v) for k, v in search_index.items() if any('\u4e00' <= c <= '\u9fff' for c in k)]
    chinese_items.sort(key=lambda x: len(x[0]), reverse=True)
    
    for name_key, prof in chinese_items:
        if name_key in text:
            if prof.name_raw not in matched:
                matched[prof.name_raw] = prof
    
    return [p.to_dict() for p in matched.values()]


def classify_content(content: dict, search_index: Dict[str, Professor], content_type: str) -> dict:
    """
    Classify a single post or comment.
    Returns the content dict with added 'classified_professors' field.
    """
    search_text = ""
    
    if content_type == 'post':
        search_text = ' '.join([
            content.get('title', ''),
            content.get('desc', ''),
            content.get('tag_list', '')
        ])
    else:  # comment
        search_text = content.get('content', '')
    
    matched_professors = find_matching_professors(search_text, search_index)
    
    result = content.copy()
    result['classified_professors'] = matched_professors
    
    return result


def process_jsonl_files(jsonl_dir: str, search_index: Dict[str, Professor]) -> Tuple[List[dict], List[dict]]:
    """Process all JSONL files and classify contents."""
    jsonl_path = Path(jsonl_dir)
    
    classified_posts = []
    classified_comments = []
    
    # Process content files (posts)
    for content_file in jsonl_path.glob('search_contents_*.jsonl'):
        print(f"Processing {content_file.name}...")
        with open(content_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    content = json.loads(line)
                    classified = classify_content(content, search_index, 'post')
                    classified_posts.append(classified)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {e}")
                    continue
    
    # Process comment files
    for comment_file in jsonl_path.glob('search_comments_*.jsonl'):
        print(f"Processing {comment_file.name}...")
        with open(comment_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    content = json.loads(line)
                    classified = classify_content(content, search_index, 'comment')
                    classified_comments.append(classified)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {e}")
                    continue
    
    return classified_posts, classified_comments


def save_classified_results(output_dir: str, posts: List[dict], comments: List[dict]):
    """Save classified posts and comments to JSONL files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save posts with professor matches only
    matched_posts = [p for p in posts if p['classified_professors']]
    
    matched_posts_file = output_path / 'posts_with_professors.jsonl'
    with open(matched_posts_file, 'w', encoding='utf-8') as f:
        for post in matched_posts:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    # Save comments with professor matches only
    matched_comments = [c for c in comments if c['classified_professors']]
    
    matched_comments_file = output_path / 'comments_with_professors.jsonl'
    with open(matched_comments_file, 'w', encoding='utf-8') as f:
        for comment in matched_comments:
            f.write(json.dumps(comment, ensure_ascii=False) + '\n')
    
    # Create summary
    prof_post_count = {}
    prof_comment_count = {}
    
    for post in matched_posts:
        for prof in post['classified_professors']:
            name = prof['name']
            prof_post_count[name] = prof_post_count.get(name, 0) + 1
    
    for comment in matched_comments:
        for prof in comment['classified_professors']:
            name = prof['name']
            prof_comment_count[name] = prof_comment_count.get(name, 0) + 1
    
    all_matched_profs = set(prof_post_count.keys()) | set(prof_comment_count.keys())
    
    summary = {
        'total_posts': len(posts),
        'total_comments': len(comments),
        'posts_with_professor_match': len(matched_posts),
        'comments_with_professor_match': len(matched_comments),
        'professors_found': len(all_matched_profs),
        'professor_statistics': []
    }
    
    for prof_name in sorted(all_matched_profs):
        summary['professor_statistics'].append({
            'name': prof_name,
            'post_count': prof_post_count.get(prof_name, 0),
            'comment_count': prof_comment_count.get(prof_name, 0),
            'total_mentions': prof_post_count.get(prof_name, 0) + prof_comment_count.get(prof_name, 0)
        })
    
    summary_file = output_path / 'professor_classification_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    return summary


def main():
    # Define paths
    base_dir = Path(__file__).parent.parent  # Go up from scripts/ to project root
    data_dir = base_dir / 'data' / 'hkbu'
    jsonl_dir = base_dir / 'data' / 'xhs' / 'jsonl'
    output_dir = base_dir / 'data' / 'xhs' / 'processed'
    
    print("=" * 60)
    print("XHS Content Professor Classifier")
    print("=" * 60)
    
    # Load professors
    print(f"\nLoading professors from {data_dir}...")
    professors = load_all_professors(str(data_dir))
    print(f"Loaded {len(professors)} professors")
    
    # Build search index
    print("\nBuilding search index...")
    search_index = build_search_index(professors)
    print(f"Index contains {len(search_index)} name variants")
    
    # Process JSONL files
    print(f"\nProcessing JSONL files from {jsonl_dir}...")
    posts, comments = process_jsonl_files(str(jsonl_dir), search_index)
    print(f"Processed {len(posts)} posts and {len(comments)} comments")
    
    # Save results
    print(f"\nSaving results to {output_dir}...")
    summary = save_classified_results(str(output_dir), posts, comments)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Classification Summary")
    print("=" * 60)
    print(f"Total posts:              {summary['total_posts']}")
    print(f"Total comments:           {summary['total_comments']}")
    print(f"Posts with professor match:  {summary['posts_with_professor_match']}")
    print(f"Comments with professor match: {summary['comments_with_professor_match']}")
    print(f"Unique professors found:  {summary['professors_found']}")
    
    if summary['professor_statistics']:
        print("\nTop 20 professors by mention count:")
        sorted_profs = sorted(summary['professor_statistics'], 
                             key=lambda x: x['total_mentions'], reverse=True)
        for i, stat in enumerate(sorted_profs[:20], 1):
            print(f"  {i:2}. {stat['name']}: {stat['total_mentions']} mentions "
                  f"({stat['post_count']} posts, {stat['comment_count']} comments)")
    
    print("\n" + "=" * 60)
    print("Output files:")
    print(f"  - {output_dir / 'posts_with_professors.jsonl'}")
    print(f"  - {output_dir / 'comments_with_professors.jsonl'}")
    print(f"  - {output_dir / 'professor_classification_summary.json'}")
    print("=" * 60)


if __name__ == '__main__':
    main()
