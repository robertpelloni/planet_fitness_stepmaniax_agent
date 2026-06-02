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
    difficulty = sys.argv[2] if len(sys.argv) > 2 else "Medium"
    intensity = float(sys.argv[3]) if len(sys.argv) > 3 else None

    generate_ssc(output_ssc, tempo, onset_times, difficulty=difficulty, intensity=intensity)

    print("--- Analysis Complete ---")

def generate_ssc(output_path, bpm, onset_times, difficulty="Medium", intensity=None):
    # Difficulty Calibration
    diff_settings = {
        "Beginner": {"meter": 2, "intensity": 0.3, "quantize": 4},
        "Easy": {"meter": 4, "intensity": 0.5, "quantize": 8},
        "Medium": {"meter": 6, "intensity": 0.7, "quantize": 16},
        "Hard": {"meter": 9, "intensity": 0.9, "quantize": 16},
        "Challenge": {"meter": 12, "intensity": 1.1, "quantize": 16}
    }

    settings = diff_settings.get(difficulty, diff_settings["Medium"])
    if intensity is None:
        intensity = settings["intensity"]

    print(f"Generating Quantized .ssc file | Difficulty: {difficulty} | Intensity: {intensity} | Target: {output_path}")

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
        f"#DESCRIPTION:ML Quantized {difficulty} Endurance Set;",
        "#CHARTSTYLE:;",
        f"#DIFFICULTY:{difficulty};",
        f"#METER:{settings['meter']};",
        "#RADARVALUES:0,0,0,0,0;",
        "#CREDIT:AutoArrow;",
        "#NOTES:"
    ]

    # Quantization Engine: Snap based on difficulty settings
    if bpm <= 0:
        bpm = 120.0 # Default fallback
    beat_duration = 60.0 / bpm
    sixteenth_duration = beat_duration / 4.0
    quantize_res = settings["quantize"] # 4, 8, or 16
    steps_per_sixteenth = 16 // quantize_res

    total_duration = max(onset_times) if len(onset_times) > 0 else 0
    total_sixteenths = int(total_duration / sixteenth_duration) + 16

    # Grid of notes (0000 = no note)
    grid = ["0000"] * total_sixteenths

    # Map onsets to grid with Pattern Generation, Metabolic Pacing & Fatigue Curve
    arrows = ["1000", "0100", "0010", "0001"] # Up, Down, Left, Right
    last_grid_idx = -1

    # Track used arrows for pattern variety
    pattern_history = []

    for t in onset_times:
        # Fatigue Curve: Intensity drops gradually over long-form session
        fatigue_modifier = max(0.6, 1.0 - (t / 18000.0))
        current_intensity = intensity * fatigue_modifier

        # Stochastic metabolic pacing
        if np.random.random() > current_intensity:
            continue

        # Standardize to sixteenth grid index
        grid_idx = int(round(t / sixteenth_duration))

        # Apply difficulty-based quantization snapping
        grid_idx = (grid_idx // steps_per_sixteenth) * steps_per_sixteenth

        if grid_idx < len(grid) and grid_idx > last_grid_idx:
            # Pattern Generation Logic (v7.6.0)

            # 1. Base selection: weighted random or cyclic
            choice_idx = np.random.choice([0, 1, 2, 3], p=[0.25, 0.25, 0.25, 0.25])
            note = arrows[choice_idx]

            # 2. Higher difficulty: Jumps (two arrows at once)
            if difficulty in ["Hard", "Challenge"] and np.random.random() < (current_intensity * 0.3):
                # Pick a second distinct arrow
                second_idx = (choice_idx + np.random.randint(1, 4)) % 4
                note_list = ["0"] * 4
                note_list[choice_idx] = "1"
                note_list[second_idx] = "1"
                note = "".join(note_list)

            # 3. Simple Flow constraint: avoid three of same arrow in row
            if len(pattern_history) >= 2 and pattern_history[-1] == note and pattern_history[-2] == note:
                 # Force change
                 choice_idx = (choice_idx + 1) % 4
                 note = arrows[choice_idx]

            grid[grid_idx] = note

            # Leg-Safety & Flow Validator (v7.7.0)
            if len(pattern_history) > 0:
                # Rule 1: No rapid double-steps on the same arrow (exhaustion prevention)
                if note == pattern_history[-1] and (grid_idx - last_grid_idx) < 4:
                    # Shift note to avoid rapid repeat
                    note_list = list(note)
                    idx = note_list.index("1") if "1" in note_list else 0
                    note_list[idx] = "0"
                    note_list[(idx + 1) % 4] = "1"
                    note = "".join(note_list)
                    grid[grid_idx] = note

            pattern_history.append(note)
            last_grid_idx = grid_idx

    # Construct measures from grid
    notes_block = []
    for i in range(0, len(grid), 16):
        measure = grid[i:i+16]
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
        print("Usage: python autoarrow_proto.py <audio_file> [difficulty] [intensity_override]")
        print("Difficulties: Beginner, Easy, Medium, Hard, Challenge")
    else:
        analyze_track(sys.argv[1])
