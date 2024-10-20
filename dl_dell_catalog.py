#================================
# Date : 20/10/2024
# Autor : Benjamin DORIER
# Comment : dl le catalog dell , rechercher un modele de server et DL tous les drivers 
#================================

#================================
# IMPORT
#================================

import os
import requests
import gzip
import shutil
import xml.etree.ElementTree as ET


# URL du fichier compressé contenant le catalogue de drivers
URL = 'https://downloads.dell.com/catalog/Catalog.gz'


# Fonction pour télécharger et décompresser le fichier Catalog.gz
def download_and_extract_catalog(url, dest_folder="catalog"):
    catalog_path = os.path.join(dest_folder, "Catalog.gz")
    extracted_path = os.path.join(dest_folder, "Catalog.xml")
    
    os.makedirs(dest_folder, exist_ok=True)
    
    # Télécharger le fichier Catalog.gz
    try:
        print(f"Téléchargement de {url}...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(catalog_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        print(f"Fichier téléchargé avec succès : {catalog_path}")
        
        # Décompresser le fichier Catalog.gz
        with gzip.open(catalog_path, 'rb') as f_in:
            with open(extracted_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"Fichier décompressé : {extracted_path}")
        
        return extracted_path
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement ou de la décompression : {e}")
        return None



# Fonction pour parser le fichier XML et trouver le systemID pour un modèle donné
def find_systemID(catalog_file, model_name):
    tree = ET.parse(catalog_file)
    root = tree.getroot()

    # Parcourir tous les systèmes dans le fichier XML
    for system in root.findall(".//Model"):
        model = system.find('Display').text
        if model == model_name:
            systemID = system.get('systemID')
            print(f"Modèle {model_name} trouvé avec systemID : {systemID}")
            return systemID
    print(f"Modèle {model_name} non trouvé.")
    return None


# Fonction pour extraire et lister les drivers associés à un systemID donné
def list_drivers(catalog_file, systemID):
    tree = ET.parse(catalog_file)
    root = tree.getroot()

    drivers = []

    # Récupérer la baseLocation depuis le manifeste
    base_location = root.attrib.get("baseLocation")

    # Parcourir les SoftwareComponents et les bundles pour trouver ceux qui correspondent au systemID
    for component in root.findall(".//SoftwareComponent"):
        for system in component.findall(".//Model"):
            if system.get('systemID') == systemID:
                driver_path = component.get('path')
                full_url = f"/{driver_path}"
                drivers.append(full_url)
    
    return drivers


# Fonction pour recréer l'arborescence de dossiers et télécharger les fichiers
def download_drivers(drivers, base_url, download_path):
    for driver_path in drivers:
        # Construire le chemin complet local en recréant l'arborescence
        local_path = os.path.join(download_path, os.path.dirname(driver_path))
        print(f"download_path : {download_path}")
        print(f"driver_path : {driver_path}")
        print(f"local_path : {local_path}")
        
        local_path = local_path.replace('/', '\\')
        final_path = f"{download_path}{local_path}"
        print(f"final_path : {final_path}")
        os.makedirs(final_path, exist_ok=True)  # Créer l'arborescence si elle n'existe pas

        # Télécharger le fichier
        driver_url = f"{base_url}/{driver_path}"
        driver_name = os.path.basename(driver_path)
        file_path = os.path.join(final_path, driver_name)

        try:
            print(f"Téléchargement de {driver_name} depuis {driver_url}")
            with requests.get(driver_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"{driver_name} téléchargé avec succès.")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du téléchargement de {driver_name} : {e}")

def main():
    # model_name = input("Entrez le nom du modèle (SystemID) : ")
    model_name = "R740"
    base_url = "https://downloads.dell.com"  # Base de l'URL de téléchargement
    
    catalog_file = download_and_extract_catalog(URL)


    # Trouver le systemID associé au modèle
    systemID = find_systemID(catalog_file, model_name)
    if not systemID:
        return
    
    # Lister les drivers associés à ce systemID
    drivers = list_drivers(catalog_file, systemID)
    
    if drivers:
        # Afficher un résumé des drivers
        print(f"\nListe des drivers pour {model_name} :")
        for driver in drivers:
            print(f"- {driver}")
        
        # Télécharger les drivers
        download_path = os.path.join("downloads", model_name)
        download_drivers(drivers, base_url, download_path)
    else:
        print(f"Aucun driver trouvé pour le modèle {model_name}.")

if __name__ == "__main__":
    main()
