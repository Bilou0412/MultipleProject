#!/usr/bin/env python3
"""
Générateur d'icônes pour l'extension CVLM
Crée des icônes simples avec PIL/Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Crée une icône carrée avec le texte 'CV'"""
    
    # Couleur de fond (violet-bleu)
    bg_color = (102, 126, 234)  # #667eea
    text_color = (255, 255, 255)  # blanc
    
    # Créer l'image
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Ajouter un dégradé simple (rectangle arrondi)
    margin = size // 10
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 8,
        fill=(118, 75, 162)  # #764ba2 (violet plus foncé)
    )
    
    # Ajouter le texte "CV"
    font_size = size // 2
    try:
        # Essayer d'utiliser une police système
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            # Fallback sur la police par défaut
            font = ImageFont.load_default()
    
    text = "CV"
    
    # Calculer la position pour centrer le texte
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # Dessiner le texte
    draw.text((x, y), text, fill=text_color, font=font)
    
    # Sauvegarder
    img.save(output_path)
    print(f"✅ Icône créée: {output_path}")

def main():
    """Crée les 3 icônes nécessaires"""
    print("🎨 Création des icônes CVLM...\n")
    
    # Vérifier que PIL est installé
    try:
        from PIL import Image
    except ImportError:
        print("❌ Erreur: Pillow n'est pas installé")
        print("Installez-le avec: pip install Pillow")
        return
    
    # Créer le dossier icons s'il n'existe pas
    icons_dir = "extension/icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    # Créer les 3 tailles
    sizes = [
        (16, "icon16.png"),
        (48, "icon48.png"),
        (128, "icon128.png")
    ]
    
    for size, filename in sizes:
        output_path = os.path.join(icons_dir, filename)
        create_icon(size, output_path)
    
    print("\n🎉 Toutes les icônes ont été créées dans extension/icons/")
    print("\n💡 Conseil: Pour des icônes plus professionnelles, utilisez:")
    print("   - Canva: https://www.canva.com")
    print("   - Figma: https://www.figma.com")
    print("   - Favicon.io: https://favicon.io/favicon-generator/")

if __name__ == "__main__":
    main()