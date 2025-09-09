#!/usr/bin/env python3
"""
JSON Video URL Diff Tool
Compares two JSON files containing video data and finds URLs that exist in one but not the other.
"""

import json
import argparse
from typing import Dict, Set, List
from pathlib import Path


def load_json_file(filepath: str) -> Dict:
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filepath}': {e}")
        return None


def extract_urls(data: Dict) -> Set[str]:
    """Extract URLs from the video data structure."""
    urls = set()
    
    if 'videos' in data and isinstance(data['videos'], list):
        for video in data['videos']:
            if isinstance(video, dict) and 'url' in video:
                urls.add(video['url'])
    
    return urls


def find_url_differences(file1_path: str, file2_path: str) -> Dict[str, List[str]]:
    """Find URLs that exist in one file but not the other."""
    
    # Load both JSON files
    data1 = load_json_file(file1_path)
    data2 = load_json_file(file2_path)
    
    if data1 is None or data2 is None:
        return None
    
    # Extract URLs from both files
    urls1 = extract_urls(data1)
    urls2 = extract_urls(data2)
    
    # Find differences
    only_in_file1 = urls1 - urls2
    only_in_file2 = urls2 - urls1
    common_urls = urls1 & urls2
    
    return {
        'only_in_file1': sorted(list(only_in_file1)),
        'only_in_file2': sorted(list(only_in_file2)),
        'common_urls': sorted(list(common_urls)),
        'file1_count': len(urls1),
        'file2_count': len(urls2),
        'common_count': len(common_urls)
    }


def print_results(results: Dict, file1_path: str, file2_path: str):
    """Print the comparison results in a readable format."""
    
    print("=" * 80)
    print("JSON VIDEO URL DIFF RESULTS")
    print("=" * 80)
    print(f"File 1: {file1_path} ({results['file1_count']} URLs)")
    print(f"File 2: {file2_path} ({results['file2_count']} URLs)")
    print(f"Common URLs: {results['common_count']}")
    print()
    
    if results['only_in_file1']:
        print(f"URLs only in {file1_path} ({len(results['only_in_file1'])}):")
        print("-" * 50)
        for url in results['only_in_file1']:
            print(f"  {url}")
        print()
    
    if results['only_in_file2']:
        print(f"URLs only in {file2_path} ({len(results['only_in_file2'])}):")
        print("-" * 50)
        for url in results['only_in_file2']:
            print(f"  {url}")
        print()
    
    if not results['only_in_file1'] and not results['only_in_file2']:
        print("✓ All URLs are identical between both files!")


def save_results_to_json(results: Dict, output_file: str):
    """Save the diff results to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(results, file, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare two JSON files and find URL differences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python json_diff.py file1.json file2.json
  python json_diff.py file1.json file2.json --output results.json
  python json_diff.py file1.json file2.json --quiet
        """
    )
    
    parser.add_argument('file1', help='First JSON file')
    parser.add_argument('file2', help='Second JSON file')
    parser.add_argument('-o', '--output', help='Save results to JSON file')
    parser.add_argument('-q', '--quiet', action='store_true', 
                       help='Only show summary, not individual URLs')
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not Path(args.file1).exists():
        print(f"Error: File '{args.file1}' does not exist.")
        return 1
    
    if not Path(args.file2).exists():
        print(f"Error: File '{args.file2}' does not exist.")
        return 1
    
    # Perform the comparison
    results = find_url_differences(args.file1, args.file2)
    
    if results is None:
        return 1
    
    # Print results
    if args.quiet:
        print(f"File 1: {results['file1_count']} URLs")
        print(f"File 2: {results['file2_count']} URLs")
        print(f"Only in File 1: {len(results['only_in_file1'])}")
        print(f"Only in File 2: {len(results['only_in_file2'])}")
        print(f"Common: {results['common_count']}")
    else:
        print_results(results, args.file1, args.file2)
    
    # Save to output file if specified
    if args.output:
        save_results_to_json(results, args.output)
    
    return 0


if __name__ == "__main__":
    exit(main())


# Example usage as a module
def example_usage():
    """Example of how to use this as a module."""
    
    # Create sample data for demonstration
    sample_data1 = {
        "videos": [
            {"title": "Video 1", "url": "https://www.youtube.com/watch?v=abc123"},
            {"title": "Video 2", "url": "https://www.youtube.com/watch?v=def456"},
            {"title": "Video 3", "url": "https://www.youtube.com/watch?v=ghi789"}
        ]
    }
    
    sample_data2 = {
        "videos": [
            {"title": "Video 1", "url": "https://www.youtube.com/watch?v=abc123"},
            {"title": "Video 4", "url": "https://www.youtube.com/watch?v=jkl012"},
            {"title": "Video 5", "url": "https://www.youtube.com/watch?v=mno345"}
        ]
    }
    
    # Save sample files
    with open('sample1.json', 'w') as f:
        json.dump(sample_data1, f, indent=2)
    
    with open('sample2.json', 'w') as f:
        json.dump(sample_data2, f, indent=2)
    
    print("Sample files created: sample1.json and sample2.json")
    print("Run: python json_diff.py sample1.json sample2.json")


# Uncomment the line below to create sample files
# example_usage()	