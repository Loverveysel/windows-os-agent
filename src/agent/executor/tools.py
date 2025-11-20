import time
import pyautogui
from pywinauto import keyboard


SPECIAL_KEYS = {
    "CTRL": "^",
    "ALT": "%",
    "SHIFT": "+",
    "ENTER": "{ENTER}",
    "TAB": "{TAB}",
    "ESC": "{ESC}",
    "SPACE": " ",
    "BACKSPACE": "{BACKSPACE}",
    "DELETE": "{DELETE}",
    "UP": "{UP}",
    "DOWN": "{DOWN}",
    "LEFT": "{LEFT}",
    "RIGHT": "{RIGHT}",
}



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
    Simulate keyboard key presses using pywinauto.send_keys.
    Supports combos like: CTRL+S, CTRL+SHIFT+ESC, ALT+F4, etc.
    """

    parts = keys.split("+")
    sequence = ""

    for p in parts:
        p_upper = p.upper()

        if p_upper in SPECIAL_KEYS:
            sequence += SPECIAL_KEYS[p_upper]
        elif len(p) == 1:
            # tek karakter tuşlar normal yazılır: "A", "s", "1" vs.
            sequence += p
        else:
            # F1, F2, HOME gibi tuşlar
            sequence += f"{{{p_upper}}}"

    keyboard.send_keys(sequence)
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
    return f"scrolled-mouse:{amount}"

