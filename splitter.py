from pydub import AudioSegment
import tempfile


def split_audio(input_file: str, chunk_duration=10):
    print(f"Loading audio file: {input_file} ...")
    audio = AudioSegment.from_file(input_file)
    print("Audio file loaded successfully.")
    chunks = []
    # chunk_duration is in seconds, convert to ms for slicing
    chunk_ms = chunk_duration * 1000


    duration_sec = len(audio) / 1000
    print(f"Audio duration: {duration_sec:.2f} seconds")
    print(f"Audio duration in ms: {len(audio)}")
    print(f"Chunk size in ms: {chunk_ms}")
    print(f"Expected chunks: {len(audio) // chunk_ms + 1}")

    total_chunks = (len(audio) + chunk_ms - 1) // chunk_ms
    print(f"Splitting audio into {total_chunks} chunks of {chunk_duration} seconds each...")
    for idx, i in enumerate(range(0, len(audio), chunk_ms)):
        print(f"  Processing chunk {idx+1}/{total_chunks} (ms {i} to {min(i+chunk_ms, len(audio))})...")
        chunk = audio[i:i + chunk_ms]
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        chunk.export(temp_file.name, format="mp3")
        chunks.append(temp_file.name)
    print(f"Finished splitting. {len(chunks)} chunks created.")
    return chunks


