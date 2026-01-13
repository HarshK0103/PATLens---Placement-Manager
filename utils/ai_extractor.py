import requests
import json

def ai_extract_offer(email):
    """
    Uses local Ollama LLM to extract fields from campus placement email.
    Returns a dict with keys:
    ["company", "category", "branches", "10th%", "12th%", "cgpa", "ctc", "stipend", "last_date", "registration_links"]
    """
    prompt = f"""
Extract all key details (best-effort) from the below campus placement offer announcement email.
If a field is missing, leave it blank.
Return a pure JSON object with these keys: company, category, branches, 10th%, 12th%, cgpa, ctc, stipend, last_date, registration_links (as a list).
DO NOT add explanations or markdown, just JSON.
---
Subject: {email["subject"]}
Body: {email["body"]}
---
"""
    api_url = "http://localhost:11434/api/generate"
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(api_url, json=payload)
    # Ollama returns streamed tokens, but in single reply if stream=False
    try:
        result = response.json()
        output = result['response']
        start = output.find('{')
        end = output.rfind('}')+1
        extracted = json.loads(output[start:end])
        return extracted
    except Exception as e:
        print("AI extract parse error:", e)
        print("Raw:", output)
        return None