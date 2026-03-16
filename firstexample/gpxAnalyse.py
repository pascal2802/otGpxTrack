#import tkinter as tk
#from tkinter import filedialog
import gpxpy
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.colors as colors
import numpy as np
gpxfile = "activity_19218242997.gpx"

def generate_ar1_error(n_points, sigma_tot=2.5, phi=0.9):
    """Génère une dérive d'erreur corrélée (Processus AR-1)."""
    sigma_w = sigma_tot * np.sqrt(1 - phi**2)
    errors = np.zeros(n_points)
    for t in range(1, n_points):
        errors[t] = phi * errors[t-1] + np.random.normal(0, sigma_w)
    return errors

def simulation_monte_carlo_ar1(segment_points, sigma_tot=2.5, phi=0.9, n_sims=1000):
    """Simule 1000 trajectoires plausibles avec calcul de sillage cumulé."""
    n_pts = len(segment_points)
    if n_pts < 2: return 0, 0, 0, []
    
    lat_to_m = 111111
    lon_to_m = 111111 * np.cos(np.radians(segment_points[0].latitude))
    
    x_ref = np.array([(p.longitude - segment_points[0].longitude) * lon_to_m for p in segment_points])
    y_ref = np.array([(p.latitude - segment_points[0].latitude) * lat_to_m for p in segment_points])
    t_ref = np.array([(p.time - segment_points[0].time).total_seconds() for p in segment_points])
    dt_total = t_ref[-1] - t_ref[0]
    
    v_simulees = []
    for _ in range(n_sims):
        err_x = generate_ar1_error(n_pts, sigma_tot, phi)
        err_y = generate_ar1_error(n_pts, sigma_tot, phi)
        # Calcul de la distance cumulée réelle du sillage bruité
        dist_sim = np.sum(np.sqrt(np.diff(x_ref + err_x)**2 + np.diff(y_ref + err_y)**2))
        v_simulees.append((dist_sim / dt_total) * 1.94384)
            
    return np.mean(v_simulees), np.percentile(v_simulees, 2.5), np.percentile(v_simulees, 97.5), v_simulees

def calculer_vitesse_distance_ar1(df, gpx_points, dist_cible, n_sims=1000):
    best_v_obs = 0
    best_indices = (0, 0)
    for i in range(len(df)):
        d_start = df.iloc[i]['dist_cum']
        mask = df['dist_cum'] >= d_start + dist_cible
        if mask.any():
            j = df[mask].index[0]
            dt = (df.iloc[j]['heure'] - df.iloc[i]['heure']).total_seconds()
            if dt > 0:
                v = (dist_cible / dt) * 1.94384
                if v > best_v_obs:
                    best_v_obs, best_indices = v, (i, j)
    if best_v_obs == 0: return 0, 0, 0, []
    return simulation_monte_carlo_ar1(gpx_points[best_indices[0] : best_indices[1]+1], n_sims=n_sims)

