# Text generation with the Gemini API

The Gemini API can generate text from a variety of inputs, including text, images, video, and audio. [1]

## Basic Text Generation

Here's a basic example that takes a single text input and generates a response. [1]

```python
from google import genai
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?"
)

print(response.text)
```

## Thinking with Gemini 2.5

By default, the 2.5 Flash and Pro models have "thinking" enabled to improve quality. This can sometimes lead to longer response times and higher token usage. You can disable this feature by setting the `thinking_budget` to zero. [1]

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
    ),
)
print(response.text)
```

## System Instructions and Other Configurations

You can use system instructions to guide the behavior of the Gemini models. You can also override default generation parameters like temperature. [1]

### System Instructions

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a cat. Your name is Neko."),
    contents="Hello there"
)
print(response.text)
```

### Generation Configuration

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["Explain how AI works"],
    config=types.GenerateContentConfig(
        temperature=0.1
    )
)
print(response.text)
```

## Multimodal Inputs

The Gemini API supports multimodal inputs, allowing you to combine text with other media files, like images. [1]

```python
from PIL import Image
from google import genai

client = genai.Client()
image = Image.open("/path/to/organ.png")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, "Tell me about this instrument"]
)

print(response.text)
```

## Streaming Responses

For a more fluid interaction, you can use streaming to receive parts of the response as they are generated, rather than waiting for the entire response to be completed. [1]

```python
from google import genai

client = genai.Client()

response = client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents=["Explain how AI works"]
)

for chunk in response:
    print(chunk.text, end="")
```

## Multi-turn Conversations (Chat)

The SDKs provide a chat functionality to manage conversation history. This makes it easy to have multi-turn conversations with the model. [1]

### Basic Chat

```python
from google import genai

client = genai.Client()
chat = client.chats.create(model="gemini-2.5-flash")

response = chat.send_message("I have 2 dogs in my house.")
print(response.text)

response = chat.send_message("How many paws are in my house?")
print(response.text)

for message in chat.get_history():
    print(f'role - {message.role}',end=": ")
    print(message.parts.text)
```

### Streaming Chat

You can also use streaming with the chat functionality. [1]

````python
from google import genai

client = genai.Client()
chat = client.chats.create(model="gemini-2.5-flash")

response = chat.send_message_stream("I have 2 dogs in my house.")
for chunk in response:
    print(chunk.text, end="")

response = chat.send_message_stream("How many paws are in my house?")
for chunk in response:
    print(chunk.text, end="")

for message in chat.get_history():
    print(f'role - {message.role}', end=": ")
    print(message.parts.text)```



# Function calling with the Gemini API

Function calling lets you connect models to external tools and APIs. [1] Instead of generating text responses, the model determines when to call specific functions and provides the necessary parameters to execute real-world actions. [1] This allows the model to act as a bridge between natural language and real-world actions and data. [1]

Function calling has 3 primary use cases: [1]
*   **Augment Knowledge:** Access information from external sources like databases, APIs, and knowledge bases. [1]
*   **Extend Capabilities:** Use external tools to perform computations and extend the limitations of the model, such as using a calculator or creating charts. [1]
*   **Take Actions:** Interact with external systems using APIs, such as scheduling appointments, creating invoices, sending emails, or controlling smart home devices. [1]

## How function calling works

Function calling involves a structured interaction between your application, the model, and external functions. Here's a breakdown of the process: [1]

1.  **Define Function Declaration:** Define the function declaration in your application code. Function Declarations describe the function's name, parameters, and purpose to the model. [1]
2.  **Call LLM with function declarations:** Send a user prompt along with the function declaration(s) to the model. It analyzes the request and determines if a function call would be helpful. If so, it responds with a structured JSON object. [1]
3.  **Execute Function Code (Your Responsibility):** The Model does not execute the function itself. It's your application's responsibility to process the response and check for a Function Call. [1] If there is one, you extract the name and arguments of the function and execute the corresponding function in your application. [1] If not, the model has provided a direct text response to the prompt. [1]
4.  **Create User friendly response:** If a function was executed, capture the result and send it back to the model in a subsequent turn of the conversation. [1] It will use the result to generate a final, user-friendly response that incorporates the information from the function call. [1]

This process can be repeated over multiple turns, allowing for complex interactions and workflows. [1] The model also supports calling multiple functions in a single turn (parallel function calling) and in sequence (compositional function calling). [1]

### Step 1: Define a function declaration

Define a function and its declaration within your application code that allows users to set light values and make an API request. [1] This function could call external services or APIs. [1]

```python
# Define a function that the model can call to control smart lights
set_light_values_declaration = {
    "name": "set_light_values",
    "description": "Sets the brightness and color temperature of a light.",
    "parameters": {
        "type": "object",
        "properties": {
            "brightness": {
                "type": "integer",
                "description": "Light level from 0 to 100. Zero is off and 100 is full brightness",
            },
            "color_temp": {
                "type": "string",
                "enum": ["daylight", "cool", "warm"],
                "description": "Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.",
            },
        },
        "required": ["brightness", "color_temp"],
    },
}

# This is the actual function that would be called based on the model's suggestion
def set_light_values(brightness: int, color_temp: str) -> dict[str, int | str]:
    """Set the brightness and color temperature of a room light. (mock API).

    Args:
        brightness: Light level from 0 to 100. Zero is off and 100 is full brightness
        color_temp: Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.

    Returns:
        A dictionary containing the set brightness and color temperature.
    """
    return {"brightness": brightness, "colorTemperature": color_temp}
````

### Step 2: Call the model with function declarations

Once you have defined your function declarations, you can prompt the model to use them. [1] It analyzes the prompt and function declarations and decides whether to respond directly or to call a function. [1] If a function is called, the response object will contain a function call suggestion. [1]

```python
from google.genai import types

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[set_light_values_declaration])
config = types.GenerateContentConfig(tools=[tools])

# Define user prompt
contents = [
    types.Content(
        role="user",
        parts=[types.Part(text="Turn the lights down to a romantic level")]
    )
]

# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=config,
)

print(response.candidates.content.parts.function_call)
```

The model then returns a `functionCall` object in an OpenAPI compatible schema specifying how to call one or more of the declared functions in order to respond to the user's question. [1]

### Step 3: Execute set_light_values function code

Extract the function call details from the model's response, parse the arguments, and execute the `set_light_values` function. [1]

```python
# Extract tool call details, it may not be in the first part.
tool_call = response.candidates.content.parts.function_call

if tool_call.name == "set_light_values":
    result = set_light_values(**tool_call.args)
    print(f"Function execution result: {result}")
```

### Step 4: Create user friendly response with function result and call the model again

Finally, send the result of the function execution back to the model so it can incorporate this information into its final response to the user. [1]

```python
# Create a function response part
function_response_part = types.Part.from_function_response(
    name=tool_call.name,
    response={"result": result},
)

# Append function call and result of the function execution to contents
contents.append(response.candidates.content)  # Append the content from the model's response.
contents.append(types.Content(role="user", parts=[function_response_part]))  # Append the function response

final_response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=config,
    contents=contents,
)

print(final_response.text)
```

This completes the function calling flow. [1] The model successfully used the `set_light_values` function to perform the requested action of the user. [1]
