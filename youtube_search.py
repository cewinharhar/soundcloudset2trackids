import requests
import urllib.parse
import re
import logging

logger = logging.getLogger(__name__)

def search_youtube_video(artist, title, max_retries=3):
    """
    Search for a YouTube video given artist and title.
    Returns the YouTube URL if found, None otherwise.
    """
    if not artist or not title:
        return None
    
    # Clean and format search query
    query = f"{artist} {title}".strip()
    
    for attempt in range(max_retries):
        try:
            # Use YouTube search without API key (scraping approach)
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Extract video ID from HTML
            # Look for watch?v= pattern in the HTML
            video_id_pattern = r'"videoId":"([^"]+)"'
            matches = re.findall(video_id_pattern, response.text)
            
            if matches:
                video_id = matches[0]
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Found YouTube video for {artist} - {title}: {youtube_url}")
                return youtube_url
            
            # Fallback: look for /watch?v= pattern
            watch_pattern = r'/watch\?v=([^&"]+)'
            matches = re.findall(watch_pattern, response.text)
            
            if matches:
                video_id = matches[0]
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Found YouTube video (fallback) for {artist} - {title}: {youtube_url}")
                return youtube_url
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {artist} - {title}: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)  # Wait before retry
            continue
        except Exception as e:
            logger.error(f"Unexpected error searching for {artist} - {title}: {e}")
            break
    
    logger.warning(f"Could not find YouTube video for {artist} - {title}")
    return None

def search_youtube_video_with_api(artist, title, api_key):
    """
    Alternative method using YouTube Data API v3 (requires API key).
    Uncomment and use this if you have a YouTube API key.
    """
    if not artist or not title or not api_key:
        return None
    
    try:
        query = f"{artist} {title}".strip()
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 1,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('items'):
            video_id = data['items'][0]['id']['videoId']
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Found YouTube video (API) for {artist} - {title}: {youtube_url}")
            return youtube_url
        
    except Exception as e:
        logger.error(f"Error searching YouTube API for {artist} - {title}: {e}")
    
    return None