def generer_rapport_fusionne():
    #root = tk.Tk()
    #root.withdraw()
    #chemin = filedialog.askopenfilename(title="Ouvrir trace GPX", filetypes=[("GPX", "*.gpx")])
    chemin = gpxfile
    if not chemin: return

    with open(chemin, 'r') as f:
        gpx = gpxpy.parse(f)

    pts_gpx, data = [], []
    for track in gpx.tracks:
        for seg in track.segments:
            pts_gpx.extend(seg.points)
            for i in range(1, len(seg.points)):
                p1, p2 = seg.points[i-1], seg.points[i]
                dt = (p2.time - p1.time).total_seconds()
                if dt > 0:
                    d = p2.distance_3d(p1)
                    data.append({'heure': p2.time, 'lat': p2.latitude, 'lon': p2.longitude, 'v_obs': (d/dt)*1.94384, 'dist': d})

    df = pd.DataFrame(data)
    df['dist_cum'] = df['dist'].cumsum()
    df['t_sec'] = (df['heure'] - df['heure'].min()).dt.total_seconds()
    nom_pdf = chemin.replace(".gpx", "_Rapport_Expert.pdf")

    with PdfPages(nom_pdf) as pdf:
        print("Calculs et Simulations AR-1 en cours...")
        
        # --- PAGE 1 : SYNTHESE ---
        df['v_10s_roll'] = df['v_obs'].rolling(window=10).mean()
        idx_v10 = df['v_10s_roll'].idxmax()
        v10_m, v10_l, v10_h, v10_all = simulation_monte_carlo_ar1(pts_gpx[idx_v10-10 : idx_v10])
        v500_m, v500_l, v500_h, _ = calculer_vitesse_distance_ar1(df, pts_gpx, 500)

        fig1 = plt.figure(figsize=(8.27, 11.69))
        ax1 = fig1.add_subplot(2, 1, 1)
        sc = ax1.scatter(df['lon'], df['lat'], c=df['v_obs'], cmap='jet', s=2)
        plt.colorbar(sc, ax=ax1, label='kts')
        ax1.set_title(f"SYNTHÈSE SESSION : {os.path.basename(chemin)}")
        ax1.axis('equal')
        
        res_txt = (f"--- RÉSULTATS CERTIFIÉS (AR-1 / 1000 SIMS) ---\n\n"
                   f"MEILLEUR V10 (10s) :\n Probable: {v10_m:.2f} kts | IC95%: [{v10_l:.2f}-{v10_h:.2f}]\n\n"
                   f"MEILLEUR 500m (Sillage) :\n Probable: {v500_m:.2f} kts | IC95%: [{v500_l:.2f}-{v500_h:.2f}]\n\n"
                   f"Vmax observée : {df['v_obs'].max():.2f} kts\n"
                   f"Distance totale : {df['dist'].sum()/1000:.2f} km")
        fig1.text(0.1, 0.40, res_txt, fontsize=11, family='monospace', va='top')
        pdf.savefig()
        plt.close()

        # --- PAGE 2 : COMPARATIF TOP 5 ---
        top_runs, df_temp = [], df.copy()
        for _ in range(5):
            if len(df_temp) < 10: break
            df_temp['v_10s_roll'] = df_temp['v_obs'].rolling(window=10).mean()
            if df_temp['v_10s_roll'].isnull().all(): break
            idx = df_temp['v_10s_roll'].idxmax()
            run = df_temp.loc[idx-9:idx].copy()
            top_runs.append({'h': run.iloc[0]['heure'].strftime('%H:%M:%S'), 'v': df_temp.loc[idx, 'v_10s_roll'], 'v_pts': run['v_obs'].values})
            df_temp.drop(index=range(max(0, idx-10), min(len(df_temp), idx+10)), inplace=True, errors='ignore')
            df_temp.reset_index(drop=True, inplace=True)

        fig2 = plt.figure(figsize=(8.27, 11.69))
        ax2 = fig2.add_subplot(2, 1, 1)
        for i, r in enumerate(top_runs):
            ax2.plot(range(10), r['v_pts'], label=f"#{i+1} ({r['h']}) - {r['v']:.2f} kts", linewidth=2)
        ax2.set_title("COMPARAISON DES TOP 5 RUNS (10s)")
        ax2.set_xlabel("Secondes")
        ax2.set_ylabel("Vitesse (kts)")
        ax2.legend(fontsize='small', loc='lower right')
        ax2.grid(True, alpha=0.3)
        pdf.savefig()
        plt.close()

        # --- PAGE 3 : AUDIT MONTE CARLO ---
        fig3 = plt.figure(figsize=(8.27, 11.69))
        ax3 = fig3.add_subplot(2, 1, 1)
        ax3.hist(v10_all, bins=50, color='lightcoral', edgecolor='black', alpha=0.6, density=True)
        ax3.axvline(v10_m, color='red', linestyle='--', label='Moyenne Probable')
        ax3.axvline(v10_l, color='black', linestyle=':', label='Limites IC 95%')
        ax3.axvline(v10_h, color='black', linestyle=':')
        ax3.set_title("AUDIT STATISTIQUE DU MEILLEUR V10")
        ax3.set_xlabel("Vitesse Simulée (kts)")
        ax3.set_ylabel("Densité de Probabilité")
        ax3.legend()
        pdf.savefig()
        plt.close()

    print(f"Analyse terminée. Rapport fusionné : {nom_pdf}")

if __name__ == "__main__":
    generer_rapport_fusionne()
