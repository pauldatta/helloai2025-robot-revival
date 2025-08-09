# Structured output

You can configure Gemini for structured output instead of unstructured text, allowing precise extraction and standardization of information for further processing. [1] For example, you can use structured output to extract information from resumes, standardize them to build a structured database. [1]

Gemini can generate either JSON or enum values as structured output. [1]

## Generating JSON

There are two ways to generate JSON using the Gemini API: [1]

- Configure a schema on the model
- Provide a schema in a text prompt

Configuring a schema on the model is the recommended way to generate JSON, because it constrains the model to output JSON. [1]

### Configuring a schema (recommended)

To constrain the model to generate JSON, configure a `responseSchema`. [1] The model will then respond to any prompt with JSON-formatted output. [1]

```python
from google import genai
from pydantic import BaseModel

class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="List a few popular cookie recipes, and include the amounts of ingredients.",
    config={
        "response_mime_type": "application/json",
        "response_schema": list[Recipe],
    },
)

# Use the response as a JSON string.
print(response.text)

# Use instantiated objects.
my_recipes: list[Recipe] = response.parsed
```

**Note:** Pydantic validators are not yet supported. [1] If a `pydantic.ValidationError` occurs, it is suppressed, and `.parsed` may be empty/null. [1]

### Providing a schema in a text prompt

Instead of configuring a schema, you can supply a schema as natural language or pseudo-code in a text prompt. [1] This method is not recommended, because it might produce lower quality output, and because the model is not constrained to follow the schema. [1]

**Warning:** Don't provide a schema in a text prompt if you're configuring a `responseSchema`. [1] This can produce unexpected or low quality results. [1]

Here's a generic example of a schema provided in a text prompt: [1]

```
List a few popular cookie recipes, and include the amounts of ingredients.
Produce JSON matching this specification:
Recipe = {
"recipeName": string,
"ingredients": array<string>
}
Return: array<Recipe>
```

Since the model gets the schema from text in the prompt, you might have some flexibility in how you represent the schema. [1] But when you supply a schema inline like this, the model is not actually constrained to return JSON. [1] For a more deterministic, higher quality response, configure a schema on the model, and don't duplicate the schema in the text prompt. [1]

## Generating enum values

In some cases you might want the model to choose a single option from a list of options. [1] To implement this behavior, you can pass an enum in your schema. [1] You can use an enum option anywhere you could use a string in the `responseSchema`, because an enum is an array of strings. [1] Like a JSON schema, an enum lets you constrain model output to meet the requirements of your application. [1]

For example, assume that you're developing an application to classify musical instruments into one of five categories: "Percussion", "String", "Woodwind", "Brass", or " "Keyboard"". [1] You could create an enum to help with this task. [1]

In the following example, you pass an enum as the `responseSchema`, constraining the model to choose the most appropriate option. [1]

```python
from google import genai
import enum

class Instrument(enum.Enum):
    PERCUSSION = "Percussion"
    STRING = "String"
    WOODWIND = "Woodwind"
    BRASS = "Brass"
    KEYBOARD = "Keyboard"

client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What type of instrument is an oboe?',
    config={
        'response_mime_type': 'text/x.enum',
        'response_schema': Instrument,
    },
)

print(response.text) # Woodwind
```

The Python library will translate the type declarations for the API. [1] However, the API accepts a subset of the OpenAPI 3.0 schema (Schema). [1]

There are two other ways to specify an enumeration. [1] You can use a `Literal`: [1]

```python
from typing import Literal

Literal["Percussion", "String", "Woodwind", "Brass", "Keyboard"]
```

And you can also pass the schema as JSON: [1]

```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What type of instrument is an oboe?',
    config={
        'response_mime_type': 'text/x.enum',
        'response_schema': {
            "type": "STRING",
            "enum": ["Percussion", "String", "Woodwind", "Brass", "Keyboard"],
        },
    },
)

print(response.text) # Woodwind
```

Beyond basic multiple choice problems, you can use an enum anywhere in a JSON schema. [1] For example, you could ask the model for a list of recipe titles and use a `Grade` enum to give each title a popularity grade: [1]

```python
from google import genai
import enum
from pydantic import BaseModel

class Grade(enum.Enum):
    A_PLUS = "a+"
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    F = "f"

class Recipe(BaseModel):
    recipe_name: str
    rating: Grade

client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='List 10 home-baked cookie recipes and give them grades based on tastiness.',
    config={
        'response_mime_type': 'application/json',
        'response_schema': list[Recipe],
    },
)

print(response.text)
```
