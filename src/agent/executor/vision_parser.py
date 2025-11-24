import cv2
import json
import pytesseract
from ultralytics import YOLO
import mss
import numpy as np

class ScreenParser:
    def __init__(self, model_path='runs/detect/yolo_ui_parser/weights/best.pt'):
        # Model Yolu: Kendi eğitimin sonucundaki best.pt yolunu buraya ver
        print("Model ve Tesseract ayarları yükleniyor...")
        self.model = YOLO(model_path) 
        self.lang = 'tur' 

    def screen_capture(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img  

    def parse_and_visualize(self, image_source=None):
        img = None
        
        # --- GÖRÜNTÜ YAKALAMA ---
        if image_source is None:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                print("Canlı ekran görüntüsü alındı.")
        else:
            img = cv2.imread(image_source)
            if img is None: raise ValueError(f"Resim bulunamadı: {image_source}")

        # Görselleştirme için kopyasını al (Orjinal resmi bozmayalım)
        debug_img = img.copy()

        # --- YOLO TESPİTİ ---
        results = self.model(img, conf=0.25)[0]
        parsed_elements = []

        print(f"Tespit edilen nesne sayısı: {len(results.boxes)}")

        
        for box in results.boxes:
            # Koordinatlar
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])
            
            # Sınıf ismini al (Eğer names dict yüklü değilse ID kullan)
            label_name = self.model.names.get(cls_id, f"Class_{cls_id}")

            # --- OCR İŞLEMİ (Padding + Thresholding Düzeltmesi) ---
            # Kutuyu biraz genişlet (Padding) - OCR başarısı için kritik
            pad = 5
            h_img, w_img, _ = img.shape
            roi_x1 = max(0, x1 - pad)
            roi_y1 = max(0, y1 - pad)
            roi_x2 = min(w_img, x2 + pad)
            roi_y2 = min(h_img, y2 + pad)

            roi = img[roi_y1:roi_y2, roi_x1:roi_x2]

            try:
                roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                # Binary Thresholding (Metni netleştirme)
                _, roi_thresh = cv2.threshold(roi_gray, 180, 255, cv2.THRESH_BINARY_INV)
                
                detected_text = pytesseract.image_to_string(
                    roi_thresh, lang=self.lang
                ).strip().replace('\n', ' ')
            except Exception:
                detected_text = ""

            # --- VERİ YAPILANDIRMA ---
            element_data = {
                "type": label_name,
                "id": cls_id,
                "confidence": round(confidence, 2),
                "bbox": {"x": x1, "y": y1, "w": x2-x1, "h": y2-y1},
                "content": detected_text
            }
            parsed_elements.append(element_data)

            # --- GÖRSEL ÇİZİM (DEBUGGING) ---
            # 1. Kutuyu çiz (Yeşil)
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 2. Label yaz (Kırmızı - Kutunun Üstüne)
            label_str = f"{label_name} ({confidence:.2f})"
            cv2.putText(debug_img, label_str, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # 3. OCR Metnini yaz (Mavi - Kutunun Altına veya İçine)
            if detected_text:
                cv2.putText(debug_img, f"OCR: {detected_text}", (x1, y2 + 15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return parsed_elements

    def save_json(self, data, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"JSON kaydedildi: {output_path}")

"""
# --- Main ---
if __name__ == "__main__":
    # Model yolunu kontrol et!
    parser = ScreenParser(model_path='runs/detect/yolo_ui_parser/weights/best.pt')
    
    try:
        # Analiz et
        json_data, visual_img = parser.parse_and_visualize() # Parametre boş = Canlı Screenshot
        
        # 1. JSON Kaydet
        parser.save_json(json_data, "debug_data.json")
        
        # 2. Görseli Kaydet
        output_img_path = "debug_visual.jpg"
        cv2.imwrite(output_img_path, visual_img)
        print(f"Görsel kaydedildi: {output_img_path}")
        
        # 3. Görseli Ekrana Bas (Kapatmak için 'q' bas)
        # Pencere boyutunu ayarla (Ekranın çok büyükse sığmayabilir)
        cv2.namedWindow("YOLO Debug", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("YOLO Debug", 1280, 720) 
        cv2.imshow("YOLO Debug", visual_img)
        
        print("Çıkmak için 'q' tuşuna bas...")
        while True:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Hata: {e}")"""