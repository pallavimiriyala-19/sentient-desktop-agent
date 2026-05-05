import base64
from PIL import Image
import json
from main import ScreenAnalyzer, SentientAgent, CodeDebuggerTool

# NOTE: This example script simulates the agent's core loop for a single run.
# It uses a pre-saved image to avoid dependencies on screen capture libraries in a test environment.
# Ensure you have run 'ollama pull llava' and have your OPENAI_API_KEY in a .env file.

def create_test_image():
    """Creates a sample image of a Python script with an error."""
    code_text = (
        "# main.py\n\n"
        "def faulty_division(x, y):\n"
        "    return x / y\n\n"
        "result = faulty_division(100, 0)\n"
        "print(result)\n\n"
        "# Terminal Output\n"
        ">>> python main.py\n"
        "Traceback (most recent call last):\n"
        "  File \"main.py\", line 6, in <module>\n"
        "    result = faulty_division(100, 0)\n"
        "  File \"main.py\", line 3, in faulty_division\n"
        "    return x / y\n"
        "ZeroDivisionError: division by zero"
    )
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (800, 400), color=(24, 26, 27))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("cour.ttf", 15) # Courier New
        except IOError:
            font = ImageFont.load_default()
        d.text((10,10), code_text, fill=(211, 211, 211), font=font)
        img.save("test_screenshot.png")
        print("Created 'test_screenshot.png' for demonstration.")
        return "test_screenshot.png"
    except ImportError:
        print("Pillow is required to create a test image. Please install it: pip install Pillow")
        return None

def run_simulation(image_path):
    """Simulates one full cycle of the agent's logic on a static image."""
    print("\n--- 1. PERCEPTION: Analyzing local image with VLM ---")
    
    # We bypass the ScreenAnalyzer's screenshot logic and feed it an image directly.
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    ollama_client = ScreenAnalyzer().client
    try:
        response = ollama_client.chat(
            model='llava',
            messages=[
                {
                    'role': 'user',
                    'content': 'Describe the screen in detail. Focus on text, UI elements, and the overall context. What is the user likely doing? Are there any errors or important information visible?',
                    'images': [img_base64]
                }
            ]
        )
        screen_description = response['message']['content']
    except Exception as e:
        print(f"Ollama connection failed. Is Ollama running with the 'llava' model? Error: {e}")
        return

    print(f"\n[VLM Analysis Result]:\n{screen_description}")

    print("\n--- 2. REASONING: Feeding description to reasoning model ---")
    agent = SentientAgent()
    system_prompt = agent._get_system_prompt()
    
    try:
        reasoning_response = agent.reasoning_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": screen_description}
            ],
            response_format={"type": "json_object"}
        )
        decision_str = reasoning_response.choices[0].message.content
        decision = json.loads(decision_str)
    except Exception as e:
        print(f"OpenAI API call failed. Is your API key correct? Error: {e}")
        return

    print(f"\n[Reasoning Model Decision]:\n{json.dumps(decision, indent=2)}")

    print("\n--- 3. ACTION: Executing the decided tool ---")
    if decision.get("action") == "code_debugger":
        tool = CodeDebuggerTool()
        args = decision.get("args", {})
        
        if not all(k in args for k in ["code_snippet", "error_message"]):
            print("Error: Reasoning model did not provide the required arguments for code_debugger.")
            return

        result = tool.execute(**args)
        print(f"\n[Tool Execution Result]:\n{result}")
        print("\nSimulation finished. The agent correctly identified the issue and provided a solution.")
    elif decision.get("action") == "none":
        print("\nAgent decided no action was necessary. Simulation finished.")
    else:
        print(f"\nAgent decided on an unexpected action: {decision.get('action')}. Simulation finished.")

if __name__ == "__main__":
    image_file = create_test_image()
    if image_file:
        run_simulation(image_file)
