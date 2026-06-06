# Technical Specification: AutoArrow ML Engine (v1.0.0)

## Objective
To develop a machine-learning based content generation engine that produces high-quality, fitness-optimized rhythm game stepfiles (arrows) for long-form (60+ minute) audio tracks, specifically targeting Psytrance marathons.

## 1. Data Acquisition & Preprocessing
- **Training Data:** A curated dataset of expert-charted .sm or .ssc files (StepManiaX, DDR, PIU).
- **Audio Processing:**
  - Spectral Analysis for onset detection.
  - Librosa-based beat tracking and BPM estimation.
  - Multi-band energy analysis to identify "Drops," "Build-ups," and "Breakdowns."

## 2. Model Architecture
- **Input:** 2D Spectrogram + Pulse/Beat timing vectors.
- **Backbone:** CNN (Convolutional Neural Network) for feature extraction.
- **Sequence Modeling:** Bidirectional LSTM or Transformer with self-attention to maintain long-term coherence across marathon sets.
- **Output:** Multi-label classification (Arrow positions: Up, Down, Left, Right) + Regression (Timing offset).

## 3. Fitness-Specific Constraints (The "Metabolic" Layer)
- **Pattern Density Scaling:** Dynamically adjusting steps per second (SPS) to match target Metabolic Equivalent of Task (MET) zones.
- **Leg-Flow Optimization:** Post-processing rules to ensure "flow state"—limiting sudden lateral shifts or excessive "double-steps" that break cardio rhythm.
- **Safety Heuristics:** Enforcing a minimum "cool-down" pattern density every 15-20 minutes.

## 4. Prototype Requirements
- **Language:** Python 3.x
- **Frameworks:** PyTorch or TensorFlow, Librosa, NumPy.
- **Output Format:** .ssc (StepManiaX compatible) with metadata for workout intensity.

## 5. Phase 1 Goals (ML Prototype)
- Generate a 15-minute "Medium" difficulty chart for a single Psytrance track with >90% beat alignment accuracy.
- Implement a "Note Density" slider to manually influence the ML's output during generation.
