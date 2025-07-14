import os
import json
import tempfile
import datetime
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import subprocess
import shutil
from threading import Thread
import time
import uuid

# Import your existing modules
from downloader import download_soundcloud_track
from splitter import split_audio
from recognizer import recognize_with_acr
from youtube_search import search_youtube_video

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'soundcloudset2trackids')
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active sessions
active_sessions = {}

def emit_progress(session_id, message, progress=None):
    """Emit progress updates to the client"""
    socketio.emit('progress_update', {
        'message': message,
        'progress': progress
    }, room=session_id)

def extract_tracklist_from_mix_async(soundcloud_url, chunk_duration, session_id):
    """Async version of tracklist extraction with progress updates"""
    try:
        emit_progress(session_id, "Starting extraction process...", 0)
        
        output_dir = './output'
        tracks_dir = os.path.join(output_dir, 'soundcloudtracks')
        os.makedirs(tracks_dir, exist_ok=True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            emit_progress(session_id, f"Downloading track from SoundCloud...", 10)
            download_soundcloud_track(soundcloud_url, tmpdir)
            
            files = [f for f in os.listdir(tmpdir) if f.endswith(".mp3")]
            if not files:
                raise RuntimeError("Download failed: No mp3 file found in temp directory.")
            
            tmp_track_path = os.path.join(tmpdir, files[0])
            archive_path = os.path.join(tracks_dir, files[0])
            shutil.copy2(tmp_track_path, archive_path)
            
            emit_progress(session_id, f"Track downloaded successfully. Splitting into {chunk_duration}s chunks...", 20)
            chunks = split_audio(tmp_track_path, chunk_duration=chunk_duration)
            
            emit_progress(session_id, f"Created {len(chunks)} chunks. Starting track identification...", 30)
            
            tracklist = []
            seen = set()
            total_chunks = len(chunks)
            
            for idx, chunk_path in enumerate(chunks):
                progress = 30 + (idx / total_chunks) * 50  # 30% to 80%
                emit_progress(session_id, f"Identifying chunk {idx+1}/{total_chunks}...", progress)
                
                match = recognize_with_acr(chunk_path)
                
                # Handle fatal errors on first chunk
                if idx == 0:
                    if (isinstance(match, dict) and (
                        ("error" in match and ("Access Key" in match["error"] or "Invalid" in match["error"]))
                        or ("status" in match and match["status"].get("code") in [3001, 3002, 3003])
                    )) or (isinstance(match, str) and "Access Key" in match):
                        emit_progress(session_id, f"FATAL: Credential or API error detected. {match}", 100)
                        return [{
                            "order": 1,
                            "chunk_seconds": [0, chunk_duration],
                            "artist": None,
                            "title": None,
                            "status": "fatal error",
                            "error": match
                        }]
                
                # Process match result
                if isinstance(match, dict) and match.get("error"):
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
                    tracklist.append({
                        "order": idx+1,
                        "chunk_seconds": [idx*chunk_duration, (idx+1)*chunk_duration],
                        "artist": None,
                        "title": None,
                        "status": "not found"
                    })
                elif match and (match["artist"], match["title"]) not in seen:
                    seen.add((match["artist"], match["title"]))
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
            
            emit_progress(session_id, "Merging sequential identical tracks...", 85)
            
            # Merge sequential identical tracks
            merged = []
            for entry in tracklist:
                if merged and entry["status"] == "ok" and merged[-1]["status"] == "ok" \
                    and entry["artist"] == merged[-1]["artist"] and entry["title"] == merged[-1]["title"]:
                    merged[-1]["chunk_seconds"][1] = entry["chunk_seconds"][1]
                else:
                    merged.append(entry)
            
            emit_progress(session_id, "Searching for YouTube videos...", 90)
            
            # Add YouTube links
            for track in merged:
                if track["status"] == "ok" and track["artist"] and track["title"]:
                    youtube_url = search_youtube_video(track["artist"], track["title"])
                    track["youtube_url"] = youtube_url
            
            # Save to file
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            json_path = os.path.join(output_dir, f'tracklist_{timestamp}.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
            
            emit_progress(session_id, f"Extraction complete! Found {len([t for t in merged if t['status'] == 'ok'])} tracks.", 100)
            
            # Send final results
            socketio.emit('extraction_complete', {
                'tracklist': merged,
                'file_path': json_path
            }, room=session_id)
            
    except Exception as e:
        logger.error(f"Error in extraction: {e}")
        emit_progress(session_id, f"Error occurred: {str(e)}", 100)
        socketio.emit('extraction_error', {'error': str(e)}, room=session_id)
    finally:
        # Clean up session
        if session_id in active_sessions:
            del active_sessions[session_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    data = request.json
    soundcloud_url = data.get('url')
    chunk_duration = data.get('chunk_duration', 10)
    
    if not soundcloud_url:
        return jsonify({'error': 'SoundCloud URL is required'}), 400
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        'url': soundcloud_url,
        'chunk_duration': chunk_duration,
        'started_at': datetime.datetime.now()
    }
    
    # Start extraction in background thread
    thread = Thread(target=extract_tracklist_from_mix_async, 
                   args=(soundcloud_url, chunk_duration, session_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({'session_id': session_id})

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    session_id = data['session_id']
    logger.info(f"Client {request.sid} joined session {session_id}")
    # Join the room for this session
    from flask_socketio import join_room
    join_room(session_id)

if __name__ == '__main__':
    # Create output directory
    os.makedirs('./output', exist_ok=True)
    os.makedirs('./output/soundcloudtracks', exist_ok=True)
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=True, host='0.0.0.0', port=port)