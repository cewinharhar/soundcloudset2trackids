import subprocess
import os

def download_soundcloud_track(url: str, output_path: str):
    """
    Downloads a single track or playlist from SoundCloud using scdl.

    Args:
        url (str): The SoundCloud track/playlist URL.
        output_path (str): The directory where the file(s) will be saved.
    """
    # Ensure output path exists
    os.makedirs(output_path, exist_ok=True)

    try:
        subprocess.run([
            "scdl",
            "-l", url,
            "--path", output_path,
            "--onlymp3",
            "--no-playlist-folder",
            "--overwrite",
            "--addtofile"
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to download SoundCloud track: {e}")