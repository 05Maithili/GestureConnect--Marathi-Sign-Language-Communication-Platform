# AI Dataset Preparation (Stage 5A)

## Overview
This document outlines the dataset preprocessing and train/validation/test split strategies employed for the BiLSTM Sign Language AI Model.

## Feature Dimensions
The `.npz` files produced by MediaPipe contain:
- `pose`: 33 landmarks x 4 coordinates (x, y, z, visibility)
- `left_hand`: 21 landmarks x 3 coordinates (x, y, z)
- `right_hand`: 21 landmarks x 3 coordinates (x, y, z)

## Preprocessing & Sequence Handling
The video samples vary in frame length (Sequence Length stats: Min 1, Max 130, Avg 64.07).
**Strategy chosen:** `Dynamic Padding + Masking`. 
Instead of modifying the normalized `.npz` files and risking temporal data loss or artificially creating bloated zero-padded files on disk, padding will be dynamically performed at the PyTorch/TensorFlow `DataLoader` stage using masking tensors. This ensures original sequence integrity is maintained.

## Label Mapping
Deterministic label indexes are mapped from `SIGN_0001` -> `0`, `SIGN_0002` -> `1`, etc. (See `label_mapping.json`).

## Split Strategy (Stage 5B)
Given there are precisely 4 samples per sign, achieving a randomized 70/15/15 global split while maintaining class distribution presents a mathematical challenge.

**Class-Aware Split Rules applied (Random Seed 42):**
1. 3 samples of each class are explicitly assigned to the **Training** set (Ensuring 100% class coverage and perfect balance for training).
2. The remaining 1 sample per class alternates between the **Validation** and **Test** sets.
3. This yields exactly **75.0% Training**, **12.5% Validation**, and **12.5% Test** distribution globally, guaranteeing no class imbalance during model training.

## Dataset Statistics
- Total valid samples: 1048
- Train count: 786
- Validation count: 131
- Test count: 131
