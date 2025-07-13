import argparse
from downloader import download_soundcloud_track
from splitter import split_audio
from recognizer import recognize_with_acr
import os
import tempfile
import datetime

"""
python main.py -st "https://soundcloud.com/your-track-url" -cd 8
"""

def extract_tracklist_from_mix(soundcloud_url, chunk_duration=10):
    import shutil
    output_dir = './output'
    tracks_dir = os.path.join(output_dir, 'soundcloudtracks')
    os.makedirs(tracks_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Downloading track to temporary folder {tmpdir}...")
        download_soundcloud_track(soundcloud_url, tmpdir)
        files = [f for f in os.listdir(tmpdir) if f.endswith(".mp3")]
        if not files:
            raise RuntimeError("Download failed: No mp3 file found in temp directory.")
        tmp_track_path = os.path.join(tmpdir, files[0])
        # Copy to output/soundcloudtracks for archival
        archive_path = os.path.join(tracks_dir, files[0])
        shutil.copy2(tmp_track_path, archive_path)
        print(f"Copied downloaded track to {archive_path}")
        # Process from temp file
        print(f"Splitting into {chunk_duration}s chunks...")
        chunks = split_audio(tmp_track_path, chunk_duration=chunk_duration)
        print(f'Length of chunks: {len(chunks)}')
        print(f"Identifying tracks...")
        tracklist = []
        seen = set()
        total_chunks = len(chunks)
        for idx, chunk_path in enumerate(chunks):
            print(f"Identifying chunk {idx+1}/{total_chunks}...", end='\r')
            match = recognize_with_acr(chunk_path)
            if idx == 0:
                if (isinstance(match, dict) and (
                    ("error" in match and ("Access Key" in match["error"] or "Invalid" in match["error"]))
                    or ("status" in match and match["status"].get("code") in [3001, 3002, 3003])
                )) or (isinstance(match, str) and "Access Key" in match):
                    print("\nFATAL: Credential or API error detected in first chunk. Stopping script.")
                    print(f"Details: {match}")
                    return [{
                        "order": 1,
                        "chunk_seconds": [0, chunk_duration],
                        "artist": None,
                        "title": None,
                        "status": "fatal error",
                        "error": match
                    }]
            if isinstance(match, dict) and match.get("error"):
                print(f"Error: {match['error']} for chunk {chunk_path}")
                tracklist.append({
                    "order": idx+1,
                    "chunk_seconds": [idx*chunk_duration, (idx+1)*chunk_duration],
                    "artist": None,
                    "title": None,
                    "status": "error",
                    "error": match["error"],
                    "file": match["file"]
                })
            elif match == "not found":
                print(f"No track found for chunk {chunk_path}")
                tracklist.append({
                    "order": idx+1,
                    "chunk_seconds": [idx*chunk_duration, (idx+1)*chunk_duration],
                    "artist": None,
                    "title": None,
                    "status": "not found"
                })
            elif match and (match["artist"], match["title"]) not in seen:
                seen.add((match["artist"], match["title"]))
                print(f"Identified: {match['artist']} - {match['title']}")
                tracklist.append({
                    "order": idx+1,
                    "chunk_seconds": [idx*chunk_duration, (idx+1)*chunk_duration],
                    "artist": match["artist"],
                    "title": match["title"],
                    "status": "ok"
                })
            else:
                tracklist.append({
                    "order": idx+1,
                    "chunk_seconds": [idx*chunk_duration, (idx+1)*chunk_duration],
                    "artist": None,
                    "title": None,
                    "status": "duplicate or unknown"
                })
        print()  # To move to the next line after the last progress print
        return tracklist


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-st", "--soundcloud_track", required=True, help="SoundCloud track URL")
    parser.add_argument("-cd", "--chunk_duration", type=int, default=10, help="Chunk duration in seconds (default: 10)")
    args = parser.parse_args()

    def extract_and_merge(soundcloud_url, chunk_duration):
        raw_tracklist = extract_tracklist_from_mix(soundcloud_url, chunk_duration)
        # Merge sequential identical tracks
        merged = []
        for entry in raw_tracklist:
            if merged and entry["status"] == "ok" and merged[-1]["status"] == "ok" \
                and entry["artist"] == merged[-1]["artist"] and entry["title"] == merged[-1]["title"]:
                # Extend the chunk window
                merged[-1]["chunk_seconds"][1] = entry["chunk_seconds"][1]
            else:
                merged.append(entry)
        return merged

    print(f"\nProcessing {args.soundcloud_track} with chunk duration {args.chunk_duration}s...")
    tracklist = extract_and_merge(args.soundcloud_track, args.chunk_duration)
    print("\nFinal Tracklist:")
    import json
    print(json.dumps(tracklist, indent=2, ensure_ascii=False))

    # Save to timestamped JSON file in output folder
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = os.path.join(output_dir, f'tracklist_{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(tracklist, f, indent=2, ensure_ascii=False)
    print(f'\nTracklist saved to {json_path}')
