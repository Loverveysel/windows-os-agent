import os
import shutil
import subprocess
import time
import uuid
from typing import List, Dict, Any, Optional, Union
import io
from PIL import ImageGrab
import pyautogui
from pywinauto import Desktop
import send2trash

# --- Helper ---
def _resolve_path(path: str) -> str:
    """
    Expand and normalize a user-provided path. Raise ValueError if path is falsy.
    This is a pure normalization helper; policy checks are the Executor's responsibility.
    """
    if not path:
        raise ValueError("path must be provided")
    return os.path.abspath(os.path.expanduser(path))


# --- File tools (7) ---
def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    Return the raw file contents as a string.
    Raises FileNotFoundError / IOError on error.
    """
    resolved = _resolve_path(path)
    with open(resolved, "r", encoding=encoding) as f:
        return f.read()


def write_file(path: str, content: Union[str, bytes], mode: str = "w", encoding: str = "utf-8") -> str:
    """
    Write content to path (creates parent dirs if necessary).
    Returns the resolved path. Raises on error.
    """
    resolved = _resolve_path(path)
    parent = os.path.dirname(resolved)
    if parent:
        os.makedirs(parent, exist_ok=True)

    if "b" in mode:
        data = content if isinstance(content, (bytes, bytearray)) else str(content).encode(encoding)
        with open(resolved, mode) as f:
            f.write(data)
    else:
        with open(resolved, mode, encoding=encoding) as f:
            f.write(str(content))
    return resolved


def append_file(path: str, content: Union[str, bytes], encoding: str = "utf-8") -> str:
    """
    Append content to path. Returns resolved path. Raises on error.
    """
    return write_file(path, content, mode="a", encoding=encoding)


def list_dir(path: str) -> List[str]:
    """
    Return a list of directory entries (names) at path.
    Raises FileNotFoundError / OSError on error.
    """
    resolved = _resolve_path(path)
    return os.listdir(resolved)


def move_file(src: str, dst: str) -> str:
    """
    Move/rename src -> dst. Returns resolved destination path. Raises on error.
    """
    s = _resolve_path(src)
    d = _resolve_path(dst)
    parent = os.path.dirname(d)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.move(s, d)
    return d


def create_dir(path: str) -> str:
    """
    Create a directory (including parents). Returns resolved path.
    Raises OSError on error (exists -> may raise depending on flags).
    """
    resolved = _resolve_path(path)
    os.makedirs(resolved, exist_ok=True)
    return resolved


def move_to_recycle_bin(path: str) -> str:
    """
    Move the file or directory to the recycle bin (trash). Uses send2trash.
    Returns a brief confirmation string. Raises on error.
    """
    resolved = _resolve_path(path)
    send2trash.send2trash(resolved)
    return f"moved-to-recycle-bin:{resolved}"


# --- CMD tool ---
def run_process_safe(command: str, args: Optional[List[str]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
    """
    Güvenli bir şekilde bir işlem çalıştırır (ExecutorCore politikası tarafından zaten kontrol edilmiştir).
    - command: yürütülebilir dosya yolu veya adı (PATH'de olabilir)
    - args: argüman listesi
    - timeout: saniye cinsinden zaman aşımı (float)
    
    Döndürür: {"returncode": int, "stdout": str, "stderr": str}
    Hata durumunda 'subprocess.TimeoutExpired' veya 'subprocess.SubprocessError' fırlatır.
    """
    cmd: List[str] = [command]
    if args:
        cmd.extend(args)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        shell=False,
        text=True  # stdout/stderr as strings
    )

    try:
        outs, errs = proc.communicate(timeout=timeout)
        print(f"Process finished: returncode={proc.returncode}, stdout: {outs}, stderr: {errs}")
    except subprocess.TimeoutExpired as e:
        proc.kill()
        outs, errs = proc.communicate()
        raise subprocess.TimeoutExpired(cmd, timeout, output=outs, stderr=errs) from e

    return {"returncode": proc.returncode, "stdout": outs, "stderr": errs}

def response_me(thing: str) -> str:
    print(thing)
    return f"printed:{thing}"

# --- UI tools (3 - dumb, policy-free) ---

def list_open_windows() -> List[Dict[str, Any]]:
    """
    Return a list of open windows as dicts: {"title": ..., "pid": ..., "window_auto_id": ...}.
    Raises pywinauto exceptions on failure.
    """
    desktop = Desktop(backend="uia")
    wins = desktop.windows()
    out: List[Dict[str, Any]] = []
    for w in wins:
        title = w.window_text()
        if not title:
            continue
        pid = w.process_id() if hasattr(w, "process_id") else None
        handle = getattr(w, "handle", None)
        out.append({"title": title, "pid": pid, "window_auto_id": f"win-{handle}"})
    return out


def set_element_text_by_auto_id(title_regex: str, auto_id: str, text: str) -> str:
    """
    Find a top-level window matching title_regex and set text on the control with auto_id.
    Prefers set_edit_text, falls back to type_keys. Returns a short confirmation string.
    Raises pywinauto exceptions if window/control not found or on other errors.
    """
    desktop = Desktop(backend="uia")
    dlg = desktop.window(title_re=title_regex)
    ctrl = dlg.child_window(auto_id=auto_id)
    wrapper = ctrl.wrapper_object()
    if hasattr(wrapper, "set_edit_text"):
        wrapper.set_edit_text(text)
    else:
        wrapper.type_keys(text, with_spaces=True, set_foreground=True)
    handle = getattr(dlg, "handle", None)
    return f"set-text:auto_id={auto_id}:window={handle}"


# --- Additional UI convenience: click control by auto_id ---
def click_element_by_auto_id(title_regex: str, auto_id: str) -> str:
    """
    Find a top-level window matching title_regex and click the control with auto_id.
    Returns a brief confirmation string. Raises on error.
    """
    desktop = Desktop(backend="uia")
    dlg = desktop.window(title_re=title_regex)
    ctrl = dlg.child_window(auto_id=auto_id)
    wrapper = ctrl.wrapper_object()
    wrapper.click_input()
    handle = getattr(dlg, "handle", None)
    return f"clicked:auto_id={auto_id}:window={handle}"


# --- Wait tool (1) ---
def wait(seconds: float) -> float:
    """
    Sadece bekler. VEYA 'ValueError/TypeError' fırlatır.
    JSON/Dict döndürmez. try/catch yapmaz.
    """
    # Executor'ın try...catch bloğu, float'a dönüştürme hatasını yakalar
    s = float(seconds)
    time.sleep(s)
    return s # JSON DEĞIL, HAM VERİ (FLOAT) DÖNDÜRÜR

# ... (diğer import'ların yanına 'from typing import List, Dict, Any, Optional' ekle) ...

def start_application_safe(app_name: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Uygulamayı başlatır. ExecutorCore politikayı (whitelist) ZATEN kontrol etti.
    
    YENİ GÜNCELLEME: 'args' listesindeki "~" veya "%USERPROFILE%" içeren
    ve bir yola benzeyen argümanları 'subprocess.Popen'e göndermeden önce
    otomatik olarak _resolve_path() ile çözer.
    """
    
    # 1. 'app_name'in kendisi bir yol olabilir (örn: C:\...), 
    #    ya da 'notepad.exe' gibi PATH'de olan bir isim olabilir.
    #    Executor'ın 'app_whitelist'i zaten 'notepad.exe'ye izin verdi.
    exe_to_run = _resolve_path(app_name) if os.path.sep in app_name or os.path.altsep in app_name else app_name

    resolved_args: List[str] = []
    if args:
        for arg in args:
            # 2. Argüman bir yola benziyor mu?
            # (Basit bir kontrol: '~', '%', '\' veya '/' içeriyorsa)
            if isinstance(arg, str) and ('~' in arg or '%' in arg or os.path.sep in arg or os.path.altsep in arg):
                try:
                    # '~/Desktop/osmanli.txt' -> 'C:\Users\...\Desktop\osmanli.txt'
                    resolved_args.append(_resolve_path(arg))
                except Exception:
                    # Çözemezse bile, ham argümanı ekle (belki bir URL'dir)
                    resolved_args.append(arg)
            else:
                resolved_args.append(arg)

    cmd: List[str] = [exe_to_run] + resolved_args

    # 3. 'shell=False' (güvenlik için) ve 'start_new_session=True' (bağımsız çalışsın diye)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        shell=False,
        start_new_session=True # Windows'ta 'creationflags=subprocess.CREATE_NEW_PROCESS_GROUP'
    )
    
    return {"pid": proc.pid, "start_id": f"start-{uuid.uuid4().hex[:8]}"}

