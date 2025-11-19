from ultralytics import YOLO

def train_ui_model():
    # Başlangıç modeli. Bilgisayarın kuvvetliyse 'yolov8m.pt' (medium) yap.
    model = YOLO('yolo11n.pt') 

    # Oluşturduğumuz yaml dosyasının yolu
    yaml_path = "ui_yolo_dataset/dataset.yaml"

    print("🔥 YOLO Eğitimi Başlıyor...")
    
    results = model.train(
        data=yaml_path,
        epochs=50,      # 50-100 arası ideal
        imgsz=640,      # Ekran görüntüleri büyükse bunu arttırmayı deneyebilirsin (örn: 960)
        batch=16,       # Hata alırsan 8 veya 4 yap
        name='yolo_ui_parser', # Çıktı klasör ismi
        device=0,       # GPU id (veya 'cpu')
        plots=True      # Eğitim grafiklerini kaydet
    )
    
    print(f"Eğitim tamamlandı. Modeli şuradan alabilirsin: {results.save_dir}")

if __name__ == '__main__':
    train_ui_model()