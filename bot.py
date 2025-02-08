import os
import yt_dlp
import shutil
import json

# Configurazione
CONFIG_FILE = "config.json"

def load_config():
    default_config = {
        "create_zip": True,
        "allow_single_video": True,
        "allow_playlist": True
    }
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get_youtube_playlist_videos(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(playlist_url, download=False)
            if 'entries' in result:
                return [entry['url'] for entry in result['entries'] if 'url' in entry]
        except Exception as e:
            print(f"Errore nel recupero della playlist: {e}")
        return []

def download_mp3(youtube_url, output_folder="downloads"):
    os.makedirs(output_folder, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([youtube_url])
        except Exception as e:
            print(f"Errore nel download del video {youtube_url}: {e}")

def create_zip(output_folder="downloads", zip_name="downloads.zip"):
    try:
        shutil.make_archive(zip_name.replace(".zip", ""), 'zip', output_folder)
        print(f"✅ Cartella compressa in {zip_name}")
    except Exception as e:
        print(f"Errore nella creazione dello ZIP: {e}")

def main():
    config = load_config()
    
    print("""
    ====================================
         🔥 Smokytek MP3 Downloader 🔥
    ====================================
    """)
    
    url = input("Inserisci l'URL del video o della playlist YouTube: ")
    
    if "playlist" in url and config["allow_playlist"]:
        video_urls = get_youtube_playlist_videos(url)
    elif config["allow_single_video"]:
        video_urls = [url]
    else:
        print("❌ Il download di questo contenuto non è consentito dalle impostazioni.")
        return
    
    if not video_urls:
        print("❌ Nessun video trovato.")
        return
    
    for video_url in video_urls:
        print(f"Scaricamento in corso: {video_url}...")
        download_mp3(video_url)
    
    if config["create_zip"]:
        create_zip()
    
    print("✅ Conversione completata!")

if __name__ == "__main__":
    main()
