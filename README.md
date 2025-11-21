# 👁️ Windows OS Agent: Vision-Based Autonomous System

Windows OS Agent is an experimental autonomous system that uses **local LLM reasoning** and **screen-based visual perception** to control Windows applications as if a human were operating the machine.  
Unlike traditional automation tools, it does not rely on API endpoints, DOM access, or accessibility trees.

---

## 📑 Table of Contents

- [Features](#-features)
- [Current Vision Pipeline](#-current-vision-pipeline)
- [Planned Vision Parser (YOLO Integration)](#-planned-vision-parser-yolo-integration)
- [Architecture](#-architecture)
- [Compatibility & Requirements](#-compatibility--requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## ✨ Features

### **Vision-First Agent Core**

The agent operates by _seeing_ the screen, interpreting what is visible, and acting accordingly.

### **Local LLM Reasoning**

Powered by **Gemma 3 (12B)** via **Ollama**.  
All reasoning, planning, and action selection is performed locally.

### **Image-Based Decision Making (Current Implementation)**

- The agent captures a **full-screen screenshot**.
- This screenshot is embedded into the LLM request as:

```json
"images": ["<base64-encoded-screenshot>"]
```

## - The model analyzes the raw image (like a human) and decides:

- where to click

- what to type

- how to proceed in an automation task> **Status:** This is the _current and only_ active perception pipeline.

### **Realtime UI Observation**

## PyQt5 interface shows:

- the agent’s reasoning

- performed actions

## 📸 Current Vision Pipeline

## At the moment, **there is no active YOLO or OCR parsing**.The LLM receives the **entire screenshot**, and the agent works as:1) Capture screenshot

2. Encode to Base64

3. Send inside the LLM message as an `images` field

4. LLM infers UI elements directly from raw pixels

5. LLM outputs a JSON action (e.g., click coordinates)This approach works but is **less accurate** and highly dependent on LLM vision capabilities.

## 🧠 Planned Vision Parser (YOLO Integration)

## The Vision Parser is designed but **not implemented yet**.

## Planned Workflow

Currently, the model receives the full screenshot via Ollama's message interface and makes decisions based on that image.

YOLOv11 integration is under development. The planned workflow is as follows:

1. Screenshot is sent through YOLOv11.
2. YOLO detects UI elements on the screen and assigns each a unique numeric ID:
   - Buttons
   - Icons
   - Input fields
   - Common Windows UI elements
   - Custom app interfaces
3. OCR can optionally extract readable text from the screenshot.
4. YOLO overlays detected objects with their IDs on the screenshot.
5. The LLM receives the screenshot (with IDs) instead of raw pixels. When the LLM needs to interact with a UI element, it references the object's ID.
6. Using the ID, the executor can retrieve the exact coordinates from YOLO's output to perform actions precisely.

Example structured JSON for reference:

```json
{
  "objects": [
    { "id": 1, "label": "button", "bbox": [x1, y1, x2, y2] },
    { "id": 2, "label": "textbox", "bbox": [x1, y1, x2, y2] }
  ],
  "texts": [
    { "text": "Username", "bbox": [x1, y1, x2, y2] }
  ]
}
```

---

### Benefits:

## - 95%+ detection accuracy

- deterministic element targeting

- stable automation

- less hallucination

- consistent across resolutions

## 🏗️ Architecture

### Perceive → Reason → Act Loop

    graph LR
        A[User Request] --> B(Planner / LLM)
        B --> C{Vision Layer}
        C -->|Current: Raw Screenshot| B
        C -->|Future: YOLO + OCR JSON| B
        B -->|Decision| D[Executor]
        D -->|Mouse/Keyboard| E[Windows OS]
        E -->|Feedback Screenshot| C

---

### Components

#### **Planner**

## - Interprets user intent

- Uses past steps

- Chooses next high-level command

#### **Vision Parser**

## - **Current:** No parsing — the LLM sees the raw screenshot

- **Future:** YOLO + OCR + object IDs + structured UI map

#### **Executor**

## Uses:

- pywinauto

- pyautogui

- send2trash

## ⚠️ Compatibility & Requirements

### OS

## - Windows 10 / 11 (64-bit)

### Hardware

## - NVIDIA GPU ≥ 8GB VRAM recommended

- 16GB RAM minimum

- CPU-only works, but slower

### Software

## - Python 3.10+

- Ollama (Gemma 3 12B)

- Tesseract OCR (only needed in the future pipeline)

- YOLO model (future vision parser)

## 🚀 Installation

### 1. Clone Repository

```bash

    git clone https://github.com/loverveysel/windows-os-agent.git
    cd windows-os-agent
```

---

### 2. Create Virtual Environment

```bash
    python -m venv venv
    venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
 pip install -r requirements.txt
```

### 4. Pull the LLM Model

```bash
ollama pull gemma3:12b\*\*\*
```

## 🎮 Usage

### Start the Agent

```bash
python mainwindow.py
```

### Example Requests

## - “Open Notepad and write ‘Hello World’.”

## - “Open Chrome, search GitHub, and click the first result.”The LLM interprets the screenshot and determines the appropriate UI coordinates.

## ⚙️ Configuration

    configs/agent.yaml

## - LLM parameters

- temperature

- model selection

- SYSTEM

## 🗺️ Roadmap

## - [ ] **Integrate YOLOv11 Vision Parser**

- [ ] **Generate numbered object maps**

- [ ] **LLM → object_id → bounding box system**

- [ ] **Memory Summarization**

- [ ] **4-bit quantization for 2s-per-step latency**

- [ ] **Linux Support\*\*\***

## 📜 License

# MIT License. See `LICENSE`.**Developer:** Alper Can Özer
