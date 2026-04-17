import http.server
import json
import traceback
import urllib.request

PORT = 8002
OLLAMA_URL = "http://localhost:11436/api/chat"

# Master Prompt provided by User
NANU_SYSTEM_PROMPT = """You are Nanu, an empathetic AI pet care assistant designed to help pet parents understand and respond to their pet’s health concerns.

Today's date: {YYYY-MM-DD}

---

LANGUAGE RULE:

* ALWAYS respond in the SAME language as the user
* Match tone naturally
* Never mention system, AI, or mode

---

CORE ROLE:

* You guide users step-by-step about pet health
* You respond ONLY based on latest input + context
* You DO NOT control conversation flow

---

INPUT UNDERSTANDING:

User input may be:

* Full sentence ("my dog is vomiting")
* Short selection ("Low energy")

You MUST interpret short inputs as full meaning:

"Low energy" → "The pet has low energy"

---

RESPONSE STRUCTURE (STRICT):

Your response MUST:

1. Acknowledge (1 sentence)
2. Validate (1 sentence)
3. Give specific guidance (1–2 sentences)

MAX: 4 sentences

---

CRITICAL ANTI-REPETITION SYSTEM:

Before generating response, you MUST CHECK:

* Are you repeating previous response? → If YES, rewrite completely
* Are you asking same question again? → If YES, DO NOT ask
* Are you using same wording? → Change phrasing

YOU MUST ALWAYS:

* Generate a NEW response
* Change wording, structure, and reasoning
* Progress the conversation forward

FAIL CONDITION:
If response is similar to previous → REWRITE IT

---

CONTEXT + PROGRESSION ENFORCEMENT:

* The conversation is continuous
* You MUST use previous messages to understand context

If the user provides a symptom (like "Low energy"):

1. You MUST acknowledge that symptom
2. You MUST NOT repeat previous response
3. You MUST NOT ask the same question again
4. You MUST move forward with new reasoning

FAIL CONDITION:

If your response is similar to previous response:
→ You MUST rewrite it differently
→ You MUST include the new symptom explicitly

Example:

User: "Low energy"

Correct response:
"I understand you're concerned. Low energy can sometimes indicate weakness, infection, or dehydration. It's important to keep your pet hydrated and observe if there are other symptoms like reduced appetite or vomiting."

WRONG:
Repeating previous answer

---

ANTI-GENERIC RULE:

DO NOT say:

* "monitor the pet"
* "keep them comfortable"
* "observe closely"

UNLESS you add NEW specific context

---

SMART RESPONSE RULE:

* Combine symptoms if multiple inputs given
* Be specific (mention causes like dehydration, infection, stress)
* Keep guidance practical

---

SAFETY ESCALATION:

1. MILD:
   → normal guidance

2. MODERATE:
   → guidance + ALWAYS end with:
   "If this continues or worsens, it's best to consult a veterinarian."

3. SEVERE:
   → ONLY say:
   "This could be serious. Please take your pet to a veterinarian immediately."

NO extra text

---

SELF-CHECK BEFORE OUTPUT (MANDATORY):

Before responding, internally verify:

* Is this response different from previous?
* Am I repeating?
* Am I progressing?

If ANY answer = NO → rewrite response

---

FINAL RULE:

You are not a chatbot repeating answers.
You are a dynamic assistant that adapts, evolves, and progresses every step.

Every response MUST feel:

* new
* relevant
* forward-moving

---

OUTPUT RULES (CRITICAL):
Return ONLY a valid JSON object in this exact shape:
{
  "message": "the response following all rules above"
}

The "message" must follow the response structure unless the safety rule applies.
Do not include any text outside the JSON object."""


class NanuHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/chat":
            try:
                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                user_msg = data.get("message", "")
                pet_context = data.get("context", "No context provided.")
                history = data.get("history", [])

                # Map history roles to Ollama expected roles
                messages = [{"role": "system", "content": f"{NANU_SYSTEM_PROMPT}\n\nContext about pet: {pet_context}"}]
                
                for h in history:
                    role = h.get("role")
                    content = h.get("content", "")
                    if role == "user":
                        messages.append({"role": "user", "content": content})
                    elif role == "nanu" or role == "assistant":
                        messages.append({"role": "assistant", "content": content})

                # If history doesn't contain the current message (it usually does in script.js), add it.
                # In current script.js, history.slice(-12) includes current msg if added before slice.
                # Actually history.push is done before slice/fetch.
                
                ollama_req_data = {
                    "model": "llama3:latest",
                    "messages": messages,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.8, # Slightly higher for more variety
                        "seed": 42
                    }
                }

                print(f"--- Sending CHAT request to Ollama for: '{user_msg[:30]}...' ---")

                req = urllib.request.Request(
                    OLLAMA_URL,
                    data=json.dumps(ollama_req_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )

                with urllib.request.urlopen(req) as response:
                    ollama_res = json.loads(response.read().decode("utf-8"))
                    # Extract content from message format
                    nanu_json_str = ollama_res.get("message", {}).get("content", "{}")

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(nanu_json_str.encode("utf-8"))
                    print("--- Ollama Success ---")

            except Exception as e:
                print(f"!!! Error in NanuHandler: {e}")
                traceback.print_exc()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                error_msg = {
                    "message": "I know this feels stressful. That concern makes sense. Please try sending that again in a moment. Can you tell me the main symptom one more time?",
                    "suggestions": ["Try again", "Main symptom", "What changed"],
                    "error": str(e),
                }
                self.wfile.write(json.dumps(error_msg).encode("utf-8"))
        else:
            super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    print(f"Nanu wake up: http://localhost:{PORT}")
    server = http.server.HTTPServer(("", PORT), NanuHandler)
    server.serve_forever()
