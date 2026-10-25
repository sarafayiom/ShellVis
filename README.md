<div align="center">

# 🐚 ShellVis: AI-Powered Seashell Identification & Valuation System

*From the beach to the lab — Snap a shell, get a full identification report in seconds.*

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-008B8B?style=for-the-badge&logo=ultralytics&logoColor=white)](https://ultralytics.com/)
[![DINOv2](https://img.shields.io/badge/Vision_Backbone-DINOv2-blue?style=for-the-badge)](https://github.com/facebookresearch/dinov2)
[![Gradio UI](https://img.shields.io/badge/UI-Gradio-FF5500?style=for-the-badge&logo=gradio&logoColor=white)](https://gradio.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[ Overview ](#overview) • [ Key Features ](#key-features) • [ System Architecture ](#system-architecture) • [ Screenshots ](#screenshots) • [ Getting Started ](#getting-started)

</div>

---

##  Overview

**ShellVis** is an advanced Computer Vision and Deep Learning web platform engineered to classify marine seashell species, isolate shell masks from natural environments, measure visual similarity against a reference dataset using deep embeddings, and estimate commercial/collector values based on curated pricing data.

Designed with a custom ocean-themed interface, ShellVis bridges the gap between field malacology and modern deep learning.

---

##  Key Features

-  **Fine-Grained Classification**: Powered by fine-tuned **YOLOv8** classification models trained to distinguish visually subtle shell taxonomies (e.g., *Dinocardium robustum*, *Euvola diegensis*, *Chlamys varia*).
-  **Automatic Background Isolation**: Integrates `rembg` (U2-Net / Session-based matting) to isolate the shell from noisy background substrates (sand, hands, fabric).
-  **Visual Embedding & KNN Matching**: Uses **DINOv2** feature embeddings (`.npy` vector representations) to retrieve the top closest reference samples from the dataset with percentage similarity scores.
-  **Automated Valuation**: Queries price dictionaries (`prices.json`) to return estimated market values based on species rarity and condition.
-  **Bilingual Interface**: Fully reactive English & Arabic interface with audio ambiance controls ("Sea Sound").

---

## 📸 Screenshots & Demonstration

<div align="center">

### 1. English Landing Page
*Clean, interactive UI allowing direct image drops or camera snapshots.*
<img src="<img width="1920" height="1080" alt="Screenshot (6067)" src="https://github.com/user-attachments/assets/e3b25548-a182-4225-82e2-564c35dcc55d" />
" width="90%" alt="ShellVis English Landing Page" />

---

### 2. Live Analysis & Processing Pipeline
*Background removal and real-time inference execution.*
<img src="<img width="1920" height="1080" alt="Screenshot (6068)" src="https://github.com/user-attachments/assets/b9c00c8e-8e7f-4467-b864-60280714f48f" />
" width="90%" alt="Processing Pipeline" />

---

### 3. Detailed Taxonomy & Valuation Report (Sample 1: *Dinocardium robustum*)
*Generated report showing confidence metrics, price estimates, mask extraction, and top 3 nearest dataset matches.*
<img src="![Uploading Screenshot (6070).png…]()
" width="90%" alt="Identification Report 1" />

---

### 4. Detailed Taxonomy & Valuation Report (Sample 2: *Euvola diegensis*)
*Handling complex shell patterns and comparing top classification candidates.*
<img src="![Uploading Screenshot (6071).png…]()
" width="90%" alt="Identification Report 2" />

</div>

---

##  Repository Structure

```tree
ShellVis/
├── seashell.py          # Main Gradio application workflow & inference pipeline
├── ocean_bg.py          # Custom CSS, HTML themes, ocean background & layout logic
```
---
Getting Started
Prerequisites
Ensure you have Python 3.10+ installed.
# Clone the repository
git clone [https://github.com/sarafayiom/ShellVis.git](https://github.com/sarafayiom/ShellVis.git)
cd ShellVis
Installation
Install PyTorch according to your compute backend (CPU or CUDA):
# For CPU execution
pip install torch torchvision --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)
Install core application dependencies:
pip install ultralytics gradio rembg opencv-python numpy pillow
Place your model weights file cls_best.pt in the project root directory.
Running the Application
Launch the local Gradio server:
python seashell.py
Open your browser and navigate to http://127.0.0.1:7860.

👤 Author
Developed with ❤️ by Sara Fayiom (@sarafayiom)

AI & Software Engineer
├── prices.json          # Taxonomy price & rarity reference database
├── .gitignore           # Git rules ignoring local model weights & datasets
└── README.md            # System documentation
