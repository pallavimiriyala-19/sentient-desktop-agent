# Sentient Desktop Agent

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Status](https://img.shields.io/badge/status-trending-brightgreen.svg)

An AI agent that proactively assists you by understanding your screen context using Vision-Language Models (VLMs) and automates tasks. It watches what you're doing and offers help when you need it most.

## ✨ Features

-   **🧠 Proactive Assistance:** Anticipates your needs without explicit commands.
-   **👁️ Visual Context-Awareness:** Uses local VLMs (like LLaVA) to understand on-screen content (text, images, UI).
-   **🛠️ Extensible Toolset:** Easily add new tools for web search, code debugging, summarization, and more.
-   **🔒 Privacy-First:** Screen analysis is performed locally; only anonymized text descriptions are sent to the reasoning model.
-   **🤖 Hybrid AI Model:** Combines the speed and privacy of local VLMs with the power of state-of-the-art reasoning LLMs (e.g., GPT-4o, Claude 3.5 Sonnet).

## 🏛️ Architecture

The agent operates in a continuous loop, following a Perception-Reasoning-Action cycle.

```mermaid
graph TD
    A[🖥️ Screen Capture] --> B{👁️ VLM Perception Module};
    B -- Screen Description --> C{🧠 Reasoning Module (LLM)};
    C -- Decides Action --> D[🛠️ Action Module];
    D -- Selects & Executes Tool --> E[🔧 Tool (e.g., Web Search)];
    E -- Result --> F[💡 User Notification];
    F --> A; % Loop back
```

1.  **Perception:** Captures a screenshot and uses a local Vision-Language Model (VLM) to generate a detailed text description of the on-screen content.
2.  **Reasoning:** The text description is fed to a powerful Large Language Model (LLM) which decides if the user might need help. If so, it formulates a plan and chooses a tool.
3.  **Action:** The chosen tool is executed with the arguments provided by the reasoning LLM.
4.  **Notification:** The result is presented to the user through a non-intrusive desktop notification.

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/sentient-desktop-agent.git
    cd sentient-desktop-agent
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up local VLM with Ollama:**
    -   Install [Ollama](https://ollama.ai/).
    -   Pull the LLaVA model:
        ```bash
        ollama pull llava
        ```

4.  **Configure API Keys:**
    -   Create a `.env` file in the root directory.
    -   Add your API key for the reasoning model:
        ```
        OPENAI_API_KEY="your_openai_api_key_here"
        ```

## 💻 Usage

Run the main agent script from your terminal:

```bash
python main.py
```

The agent will now run in the background, analyzing your screen every 15 seconds. 

**To test it:**
Open a text editor and paste the following Python code, which contains an obvious error:

```python
def calculate_ratio(a, b):
    # This function has a potential error
    return a / b

result = calculate_ratio(10, 0)
print(result)
```

Within a few cycles, the agent should detect the `ZeroDivisionError` context and pop up a notification with a debugging suggestion.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