def inspect_window_elements(title_regex: str) -> List[Dict[str, str]]:
    """
    Inspect a top-level window matching title_regex and return a list of interactive elements.

    - Finds the window via Desktop(backend="uia").window(title_re=title_regex)
    - Iterates over .descendants()
    - Filters to elements that are clickable (is_clickable) or editable (is_editable)
    - Returns a clean list of dicts: {"auto_id": <str>, "title": <str>, "type": <control_type>}

    NOTE: This is a dumb helper: it performs no policy checks and raises pywinauto errors
    to the caller on failure (no try/except here).
    """
    desktop = Desktop(backend="uia")
    dlg = desktop.window(title_re=title_regex)
    descendants = dlg.descendants()

    out: List[Dict[str, str]] = []
    for e in descendants:
        # Determine click/edit capabilities if available
        is_clickable = False
        is_editable = False

        if hasattr(e, "is_clickable"):
            attr = getattr(e, "is_clickable")
            is_clickable = attr() if callable(attr) else bool(attr)

        if hasattr(e, "is_editable"):
            attr = getattr(e, "is_editable")
            is_editable = attr() if callable(attr) else bool(attr)

        if not (is_clickable or is_editable):
            continue

        # Extract automation id / name / control type from element_info when possible
        auto_id = ""
        title = ""
        control_type = ""

        if hasattr(e, "element_info") and e.element_info is not None:
            ei = e.element_info
            auto_id = getattr(ei, "automation_id", "") or getattr(ei, "auto_id", "") or ""
            title = getattr(ei, "name", "") or ""
            control_type = getattr(ei, "control_type", "") or ""

        # Fallbacks: wrapper/window_text if available
        if not title and hasattr(e, "window_text"):
            # window_text() is commonly present on wrappers
            title = e.window_text()

        # Normalize to strings
        auto_id = str(auto_id) if auto_id is not None else ""
        title = str(title) if title is not None else ""
        control_type = str(control_type) if control_type is not None else ""

        out.append({"auto_id": auto_id, "title": title, "type": control_type})

    return out

