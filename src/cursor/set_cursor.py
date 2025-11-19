import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

cursor_ids = [
    32512,  # OCR_NORMAL
    32513,  # OCR_IBEAM
    32649,  # OCR_HAND
    32514,  # OCR_WAIT
    32650,  # OCR_CROSS
    32651,  # OCR_UP
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


def change_cursor_to_red(ocr):
    hcur = user32.LoadCursorW(None, ctypes.c_int(ocr))
    hicon = user32.CopyIcon(hcur)

    iconinfo = ICONINFO()
    user32.GetIconInfo(hicon, ctypes.byref(iconinfo))

    bmpinfo = BITMAP()
    gdi32.GetObjectW(ctypes.c_void_p(iconinfo.hbmColor), ctypes.sizeof(bmpinfo), ctypes.byref(bmpinfo))

    width = bmpinfo.bmWidth
    height = bmpinfo.bmHeight

    buf_size = width * height * 4
    pixels = (ctypes.c_uint8 * buf_size)()
    gdi32.GetBitmapBits(iconinfo.hbmColor, buf_size, pixels)

    # OK ŞEKLİNİ BOZMAMAK İÇİN SADECE ALPHA KANALINA ETKİ EDEN "overlay" UYGULA
    for i in range(0, buf_size, 4):
        # Eğer piksel tamamen şeffaf değilse → yani ok'un bir parçasıysa
        if pixels[i+3] != 0:
            # RENGİ YAVAŞÇA KIRMIZIYA KAYDIR
            pixels[i+2] = 255    # Red
            pixels[i+1] = int(pixels[i+1] * 0.3)
            pixels[i+0] = int(pixels[i+0] * 0.3)

    gdi32.SetBitmapBits(iconinfo.hbmColor, buf_size, pixels)

    new_cursor = user32.CreateIconIndirect(ctypes.byref(iconinfo))
    user32.SetSystemCursor(new_cursor, ocr)

def tint_cursor_red_correct():
    for cursor_id in cursor_ids:
        change_cursor_to_red(0)


def restore_cursor():
    SPI_SETCURSORS = 0x57
    user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)
