import os
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup

# The base URL for your content
BASE_URL = "https://index.neonmartial.workers.dev/0:/Harry/"

# Headers to mimic a web browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
}

# Supported video file extensions
VIDEO_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv']

def get_content_list(url):
    """
    Fetches the page and extracts a list of files and directories
    based on the link's visible text, not its href attribute.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content_list = []

        for link in soup.find_all('a'):
            link_text = link.text.strip()
            link_href = link.get('href')

            if not link_href or not link_text or link_text == '../':
                continue

            # Case 1: The link is a directory
            if link_href.endswith('/') and link_text.endswith('/'):
                content_list.append({'type': 'dir', 'name': link_text, 'href': link_href})
            
            # Case 2: The link text is a video file name
            elif any(link_text.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                # We use the TEXT as the href, because the actual href is '?a=view'
                content_list.append({'type': 'file', 'name': link_text, 'href': link_text})

        if not content_list:
            print(f"!!! WARNING: Could not extract any valid files or directories from {url}.")
        else:
            print(f"Found {len(content_list)} items on {url}.")
            
        return content_list

    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR: Could not fetch {url}. Reason: {e}")
        return []

def generate_m3u():
    """Generates the M3U file content from the extracted list."""
    m3u_content = ["#EXTM3U"]
    
    root_content = get_content_list(BASE_URL)

    for item in root_content:
        item_type = item['type']
        item_name = item['name']
        item_href = item['href']

        # If the item is a file, treat it as a movie
        if item_type == 'file':
            # Use the filename (without extension) as the movie title
            movie_title = os.path.splitext(item_name)[0]
            m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{movie_title}" group-title="Movies",{movie_title}')
            # IMPORTANT: Build the URL from the filename (item_href)
            absolute_url = urljoin(BASE_URL, quote(item_href))
            m3u_content.append(absolute_url)

        # If the item is a directory, treat it as a series
        elif item_type == 'dir':
            series_name = item_name.strip('/')
            series_url = urljoin(BASE_URL, item_href)
            
            print(f"\n--- Processing Series: {series_name} ---")
            episodes = get_content_list(series_url)
            episode_counter = 1
            for episode in episodes:
                if episode['type'] == 'file':
                    episode_title = os.path.splitext(episode['name'])[0]
                    season_episode = f"S01E{str(episode_counter).zfill(2)}"
                    full_episode_name = f"{series_name} {season_episode} - {episode_title}"
                    
                    m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{full_episode_name}" group-title="{series_name}",{full_episode_name}')
                    # IMPORTANT: Build the URL from the filename (episode['href'])
                    absolute_episode_url = urljoin(series_url, quote(episode['href']))
                    m3u_content.append(absolute_episode_url)
                    episode_counter += 1

    return "\n".join(m3u_content)

if __name__ == "__main__":
    m3u_data = generate_m3u()
    if len(m3u_data.splitlines()) <= 1:
        print("\n!!! CRITICAL: M3U file is empty. Check the warnings above. !!!")
    else:
        print("\n--- M3U file generated successfully. ---")
        
    with open("iptv-list.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_data)
