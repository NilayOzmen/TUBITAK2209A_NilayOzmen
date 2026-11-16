"""Pilot veri seti (olaylar_v03.csv) üzerinde H1–H4 testleri.

H1: Günlük olay sayısı ~ kriz sonrası + kriz sabit etkileri  (Poisson GLM, kesintili zaman serisi)
    Ana model seviye değişimini ölçer; ek model eğim değişimini de içerir.
H2: Türkiye kaynaklı hacktivist saldırılarda karşı tarafı hedef alanların oranı, önce/sonra (Fisher kesin testi).
H3: Kriz öncesi/sonrası yönlü saldırgan→hedef ülke ağları; yoğunluk, derece ve arasındalık merkeziliği.
H4: Günlük gerginlik endeksi (Goldstein ve ton z-puanlarının ortalaması) ile iki gösterge ayrı ayrı →
    ertesi günlerdeki karşı tarafa yönelik saldırı sayısı (Granger, 1–7 gün), Rusya ve Hollanda pencereleri.
    Eşit ağırlık kontrolü: iki standart göstergeyle PCA'nın birinci bileşeni matematiksel olarak eşit ağırlığa denk
    düştüğünden, PCA endeksi üç göstergeyle (Goldstein, ton ve günlük çatışma olayı payı) kurulur ("endeks_pca").
    Barış Pınarı'nda saldırıların hedefi PYD/PKK olduğundan gerginlik Türkiye–Suriye ikilisiyle ölçülür;
    Türkiye–ABD ikilisi alternatif olarak raporlanır ("barispinari_2019_ABD").
    Ek analizler (h4_kriz_turu.csv, h4_havuz.csv):
      - Kriz türü: kriz öncesi 14 gündeki gerginlik eğilimi (endeks ~ gün, EKK). Eğim pozitif ve anlamlıysa
        kriz "tırmanan", değilse "ani" sayılır. Erken uyarı mantığı yalnızca tırmanan krizlerde beklenir.
      - Havuzlanmış model: üç kriz tek Poisson modelinde; günlük karşı tarafa saldırı ~ önceki 1–3 (ve 1–7)
        günün ortalama gerginliği + aynı günün gerginliği + kriz sonrası kukla + kriz sabit etkisi.
        Kriz sonrası kukla, kriz günündeki ortak şokun (gerginlik ve saldırıların birlikte sıçraması)
        gecikmeli gerginliğin etkisi gibi görünmesini önler.
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


def h2(s):
    from scipy.stats import fisher_exact
    print("\n" + "=" * 70 + "\nH2 — Hedef kayması (Türkiye kaynaklı hacktivist saldırılar, Fisher)\n" + "=" * 70)
    x = s[(s.aktor_turu == "hacktivist") & s.saldirgan_ulke.fillna("").str.contains("TR")]
    satir = []
    for k in list(KRIZ) + ["toplam"]:
        y = x if k == "toplam" else x[x.kriz == k]
        once, sonra = y[y.gun_farki < 0], y[y.gun_farki >= 0]
        a, b = int((once.kriz_ikilisi == "evet").sum()), len(once)
        c, d_ = int((sonra.kriz_ikilisi == "evet").sum()), len(sonra)
        p = fisher_exact([[c, d_ - c], [a, b - a]], alternative="greater")[1] if b + d_ else float("nan")
        satir.append(dict(kriz=k, once=f"{a}/{b}", sonra=f"{c}/{d_}", p=round(p, 4)))
        print(f"  {k:18s} önce {a}/{b}  sonra {c}/{d_}  p = {p:.4f}")
    pd.DataFrame(satir).to_csv(P / "h2_fisher.csv", index=False)


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


def z(x):
    return (x - x.mean()) / x.std()


def pca_endeks(df):
    """Standart göstergelerin korelasyon matrisinden birinci temel bileşen; ağırlıklar toplamı 1 olacak şekilde."""
    zz = df.apply(z)
    deger, vektor = np.linalg.eigh(np.corrcoef(zz.T.values))
    w = vektor[:, -1] * np.sign(vektor[:, -1].sum())
    w = w / w.sum()
    return zz.values @ w, dict(zip(df.columns, np.round(w, 3))), round(deger[-1] / deger.sum(), 3)


def h4(s):
    print("\n" + "=" * 70 + "\nH4 — Granger: gerginlik → karşı tarafa yönelik saldırılar\n" + "=" * 70)
    satir, pca_ozet, tur, havuz = [], [], [], []
    for etiket, k, yil, iso3 in [("rusya_2015", "rusya_2015", 2015, "RUS"),
                                 ("hollanda_2017", "hollanda_2017", 2017, "NLD"),
                                 ("barispinari_2019", "barispinari_2019", 2019, "SYR"),
                                 ("barispinari_2019_ABD", "barispinari_2019", 2019, "USA")]:
        g = pd.read_csv(P / f"gdelt_gunluk_{yil}_{iso3}.csv")[["gun", "goldstein", "ton", "catisma_orani"]]
        y = (s[(s.kriz == k) & (s.kriz_ikilisi == "evet")].groupby("gun_farki").size()
             .reindex(range(-60, 61), fill_value=0).rename("saldiri"))
        d = g.set_index("gun").join(y, how="right").interpolate().bfill()
        d["goldstein_g"] = -d.goldstein          # yüksek değer = daha çatışmacı
        d["ton_g"] = -d.ton                      # daha olumsuz ton = daha yüksek gerginlik
        d["endeks"] = (z(d.goldstein_g) + z(d.ton_g)) / 2
        d["endeks_pca"], agirlik, aciklanan = pca_endeks(d[["goldstein_g", "ton_g", "catisma_orani"]])
        d[["saldiri", "goldstein", "ton", "catisma_orani", "endeks", "endeks_pca"]].to_csv(P / f"gerginlik_endeksi_{etiket}.csv")
        print(f"\n[{etiket}] Türkiye–{iso3}, karşı tarafa yönelik saldırı: {int(y.sum())} ({int((y > 0).sum())} gün)")
        print(f"  PCA ağırlıkları {agirlik}, açıklanan varyans {aciklanan}; "
              f"eşit ağırlıklı endeksle korelasyon {d.endeks.corr(d.endeks_pca):.2f}")
        pca_ozet.append(dict(kriz=etiket, **{f"w_{a}": b for a, b in agirlik.items()}, aciklanan_varyans=aciklanan,
                             r_esit_endeks=round(d.endeks.corr(d.endeks_pca), 3)))
        for x in ["endeks", "endeks_pca", "goldstein_g", "ton_g"]:
            sonuc = grangercausalitytests(d[["saldiri", x]], maxlag=7)
            for lag, r in sonuc.items():
                f, p = r[0]["ssr_ftest"][:2]
                satir.append(dict(kriz=etiket, gosterge=x, gecikme=lag, F=round(f, 2), p=round(p, 4)))
        ilk = y[y > 0].index.min()
        esik = d.endeks[d.index >= -14]
        kirilma = int(esik[esik > 1].index.min()) if (esik > 1).any() else None
        print(f"  ilk karşı tarafa saldırı günü = {int(ilk)}, endeksin ilk kez +1 SS'yi aştığı gün (≥ -14) = {kirilma}")
        # Kriz türü: kriz öncesi 14 günde gerginlik tırmanıyor mu?
        on = d.loc[-14:-1]
        e = smf.ols("endeks ~ gun", data=on.rename_axis("gun").reset_index()).fit()
        fark = d.loc[-14:-1, "endeks"].mean() - d.loc[-60:-15, "endeks"].mean()
        tur.append(dict(kriz=etiket, egim_gunluk=round(e.params["gun"], 3), p_egim=round(e.pvalues["gun"], 4),
                        son14_eksi_onceki=round(fark, 2),
                        tur="tırmanan" if e.params["gun"] > 0 and e.pvalues["gun"] < 0.05 else "ani",
                        ilk_saldiri_gunu=int(ilk), endeks_ilk_1ss_gunu=kirilma))
        if etiket != "barispinari_2019_ABD":
            h = d[["saldiri", "endeks"]].copy()
            h["gecikme_1_3"] = h.endeks.shift(1).rolling(3).mean()
            h["gecikme_1_7"] = h.endeks.shift(1).rolling(7).mean()
            h["sonra"] = (h.index >= 0).astype(int)
            h["kriz"] = k
            havuz.append(h)
    t = pd.DataFrame(satir)
    t.to_csv(P / "h4_granger.csv", index=False)
    pd.DataFrame(pca_ozet).to_csv(P / "h4_pca_agirliklari.csv", index=False)
    print(t[t.gosterge == "endeks"].pivot_table(index="gecikme", columns="kriz", values="p").round(3).to_string())
    tt = pd.DataFrame(tur)
    tt.to_csv(P / "h4_kriz_turu.csv", index=False)
    print("\nKriz türü (kriz öncesi 14 günde gerginlik eğilimi):\n" + tt.to_string(index=False))
    hv = pd.concat(havuz).dropna()
    sonuc = []
    for gec in ["gecikme_1_3", "gecikme_1_7"]:
        for ad, f in [("gecikmeli", f"saldiri ~ {gec} + C(kriz)"),
                      ("gecikmeli + aynı gün + kriz sonrası", f"saldiri ~ {gec} + endeks + sonra + C(kriz)")]:
            m = smf.glm(f, data=hv, family=sm.families.Poisson()).fit()
            ci = np.exp(m.conf_int().loc[gec])
            sonuc.append(dict(gecikme=gec, model=ad, irr_1ss=round(np.exp(m.params[gec]), 2),
                              ga_alt=round(ci[0], 2), ga_ust=round(ci[1], 2), p=round(m.pvalues[gec], 4),
                              n_gun=int(m.nobs), saldiri=int(hv.saldiri.sum())))
    ht = pd.DataFrame(sonuc)
    ht.to_csv(P / "h4_havuz.csv", index=False)
    print("\nHavuzlanmış Poisson (3 kriz; IRR = gerginlik 1 SS arttığında):\n" + ht.to_string(index=False))


def main():
    d = pd.read_csv(P / "olaylar_v03.csv")
    s = d[d.sayima_dahil == "evet"].copy()
    panel = gunluk_panel(s)
    panel.to_csv(P / "gunluk_panel.csv", index=False)
    h1(panel)
    h2(s)
    h3(s)
    h4(s)


if __name__ == "__main__":
    main()
