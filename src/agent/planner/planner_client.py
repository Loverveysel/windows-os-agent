from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import re
import pyautogui
import ollama  # Lütfen 'pip install ollama' ile kütüphaneyi yükleyin.

class PlannerClient:
    """
    Lightweight planner client skeleton that talks to an LLM (e.g. Ollama).
    Responsibilities:
      - load two system prompts (ReAct / Summarizer)
      - maintain a history list of dict entries
      - get the next single-step from the planner LLM
      - add executor/tool responses to history
      - ask the summarizer LLM to reduce history into a short memory and replace history
    """
    
    def __init__(self, react_prompt_path: str, summarizer_prompt_path: str) -> None:
        self.react_prompt = self._load_prompt(react_prompt_path)
        self.summarizer_prompt = self._load_prompt(summarizer_prompt_path)
        self._history: List[Dict[str, Any]] = []  # list of dicts: {'role':..., 'content':...}
        self.model = "windows-agent:gemma"

    def _load_prompt(self, path: str) -> str:
        p = Path(path)
        return p.read_text(encoding="utf-8") if p.exists() else ""
    
    def screen_capture(self):
        pyautogui.screenshot('screenshot.png')
        

    def _serialize_history_for_messages(self) -> List[Dict[str, str]]:
        """
        Convert internal history entries into a list of messages suitable for LLM input.
        Each entry becomes {'role': <role>, 'content': <string>}. Dict-like contents are JSON-dumped.
        """
        msgs: List[Dict[str, str]] = []
        for e in self._history:
            role = e.get("role", "user")
            content = e.get("content", "")
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            else:
                content = str(content)
            msgs.append({"role": role, "content": content})
        return msgs

    def _call_ollama(self, system_prompt: str, messages: List[Dict[str, str]], images = False) -> str:
        """
        Call Ollama chat endpoint and return raw assistant text.

        Expects 'ollama' python package to be installed. Uses:
          ollama.chat(model='llama3', messages=messages)

        The 'messages' argument should be a list of {"role": "...", "content": "..."} dicts.
        This function is robust about ensuring the system prompt is included and about
        extracting the assistant text from common response shapes.

        Raises RuntimeError on failure.
        """

        # Ensure messages is a list and include system prompt if not present
        msgs = list(messages or [])
        if not msgs or msgs[0].get("role") != "system":
            # Prepend system prompt to be explicit
            msgs = [{"role": "system", "content": system_prompt}] + msgs
        
        if images is True:
            msgs.append({"role": "user", "content": "Here is the current screen image.", "images": ["D:\\Software\\Python\\windows-os-agent\\screenshot.png"]})

        try:
            # Call Ollama. The exact signature/return shape may vary by version; handle common shapes below.
            resp = ollama.chat(model=self.model , messages=msgs, format="json")  
        except Exception as e:
            raise RuntimeError("ollama.chat call failed", e) from e

        # Extract assistant text from response
        assistant_text = None

        # Common expected shape: {'message': {'content': '...'}}
        assistant_text = resp.get("message", {}).get("content")

        print("assistant_text:", assistant_text)
        if assistant_text is None:
            raise RuntimeError(f"unable to extract assistant text from ollama response: {repr(resp)}")

        # Normalize to string
        return str(assistant_text)

    def _extract_json_block(self, text: str) -> str:
        """
        Robustly extract the first JSON object/array from a noisy assistant text.
        Strategy:
          1. Look for fenced ```json ... ``` or ``` ... ``` blocks first.
          2. Otherwise scan for the first '{' or '[' and perform a JSON-aware brace/quote-balanced extraction.
        Returns the JSON substring or raises ValueError if none found.
        """
        if not text:
            raise ValueError("empty assistant text")

        # 1) Try fenced code blocks
        for m in re.finditer(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL):
            json_block = m.group(1)
            # Validate that this is a standalone JSON block, not part of a larger text
            if re.match(r"^\s*(\{.*\}|\[.*\])\s*$", json_block, re.DOTALL):
                return json_block

        # 2) Scan for first '{' or '[' and extract a brace/quote-balanced substring
        stack = []
        start_idx = -1
        for i, char in enumerate(text):
            if char in "{[":
                if not stack:
                    start_idx = i  # potential start of JSON block
                stack.append(char)
            elif char in "}]" and stack:
                stack.pop()
                # If the stack is empty, we found a complete JSON structure
                if not stack:
                    return text[start_idx : i + 1]

        raise ValueError("no valid JSON block found in assistant text")

    def get_next_step(self, user_input: Optional[str] = None) -> Dict:
        """
        Send current history + optional user_input to the ReAct planner prompt,
        expect a single JSON object (tool_call OR final_response). Append assistant result to history
        and return the parsed JSON as a dict.
        """
        if user_input:
            self._history.append({"role": "user", "content": user_input})

        messages = self._serialize_history_for_messages()
        # Prepend system prompt as a message for the LLM
        system_message = {"role": "system", "content": self.react_prompt}
        full_messages = [system_message] + messages

        self.screen_capture()
        assistant_text = self._call_ollama(self.react_prompt, full_messages, True)
        # Expect assistant_text to be a single JSON object string per protocol
        try:
            parsed = json.loads(self._extract_json_block(assistant_text))
        except Exception as exc:
            # Keep a short failure entry in history and re-raise for the integrator to handle
            self._history.append({"role": "assistant", "content": {"status": "error", "error": f"invalid-json: {str(exc)}"}})
            raise

        # Validate that the parsed JSON is either a tool_call or a final_response
        if not isinstance(parsed, dict) or ("tool_call" not in parsed and "final_response" not in parsed):
            self._history.append({"role": "assistant", "content": {"status": "error", "error": "invalid-response", "note": "missing tool_call and final_response"}})
            raise ValueError("LLM'in yanıtı ne tool_call ne de final_response içeriyor.")

        # Store assistant response (the tool_call or final_response) in history
        self._history.append({"role": "assistant", "content": parsed})
        return parsed

    def add_tool_response(self, result_json: Dict) -> None:
        """
        Add executor/tool result (e.g. {"status":"success", ...} or {"status":"error", ...})
        to history so the planner can observe it on the next get_next_step call.
        """
        self._history.append({"role": "tool", "content": result_json})

    def summarize_and_clear_history(self) -> None:
        """
        Send full history + summarizer prompt to the Summarizer LLM, receive a short summary string,
        clear history and store only the summary as the single memory entry so next get_next_step sees it.
        """
        messages = self._serialize_history_for_messages()
        system_message = {"role": "system", "content": self.summarizer_prompt}
        full_messages = [system_message] + messages

        summary_text = self._call_ollama(self.summarizer_prompt, full_messages, False)
        # Ensure we keep only short memory (string). Do not preserve raw logs.
        self._history.clear()
        self._history.append({"role": "memory", "content": summary_text})
        return None
    
    def _call_gemini(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """
        Gemini API'sini (Google) çağırır ve ham JSON metnini döndürür.
        Zorunlu JSON modu ve DOĞRU 'parts' formatını kullanır.
        """
        try:
            import google.generativeai as genai
            import os
            import json
        except ImportError:
            raise RuntimeError("Lütfen 'pip install google.generativeai' ile kütüphaneyi yükleyin.")

        try:
            api_key = "AIzaSyDxXJfNUDzP_zDYAk2zpWLIkg2-VVr8VoU"
            genai.configure(api_key=api_key)
        except KeyError:
            raise RuntimeError("GOOGLE_API_KEY ortam değişkeni ayarlanmamış.")

        # 1. Gemini'nin zorunlu JSON modunu ayarla
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        
        # 2. Modeli başlat (Flash hızlı ve ucuzdur, Pro daha akıllıdır)
        model = genai.GenerativeModel(
            'gemini-2.5-flash', # Veya 'gemini-1.5-pro-latest'
            system_instruction=system_prompt,
            generation_config=generation_config
        )

        # 3. MESAJLARI DÖNÜŞTÜR (HATA DÜZELTMESİ BURADA)
        # Bizim format: [{'role': 'user', 'content': '...'}]
        # Gemini format: [{'role': 'user', 'parts': [{'text': '...'}]}]
        gemini_history = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "") # 'content' şu anda 'str' VEYA 'dict' olabilir

            if role == "assistant":
                role = "model"
            elif role == "tool":
                role = "user"
            
            elif role == "system":
                role = "user"  # Gemini'de sistem mesajları 'user' rolü olarak işlenir
            elif role == "memory":
                role = "user"  # Bellek mesajları da 'user' rolü olarak işlenir

            # --- DÜZELTME BURADA ---
            # 'content' eğer bir sözlük (dict) ise (örn: tool_call veya status)
            # Gemini API'sine göndermeden önce onu JSON string'ine dönüştür.
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            # --- DÜZELTME SONU ---

            gemini_history.append({'role': role, 'parts': [{'text': content_str}]}) # 'content' yerine 'content_str' kullan

        try:
            # 4. API'yi Çağır
            # 'generate_content', 'contents' parametresi olarak List[Content] bekler
            response = model.generate_content(gemini_history)
            
            # 5. Ham JSON metnini döndür
            print("Gemini yanıtı:", response.text)
            return response.text
        except Exception as e:
            # (örn: Kimlik doğrulama hatası, API hatası vb.)
            raise RuntimeError(f"Gemini API çağrısı başarısız oldu: {e}")

    # _call_ollama fonksiyonunu sil ve
    # get_next_step / summarize_and_clear_history içindeki
    # `self._call_ollama` çağrılarını `self._call_gemini` olarak değiştir.