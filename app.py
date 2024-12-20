import os
from flask import Flask, request, jsonify
import cv2
import pytesseract
from werkzeug.utils import secure_filename
import re
from flask_cors import CORS

# Configurez le chemin vers Tesseract OCR si nécessaire
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Modifier selon votre chemin

# Initialisation de Flask
app = Flask(__name__)
CORS(app)

# Configuration du dossier pour stocker les images uploadées
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fonction pour nettoyer et formater les données extraites par OCR pour l'anglais
def clean_text(data):
    """
    Nettoyer et formater les données extraites par OCR (anglais).
    """
    # Supprimer les espaces multiples, caractères inutiles
    data = re.sub(r'\s+', ' ', data)  # Remplacer plusieurs espaces par un seul
    data = re.sub(r'[^\w\u0600-\u06FF\s:/.-]', '', data)  # Supprimer les caractères non désirés sauf l'arabe

    # Séparer par lignes logiques si possible
    lines = data.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()  # Supprimer les espaces au début/fin de ligne
        if line:  # Ignorer les lignes vides
            cleaned_lines.append(line)

    # Retourner les lignes sous forme de texte formaté
    return '\n'.join(cleaned_lines)

# Fonction pour nettoyer et formater les données extraites par OCR pour l'arabe
def clean_text_arabic(data):
    """
    Nettoyer et formater les données extraites par OCR (arabe).
    """
    # Supprimer les espaces multiples
    data = re.sub(r'\s+', ' ', data)  # Remplacer plusieurs espaces par un seul

    # Supprimer les caractères non arabes ou non nécessaires
    # Nous voulons garder les caractères arabes, les espaces, et les signes de ponctuation standard
    data = re.sub(r'[^\u0600-\u06FF\s,:;!?.-]', '', data)  # Garder uniquement les caractères arabes et les ponctuations de base

    # Supprimer les espaces en trop au début et à la fin
    data = data.strip()

    # Retourner les lignes sous forme de texte formaté
    return data

# Fonction pour traiter l'image avec OCR
def process_cin_image(image_path, lang):
    # Charger l'image
    img = cv2.imread(image_path)

    # Convertir en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Améliorer l'image (optionnel : binarisation, réduction de bruit)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Effectuer l'OCR
    raw_data = pytesseract.image_to_string(gray, lang=lang, config='--psm 6')

    # Nettoyer et formater les données
    if lang == 'ara':  # Si la langue est arabe, appliquer le nettoyage spécifique pour l'arabe
        cleaned_data = clean_text_arabic(raw_data)
    else:  # Sinon, appliquer le nettoyage standard
        cleaned_data = clean_text(raw_data)

    # Supprimer l'image après traitement
    os.remove(image_path)

    return cleaned_data

# Route pour extraire les données en anglais
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "Aucune image n'a été envoyée"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    # Sauvegarde du fichier
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Traitement OCR
    extracted_data = process_cin_image(file_path, lang='eng')
    return jsonify({"data": extracted_data})

# Route pour extraire les données en arabe
@app.route('/upload_arabic', methods=['POST'])
def upload_image_arabic():
    if 'image' not in request.files:
        return jsonify({"error": "Aucune image n'a été envoyée"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    # Sauvegarde du fichier
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Traitement OCR pour les données en arabe
    extracted_data_arabic = process_cin_image(file_path, lang='ara')
    return jsonify({"data_arabic": extracted_data_arabic})

# Route pour extraire les données combinées (anglais + arabe)
@app.route('/upload_combined', methods=['POST'])
def upload_image_combined():
    if 'image' not in request.files:
        print("Erreur : Pas d'image dans la requête")
        return jsonify({"error": "Aucune image n'a été envoyée"}), 400

    file = request.files['image']
    if file.filename == '':
        print("Erreur : Aucune image sélectionnée")
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    # Sauvegarde et traitement de l'image
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    print(f"Fichier sauvegardé à : {file_path}")

    # Traitement OCR
    extracted_data_combined = process_cin_image(file_path, lang='ara+eng')
    return jsonify({"data_combined": extracted_data_combined})

# Lancer le serveur Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
