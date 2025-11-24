import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

gdi32.GetBitmapBits.argtypes = [wintypes.HBITMAP, wintypes.LONG, ctypes.c_void_p]
gdi32.GetBitmapBits.restype = wintypes.LONG
gdi32.SetBitmapBits.argtypes = [wintypes.HBITMAP, wintypes.DWORD, ctypes.c_void_p]
gdi32.SetBitmapBits.restype = wintypes.LONG
gdi32.GetObjectW.argtypes = [wintypes.HGDIOBJ, ctypes.c_int, ctypes.c_void_p]
gdi32.GetObjectW.restype = ctypes.c_int

cursor_ids = [
    32512,  # OCR_NORMAL
    32513,  # OCR_IBEAM
    32649,  # OCR_HAND
    32514,  # OCR_WAIT
    32650,  # OCR_CROSS
    32651,  # OCR_UP
    32642,
    32643,
    32644,
    32645
]

class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP)
    ]

class BITMAP(ctypes.Structure):
    _fields_ = [
        ("bmType", wintypes.LONG),
        ("bmWidth", wintypes.LONG),
        ("bmHeight", wintypes.LONG),
        ("bmWidthBytes", wintypes.LONG),
        ("bmPlanes", wintypes.WORD),
        ("bmBitsPixel", wintypes.WORD),
        ("bmBits", ctypes.c_void_p)
    ]

def change_cursor_color(ocr): # Fonksiyon ismini düzelttim
    hcur = user32.LoadCursorW(None, ctypes.c_int(ocr))
    if not hcur:
        return # Cursor yüklenemezse çık

    hicon = user32.CopyIcon(hcur)

    iconinfo = ICONINFO()
    if not user32.GetIconInfo(hicon, ctypes.byref(iconinfo)):
        return

    # KRİTİK KONTROL: Siyah-beyaz imleçlerin renk bitmap'i olmaz
    if not iconinfo.hbmColor:
        # Mask bitmap'i silip çıkmalıyız yoksa leak oluşur (Handle sızıntısı)
        gdi32.DeleteObject(iconinfo.hbmMask)
        user32.DestroyIcon(hicon)
        print(f"Cursor {ocr} has no color map (monochrome). Skipping.")
        return

    bmpinfo = BITMAP()
    gdi32.GetObjectW(iconinfo.hbmColor, ctypes.sizeof(bmpinfo), ctypes.byref(bmpinfo))

    width = bmpinfo.bmWidth
    height = bmpinfo.bmHeight

    # Buffer boyutunu hesapla
    buf_size = width * height * 4
    pixels = (ctypes.c_uint8 * buf_size)()

    # ARTIK BURASI PATLAMAYACAK
    gdi32.GetBitmapBits(iconinfo.hbmColor, buf_size, pixels)

    for i in range(0, buf_size, 4):
        if pixels[i+3] != 0: # Alpha kanalı kontrolü
            # Basit bir grileştirme/renklendirme
            pixels[i+2] = 20   # Red
            pixels[i+1] = 40   # Green
            pixels[i+0] = 40   # Blue

    gdi32.SetBitmapBits(iconinfo.hbmColor, buf_size, pixels)

    new_cursor = user32.CreateIconIndirect(ctypes.byref(iconinfo))
    user32.SetSystemCursor(new_cursor, ocr)

    # TEMİZLİK YAPMAK ZORUNDASIN
    # CreateIconIndirect yeni bir kopya oluşturdu, eskileri silmelisin.
    # Yoksa GDI Object limitini doldurup Windows'u çökertirsin.
    gdi32.DeleteObject(iconinfo.hbmMask)
    gdi32.DeleteObject(iconinfo.hbmColor)
    user32.DestroyIcon(hicon)

def tint_cursor_color_correct():
    for cursor_id in cursor_ids:
        try:
            change_cursor_color(cursor_id)
        except Exception as e:
            print(f"Error on cursor {cursor_id}: {e}")

def restore_cursor():
    SPI_SETCURSORS = 0x57
    user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)

restore_cursor()
