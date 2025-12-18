"""
Application Streamlit pour le traitement automatisé de factures.
"""

import streamlit as st
import pandas as pd
import os
import sys
import zipfile

# Configuration du chemin pour les imports
# Ajoute le répertoire courant au chemin Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.processor import FactureProcessor, DICT_FOURNI_CLE
    from utils.file_utils import setup_directories, save_uploaded_files, get_file_stats, clear_directory
except ImportError as e:
    st.error(f"Erreur d'import: {e}")
    st.info("Vérifiez que les fichiers suivants existent:")
    st.info("- src/__init__.py")
    st.info("- src/processor.py")
    st.info("- src/facture_functions.py")
    st.info("- utils/__init__.py")
    st.info("- utils/file_utils.py")
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="Traitement de Factures",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre de l'application
st.title("📄 Traitement Automatisé de Factures")
st.markdown("---")

# Initialisation des dossiers
BASE_DIR = "data"
INPUT_DIR = os.path.join(BASE_DIR, "input")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
LCR_DIR = os.path.join(BASE_DIR, "lcr_processed")
UNPROCESSED_DIR = os.path.join(BASE_DIR, "unprocessed")

# Création des dossiers
setup_directories(BASE_DIR)

# Sidebar (instructions + statistiques uniquement)
with st.sidebar:
    st.title("Informations")

    st.markdown("---")
    st.info(
        """
        **Instructions:**
        1. Uploader des factures PDF
        2. Lancer le traitement
        3. Télécharger les résultats (Excel + factures)
        """
    )

    # Statistiques
    st.markdown("---")
    st.subheader("📈 Statistiques")
    input_count, _ = get_file_stats(INPUT_DIR)
    processed_count, _ = get_file_stats(PROCESSED_DIR)
    lcr_count, _ = get_file_stats(LCR_DIR)
    unprocessed_count, _ = get_file_stats(UNPROCESSED_DIR)

    st.metric("Factures à traiter", input_count)
    st.metric("Factures traitées", processed_count)
    st.metric("Factures LCR", lcr_count)
    st.metric("Non traitées", unprocessed_count)


def create_results_archive(zip_path: str, excel_path: str, processed_dir: str, lcr_dir: str, unprocessed_dir: str):
    """Crée une archive ZIP contenant le fichier Excel et les dossiers processed, lcr_processed et unprocessed."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        # Ajouter le fichier Excel
        if os.path.exists(excel_path):
            archive.write(excel_path, arcname=os.path.basename(excel_path))

        # Ajouter récursivement le contenu des dossiers de factures
        for dir_path in [processed_dir, lcr_dir, unprocessed_dir]:
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # arcname = chemin relatif à partir de BASE_DIR (donc processed/..., lcr_processed/..., unprocessed/...)
                        arcname = os.path.relpath(file_path, start=BASE_DIR)
                        archive.write(file_path, arcname=arcname)

    return zip_path


# Page unique : Upload, traitement et résultats
st.header("Upload et Traitement des Factures")

col1, col2 = st.columns([2, 1])

with col1:
    # Section d'upload
    uploaded_files = st.file_uploader(
        "Sélectionnez les fichiers PDF à traiter",
        type=['pdf', 'PDF'],
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs fichiers PDF"
    )

    if uploaded_files:
        with st.spinner(f"Sauvegarde de {len(uploaded_files)} fichier(s)..."):
            saved_files = save_uploaded_files(uploaded_files, INPUT_DIR)
            st.success(f"{len(saved_files)} fichier(s) sauvegardé(s) avec succès!")

            # Afficher la liste des fichiers uploadés
            with st.expander("Voir les fichiers uploadés"):
                for file in saved_files:
                    st.write(f"📄 {file}")

with col2:
    # Boutons d'action
    st.subheader("Actions")

    if st.button("🚀 Lancer le traitement", type="primary", use_container_width=True):
        if get_file_stats(INPUT_DIR)[0] == 0:
            st.warning("Aucun fichier à traiter. Veuillez uploader des factures d'abord.")
        else:
            with st.spinner("Traitement en cours..."):
                try:
                    # Nettoyage automatique des dossiers de sortie avant un nouveau traitement
                    clear_directory(PROCESSED_DIR)
                    clear_directory(LCR_DIR)
                    clear_directory(UNPROCESSED_DIR)

                    # Initialisation du processeur
                    processor = FactureProcessor(INPUT_DIR)

                    # Traitement
                    df, processed, unprocessed, processed_lcr = processor.process_directory()

                    # Déplacement des fichiers
                    processor.move_processed_files(PROCESSED_DIR, LCR_DIR, UNPROCESSED_DIR)

                    # Sauvegarde des résultats en session
                    st.session_state['results_df'] = df
                    st.session_state['processed_count'] = len(processed)
                    st.session_state['unprocessed_count'] = len(unprocessed)
                    st.session_state['processed_lcr_count'] = len(processed_lcr)
                    st.session_state['processed_files'] = processed
                    st.session_state['unprocessed_files'] = unprocessed
                    st.session_state['processed_lcr_files'] = processed_lcr

                    # Export des résultats
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"resultats_{timestamp}.xlsx"
                    processor.export_results(output_path)
                    st.session_state['output_path'] = output_path

                    st.success("Traitement terminé avec succès!")

                except Exception as e:
                    st.error(f"Erreur lors du traitement: {str(e)}")

    if st.button("🗑️ Vider les dossiers", type="secondary", use_container_width=True):
        with st.spinner("Nettoyage en cours..."):
            clear_directory(INPUT_DIR)
            clear_directory(PROCESSED_DIR)
            clear_directory(LCR_DIR)
            clear_directory(UNPROCESSED_DIR)
            st.success("Tous les dossiers ont été vidés!")
            # Rafraîchir la page
            st.rerun()

    # Liste des fournisseurs gérés
    with st.expander("📜 Voir la liste des fournisseurs pris en charge"):
        fournisseurs = sorted(DICT_FOURNI_CLE.keys())
        for f in fournisseurs:
            st.write(f"• {f}")


st.markdown("---")

# Affichage des résultats (si disponibles)
if 'results_df' in st.session_state and not st.session_state['results_df'].empty:
    df = st.session_state['results_df']

    st.subheader("📋 Détails des factures traitées")

    # Bouton unique pour télécharger Excel + dossiers de factures dans data/
    if 'output_path' in st.session_state and os.path.exists(st.session_state['output_path']):
        zip_name = "resultats_et_factures.zip"
        zip_path = os.path.join(BASE_DIR, zip_name)
        os.makedirs(BASE_DIR, exist_ok=True)
        zip_path = create_results_archive(
            zip_path,
            st.session_state['output_path'],
            PROCESSED_DIR,
            LCR_DIR,
            UNPROCESSED_DIR,
        )

        with open(zip_path, "rb") as f:
            zip_bytes = f.read()

        st.download_button(
            label="📥 Télécharger les résultats (Excel + dossiers de factures)",
            data=zip_bytes,
            file_name=zip_name,
            mime="application/zip",
            use_container_width=True,
        )

    # Tableau des résultats
    st.dataframe(df, use_container_width=True)

# CSS personnalisé
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stAlert {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)