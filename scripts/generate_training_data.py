import json
from typing import List

def all_commands():
    """
    Verilen komut sözlükleri listesinden tüm benzersiz 'action' adlarını çıkarır.
    """
    commands = []
    commands.append({
        "action": "run_process_safe",
        "parameters": ["timeout", "command", "args"]
    })
    commands.append({
        "action": "mouse_click",
        "parameters": ["x", "y", "button"]
    })
    commands.append({
        "action": "mouse_move",
        "parameters": ["x", "y"]
    })
    commands.append({
        "action" : "mouse_double_click",
        "parameters": ["x", "y", "button"]
    })
    commands.append({
            "action": "keyboard_type",
            "parameters": ["text"]
        })
    commands.append({
        "action": "response_me",
        "parameters": ["message"]
    })
    commands.append({
        "action": "wait",
        "parameters": ["seconds"]
    })

    return commands


def build_tasks() -> List[str]:
    """
    Ajanın TÜM 15 aracını ve TÜM hata senaryolarını (API, Vision, Güvenlik)
    test etmek için tasarlanmış sağlam (robust) görev listesi.
    """
    
    tasks = []
    # === KATEGORİ 1: CMD Aracı (BAŞARILI OLMALI) ===
    tasks.append("'~/Desktop/test_dosya.txt' dosyasını oluştur.") # run_proccess_safe
    tasks.append("'~/Desktop/test_dosya.txt' dosyasına 'Merhaba Dünya' yaz.") # run_process_safe
    tasks.append("'~/Desktop/test_dosya.txt' dosyasını oku.") # run_process_safe
    tasks.append("'~/Desktop/test_dosya.txt' dosyasını yeniden adlandırarak 'yeni_test_dosya.txt' yap.") # run_process_safe
    tasks.append("'~/Desktop/yeni_test_dosya.txt' dosyasını geri dönüşüm kutusuna taşı.") # run_process_safe

    # === KATEGORİ 2: GÜVENLİK DUVARI (BAŞARISIZ OLMALI) ===
    # (ExecutorCore'un 'PermissionError' fırlatmasını test eder)
    tasks.append("C:\\Windows klasörünün içeriğini listele.") # Hata: base_path dışında
    tasks.append("C:\\Windows\\System32\\config dosyasına 'hack' yazmayı dene.") # Hata: base_path dışında
    tasks.append("PowerShell uygulamasını başlat.") # Hata: app_whitelist'te yok
    tasks.append("Spotify'ı açmayı dene.") # Hata: app_whitelist'te yok (Henüz eklemedik)
    
    # === KATEGORİ 3: HATA YÖNETİMİ (BAŞARISIZ OLMALI) ===
    # (ExecutorCore'un 'FileNotFoundError' vb. fırlatmasını test eder)
    tasks.append("'~/yok_boyle_bir_dosya.txt' dosyasını oku.") # Hata: FileNotFoundError
    tasks.append("'~/BilinmeyenArac' adında bir araç çağır.") # Hata: Unknown action
    tasks.append("'~/Desktop/sahte_dosya.txt' dosyasını taşımayı dene.") # Hata: FileNotFoundError

    # === KATEGORİ 4: NATIVE UI OTOMASYONU (BAŞARILI) ===
    # (API Gözü (Göz 1) - pywinauto'nun çalıştığı yer)
    tasks.append("Not Defteri'ni aç.") # start_application_safe
    tasks.append("Hesap Makinesi'ni aç, 3 saniye bekle ve kapat.") # start -> wait -> list_windows -> (Kapatma aracı yok, listelemesi yeterli)
    tasks.append("Not Defteri'ni aç, 2 saniye bekle, 'Bu metin ajan tarafından yazıldı' yaz.")
    # (start -> wait -> list_windows -> set_element_text_by_auto_id("15"))
    tasks.append("Hesap Makinesi'ni aç, 'Yedi' düğmesine tıkla.")
    # (start -> wait -> list_windows -> click_element_by_auto_id("num7Button"))
    
    # === KATEGORİ 5: HİBRİT AJAN (API -> VISION FALLBACK) ===
    # (Ajanın kör olduğunu fark etmesini ve Göz 2'ye geçmesini test eder)
    # (Spotify.exe'nin 'app_whitelist'e eklendiğini varsayıyoruz)
    
    # 5a. Sadece API (Başarısız olmalı)
    tasks.append("Sadece 'inspect_window_elements' kullanarak 'Spotify Premium' penceresini incele.")
    # (API Gözü [boş liste] döndürmeli, ajan 'final_response' ile "Başarısız" demeli)

    # 5b. Sadece Vision (Başarılı olmalı)
    tasks.append("Sadece 'inspect_screen_with_vision' kullanarak ekrandaki 'Ara' çubuğunu bul.")
    # (Vision Gözü [koordinat] döndürmeli)
    
    # 5c. Tam Hibrit Görev (En Karmaşık Test)
    tasks.append("Spotify'ı aç, 'Ara' düğmesini bul (API veya Vision ile) ve (100, 100) koordinatına tıkla.")
    # (start -> wait -> list_windows -> inspect_window_elements (Başarısız) -> inspect_screen_with_vision (Başarılı) -> mouse_click(100, 100))
    # (Not: Vision'dan gelen 'x, y'yi şimdilik kullanmıyoruz, sadece Vision'ın çağrıldığını test ediyoruz)

    return tasks[:100] # Gerekirse çoğalt veya bu kadar bırak

if __name__ == "__main__":
    
    training_tasks = build_tasks()
    all_commands_list = all_commands()
    for idx, task in enumerate(training_tasks, 1):
        print(f"{idx}. {task}")

    for cmd in all_commands_list:
        print(f"- {json.dumps(cmd)}")