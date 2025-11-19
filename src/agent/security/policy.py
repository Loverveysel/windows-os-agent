# policy/policy_rules.py
import os
from typing import List

#
# --- 1. GÜVENLİ KÖK DİZİN ---
# Ajanın dokunabileceği tek yer.
# 'os.path.expanduser('~')' -> 'C:\Users\[SeninAdin]'
# Bu, ajanın C:\Windows veya C:\Program Files gibi yerlere dokunmasını engeller.
#
# (Bunu bir config.py dosyasından da okuyabilirsin, ama varsayılan olarak
# kullanıcının kendi 'home' dizinini kullanmak en güvenlisidir.)
#
ALLOWED_BASE_PATH = os.path.abspath(os.path.expanduser('~'))


def is_path_safe(path: str, base_path: str = ALLOWED_BASE_PATH) -> bool:
    """
    Bir yolun (path), güvenli 'base_path' içinde olup olmadığını KESİN olarak kontrol eder.
    '../' (Path Traversal) saldırılarına karşı korumalıdır.
    """
    
    # 1. Adım: Yolu normalize et (örn: '~' veya '..' karakterlerini çöz)
    # LLM'in gönderdiği: "~\..\..\Windows\System32"
    # normalized_path: "C:\Windows\System32"
    try:
        # _resolve_path (tools.py'deki helper) burada da kullanılabilir veya
        # aynı mantık burada tekrarlanabilir:
        if not path:
            return False
        normalized_path = os.path.abspath(os.path.expanduser(path))
    except Exception:
        # Bozuk veya geçersiz bir yol (örn: null byte)
        return False

    # 2. Adım: Güvenlik Kontrolü (Path Traversal Koruması)
    #
    # YANLIŞ YÖNTEM (Güvensiz):
    # if normalized_path.startswith(base_path): ...
    # Bu, "C:\Users\Admin-Sahte" yolunun "C:\Users\Admin" ile başladığını sanır.
    #
    # DOĞRU YÖNTEM (Güvenli):
    # 'commonpath', iki yolun en derin ortak klasörünü bulur.
    # Eğer bu ortak klasör, 'base_path'ın kendisi DEĞİLSE,
    # bu, 'normalized_path'ın 'base_path'ın DIŞINDA olduğu anlamına gelir.
    #
    # Örnek:
    # path = "C:\Windows"
    # base_path = "C:\Users\Admin"
    # commonpath = "C:\"  -> (base_path ile aynı değil) -> GÜVENSİZ
    #
    # path = "C:\Users\Admin\Documents"
    # base_path = "C:\Users\Admin"
    # commonpath = "C:\Users\Admin" -> (base_path ile aynı) -> GÜVENLİ
    
    
    
    try:
        common = os.path.commonpath([normalized_path, base_path])
    except ValueError:
        # Yollar farklı sürücülerdeyse (C: vs D:)
        return False
        
    return os.path.normpath(common) == os.path.normpath(base_path)


def is_executable_allowed(app_name: str, whitelist: List[str]) -> bool:
    """
    Bir uygulamanın, 'Executor'ın statik beyaz listesinde olup olmadığını kontrol eder.
    (Case-insensitive - Büyük/küçük harf duyarsız)
    """
    if not app_name:
        return False
        
    # 'notepad.exe' veya 'NOTEPAD.EXE' gibi isimleri kontrol et
    app_basename = os.path.basename(app_name).lower()
    
    for allowed_app in whitelist:
        if app_basename == allowed_app.lower():
            return True
            
    return False