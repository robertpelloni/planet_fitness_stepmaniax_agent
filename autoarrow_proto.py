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
    intensity = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    generate_ssc(output_ssc, tempo, onset_times, intensity=intensity)

    print("--- Analysis Complete ---")

def generate_ssc(output_path, bpm, onset_times, intensity=1.0):
    print(f"Generating Quantized .ssc file (Intensity: {intensity}): {output_path}")

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
        "#DESCRIPTION:ML Quantized Endurance Set;",
        "#CHARTSTYLE:;",
        "#DIFFICULTY:Medium;",
        "#METER:5;",
        "#RADARVALUES:0,0,0,0,0;",
        "#CREDIT:AutoArrow;",
        "#NOTES:"
    ]

    # Quantization Engine: Snap to 16th notes
    # 1 measure = 4 beats = 16 sixteenths
    beat_duration = 60.0 / bpm
    sixteenth_duration = beat_duration / 4.0

    total_duration = max(onset_times) if len(onset_times) > 0 else 0
    total_sixteenths = int(total_duration / sixteenth_duration) + 16

    # Grid of notes (0000 = no note)
    grid = ["0000"] * total_sixteenths

    # Map onsets to grid with Metabolic Pacing & Fatigue Curve
    arrows = ["1000", "0100", "0010", "0001"] # Up, Down, Left, Right
    last_grid_idx = -1

    for t in onset_times:
        # Fatigue Curve: Intensity drops by 5% every 15 minutes (900 seconds)
        fatigue_modifier = max(0.5, 1.0 - (t / 18000.0)) # Gradual drop over 5 hours
        current_intensity = intensity * fatigue_modifier

        # Stochastic metabolic pacing: skip notes based on intensity
        if np.random.random() > current_intensity:
            continue

        grid_idx = int(round(t / sixteenth_duration))
        if grid_idx < len(grid) and grid_idx > last_grid_idx:
            # Basic pattern: cycle through arrows
            grid[grid_idx] = arrows[grid_idx % 4]
            last_grid_idx = grid_idx

    # Construct measures from grid
    notes_block = []
    for i in range(0, len(grid), 16):
        measure = grid[i:i+16]
        # Pad short last measure
        if len(measure) < 16:
            measure += ["0000"] * (16 - len(measure))
        notes_block.extend(measure)
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
