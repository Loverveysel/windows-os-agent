Windows OS Agent: Vision-Based Multimodal Autonomous Agent
Windows OS Agent is an experimental autonomous agent designed to interact with the operating system using a Vision-First approach, bypassing traditional Accessibility APIs (DOM, UI Automation).

Leveraging the power of Large Language Models (LLMs) for reasoning and Computer Vision (YOLO + OCR) for grounding, this agent perceives the screen like a human and executes actions via mouse/keyboard simulation. This project explores the potential of Multimodal AI in automating legacy or non-standard interfaces (e.g., Spotify, Discord, Games).

🎯 Problem Statement & Vision
Traditional automation tools (Selenium, PyWinAuto) rely on structured data provided by the OS. However, many modern applications (Electron-based) or legacy software do not expose these structures effectively.

Windows OS Agent solves this by implementing a closed-loop cognitive cycle:

Perceive: Capture and analyze the screen using a hybrid vision parser.

Reason: Determine the next logical step using a local LLM.

Act: Execute the action physically (Human-Computer Interaction simulation).

🏗️ System Architecture
The project follows a modular architecture designed for extensibility and research:

Kod snippet'i

graph TD
User[User Prompt] --> GUI[PyQt5 Dashboard]
GUI --> Planner[Planner (Gemma 3 12b)]

    subgraph "Perception Loop"
        Screenshot[Screen Capture] --> Vision[Vision Parser]
        Vision -- "Object Detection" --> YOLO[YOLOv11n]
        Vision -- "Text Recognition" --> OCR[Tesseract / EasyOCR]
        YOLO & OCR --> SemanticData[Structured UI Elements]
    end

    Planner -- "Decision & Tool Call" --> Executor[Executor Core]
    Executor -- "Action (Click/Type)" --> OS[Windows OS]
    OS --> Screenshot
    SemanticData --> Planner

Core Components
🧠 Planner (The Brain): Powered by Gemma 3 12b (via Ollama). It handles intent understanding, step-by-step planning, and error recovery.

👁️ Vision Parser (The Eye): A hybrid module combining YOLOv11 for UI element detection (buttons, inputs) and OCR for text extraction. This reduces the hallucination rate common in pure Vision-Language Models (VLMs).

🦾 Executor (The Hand): Handles low-level OS interactions. It includes safety policies to prevent hazardous commands.

🖥️ Observer UI: A real-time PyQt5 dashboard that visualizes the agent's "Chain of Thought," current vision analysis, and execution logs.

🚀 Installation
This project requires a local LLM server.

Prerequisites
Python 3.10+

Ollama (Must be installed and running)

NVIDIA GPU with CUDA support (Recommended for real-time performance)

Setup
Clone the Repository:

Bash

git clone https://github.com/loverveysel/windows-os-agent.git
cd windows-os-agent
Create Virtual Environment:

Bash

python -m venv venv

# Windows:

venv\Scripts\activate

# Linux/Mac:

source venv/bin/activate
Install Dependencies:

Bash

pip install -r requirements.txt
Pull the LLM:

Bash

ollama pull gemma:3-12b
Run the Agent:

Bash

python main.py
🧪 Usage
Launch the application. The control panel will appear on the top-right.

Enter a natural language command (e.g., "Open Spotify and play some rock music").

Observe the agent as it captures the screen, reasons about the UI, and moves the mouse.

🚧 Research Roadmap & Current Limitations
This project is an active R&D initiative focused on overcoming the following challenges:

🔴 Inference Latency: Current local inference (Laptop GPU) averages ~10 seconds per step, limiting real-time interactivity.

Goal: Implement 4-bit Quantization and benchmark on high-end hardware (RTX 4090/5080) to reach <2s latency.

🔴 Visual Grounding Accuracy: Small UI elements can sometimes be missed by the vision parser.

Goal: Integrate Set-of-Mark (SoM) prompting techniques to improve spatial reasoning.

🔴 Long-Horizon Planning: The context window limits complex, multi-step workflows.

Goal: Implement a dynamic memory summarizer.

🤝 Contributing
Contributions are welcome! This project is intended for educational and research purposes. If you are interested in Model Optimization or Visual Prompting, feel free to open an issue or PR.

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

Developed by Alper Can Özer - Computer Engineering Senior Student
