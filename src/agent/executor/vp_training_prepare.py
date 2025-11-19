import os
import shutil
from huggingface_hub import snapshot_download
from pathlib import Path
import yaml

# --- AYARLAR ---
REPO_ID = "YashJain/UI-Elements-Detection-Dataset"
DOWNLOAD_DIR = "./raw_download"  # Geçici indirme klasörü
FINAL_DIR = "./ui_yolo_dataset"  # Eğitime girecek temiz klasör

def setup_dataset():
    # 1. Temizlik
    if os.path.exists(FINAL_DIR): shutil.rmtree(FINAL_DIR)
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)

    # 2. İndirme
    print(f"📥 Dataset indiriliyor: {REPO_ID}...")
    # Sadece gerekli dosyaları indir (git dosyalarını vs. atla)
    snapshot_download(repo_id=REPO_ID, local_dir=DOWNLOAD_DIR, repo_type="dataset", 
                      ignore_patterns=[".gitattributes", "README.md"])

    # 3. Klasör Yapısını Oluştur
    # YOLO şunları bekler: dataset/train/images, dataset/train/labels
    for split in ['train', 'valid']:
        os.makedirs(os.path.join(FINAL_DIR, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(FINAL_DIR, split, 'labels'), exist_ok=True)

    print("📂 Dosyalar organize ediliyor...")

    # 4. Dosyaları Taşıma Fonksiyonu
    def move_files(source_split, target_split):
        # İndirilen klasörde bazen iç içe klasörler olur, onları bulalım
        src_path = Path(DOWNLOAD_DIR)
        
        # Kaynakta 'images' ve 'labels' klasörlerini ara
        # pattern: raw_download/train/images/*.png
        found_images = list(src_path.rglob(f"{source_split}/**/images/*.*"))
        found_labels = list(src_path.rglob(f"{source_split}/**/labels/*.txt"))

        if not found_images:
            print(f"⚠️ UYARI: {source_split} için resim bulunamadı!")
            return

        print(f"   -> {source_split}: {len(found_images)} resim, {len(found_labels)} etiket taşınıyor...")

        # Resimleri taşı
        for img_file in found_images:
            shutil.copy(img_file, os.path.join(FINAL_DIR, target_split, 'images', img_file.name))
        
        # Label'ları taşı
        for lbl_file in found_labels:
            shutil.copy(lbl_file, os.path.join(FINAL_DIR, target_split, 'labels', lbl_file.name))

    # Train -> Train
    move_files('train', 'train')
    # Test -> Valid (YOLO eğitimde validation ister, test klasörünü valid yapıyoruz)
    move_files('test', 'valid')

    # 5. Sınıf Sayısını (Number of Classes) Tespit Et
    print("🔍 Sınıf sayısı analiz ediliyor...")
    max_id = -1
    label_files = list(Path(FINAL_DIR).rglob("*.txt"))
    
    for lf in label_files:
        with open(lf, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if parts:
                    try:
                        class_id = int(parts[0])
                        if class_id > max_id: max_id = class_id
                    except ValueError:
                        pass # Bozuk satır varsa geç

    num_classes = max_id + 1
    print(f"✅ Toplam {num_classes} adet sınıf tespit edildi (IDs: 0-{max_id}).")

    # 6. data.yaml Oluştur
    # Not: Sınıf isimlerini bilmediğimiz için generic isimler veriyoruz.
    # Eğer gerçek isimleri biliyorsan (örn: Button, Input), listeyi aşağıda elle güncelle.
    
    # YashJain Dataset Tahmini Sınıf Listesi (Genelde şöyledir ama garanti değil):
    # class_names = ['Button', 'Input', 'Image', 'Label', 'Icon'] 
    # Biz güvenli olması için generic yapıyoruz:
    class_names = [f"Class_{i}" for i in range(num_classes)]

    yaml_data = {
        'path': os.path.abspath(FINAL_DIR),
        'train': 'train/images',
        'val': 'valid/images',
        'nc': num_classes,
        'names': class_names
    }

    yaml_path = os.path.join(FINAL_DIR, 'data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f)

    print(f"\n🚀 Hazırlık Tamam! Config dosyası: {yaml_path}")
    print("Artık eğitim kodunu çalıştırabilirsin.")

if __name__ == "__main__":
    setup_dataset()