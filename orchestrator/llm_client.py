import os
import requests
import json
import re

API_URL = os.getenv("LLM_GATEWAY_URL", "https://imllm.intermesh.net/v1/chat/completions").strip()

def call_llm(api_key: str, system_prompt: str, user_prompt: str, model: str = "google/gemini-2.5-flash", tools=None) -> str:
    """
    Generic function to call the custom LLM API.
    This ensures all agents use the same gateway.
    """
    if not api_key:
        print("Error: API Key is missing. Attempting to run without LLM credentials.")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model, 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    if tools:
        payload["tools"] = tools
    
    url = API_URL
    if "/chat/completions" not in url:
        url = f"{url.rstrip('/')}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"LLM API Error {response.status_code}: {response.text[:500]}")
        response.raise_for_status()
        
        # Safely extract the content string
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        # Clean markdown formatting if present
        if content:
            content = content.replace("```json", "").replace("```", "").strip()
        return content
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return None
        
def call_llm_with_reasoning(api_key: str, system_prompt: str, user_prompt: str, model: str = "google/gemini-2.5-pro", mcat_id: str = "", cat_name: str = ""):
    """
    Non-streaming LLM call that returns both content and reasoning_content.
    Saves the full raw API response to master_agent_raw_output.txt.
    Appends the output with MCAT info to output.txt.
    Returns (content_str, reasoning_content_str).
    """
    if not api_key:
        return "", ""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model, 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    url = API_URL
    if "/chat/completions" not in url:
        url = f"{url.rstrip('/')}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # 1. Overwrite the raw JSON file for absolute latest debug (as before)
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw_path = os.path.join(base_dir, "master_agent_raw_output.txt")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 2. Append to output.txt Every Time with MCAT ID and Cat Name
        log_path = os.path.join(base_dir, "output.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"MCAT ID: {mcat_id} | Category: {cat_name}\n")
            f.write(f"TIMESTAMP: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}\n")
            f.write(f"{'='*80}\n")
            # f.write(json.dumps(data, indent=2, ensure_ascii=False)) # User said "wo output.txt mai store chaiyee"
            # I'll store the full raw JSON response here too, but appended.
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
            f.write("\n\n")

        # 3. Append to input.txt Every Time (Full Input Prompt)
        input_log_path = os.path.join(base_dir, "input.txt")
        with open(input_log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"MCAT ID: {mcat_id} | Category: {cat_name}\n")
            f.write(f"TIMESTAMP: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}\n")
            f.write(f"{'='*80}\n")
            f.write(f"--- SYSTEM PROMPT ---\n{system_prompt}\n\n")
            f.write(f"--- USER PROMPT ---\n{user_prompt}\n")
            f.write(f"{'='*80}\n\n")

        message = data.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "")
        
        message = data.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "")
        
        # Robustly extract reasoning from the first available location
        reasoning = message.get("reasoning_content")
        if not reasoning:
            provider_fields = message.get("provider_specific_fields", {})
            reasoning = provider_fields.get("reasoning_content") or provider_fields.get("reasoning")
        
        return content, (reasoning or "")

    except Exception as e:
        print(f"Error calling LLM with reasoning: {str(e)}")
        return "", ""

def stream_llm(api_key: str, system_prompt: str, user_prompt: str, model: str = "google/gemini-2.5-flash"):
    """
    Streaming version of call_llm.
    Yields text chunks as they arrive from the gateway.
    """
    if not api_key:
        yield "Error: API Key is missing."
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": True
    }

    url = API_URL
    if "/chat/completions" not in url:
        url = f"{url.rstrip('/')}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except:
                        continue
    except Exception as e:
        yield f"\n[STREAM_ERROR] {str(e)}"

def extract_json(llm_output: str) -> dict:
    if not llm_output:
        return {}
        
    def scrub_json(s: str) -> str:
        # Step 1: Replace common problematic quotes and dashes
        s = s.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
        
        # Step 2: Industrial Clean (Remove control characters and non-ASCII garbage)
        # Often LLMs spit out hidden control chars or non-UTF8 noise
        s = re.sub(r'[\x00-\x1F\x7F]', '', s) 
        
        # Step 3: Repair trailing commas in lists/objects
        s = re.sub(r",\s*([}\]])", r"\1", s)
        
        # Step 4: Brace Balancing (Recovery from Truncation)
        # If the LLM was cut off, try to add missing closing braces
        open_braces = s.count('{')
        close_braces = s.count('}')
        open_brackets = s.count('[')
        close_brackets = s.count(']')
        
        if open_braces > close_braces: s += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets: s += ']' * (open_brackets - close_brackets)
        
        return s.strip()

    # Strategy 1: The Marker Strategy (Most Precise)
    if "[JSON_PAYLOAD_START]" in llm_output:
        try:
            parts = llm_output.split("[JSON_PAYLOAD_START]")
            candidate = parts[-1].split("[JSON_PAYLOAD_END]")[0]
            if "```json" in candidate:
                candidate = candidate.split("```json")[-1].split("```")[0]
            return json.loads(scrub_json(candidate))
        except:
            pass

    # Strategy 2: Triple Backtick Strategy (Markdown blocks)
    try:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_output)
        for b in reversed(blocks):
            try:
                if b.strip(): return json.loads(scrub_json(b))
            except:
                continue
    except:
        pass

    # Strategy 3: Brute Force Brace Search (Find largest container)
    try:
        # Regex to find anything starting with { or [ and ending with } or ]
        matches = re.findall(r"([\{\[].*[\}\]])", llm_output, re.DOTALL)
        if matches:
            longest = max(matches, key=len)
            try:
                return json.loads(scrub_json(longest))
            except:
                # Fallback: find any { and just try the scrubbed rest
                idx = llm_output.find('{')
                if idx != -1:
                    try: return json.loads(scrub_json(llm_output[idx:]))
                    except: pass
    except:
        pass

    # Final Failure Mode
    return {"error": "All JSON extraction strategies failed", "raw_snippet": llm_output[-300:]}
