import pandas as pd
from fitparse import FitFile
import tkinter as tk
from tkinter import filedialog
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np


def semicircles_to_deg(semicircles):
    """Conversion des semicircles Garmin en degrés décimaux."""
    return semicircles * (180.0 / 2**31) if semicircles else None


def extraire_donnees_fit(chemin_fit):
    """Extraction des données avec gestion du fail-safe Doppler."""
    fitfile = FitFile(chemin_fit)
    data = []
    print(f"Extraction des données natives : {os.path.basename(chemin_fit)}...")

    for record in fitfile.get_messages("record"):
        v = record.get_values()
        if all(k in v for k in ("position_lat", "position_long", "timestamp")):
            # Priorité à la vitesse 'enhanced_speed' (Doppler haute résolution)
            v_ms = v.get("enhanced_speed") or v.get("speed") or 0
            data.append(
                {
                    "t": v.get("timestamp"),
                    "lat": semicircles_to_deg(v.get("position_lat")),
                    "lon": semicircles_to_deg(v.get("position_long")),
                    "v_doppler": v_ms * 1.94384,
                }
            )

    df = pd.DataFrame(data).sort_values("t").reset_index(drop=True)
    df["dt"] = df["t"].diff().dt.total_seconds()

    # Calcul de la vitesse positionnelle pour comparaison
    lat_to_m = 111111
    d_lat = df["lat"].diff() * lat_to_m
    d_lon = df["lon"].diff() * lat_to_m * np.cos(np.radians(df["lat"]))
    dist_inst = np.sqrt(d_lat**2 + d_lon**2)

    df["v_pos"] = (dist_inst / df["dt"]) * 1.94384
    df["dist_cum"] = dist_inst.fillna(0).cumsum()
    return df


def identifier_runs(df, seuil_vitesse=5.0, duree_min_points=10):
    """Découpe la session en segments (runs) dès que la vitesse dépasse le seuil."""
    df["is_run"] = df["v_doppler"] > seuil_vitesse
    # Création d'un ID unique pour chaque séquence continue de vitesse > seuil
    df["run_id"] = (df["is_run"] != df["is_run"].shift()).cumsum()

    runs = []
    for rid, group in df[df["is_run"]].groupby("run_id"):
        if len(group) >= duree_min_points:
            runs.append(group.copy())
    return runs


def tracer_page_run(pdf, df_run, num_run):
    """Génère une page PDF dédiée à un run spécifique."""
    fig = plt.figure(figsize=(8.27, 11.69))

    # 1. Carte zoomée du Run
    ax1 = fig.add_subplot(3, 1, 1)
    sc = ax1.scatter(
        df_run["lon"], df_run["lat"], c=df_run["v_doppler"], cmap="jet", s=15
    )
    plt.colorbar(sc, ax=ax1, label="kts")
    ax1.set_title(f"TRACÉ GPS - RUN #{num_run}")
    ax1.axis("equal")
    ax1.axis("off")  # Nettoyage de la carte

    # 2. Comparaison Doppler / Position sur le segment
    ax2 = fig.add_subplot(3, 1, 2)
    ax2.plot(
        df_run["t"],
        df_run["v_doppler"],
        label="Doppler (Précis)",
        color="#2ecc71",
        lw=2,
    )
    ax2.plot(
        df_run["t"],
        df_run["v_pos"],
        label="Position (Bruité)",
        color="#e74c3c",
        alpha=0.4,
        ls="--",
    )
    ax2.set_title("Profil de vitesse du run")
    ax2.set_ylabel("Noeuds (kts)")
    ax2.legend(loc="upper right", fontsize="small")
    ax2.grid(True, alpha=0.2)

    # 3. Calculs et Statistiques du Run
    v_moy = df_run["v_doppler"].mean()
    v_max = df_run["v_doppler"].max()
    dist_run = df_run["v_doppler"].count()  # Hypothèse 1 point = 1 sec
    duree_run = (df_run["t"].iloc[-1] - df_run["t"].iloc[0]).total_seconds()

    stats_txt = (
        f"--- ANALYSE DÉTAILLÉE DU RUN #{num_run} ---\n\n"
        f"Vitesse Moyenne : {v_moy:.2f} kts\n"
        f"Vitesse Max     : {v_max:.2f} kts\n"
        f"Durée du Run    : {duree_run:.0f} secondes\n"
        f"Début du Run    : {df_run['t'].iloc[0].strftime('%H:%M:%S')}\n\n"
        f"Note : Ce zoom permet de comparer la stabilité du flux Doppler\n"
        f"par rapport aux oscillations du calcul positionnel sur ce bord."
    )

    fig.text(
        0.1,
        0.28,
        stats_txt,
        fontsize=12,
        family="monospace",
        va="top",
        bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.5, pad=10),
    )

    pdf.savefig()
    plt.close()


def generer_rapport_multi_pages():
    root = tk.Tk()
    root.withdraw()
    chemin = filedialog.askopenfilename(
        title="Ouvrir fichier Garmin .FIT", filetypes=[("FIT files", "*.fit")]
    )
    if not chemin:
        return

    df = extraire_donnees_fit(chemin)
    runs = identifier_runs(df)
    nom_pdf = chemin.replace(".fit", "_Rapport_Complet_Runs.pdf")

    with PdfPages(nom_pdf) as pdf:
        print(f"Identification de {len(runs)} runs. Génération du rapport...")

        # --- PAGE DE GARDE ---
        fig_front = plt.figure(figsize=(8.27, 11.69))
        plt.text(
            0.5,
            0.7,
            "RAPPORT D'ANALYSE DOPPLER",
            ha="center",
            fontsize=22,
            weight="bold",
        )
        plt.text(
            0.5,
            0.65,
            f"Fichier : {os.path.basename(chemin)}",
            ha="center",
            fontsize=10,
            color="gray",
        )

        info_globale = (
            f"Distance Totale : {df['dist_cum'].max()/1000:.2f} km\n"
            f"Vitesse Max de la session : {df['v_doppler'].max():.2f} kts\n"
            f"Nombre de runs (>5kts) : {len(runs)}"
        )
        plt.text(0.5, 0.45, info_globale, ha="center", fontsize=14, linespacing=1.8)
        plt.axis("off")
        pdf.savefig()
        plt.close()

        # --- PAGES DES RUNS ---
        for i, run_df in enumerate(runs):
            tracer_page_run(pdf, run_df, i + 1)

    print(f"Analyse terminée avec succès : {nom_pdf}")


if __name__ == "__main__":
    generer_rapport_multi_pages()
