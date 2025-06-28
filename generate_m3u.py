import os
import re
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup

# The new base URL for your content
BASE_URL = "https://index.neonmartial.workers.dev/0:/Harry/"

def get_links_and_names(url):
    """
    Fetches and parses links from a given URL.
    Returns a list of tuples (href, text).
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            text = link.text.strip()
            if href and text and href != '../':
                links.append((href, text))
        return links
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

def generate_m3u():
    """Generates the M3U file content."""
    m3u_content = ["#EXTM3U"]
    
    links_at_root = get_links_and_names(BASE_URL)

    for href, text in links_at_root:
        # Check for video files to be treated as movies
        if any(href.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov']):
            movie_name = os.path.splitext(text)[0]
            m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{movie_name}" group-title="Movies",{movie_name}')
            # urljoin handles combining the base URL and the relative link
            absolute_url = urljoin(BASE_URL, quote(href))
            m3u_content.append(absolute_url)

        # Check for subdirectories to be treated as series
        elif href.endswith('/'):
            series_name = text.replace('/', '')
            series_url = urljoin(BASE_URL, href)
            
            # Get episodes from the series subdirectory
            episode_links = get_links_and_names(series_url)
            episode_counter = 1
            for episode_href, episode_text in episode_links:
                if any(episode_href.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov']):
                    # Use the file name as the episode name
                    episode_name = os.path.splitext(episode_text)[0]
                    season_episode = f"S01E{str(episode_counter).zfill(2)}"
                    
                    full_episode_name = f"{series_name} {season_episode} - {episode_name}"
                    group_title = f"{series_name}" # Group by series name
                    
                    m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{full_episode_name}" group-title="{group_title}",{full_episode_name}')
                    absolute_episode_url = urljoin(series_url, quote(episode_href))
                    m3u_content.append(absolute_episode_url)
                    episode_counter += 1

    return "\n".join(m3u_content)

if __name__ == "__main__":
    m3u_data = generate_m3u()
    with open("iptv-list.m3u", "w") as f:
        f.write(m3u_data)
    print("M3U file generated successfully for the new URL.")
