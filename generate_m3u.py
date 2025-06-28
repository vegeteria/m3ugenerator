import os
import re
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://index.neonmartial.workers.dev/0:/Harry/"

def get_links(url):
    """Fetches and parses links from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return [link.get('href') for link in soup.find_all('a')]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

def generate_m3u():
    """Generates the M3U file content."""
    m3u_content = ["#EXTM3U"]
    
    # Process movies in the root directory
    for link in get_links(BASE_URL):
        if link.endswith(('.mp4', '.mkv', '.avi', '.mov')):
            movie_name = os.path.splitext(link)[0]
            m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{movie_name}" group-title="Movies",{movie_name}')
            m3u_content.append(BASE_URL + quote(link))

    # Process series in the /series/ directory
    series_links = get_links(BASE_URL + "series/")
    for series_link in series_links:
        if series_link.endswith('/'):
            series_name = series_link.strip('/')
            episode_links = get_links(BASE_URL + "series/" + series_link)
            for episode_link in episode_links:
                if episode_link.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    episode_name = os.path.splitext(episode_link)[0]
                    # Simple S01E01, S01E02, etc. numbering for each series
                    season_episode = ""
                    numbers = re.findall(r'\d+', episode_name)
                    if len(numbers) >= 2:
                        season_episode = f"S{numbers[-2].zfill(2)}E{numbers[-1].zfill(2)}"
                    elif len(numbers) == 1:
                        season_episode = f"S01E{numbers[0].zfill(2)}"
                        
                    full_episode_name = f"{series_name} {season_episode}"
                    m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{full_episode_name}" group-title="Series",{full_episode_name}')
                    m3u_content.append(BASE_URL + "series/" + series_link + quote(episode_link))

    return "\n".join(m3u_content)

if __name__ == "__main__":
    m3u_data = generate_m3u()
    with open("iptv-list.m3u", "w") as f:
        f.write(m3u_data)
    print("M3U file generated successfully.")
