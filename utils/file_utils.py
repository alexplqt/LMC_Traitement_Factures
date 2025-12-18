"""
Utilitaires pour la gestion des fichiers.
"""

import os
import shutil
from datetime import datetime

def setup_directories(base_path="data"):
    """Crée la structure de répertoires nécessaire."""
    directories = [
        os.path.join(base_path, "input"),
        os.path.join(base_path, "processed"),
        os.path.join(base_path, "lcr_processed"),
        os.path.join(base_path, "unprocessed"),
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
        # Créer un fichier .gitkeep si le dossier est vide
        gitkeep_path = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                pass
    
    return directories

def clear_directory(directory):
    """Supprime tous les fichiers d'un répertoire."""
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Erreur lors de la suppression de {file_path}: {e}')

def save_uploaded_files(uploaded_files, save_dir):
    """Sauvegarde les fichiers uploadés dans Streamlit."""
    saved_files = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_files.append(uploaded_file.name)
    return saved_files

def get_file_stats(directory):
    """Retourne des statistiques sur les fichiers d'un répertoire."""
    if not os.path.exists(directory):
        return 0, []
    
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f != '.gitkeep']
    return len(files), files