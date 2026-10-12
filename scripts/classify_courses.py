#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to classify XHS posts and comments by HKBU course codes.
Matches course codes like "ACCT1006" or "1006" in post/comment content.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set


def load_courses(courses_file: str) -> Dict[str, dict]:
    """
    Load courses from JSON file and create a lookup dictionary.
    Returns a dict mapping various forms of course codes to course info.
    """
    with open(courses_file, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    
    # Create lookup dictionary with multiple key forms
    course_lookup = {}
    course_full_codes = {}  # Only full codes (e.g., "ACCT1006")
    
    for course in courses:
        code = course.get('code', '')
        if not code:
            continue
        
        # Full code (e.g., "ACCT1006") - primary matching
        course_lookup[code.upper()] = course
        course_lookup[code] = course
        course_full_codes[code.upper()] = course
        
        # For numeric part, we need to be careful to avoid matching years
        # Only add if the code follows pattern like ACCT1006 (letters + 4 digits)
        # and the numeric part is not a common year (2024, 2025, 2026, etc.)
        numeric_match = re.match(r'^[A-Z]+(\d{4})$', code.upper())
        if numeric_match:
            numeric_part = numeric_match.group(1)
            # Skip years 2020-2030 to avoid false positives
            if not numeric_part.startswith('202'):
                course_lookup[numeric_part] = course
    
    return course_lookup, course_full_codes


def find_matching_courses(text: str, course_lookup: Dict[str, dict]) -> List[str]:
    """
    Find all course codes mentioned in the text.
    Returns a list of matched course codes.
    Uses strict matching to avoid false positives.
    Handles both "MGNT7090" and "MGNT 7090" formats.
    """
    if not text:
        return []
    
    matched_courses = {}
    
    # Pattern for full course codes: 2-5 letters followed by optional space and 4 digits
    # Examples: ACCT1006, BIOL2026, MGNT7090, MCM7060, MGNT 7090, BIOL 2026
    # Also handles formats like "FIN 7250" where letters and numbers are separated
    full_code_pattern = r'\b([A-Z]{2,5})\s*(\d{4})\b'
    
    for match in re.finditer(full_code_pattern, text.upper()):
        letters = match.group(1)
        numbers = match.group(2)
        # Combine without space for lookup
        code = letters + numbers
        if code in course_lookup:
            course = course_lookup[code]
            course_code = course.get('code', code)
            if course_code not in matched_courses:
                matched_courses[course_code] = course
    
    return sorted(list(matched_courses.keys()))


def classify_content(content: dict, course_lookup: Dict[str, dict], content_type: str) -> dict:
    """
    Classify a single post or comment.
    Returns the content dict with added 'classified_courses' field.
    """
    # Build text to search based on content type
    search_text = ""
    
    if content_type == 'post':
        search_text = ' '.join([
            content.get('title', ''),
            content.get('desc', ''),
            content.get('tag_list', '')
        ])
    else:  # comment
        search_text = content.get('content', '')
    
    # Find matching courses
    matched_courses = find_matching_courses(search_text, course_lookup)
    
    # Add classification to content
    result = content.copy()
    result['classified_courses'] = matched_courses if matched_courses else []
    
    return result


def process_jsonl_files(jsonl_dir: str, course_lookup: Dict[str, dict]) -> tuple:
    """
    Process all JSONL files and classify contents.
    Returns tuple of (classified_posts, classified_comments)
    """
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
                    classified = classify_content(content, course_lookup, 'post')
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
                    classified = classify_content(content, course_lookup, 'comment')
                    classified_comments.append(classified)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {e}")
                    continue
    
    return classified_posts, classified_comments


def save_classified_results(output_dir: str, posts: List[dict], comments: List[dict]):
    """
    Save classified posts and comments to JSONL files.
    Also creates a summary file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save posts with course matches only
    matched_posts_file = output_path / 'posts_with_courses.jsonl'
    all_posts_file = output_path / 'all_posts_classified.jsonl'
    
    matched_posts = [p for p in posts if p['classified_courses']]
    
    with open(matched_posts_file, 'w', encoding='utf-8') as f:
        for post in matched_posts:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    with open(all_posts_file, 'w', encoding='utf-8') as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    # Save comments with course matches only
    matched_comments_file = output_path / 'comments_with_courses.jsonl'
    all_comments_file = output_path / 'all_comments_classified.jsonl'
    
    matched_comments = [c for c in comments if c['classified_courses']]
    
    with open(matched_comments_file, 'w', encoding='utf-8') as f:
        for comment in matched_comments:
            f.write(json.dumps(comment, ensure_ascii=False) + '\n')
    
    with open(all_comments_file, 'w', encoding='utf-8') as f:
        for comment in comments:
            f.write(json.dumps(comment, ensure_ascii=False) + '\n')
    
    # Create summary
    course_post_count = {}
    course_comment_count = {}
    
    for post in matched_posts:
        for course in post['classified_courses']:
            course_post_count[course] = course_post_count.get(course, 0) + 1
    
    for comment in matched_comments:
        for course in comment['classified_courses']:
            course_comment_count[course] = course_comment_count.get(course, 0) + 1
    
    # Get all courses that had matches
    all_matched_courses = set(course_post_count.keys()) | set(course_comment_count.keys())
    
    summary = {
        'total_posts': len(posts),
        'total_comments': len(comments),
        'posts_with_course_match': len(matched_posts),
        'comments_with_course_match': len(matched_comments),
        'courses_found': len(all_matched_courses),
        'course_statistics': []
    }
    
    for course in sorted(all_matched_courses):
        summary['course_statistics'].append({
            'course_code': course,
            'post_count': course_post_count.get(course, 0),
            'comment_count': course_comment_count.get(course, 0),
            'total_mentions': course_post_count.get(course, 0) + course_comment_count.get(course, 0)
        })
    
    summary_file = output_path / 'classification_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    return summary


def main():
    # Define paths
    base_dir = Path(__file__).parent
    courses_file = base_dir / 'data' / 'hkbu' / 'courses_sem2.json'
    jsonl_dir = base_dir / 'data' / 'xhs' / 'jsonl'
    output_dir = base_dir / 'data' / 'xhs' / 'processed'
    
    print("=" * 60)
    print("XHS Content Course Classifier")
    print("=" * 60)
    
    # Load courses
    print(f"\nLoading courses from {courses_file}...")
    course_lookup, course_full_codes = load_courses(str(courses_file))
    print(f"Loaded {len(course_lookup)} course code variants ({len(course_full_codes)} full codes)")
    
    # Process JSONL files
    print(f"\nProcessing JSONL files from {jsonl_dir}...")
    posts, comments = process_jsonl_files(str(jsonl_dir), course_lookup)
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
    print(f"Posts with course match:  {summary['posts_with_course_match']}")
    print(f"Comments with course match: {summary['comments_with_course_match']}")
    print(f"Unique courses found:     {summary['courses_found']}")
    
    if summary['course_statistics']:
        print("\nTop 20 courses by mention count:")
        sorted_courses = sorted(summary['course_statistics'], 
                               key=lambda x: x['total_mentions'], reverse=True)
        for i, stat in enumerate(sorted_courses[:20], 1):
            print(f"  {i:2}. {stat['course_code']}: {stat['total_mentions']} mentions "
                  f"({stat['post_count']} posts, {stat['comment_count']} comments)")
    
    print("\n" + "=" * 60)
    print("Output files:")
    print(f"  - {output_dir / 'all_posts_classified.jsonl'}")
    print(f"  - {output_dir / 'all_comments_classified.jsonl'}")
    print(f"  - {output_dir / 'posts_with_courses.jsonl'}")
    print(f"  - {output_dir / 'comments_with_courses.jsonl'}")
    print(f"  - {output_dir / 'classification_summary.json'}")
    print("=" * 60)


if __name__ == '__main__':
    main()
