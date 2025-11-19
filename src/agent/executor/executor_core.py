# executor/executor_core.py
import os
import subprocess
import traceback
from typing import Dict, Any
import pywinauto  # Hata yakalama için import gerekli
import send2trash   # Hata yakalama için import gerekli

# Kendi modüllerimiz
from . import tools

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ..security.policy import is_path_safe, ALLOWED_BASE_PATH

#
# --- ARAÇ YÖNLENDİRME HARİTASI (NİHAİ) ---
# 'action' (string) adını, 'tools.py' içindeki 'aptal' fonksiyona eşler
#
TOOL_DISPATCH_MAP = {
    # File tools (7)
    
    "read_file": tools.read_file,
    "write_file": tools.write_file,
    "append_file": tools.append_file, # Bu, tools.write_file'ı 'a' moduyla çağırır
    "list_dir": tools.list_dir,
    "move_file": tools.move_file,
    "create_dir": tools.create_dir,
    "move_to_recycle_bin": tools.move_to_recycle_bin, # YASAKLI 'safe_delete_file' DEĞİL
    
    "run_process_safe": tools.run_process_safe, # YASAKLI (Asla eklenme)
    "response_me": tools.response_me,

    # UI tools (3)
    "list_open_windows": tools.list_open_windows,
    "click_element_by_auto_id": tools.click_element_by_auto_id,
    "set_element_text_by_auto_id": tools.set_element_text_by_auto_id,
    "inspect_window_elements": tools.inspect_window_elements,
    "inspect_screen_with_vision": tools.inspect_screen_with_vision,
    "mouse_click": tools.mouse_click,
    "mouse_move": tools.mouse_move,
    "mouse_double_click": tools.mouse_double_click,
    "keyboard_type": tools.keyboard_type,
    "keyboard_press": tools.keyboard_press,
    "scroll": tools.scroll,

    
    # Application tool (1)
    "start_application_safe": tools.start_application_safe, # Politika (whitelist) parametresi YOK
    
    # Wait tool (1)
    "wait": tools.wait, # JSON döndürmeyen, aptal versiyon
    
    # YASAKLI ARAÇ (Asla eklenme)
    # "run_process_safe": tools.run_process_safe,
}


class ExecutorCore:
    def __init__(self):
        """
        Executor, politikayı (Policy) başlatır.
        Politika, LLM (Planner) tarafından DEĞİŞTİRİLEMEZ.
        """
        self.policy = {
            # Sadece bu dizin ve alt dizinlerine izin ver
            "base_path": ALLOWED_BASE_PATH, 
            
            # Sadece bu uygulamaların başlatılmasına izin ver
            "app_whitelist": [
                "notepad.exe",
                "calc.exe",
                "mspaint.exe",
                "Spotify.exe"
            ], # POWERSHELL.EXE YOK.
        }
        print(f"--- ExecutorCore başlatıldı. Güvenli Kök Dizin: {self.policy['base_path']} ---")

    def execute_command(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planner'dan (LLM) 'tool_call' JSON'unu alır,
        1. Politikayı uygular (Güvenlik)
        2. Aracı çalıştırır (İş)
        3. Hataları yakalar (Sağlamlık)
        4. Planner'a 'status' JSON'unu döndürür.
        """
        action = tool_call.get("action")
        parameters = tool_call.get("parameters", {})

        if not action:
            return {"status": "error", "error": "JSON'da 'action' anahtarı eksik."}

        if action not in TOOL_DISPATCH_MAP:
            return {"status": "error", "error": f"Bilinmeyen eylem (action): '{action}'"}

        try:
            # 1. GÜVENLİK: Politikayı uygula (Çağırmadan ÖNCE)
            self._enforce_policy(action, parameters)

            # 2. İŞ: "Aptal" aracı çağır
            tool_function = TOOL_DISPATCH_MAP[action]
            result = tool_function(**parameters)
            
            # 3. BAŞARI: Başarılı sonucu JSON'a paketle
            print(f"--- EXECUTOR BAŞARILI (Action: {action}) ---\nSonuç: {result}\n--- END RESULT ---")
            return {"status": "success", "result": result}
        
        # 4. HATA YÖNETİMİ (Sağlamlık)
        except (
            # Dosya Sistemi Hataları
            FileNotFoundError, IsADirectoryError, NotADirectoryError,
            PermissionError, FileExistsError,
            # UI Otomasyon Hataları
            pywinauto.findwindows.WindowNotFoundError,
            # Diğer Araç Hataları
            send2trash.exceptions.TrashPermissionError,
            subprocess.SubprocessError,
            ValueError, #örn: wait('beş') -> float('beş')
            TypeError   #örn: read_file() -> parametre eksik
        ) as e:
            # Öngörülen, kurtarılabilir hatalar
            error_type = type(e).__name__
            return {"status": "error", "error": f"{error_type}: {e}"}
        except Exception as e:
            # Öngörülemeyen (Fatal) hatalar (örn: 'tools.py' içindeki bir kodlama hatası)
            error_type = type(e).__name__
            print(f"--- FATAL EXECUTOR ERROR (Action: {action}) ---\n{traceback.format_exc()}\n--- END TRACE ---")
            return {"status": "fatal", "error": f"Executor iç hatası: {error_type}: {e}"}

    def _enforce_policy(self, action: str, params: Dict[str, Any]):
        """
        LLM'in GÜVENEMEYECEĞİ statik politika kontrolleri.
        İhlal durumunda 'PermissionError' fırlatır.
        """
        
        # 1. Dosya Sistemi Politikası (Tüm ilgili araçlar için)
        paths_to_check = []
        if "path" in params: paths_to_check.append(params["path"])
        if "src" in params: paths_to_check.append(params["src"])
        if "dst" in params: paths_to_check.append(params["dst"])
        
        for path in paths_to_check:
            # 'is_path_safe', 'policy_rules.py' dosyasından gelir
            if not is_path_safe(path, self.policy["base_path"]):
                # Bu hata Executor'ın try...catch bloğunda yakalanır
                raise PermissionError(f"Yol '{path}' güvenli temel dizin '{self.policy['base_path']}' içinde değil.")

        # 2. Uygulama Politikası
        if action == "start_application_safe":
            app_name = params.get("app_name") # LLM'in istediği uygulama
            if not app_name:
                raise ValueError("'start_application_safe' için 'app_name' gereklidir.")
            # 'is_executable_allowed', 'policy_rules.py' dosyasından gelir
            """
            if not is_executable_allowed(app_name, self.policy["app_whitelist"]):
                raise PermissionError(f"Uygulama '{app_name}' beyaz listede (whitelist) değil.")"""
        
        # 3. YASAKLI ARAÇLAR (Eğer 'TOOL_DISPATCH_MAP'e yanlışlıkla eklenseler bile)
        if action == "run_process_safe":
            raise PermissionError("'run_process_safe' aracı güvenlik nedeniyle kalıcı olarak devre dışı bırakıldı.")
        
    def result(self) -> Dict[str, Any]:
        parsed = self.vision_parser.describe_ui()
        return parsed