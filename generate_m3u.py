import os
import re
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup

# The base URL for your content
BASE_URL = "https://index.neonmartial.workers.dev/0:/Harry/"

# Headers to mimic a web browser to prevent being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
}

def get_content_list(url):
    """
    Fetches and parses the content list from the target URL.
    
    This function is now designed to handle the specific table structure of the index page.
    It finds each row, extracts the filename, and then finds the specific download link
    for that file, ignoring the "?a=view" preview links.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content_list = []

        # Find the main table containing the file list
        table = soup.find('table')
        if not table:
            print(f"!!! WARNING: No <table> found on {url}. Cannot parse content.")
            return []

        # Iterate over each row in the table body
        for row in table.find_all('tr'):
            # Find all cells in the row
            cells = row.find_all('td')
            if len(cells) < 2:  # Skip header or malformed rows
                continue

            # The first cell should contain the main link with the filename
            name_cell = cells[0]
            name_link = name_cell.find('a')
            
            if not name_link:
                continue

            # This is the filename or directory name
            name_text = name_link.text.strip()
            
            # This is the href for the directory or the preview link
            preview_href = name_link.get('href')

            # This cell should contain the download button
            action_cell = cells[1] 
            
            # Find the download link, identified by it containing a download-related SVG
            # This is the key change to get the correct link
            download_link = action_cell.find('a', href=lambda h: h and 'a=download' in h)
            
            if download_link:
                # We found a file with a download link
                file_href = download_link.get('href')
                content_list.append({'type': 'file', 'name': name_text, 'href': file_href})
            elif preview_href.endswith('/'):
                # This is a directory
                content_list.append({'type': 'dir', 'name': name_text, 'href': preview_href})

        if not content_list:
            print(f"!!! WARNING: Found a table but could not extract any files or directories from {url}.")
        else:
            print(f"Found {len(content_list)} items on {url}.")
            
        return content_list

    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR: Could not fetch {url}. Reason: {e}")
        return []

def generate_m3u():
    """Generates the M3U file content."""
    m3u_content = ["#EXTM3U"]
    
    root_content = get_content_list(BASE_URL)

    for item in root_content:
        item_type = item['type']
        item_name = item['name']
        item_href = item['href']

        # If the item is a file, treat it as a movie
        if item_type == 'file':
            movie_name = os.path.splitext(item_name)[0]
            m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{movie_name}" group-title="Movies",{movie_name}')
            absolute_url = urljoin(BASE_URL, quote(item_href))
            m3u_content.append(absolute_url)

        # If the item is a directory, treat it as a series
        elif item_type == 'dir':
            series_name = item_name.replace('/', '')
            series_url = urljoin(BASE_URL, item_href)
            
            print(f"\n--- Processing Series: {series_name} ---")
            episodes = get_content_list(series_url)
            episode_counter = 1
            for episode in episodes:
                if episode['type'] == 'file':
                    episode_name = os.path.splitext(episode['name'])[0]
                    season_episode = f"S01E{str(episode_counter).zfill(2)}"
                    full_episode_name = f"{series_name} {season_episode} - {episode_name}"
                    
                    m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{full_episode_name}" group-title="{series_name}",{full_episode_name}')
                    absolute_episode_url = urljoin(series_url, quote(episode['href']))
                    m3u_content.append(absolute_episode_url)
                    episode_counter += 1

    return "\n".join(m3u_content)

if __name__ == "__main__":
    m3u_data = generate_m3u()
    if len(m3u_data.splitlines()) <= 1:
        print("\n!!! CRITICAL: M3U file is empty. No media files were found. Check the warnings above. !!!")
    else:
        print("\n--- M3U file generated successfully. ---")
        
    with open("iptv-list.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_data)
