"""Pilot veri seti (olaylar_v02.csv) üzerinde H1, H3 ve H4 testleri.

H1: Günlük olay sayısı ~ kriz sonrası + kriz sabit etkileri  (Poisson GLM, kesintili zaman serisi)
    Ana model seviye değişimini ölçer; ek model eğim değişimini de içerir.
H3: Kriz öncesi/sonrası yönlü saldırgan→hedef ülke ağları; yoğunluk, derece ve arasındalık merkeziliği.
H4: Günlük Goldstein ve ton → ertesi günlerdeki karşı tarafa yönelik saldırı sayısı (Granger, 1–7 gün).
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import networkx as nx
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.tsa.stattools import grangercausalitytests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
OUT = ROOT / "outputs"
KRIZ = {"rusya_2015": ("2015-11-24", "RUS", "RU"), "hollanda_2017": ("2017-03-11", "NLD", "NL"),
        "barispinari_2019": ("2019-10-09", "USA", "US")}


def gunluk_panel(s):
    satir = []
    for k in KRIZ:
        for g in range(-60, 61):
            x = s[(s.kriz == k) & (s.gun_farki == g)]
            satir.append(dict(kriz=k, gun=g, sonra=int(g >= 0), sonra_gun=max(g, 0),
                              olay=len(x), ikili=int((x.kriz_ikilisi == "evet").sum())))
    return pd.DataFrame(satir)


def h1(panel):
    print("=" * 70 + "\nH1 — Poisson kesintili zaman serisi (363 gün, 3 kriz)\n" + "=" * 70)
    sonuc = []
    for y in ["olay", "ikili"]:
        # Barış Pınarı'nda hiç olay yok; sabit etkisi tanımsız olacağından modelden çıkar
        d = panel[panel.groupby("kriz")[y].transform("sum") > 0]
        once_n = int(d[d.sonra == 0][y].sum())
        if once_n == 0:
            # Tam ayrışma: kriz öncesi hiç olay yok → Poisson MLE sonsuza gider.
            # Eşit uzunluklu pencerelerde kesin koşullu test kullanılır.
            from scipy.stats import binomtest
            sonra_n = int(d[d.sonra == 1][y].sum())
            p = binomtest(sonra_n, sonra_n, 0.5, alternative="greater").pvalue
            print(f"\n[{y}] kriz öncesi 0, sonrası {sonra_n} olay → tam ayrışma; kesin koşullu test p = {p:.4f}")
            sonuc.append(dict(bagimli=y, kriz_sayisi=d.kriz.nunique(), olay=sonra_n, irr="tanımsız (0 → %d)" % sonra_n,
                              ga_alt="", ga_ust="", p=round(p, 4), asiri_yayilim=""))
            continue
        m = smf.glm(f"{y} ~ sonra + C(kriz)", data=d, family=sm.families.Poisson()).fit()
        irr = np.exp(m.params["sonra"])
        ci = np.exp(m.conf_int().loc["sonra"])
        disp = m.pearson_chi2 / m.df_resid
        print(f"\n[{y}] kriz sayısı={d.kriz.nunique()}, gün={len(d)}, olay={int(d[y].sum())}")
        print(f"  IRR (kriz sonrası) = {irr:.2f}  %95 GA [{ci[0]:.2f}, {ci[1]:.2f}]  p = {m.pvalues['sonra']:.4f}")
        print(f"  aşırı yayılım (Pearson χ²/sd) = {disp:.2f}")
        sonuc.append(dict(bagimli=y, kriz_sayisi=d.kriz.nunique(), olay=int(d[y].sum()), irr=round(irr, 2),
                          ga_alt=round(ci[0], 2), ga_ust=round(ci[1], 2), p=round(m.pvalues["sonra"], 4),
                          asiri_yayilim=round(disp, 2)))
        if y == "olay":
            # Eğim değişimi: kriz sonrası günlerin doğrusal etkisi
            m2 = smf.glm(f"{y} ~ gun + sonra + sonra_gun + C(kriz)", data=d, family=sm.families.Poisson()).fit()
            print(f"  [eğim modeli] seviye IRR={np.exp(m2.params['sonra']):.2f} (p={m2.pvalues['sonra']:.3f}), "
                  f"eğim değişimi IRR/gün={np.exp(m2.params['sonra_gun']):.3f} (p={m2.pvalues['sonra_gun']:.3f})")
    pd.DataFrame(sonuc).to_csv(P / "h1_poisson.csv", index=False)


TAKMA_AD = {"ayyildiz tim": "Ayyıldız Tim", "ayyıldız tim": "Ayyıldız Tim",
            "the börteçine cyber team": "Börteçine Siber Tim", "börteçine siber tim": "Börteçine Siber Tim",
            "turk hack team": "Turk Hack Team", "aslan neferler tim": "Aslan Neferler Tim",
            "akincilar": "Akıncılar"}


def grup_adi(r):
    """Farklı kaynaklardaki yazım farklarını tek bir grup adında birleştirir."""
    ham = "" if pd.isna(r.saldirgan) else str(r.saldirgan).split("(")[0].strip()
    if ham in ("", "?"):
        return "kimliği belirsiz Türk grup" if "TR" in str(r.saldirgan_ulke) else "bilinmeyen"
    return TAKMA_AD.get(ham.lower(), ham)


def ag_kur(x):
    G = nx.DiGraph()
    for _, r in x.iterrows():
        kaynak = grup_adi(r)
        hu = "?" if pd.isna(r.hedef_ulke) else str(r.hedef_ulke)
        for hedef in hu.replace(">1", "çok_ülke").split(";"):
            hedef = hedef.strip() or "?"
            if G.has_edge(kaynak, hedef):
                G[kaynak][hedef]["weight"] += 1
            else:
                G.add_edge(kaynak, hedef, weight=1)
            G.nodes[kaynak]["tur"] = "saldirgan"
            G.nodes[hedef]["tur"] = "hedef"
    return G


def h3(s):
    print("\n" + "=" * 70 + "\nH3 — Saldırgan→hedef ülke ağları\n" + "=" * 70)
    satir, aglar = [], {}
    for donem, x in [("once", s[s.gun_farki < 0]), ("sonra", s[s.gun_farki >= 0])]:
        G = ag_kur(x)
        aglar[donem] = G
        hedefler = [n for n, d in G.nodes(data=True) if d.get("tur") == "hedef"]
        gelen = sorted(((G.in_degree(n, weight="weight"), n) for n in hedefler), reverse=True)
        # Hedef merkezileşmesi: en çok saldırı alan hedefin toplam içindeki payı
        toplam = sum(v for v, _ in gelen) or 1
        satir.append(dict(donem=donem, olay=len(x), dugum=G.number_of_nodes(), kenar=G.number_of_edges(),
                          yogunluk=round(nx.density(G), 3), en_cok_hedef=gelen[0][1] if gelen else "",
                          en_cok_hedef_payi=round(gelen[0][0] / toplam, 2) if gelen else 0))
        print(f"\n[{donem}] olay={len(x)} düğüm={G.number_of_nodes()} kenar={G.number_of_edges()} "
              f"yoğunluk={nx.density(G):.3f}")
        print("  en çok saldırı alan hedefler:", gelen[:4])
    pd.DataFrame(satir).to_csv(P / "h3_ag_olcutleri.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, (donem, G) in zip(axes, aglar.items()):
        pos = nx.spring_layout(G, seed=3, k=1.2)
        renk = ["#c0392b" if G.nodes[n].get("tur") == "hedef" else "#2f6db3" for n in G.nodes]
        boyut = [300 + 250 * G.in_degree(n, weight="weight") for n in G.nodes]
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=renk, node_size=boyut, alpha=0.85)
        nx.draw_networkx_edges(G, pos, ax=ax, width=[1 + G[u][v]["weight"] for u, v in G.edges],
                               arrowsize=12, edge_color="#777", connectionstyle="arc3,rad=0.08")
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=7)
        ax.set_title(f"Kriz {'öncesi' if donem == 'once' else 'sonrası'} (60 gün) — {G.number_of_edges()} bağ",
                     fontsize=10)
        ax.axis("off")
    fig.suptitle("Saldırgan grup (mavi) → hedef ülke (kırmızı) ağı, üç kriz birlikte; düğüm boyutu = alınan saldırı",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "h3_ag.png", dpi=150)


def h4(s):
    print("\n" + "=" * 70 + "\nH4 — Granger: gerginlik → karşı tarafa yönelik saldırılar (Rusya penceresi)\n" + "=" * 70)
    k, (tarih, iso3, iso2) = "rusya_2015", KRIZ["rusya_2015"]
    g = pd.read_csv(P / f"gdelt_gunluk_2015_{iso3}.csv")[["gun", "goldstein", "ton"]]
    y = (s[(s.kriz == k) & (s.kriz_ikilisi == "evet")].groupby("gun_farki").size()
         .reindex(range(-60, 61), fill_value=0).rename("saldiri"))
    d = g.set_index("gun").join(y, how="right").interpolate().bfill()
    d["gerginlik"] = -d.goldstein   # yüksek değer = daha çatışmacı
    satir = []
    for x in ["gerginlik", "ton"]:
        seri = d[["saldiri", x]].copy()
        if x == "ton":
            seri[x] = -seri[x]      # daha olumsuz ton = daha yüksek gerginlik
        sonuc = grangercausalitytests(seri, maxlag=7)
        for lag, r in sonuc.items():
            f, p = r[0]["ssr_ftest"][:2]
            satir.append(dict(gosterge=x, gecikme=lag, F=round(f, 2), p=round(p, 4)))
    t = pd.DataFrame(satir)
    t.to_csv(P / "h4_granger.csv", index=False)
    print(t.pivot(index="gecikme", columns="gosterge", values="p").rename(columns=lambda c: f"p ({c})").to_string())
    # Eş zamanlılık: gerginlik serisindeki kırılma günü ile ilk saldırı
    print(f"\n  Rusya: ilk karşı tarafa yönelik saldırı günü = {int(y[y > 0].index.min())}, "
          f"Goldstein'ın ilk kez -1'in altına düştüğü gün = {int(d[d.goldstein < -1].index[d[d.goldstein < -1].index >= -5].min())}")


def main():
    d = pd.read_csv(P / "olaylar_v02.csv")
    s = d[d.sayima_dahil == "evet"].copy()
    panel = gunluk_panel(s)
    panel.to_csv(P / "gunluk_panel.csv", index=False)
    h1(panel)
    h3(s)
    h4(s)


if __name__ == "__main__":
    main()
