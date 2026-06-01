import librosa
import numpy as np
import sys
import os

def analyze_track(file_path):
    print(f"--- AutoArrow ML Engine: Onset Analysis Prototype ---")
    print(f"Analyzing: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    # 1. Load the audio file
    print("Loading audio...")
    y, sr = librosa.load(file_path)

    # 2. Beat Tracking
    print("Extracting tempo and beat frames...")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    # Handle cases where tempo is returned as an array
    if isinstance(tempo, np.ndarray):
        tempo = tempo[0]
    print(f"Detected Tempo: {tempo:.2f} BPM")

    # 3. Onset Strength
    print("Calculating onset strength...")
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    times = librosa.times_like(onset_env, sr=sr)

    # 4. Detect Onsets (Arrow Candidate Timings)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    onset_times = librosa.frames_to_time(onsets, sr=sr)

    print(f"Total Onsets Detected: {len(onsets)}")
    print(f"First 5 onset timings (s): {onset_times[:5]}")

    # 5. Summary
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"Track Duration: {duration:.2f} seconds")
    print(f"Average Density: {len(onsets)/duration:.2f} notes per second")
    print("--- Analysis Complete ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python autoarrow_proto.py <path_to_audio_file>")
    else:
        analyze_track(sys.argv[1])
