# Tool use with Live API

Tool use allows the Live API to go beyond just conversation by enabling it to perform actions in the real world and pull in external context while maintaining a real-time connection. You can define tools such as Function calling, Code execution, and Google Search with the Live API. [1]

## Function calling

The Live API supports function calling, which lets it interact with external data and programs. You define function declarations in the session configuration. After the model sends a tool call, the client must respond with a list of `FunctionResponse` objects using the `session.send_tool_response` method. [1]

**Note:** Unlike the `generateContent` API, the Live API doesn't support automatic tool response handling. You must handle tool responses manually in your client code. [1]

```python
import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

# Simple function definitions
turn_on_the_lights = {"name": "turn_on_the_lights"}
turn_off_the_lights = {"name": "turn_off_the_lights"}

tools = [{"function_declarations": [turn_on_the_lights, turn_off_the_lights]}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "Turn on the lights please"
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)
                elif chunk.tool_call:
                    function_responses = []
                    for fc in chunk.tool_call.function_calls:
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response={
                                "result": "ok"
                            }  # simple, hard-coded function response
                        )
                        function_responses.append(function_response)
                    await session.send_tool_response(function_responses=function_responses)

if __name__ == "__main__":
    asyncio.run(main())
```

### Asynchronous Function Calling

By default, function calling is sequential. To avoid blocking the conversation, you can define functions to run asynchronously by adding a `NON_BLOCKING` behavior. [1]

```python
# Non-blocking function definition
turn_on_the_lights = {"name": "turn_on_the_lights", "behavior": "NON_BLOCKING"}
# Blocking function definition
turn_off_the_lights = {"name": "turn_off_the_lights"}
```

When you send the function response back, you must also specify a `scheduling` parameter to tell the model how to handle the result: [1]

- `INTERRUPT`: Interrupts the current model output to deliver the response.
- `WHEN_IDLE`: Delivers the response when the model is not generating output.
- `SILENT`: The model takes note of the response without delivering an immediate output.

```python
# For a non-blocking function definition, apply scheduling in the function response:
function_response = types.FunctionResponse(
    id=fc.id,
    name=fc.name,
    response={
        "result": "ok",
        "scheduling": "INTERRUPT" # Can also be WHEN_IDLE or SILENT
    }
)
```

## Code execution

You can enable the `code_execution` tool to allow the Live API to generate and run Python code in a sandboxed environment. This is useful for dynamic computations. [1]

```python
import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

tools = [{'code_execution': {}}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "Compute the largest prime palindrome under 100000."
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)
                model_turn = chunk.server_content.model_turn
                if model_turn:
                    for part in model_turn.parts:
                        if part.executable_code is not None:
                            print(part.executable_code.code)
                        if part.code_execution_result is not None:
                            print(part.code_execution_result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Grounding with Google Search

Enabling `google_search` helps increase the model's accuracy and prevent hallucinations by grounding its responses with information from Google Search. [1]

```python
import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

tools = [{'google_search': {}}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "When did the last Brazil vs. Argentina soccer match happen?"
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)
                # The model might generate and execute Python code to use Search
                model_turn = chunk.server_content.model_turn
                if model_turn:
                    for part in model_turn.parts:
                        if part.executable_code is not None:
                            print(part.executable_code.code)
                        if part.code_execution_result is not None:
                            print(part.code_execution_result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Combining multiple tools

You can combine multiple tools in a single session to enhance your application's capabilities. [1]

```python
prompt = """
Hey, I need you to do three things for me.
1. Compute the largest prime palindrome under 100000.
2. Then use Google Search to look up information about the largest earthquake in California the week of Dec 5 2024?
3. Turn on the lights
Thanks!
"""

tools = [
    {"google_search": {}},
    {"code_execution": {}},
    {"function_declarations": [turn_on_the_lights, turn_off_the_lights]},
]

config = {"response_modalities": ["TEXT"], "tools": tools}

# ... remaining model call
```