def inspect_screen_with_vision(vision_client, image_format: str = "PNG") -> List[Dict[str, Any]]:
    """
    Capture the current screen and send the image bytes to the provided vision_client callable.
    - vision_client: a callable that accepts raw image bytes and returns a List[Dict] describing
      clickable/editable regions, e.g. [{"x": 123, "y": 456, "w": 50, "h": 20, "label": "Play"} ...]
    - image_format: PNG/JPEG etc.
    Returns the vision_client result directly.
    Raises RuntimeError if vision_client is not provided or not callable.
    Raises any underlying exceptions (no try/except here).
    """
    # Capture full screen as PIL Image
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format=image_format)
    img_bytes = buf.getvalue()

    if not callable(vision_client):
        raise RuntimeError("vision_client callable is required for inspect_screen_with_vision")

    # vision_client is expected to perform inference and return a structured List[Dict]
    result = vision_client(img_bytes)
    return result


def mouse_click(x: int, y: int, button: str = "left") -> str:
    """
    Perform a raw mouse click at (x, y) screen coordinates.
    - button: "left"|"right"|"middle"
    Returns a short confirmation string.
    Raises on underlying errors (no try/except here).
    """
    # pywinauto.mouse.click expects integer coordinates

    pyautogui.click(x=int(x), y=int(y), button=button, duration=0.8)
    return f"clicked:{int(x)},{int(y)}:{button}"

def keyboard_type(text: str) -> str:
    """
    Simulate keyboard typing of the provided text.
    Returns a short confirmation string.
    Raises on underlying errors (no try/except here).
    """
    from pywinauto import keyboard
    keyboard.send_keys(text, with_spaces=True)
    return f"typed-text:{text}"

def mouse_move(x: int, y: int) -> str:
    """
    Move the mouse cursor to (x, y) screen coordinates.
    Returns a short confirmation string.
    Raises on underlying errors (no try/except here).
    """
    pyautogui.moveTo(int(x), int(y), duration=0.8)
    return f"moved-mouse:{int(x)},{int(y)}"

def mouse_double_click(x: int, y: int, button: str = "left") -> str:
    """
    Perform a raw mouse double-click at (x, y) screen coordinates.
    - button: "left"|"right"|"middle"
    Returns a short confirmation string.
    Raises on underlying errors (no try/except here).
    """
    pyautogui.doubleClick(x=int(x), y=int(y), button=button, duration=0.8)
    return f"double-clicked:{int(x)},{int(y)}:{button}"

def keyboard_press(keys: str = "ENTER") -> str:
    """
    Simulate keyboard key presses of the provided keys.
    Returns a short confirmation string.
    Raises on underlying errors (no try/except here).
    """
    keys = '{' + keys + '}'
    from pywinauto import keyboard
    keyboard.send_keys(keys)
    return f"pressed-keys:{keys}"

def scroll(amount: int) -> str:
    """
    Scroll the mouse wheel.
    - amount: number of scroll units (positive or negative)
    - direction: "vertical" or "horizontal"
    Returns a short confirmation string.
    Raises on underlying errors (no try/except here).
    """
    pyautogui.scroll(amount)
    #   
    return f"scrolled-mouse:{amount}"