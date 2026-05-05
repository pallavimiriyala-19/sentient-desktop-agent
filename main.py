import ollama
import openai
from dotenv import load_dotenv
import os
import time
import base64
from io import BytesIO
from PIL import Image
import pyautogui
from abc import ABC, abstractmethod
import json
import tkinter as tk
from tkinter import messagebox
from duckduckgo_search import DDGS
import threading

# Load environment variables
load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REASONING_MODEL = "gpt-4o"
VISION_MODEL = "llava"
AGENT_LOOP_DELAY_SECONDS = 15

# --- Tool Definitions ---
class Tool(ABC):
    """Abstract base class for a tool."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, **kwargs):
        pass

class WebSearchTool(Tool):
    """Tool for performing web searches."""
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Searches the web for information on a given query."
        )

    def execute(self, query: str):
        print(f"Executing web search for: {query}")
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=3)]
            return json.dumps(results)
        except Exception as e:
            return f"Error during web search: {e}"

class CodeDebuggerTool(Tool):
    """Tool for debugging code snippets."""
    def __init__(self):
        super().__init__(
            name="code_debugger",
            description="Analyzes a code snippet and its error to provide a fix or explanation."
        )
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def execute(self, code_snippet: str, error_message: str):
        print(f"Executing code debugger for error: {error_message}")
        try:
            prompt = f"I have a Python code snippet that produced an error. Please explain the error and suggest a fix.\n\nCode:\n```python\n{code_snippet}\n```\n\nError:\n```\n{error_message}\n```"
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during code debugging: {e}"

# --- Core Modules ---
class ScreenAnalyzer:
    """Captures and analyzes the screen using a local VLM."""
    def __init__(self, model=VISION_MODEL):
        self.model = model
        self.client = ollama.Client()

    def analyze(self) -> str:
        print("Capturing screen...")
        try:
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            print("Analyzing screen with VLM...")
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': 'Describe the screen in detail. Focus on text, UI elements, and the overall context. What is the user likely doing? Are there any errors or important information visible?',
                        'images': [img_base64]
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Error analyzing screen: {e}")
            return f"Error: Could not analyze screen. {e}"

class Notifier:
    """Handles desktop notifications in a separate thread."""
    def show_notification(self, title, message):
        def _show():
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(title, message)
            root.destroy()
        
        # Run tkinter in a separate thread to avoid blocking the main agent loop
        threading.Thread(target=_show, daemon=True).start()


# --- The Main Agent ---
class SentientAgent:
    """The main agent class orchestrating the perception, reasoning, and action loop."""
    def __init__(self):
        self.screen_analyzer = ScreenAnalyzer()
        self.reasoning_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.notifier = Notifier()
        self.tools = {
            "web_search": WebSearchTool(),
            "code_debugger": CodeDebuggerTool()
        }
        self.last_action_summary = "None"

    def _get_system_prompt(self):
        tool_definitions = "\n".join(
            f'- {name}: {tool.description}' for name, tool in self.tools.items()
        )
        return f"""You are a proactive AI desktop assistant. Your goal is to help the user by observing their screen and taking initiative.

You will be given a description of the user's screen. Your task is to determine if the user might need help.

If you think the user could use assistance, you must respond with a JSON object specifying a tool to use. If no action is needed, respond with {{"action": "none"}}.

Available tools:
{tool_definitions}

The JSON format must be:
{{"action": "tool_name", "args": {{"arg1": "value1", ...}}}}

Example for code debugging:
{{"action": "code_debugger", "args": {{"code_snippet": "a=10\nb=0\nprint(a/b)", "error_message": "ZeroDivisionError: division by zero"}}}}

Example for web search:
{{"action": "web_search", "args": {{"query": "latest AI research papers"}}}}

Based on the screen description, decide if an action is warranted. Do not be overly intrusive. Only act if there is a clear opportunity to help (e.g., an error message, a complex topic, a clear question being typed). The user is a software developer.

Summary of last action taken: {self.last_action_summary}"""

    def run_once(self):
        screen_description = self.screen_analyzer.analyze()
        print(f"\n--- Screen Analysis ---\n{screen_description}\n-----------------------")

        system_prompt = self._get_system_prompt()
        
        print("Reasoning about the next action...")
        try:
            response = self.reasoning_client.chat.completions.create(
                model=REASONING_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": screen_description}
                ],
                response_format={"type": "json_object"}
            )
            decision_str = response.choices[0].message.content
            decision = json.loads(decision_str)
            print(f"Agent Decision: {decision}")

            if decision.get("action") and decision["action"] != "none":
                tool_name = decision["action"]
                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    args = decision.get("args", {})
                    result = tool.execute(**args)
                    
                    self.last_action_summary = f"Used {tool_name} with args {args}. Result: {result[:100]}..."
                    
                    print(f"--- Tool Result ---\n{result}\n-------------------")
                    self.notifier.show_notification(
                        f"Assistant Suggestion ({tool_name})",
                        result
                    )
                else:
                    self.last_action_summary = f"Attempted to use unknown tool: {tool_name}"
                    print(f"Error: Unknown tool '{tool_name}'")
            else:
                self.last_action_summary = "No action was taken."
                print("No action needed.")

        except Exception as e:
            self.last_action_summary = f"An error occurred during the reasoning step: {e}"
            print(f"Error during reasoning or execution: {e}")

    def run(self):
        if not OPENAI_API_KEY:
            print("FATAL: OPENAI_API_KEY not found in .env file.")
            return
        print("Sentient Desktop Agent is now running...")
        while True:
            self.run_once()
            print(f"\nSleeping for {AGENT_LOOP_DELAY_SECONDS} seconds...")
            time.sleep(AGENT_LOOP_DELAY_SECONDS)

if __name__ == "__main__":
    agent = SentientAgent()
    agent.run()
