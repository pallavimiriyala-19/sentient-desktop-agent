# Functionality Deep Dive: Sentient Desktop Agent

This document provides a detailed explanation of the architecture, data flow, and design decisions behind the Sentient Desktop Agent.

## Core Concept

The Sentient Desktop Agent is built on the principle of **proactive assistance**. Unlike traditional assistants that wait for a command, this agent actively perceives the user's environment (their desktop screen), reasons about their context and potential needs, and takes action to offer help. This is achieved through a modern AI stack combining local Vision-Language Models (VLMs) for privacy and speed with powerful cloud-based LLMs for high-quality reasoning.

## Architecture & Data Flow

The agent operates in a continuous Perception-Reasoning-Action loop. Here's a breakdown of each module:

### 1. Perception Module (`ScreenAnalyzer`)

-   **Responsibility:** To capture the visual state of the user's desktop and convert it into a rich, structured textual description.
-   **Technology:**
    -   `pyautogui`: A cross-platform library used to take screenshots of the entire screen.
    -   `Pillow (PIL)`: Used to handle the image data in memory.
    -   `Ollama` with `llava`: LLaVA is a powerful open-source VLM. By running it locally via Ollama, we ensure that the user's raw screen data never leaves their machine. This is a critical design decision for user privacy and trust.
-   **Data Flow:**
    1.  `pyautogui.screenshot()` captures the screen as a PIL Image object.
    2.  The image is saved to an in-memory buffer (`io.BytesIO`).
    3.  This binary data is then base64-encoded to create a string representation suitable for the Ollama API.
    4.  A request is sent to the local Ollama server's chat endpoint, with the base64 image and a carefully crafted prompt asking the VLM to describe the scene in detail.
    5.  The VLM returns a text description, e.g., *"The user is viewing a VS Code window with Python code. There is a traceback in the terminal pane indicating a 'ZeroDivisionError' on line 5."*
    6.  This text description is the output of the perception module.

### 2. Reasoning Module (`SentientAgent.run_once`)

-   **Responsibility:** To analyze the screen description, decide if an action is required, and if so, determine which tool to use and with what arguments.
-   **Technology:**
    -   `openai`: The client library for a state-of-the-art reasoning model like GPT-4o. This model is chosen for its superior ability to understand nuanced contexts, follow complex instructions, and format its output reliably (e.g., as JSON).
-   **Data Flow:**
    1.  The text description from the `ScreenAnalyzer` is received.
    2.  A detailed system prompt is constructed. This prompt is crucial for steering the LLM's behavior. It includes:
        -   The agent's persona (a proactive assistant).
        -   The task (decide if help is needed).
        -   A list of available tools, their names, and descriptions.
        -   Strict instructions on the required JSON output format (`{"action": "tool_name", "args": {...}}` or `{"action": "none"}`).
        -   A short-term memory component (`last_action_summary`) to prevent repetitive or unhelpful actions.
    3.  An API call is made to the OpenAI Chat Completions endpoint with the system prompt and the screen description.
    4.  The LLM processes the input and returns a JSON object containing its decision.

### 3. Action Module (Tool Execution)

-   **Responsibility:** To execute the action decided upon by the Reasoning Module.
-   **Technology:**
    -   **Abstract Base Class (`Tool`):** A simple but powerful design pattern. All tools inherit from this class, ensuring they have a consistent interface (an `execute` method). This makes the system highly extensible—adding a new capability is as simple as creating a new class that inherits from `Tool`.
    -   **Concrete Tools (`WebSearchTool`, `CodeDebuggerTool`):** Each tool implements specific logic. For example, `WebSearchTool` uses the `duckduckgo-search` library, while `CodeDebuggerTool` makes another LLM call focused specifically on code analysis.
-   **Data Flow:**
    1.  The `SentientAgent` parses the JSON response from the reasoning LLM.
    2.  It checks the `action` field. If it's `"none"`, the loop concludes for this cycle.
    3.  If a tool name is specified, it looks up the corresponding tool object in its `self.tools` dictionary.
    4.  It calls the `execute` method on the selected tool, unpacking the `args` dictionary from the JSON as keyword arguments.
    5.  The tool runs its course and returns a string result.

### 4. Notification Module (`Notifier`)

-   **Responsibility:** To present the result of an action to the user in a simple, non-blocking way.
-   **Technology:**
    -   `tkinter`: Python's standard GUI toolkit, used here for its simplicity and cross-platform availability to create native-looking message boxes.
    -   `threading`: The `tkinter` main loop is blocking. To prevent the notification from freezing the entire agent, the message box is displayed in a separate daemon thread.
-   **Data Flow:**
    1.  The string result from the executed tool is passed to `notifier.show_notification()`.
    2.  The method launches a new thread.
    3.  Inside the thread, a temporary `Tk` root window is created and immediately hidden. The `messagebox.showinfo()` function is called, which displays the modal dialog. Once the user clicks "OK", the temporary root window is destroyed, and the thread terminates.

## Design Decisions

-   **Hybrid LLM Approach:** We use a local VLM for perception and a cloud LLM for reasoning. This hybrid model provides the best of both worlds: user privacy and low latency for screen analysis, combined with the immense reasoning power of a flagship model for decision-making.
-   **Stateless Loop with Short-Term Memory:** Each agent cycle is largely independent. However, to prevent the agent from repeatedly offering the same help, a `last_action_summary` is included in the reasoning prompt. This gives the LLM context about its most recent action, allowing it to make more informed decisions.
-   **JSON-forced Reasoning:** Using the `response_format={"type": "json_object"}` feature of modern LLMs ensures reliable, parsable output from the reasoning module, making the connection between reasoning and action robust.
-   **Extensible Tool Architecture:** The `Tool` abstract base class makes it trivial for developers to add new capabilities to the agent without modifying the core agent loop.