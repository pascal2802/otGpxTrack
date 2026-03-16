import pandas as pd
from fitparse import FitFile
import tkinter as tk
from tkinter import filedialog
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np


def semicircles_to_deg(semicircles):
    """Conversion du format propriétaire Garmin (semicircles) en degrés décimaux."""
    return semicircles * (180.0 / 2**31) if semicircles else None


def extraire_donnees_fit(chemin_fit):
    """Décrypte le fichier binaire FIT et calcule les deux flux de vitesse."""
    fitfile = FitFile(chemin_fit)
    data = []

    print(f"Analyse du fichier binaire : {os.path.basename(chemin_fit)}...")

    for record in fitfile.get_messages("record"):
        v = record.get_values()
        if all(k in v for k in ("position_lat", "position_long", "timestamp")):
            data.append(
                {
                    "t": v.get("timestamp"),
                    "lat": semicircles_to_deg(v.get("position_lat")),
                    "lon": semicircles_to_deg(v.get("position_long")),
                    # Vitesse 'speed' enregistrée par la puce (Doppler)
                    "v_doppler": (
                        v.get("speed", 0) * 1.94384 if v.get("speed") is not None else 0
                    ),
                }
            )

    df = pd.DataFrame(data).sort_values("t").reset_index(drop=True)

    # --- CALCUL DE LA VITESSE PAR POSITION (FLUX SECONDAIRE) ---
    df["dt"] = df["t"].diff().dt.total_seconds()

    # Calcul de distance par projection locale
    lat_to_m = 111111
    d_lat = df["lat"].diff() * lat_to_m
    d_lon = df["lon"].diff() * lat_to_m * np.cos(np.radians(df["lat"]))
    dist_inst = np.sqrt(d_lat**2 + d_lon**2)

    # Vitesse recalculée (kts) et Distance cumulée (m)
    df["v_pos"] = (dist_inst / df["dt"]) * 1.94384
    df["dist_cum"] = dist_inst.fillna(0).cumsum()

    # Calcul de l'écart de précision (Bruit GPS)
    df["ecart"] = df["v_doppler"] - df["v_pos"]

    return df


def generer_rapport_comparatif():
    root = tk.Tk()
    root.withdraw()
    chemin = filedialog.askopenfilename(
        title="Sélectionner fichier .FIT Garmin", filetypes=[("FIT files", "*.fit")]
    )
    if not chemin:
        return

    df = extraire_donnees_fit(chemin)
    nom_pdf = chemin.replace(".fit", "_Analyse_Expert.pdf")

    with PdfPages(nom_pdf) as pdf:
        print("Génération du rapport PDF...")

        # --- PAGE 1 : COMPARAISON DES FLUX ET STATISTIQUES ---
        fig1 = plt.figure(figsize=(8.27, 11.69))

        ax1 = fig1.add_subplot(3, 1, 1)
        ax1.plot(
            df["v_doppler"], label="Flux Doppler (Précis)", color="#2ecc71", linewidth=1
        )
        ax1.plot(
            df["v_pos"],
            label="Flux Position (Bruité)",
            color="#e74c3c",
            alpha=0.3,
            linestyle="--",
        )
        ax1.set_title("Comparaison des flux de vitesse (kts)")
        ax1.set_ylabel("Noeuds")
        ax1.legend(loc="upper right", fontsize="x-small")
        ax1.grid(True, alpha=0.15)

        ax2 = fig1.add_subplot(3, 1, 2)
        ax2.fill_between(
            range(len(df)),
            df["ecart"],
            color="#9b59b6",
            alpha=0.2,
            label="Delta Doppler/Pos",
        )
        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.set_title("Analyse du bruit de positionnement")
        ax2.set_ylabel("Écart (kts)")
        ax2.grid(True, alpha=0.1)

        v10_max = df["v_doppler"].rolling(10).mean().max()
        v5_max = df["v_doppler"].rolling(5).mean().max()
        bruit_moyen = df["ecart"].abs().mean()

        stats_txt = (
            f"--- RÉSULTATS EXPERTS (DONNÉES NATIVES .FIT) ---\n\n"
            f"MEILLEUR V10 (10s moy.) : {v10_max:.2f} kts\n"
            f"MEILLEUR V5  (5s moy.)  : {v5_max:.2f} kts\n"
            f"VMAX INSTANTANÉE (DOPPLER) : {df['v_doppler'].max():.2f} kts\n\n"
            f"INDICE DE FIABILITÉ GPS :\n"
            f"Écart moyen Doppler/Position : {bruit_moyen:.3f} kts\n"
            f"Distance totale parcourue : {df['dist_cum'].max()/1000:.2f} km\n\n"
            f"Note technique :\n"
            f"Le Doppler est la mesure de référence. Un écart faible (<0.2 kts)\n"
            f"indique une excellente réception satellite durant la session."
        )

        fig1.text(
            0.1,
            0.32,
            stats_txt,
            fontsize=10,
            family="monospace",
            va="top",
            bbox=dict(facecolor="none", edgecolor="gray", alpha=0.2),
        )

        pdf.savefig()
        plt.close()

        # --- PAGE 2 : FOCUS SUR LE MEILLEUR RUN DE 500m ---
        best_v, idx_s, idx_e = 0, 0, 0
        for i in range(len(df)):
            d0 = df.iloc[i]["dist_cum"]
            target = df["dist_cum"] >= d0 + 500
            if target.any():
                j = target.idxmax()
                v_moy = df.iloc[i:j]["v_doppler"].mean()
                if v_moy > best_v:
                    best_v, idx_s, idx_e = v_moy, i, j

        fig2 = plt.figure(figsize=(8.27, 11.69))
        ax3 = fig2.add_subplot(2, 1, 1)
        run = df.iloc[idx_s:idx_e]
        ax3.plot(
            run["v_doppler"], color="#2196F3", label="Vitesse Doppler", linewidth=2
        )
        ax3.fill_between(run.index, run["v_doppler"], color="#2196F3", alpha=0.1)
        ax3.set_title(f"Analyse du meilleur 500m : {best_v:.2f} kts")
        ax3.set_ylabel("Vitesse (kts)")
        ax3.set_xlabel("Points d'enregistrement")
        ax3.legend()
        ax3.grid(True, alpha=0.2)

        pdf.savefig()
        plt.close()

    print(f"Rapport généré avec succès : {nom_pdf}")


if __name__ == "__main__":
    generer_rapport_comparatif()
