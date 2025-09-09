#!/usr/bin/env python3
"""
YouTube Channel Videos HTML Parser

This script parses a downloaded HTML file from a YouTube channel's videos page
and extracts video URLs into JSON format.

Usage:
    python3 youtube_parser.py <html_file_path> [output_file_path]

Example:
    python3 youtube_parser.py channel_videos.html videos.json
"""

import json
import re
import sys
import argparse
from bs4 import BeautifulSoup


def parse_youtube_html(html_file_path):
    """
    Parse YouTube channel videos HTML and extract video URLs.
    
    Args:
        html_file_path (str): Path to the downloaded HTML file
        
    Returns:
        list: List of dictionaries containing video URLs
    """
    videos = []
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print(f"Error: File '{html_file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Method 1: Try to find video data in JavaScript/JSON
    script_tags = soup.find_all('script')
    for script in script_tags:
        if script.string and 'ytInitialData' in script.string:
            # Extract JSON data from the script
            script_content = script.string
            
            # Find the ytInitialData object
            start_marker = 'var ytInitialData = '
            end_marker = '};'
            
            start_idx = script_content.find(start_marker)
            if start_idx != -1:
                start_idx += len(start_marker)
                end_idx = script_content.find(end_marker, start_idx)
                if end_idx != -1:
                    end_idx += 1  # Include the closing brace
                    json_str = script_content[start_idx:end_idx]
                    
                    try:
                        data = json.loads(json_str)
                        videos = extract_videos_from_json(data)
                        if videos:
                            return videos
                    except json.JSONDecodeError:
                        continue
    
    # Method 2: Fallback to HTML parsing if JSON method fails
    print("JSON extraction failed, trying HTML parsing...")
    videos = extract_videos_from_html(soup)
    
    return videos


def extract_videos_from_json(data):
    """
    Extract video URLs from YouTube's ytInitialData JSON structure.
    
    Args:
        data (dict): Parsed ytInitialData JSON
        
    Returns:
        list: List of video dictionaries
    """
    videos = []
    
    try:
        # Navigate through the YouTube data structure
        contents = data.get('contents', {})
        
        # Try different possible paths in the YouTube data structure
        possible_paths = [
            ['twoColumnBrowseResultsRenderer', 'tabs'],
            ['contents', 'twoColumnBrowseResultsRenderer', 'tabs']
        ]
        
        tabs = None
        for path in possible_paths:
            current = data
            try:
                for key in path:
                    current = current[key]
                tabs = current
                break
            except (KeyError, TypeError):
                continue
        
        if not tabs:
            return videos
        
        # Find the videos tab
        for tab in tabs:
            tab_renderer = tab.get('tabRenderer', {})
            if tab_renderer.get('title') == 'Videos':
                content = tab_renderer.get('content', {})
                section_list = content.get('sectionListRenderer', {})
                contents = section_list.get('contents', [])
                
                for content_item in contents:
                    item_section = content_item.get('itemSectionRenderer', {})
                    grid_renderer = item_section.get('contents', [{}])[0].get('gridRenderer', {})
                    items = grid_renderer.get('items', [])
                    
                    for item in items:
                        video_renderer = item.get('gridVideoRenderer', {})
                        if video_renderer:
                            video_info = extract_video_info(video_renderer)
                            if video_info:
                                videos.append(video_info)
                break
        
    except Exception as e:
        print(f"Error extracting from JSON: {e}")
    
    return videos


def extract_video_info(video_renderer):
    """
    Extract individual video URL from video renderer object.
    
    Args:
        video_renderer (dict): Video renderer object from YouTube data
        
    Returns:
        dict: Video information dictionary with url only
    """
    try:
        # Extract video ID and construct clean URL
        video_id = video_renderer.get('videoId', '')
        url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ''
        
        if url:
            return {'url': url}
        else:
            return None
            
    except Exception as e:
        print(f"Error extracting video info: {e}")
        return None


def clean_youtube_url(url):
    """
    Clean YouTube URL by removing tracking parameters and keeping only video ID.
    
    Args:
        url (str): Original YouTube URL that may contain tracking parameters
        
    Returns:
        str: Clean YouTube URL with only the video ID
    """
    if not url:
        return url
    
    # Extract video ID from URL
    video_id = video_id_from_url(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # If we can't extract video ID, try to clean manually
    if '&' in url:
        return url.split('&')[0]
    
    return url


def extract_videos_from_html(soup):
    """
    Fallback method to extract video URLs from HTML elements.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        list: List of video dictionaries
    """
    videos = []
    
    # Look for video links
    video_links = soup.find_all('a', href=re.compile(r'/watch\?v='))
    
    for link in video_links:
        try:
            # Extract URL and clean it
            href = link.get('href', '')
            if href.startswith('/'):
                url = f"https://www.youtube.com{href}"
            else:
                url = href
            
            # Clean the URL to remove tracking parameters
            url = clean_youtube_url(url)
            
            if url and video_id_from_url(url):
                videos.append({'url': url})
                
        except Exception as e:
            print(f"Error parsing video link: {e}")
            continue
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_videos = []
    for video in videos:
        if video['url'] not in seen_urls:
            seen_urls.add(video['url'])
            unique_videos.append(video)
    
    return unique_videos


def video_id_from_url(url):
    """Extract video ID from YouTube URL."""
    match = re.search(r'[?&]v=([^&]+)', url)
    return match.group(1) if match else None


def main():
    parser = argparse.ArgumentParser(description='Parse YouTube channel videos HTML file')
    parser.add_argument('html_file', help='Path to the downloaded HTML file')
    parser.add_argument('output_file', nargs='?', default='videos.json', 
                       help='Output JSON file path (default: videos.json)')
    
    args = parser.parse_args()
    
    print(f"Parsing HTML file: {args.html_file}")
    videos = parse_youtube_html(args.html_file)
    
    if not videos:
        print("No videos found or error occurred during parsing.")
        return
    
    # Create output JSON structure
    output_data = {
        "videos": videos
    }
    
    # Write to output file
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully extracted {len(videos)} videos to {args.output_file}")
        
        # Print first few videos as preview
        print("\nPreview of extracted videos:")
        for i, video in enumerate(videos[:5]):
            print(f"{i+1}. {video['url']}")
            
    except Exception as e:
        print(f"Error writing output file: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 youtube_parser.py <html_file_path> [output_file_path]")
        print("Example: python3 youtube_parser.py channel_videos.html videos.json")
        sys.exit(1)
    
    main()