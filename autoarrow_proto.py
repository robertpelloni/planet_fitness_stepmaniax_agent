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

    # 6. Generate Basic .ssc File
    output_ssc = file_path.rsplit('.', 1)[0] + ".ssc"
    generate_ssc(output_ssc, tempo, onset_times)

    print("--- Analysis Complete ---")

def generate_ssc(output_path, bpm, onset_times):
    print(f"Generating .ssc file: {output_path}")

    # Header
    ssc_content = [
        "#VERSION:0.81;",
        "#TITLE:AutoArrow ML Marathon;",
        "#ARTIST:AutoArrow Engine;",
        "#MUSIC:marathon_set.mp3;",
        f"#OFFSET:0.000;",
        f"#BPMS:0.000={bpm:.3f};",
        "#STOPS:;",
        "#SAMPLESTART:0.000;",
        "#SAMPLELENGTH:10.000;",
        "",
        "//---------------Dance - Single----------------",
        "#NOTEDATA:;",
        "#CHARTNAME:Marathon Cardio;",
        "#STEPSTYPE:dance-single;",
        "#DESCRIPTION:ML Generated Endurance Set;",
        "#CHARTSTYLE:;",
        "#DIFFICULTY:Medium;",
        "#METER:5;",
        "#RADARVALUES:0,0,0,0,0;",
        "#CREDIT:AutoArrow;",
        "#NOTES:"
    ]

    # Basic Pattern Mapping (Simplified for Prototype)
    # Mapping onsets to 4ths/8ths based on proximity to beats
    notes_block = []
    current_beat = 0
    beat_duration = 60.0 / bpm

    # For prototype, we'll just output one measure per second with a simple pattern
    for i in range(int(max(onset_times)) + 1):
        # measure (4 lines = 4 beats)
        notes_block.append("1000") # Up
        notes_block.append("0100") # Down
        notes_block.append("0010") # Left
        notes_block.append("0001") # Right
        notes_block.append(",")

    ssc_content.extend(notes_block)
    ssc_content.append(";")

    with open(output_path, 'w') as f:
        f.write("\n".join(ssc_content))
    print(f"Success: {output_path} written.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python autoarrow_proto.py <path_to_audio_file>")
    else:
        analyze_track(sys.argv[1])
