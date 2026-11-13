import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

key = os.getenv("XAI_API_KEY")

print("Key loaded:", bool(key))

client = OpenAI(
    api_key=key,
    base_url="https://api.x.ai/v1"
)

response = client.responses.create(
    model="grok-4.6",
    input="Reply with only: WORKING"
)

print(response.output_text)