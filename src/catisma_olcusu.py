"""H4 için çatışmaya dayalı gerginlik ölçüsü.

Neden: Goldstein ortalaması çatışma ve işbirliği olaylarını birlikte ortalar. Doğu Akdeniz 2020 gibi yoğun
diplomasinin (arabuluculuk, görüşmeler) yaşandığı krizlerde işbirliği olayları ortalamayı yükseltir ve gerginliği
olduğundan düşük gösterir. Bu betik yalnızca çatışma olaylarına dayanan iki ölçü kurar ve H4 analizlerini tekrarlar.

Ölçüler (Türkiye–karşı taraf, günlük, GDELT olay verisi; QuadClass 3 = sözlü çatışma, 4 = maddi çatışma)
  catisma_yogunlugu : log(1 + Σ |Goldstein| × anma sayısı), yalnız çatışma olayları
  catisma_payi      : çatışma olaylarının |Goldstein| × anma ağırlığının, bütün olayların ağırlığına oranı
                      (haber ilgisinin genel artışından etkilenmez)

Analizler (beş kriz): kriz türü (kriz öncesi 14 gün), Granger (1–7 gün), havuzlanmış Poisson
(önceki 1–3 günün ölçüsü + aynı gün + kriz sonrası kukla + kriz sabit etkisi), tırmanan × gecikmeli etkileşimi.
Çıktılar: data/processed/catisma_gunluk_<kriz>.csv, h4_catisma_kriz_turu.csv, h4_catisma_granger.csv,
          h4_catisma_havuz.csv, outputs/h4_catisma_olcusu.png
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.tsa.stattools import grangercausalitytests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gdelt_gerginlik as g

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
OUT = ROOT / "outputs"
W = 60
KRIZLER = {  # kriz: (tarih, karşı taraf GDELT kodu, saldırı serisinin bulunduğu dosya)
    "rusya_2015": ("2015-11-24", "RUS", "gerginlik_endeksi_rusya_2015.csv"),
    "hollanda_2017": ("2017-03-11", "NLD", "gerginlik_endeksi_hollanda_2017.csv"),
    "barispinari_2019": ("2019-10-09", "SYR", "gerginlik_endeksi_barispinari_2019.csv"),
    "brunson_2018": ("2018-08-10", "USA", "gerginlik_endeksi_brunson_2018.csv"),
    "dogu_akdeniz_2020": ("2020-08-10", "GRC", "gerginlik_endeksi_dogu_akdeniz_2020.csv"),
}
OLCULER = ["catisma_yogunlugu", "catisma_payi", "endeks_goldstein_ton"]


def z(x):
    return (x - x.mean()) / x.std()


def catisma_serisi(tarih, karsi):
    t = pd.Timestamp(tarih)
    df = g.yukle(t - pd.Timedelta(days=W), t + pd.Timedelta(days=W))
    m = ((df.a1 == "TUR") & (df.a2 == karsi)) | ((df.a2 == "TUR") & (df.a1 == karsi))
    d = df[m].copy()
    d["agirlik"] = d.goldstein.abs() * d.mentions
    d["cat_agirlik"] = np.where(d.quad.isin([3, 4]), d.agirlik, 0.0)
    s = d.groupby("tarih").agg(olay=("id", "size"), cat_agirlik=("cat_agirlik", "sum"), agirlik=("agirlik", "sum"))
    s = s.reindex(pd.date_range(t - pd.Timedelta(days=W), t + pd.Timedelta(days=W)), fill_value=0)
    s["gun"] = (s.index - t).days
    s["catisma_yogunlugu"] = np.log1p(s.cat_agirlik)
    s["catisma_payi"] = (s.cat_agirlik / s.agirlik.replace(0, np.nan)).fillna(0)
    return s.set_index("gun")


def kriz_turu(h, x):
    on = h.loc[-14:-1].reset_index()
    e = smf.ols(f"{x} ~ gun", data=on).fit()
    fark = h.loc[-14:-1, x].mean() - h.loc[-W:-15, x].mean()
    return e.params["gun"], e.pvalues["gun"], fark, (e.params["gun"] > 0 and e.pvalues["gun"] < 0.05) or fark >= 1


def main():
    pd.set_option("display.width", 220)
    seriler, tur, granger = {}, [], []
    for k, (tarih, karsi, dosya) in KRIZLER.items():
        s = catisma_serisi(tarih, karsi)
        e = pd.read_csv(P / dosya, index_col=0)
        h = s[["olay", "catisma_yogunlugu", "catisma_payi"]].join(e[["saldiri", "endeks"]].rename(
            columns={"endeks": "endeks_goldstein_ton"}), how="inner")
        for x in OLCULER:
            h[x] = z(h[x])
        h.to_csv(P / f"catisma_gunluk_{k}.csv")
        seriler[k] = h
        for x in OLCULER:
            egim, p, fark, tir = kriz_turu(h, x)
            tur.append(dict(kriz=k, olcu=x, egim=round(egim, 3), p_egim=round(p, 4), son14_eksi_onceki=round(fark, 2),
                            tur="tırmanan" if tir else "ani"))
            if (h.saldiri > 0).sum() >= 2:
                for lag, r in grangercausalitytests(h[["saldiri", x]], maxlag=7).items():
                    granger.append(dict(kriz=k, olcu=x, gecikme=lag, p=round(r[0]["ssr_ftest"][1], 4)))
    tt = pd.DataFrame(tur)
    tt.to_csv(P / "h4_catisma_kriz_turu.csv", index=False)
    print("Kriz türü (kriz öncesi 14 gün; tırmanan = eğim anlamlı pozitif ya da ≥ 1 SS yüksek):")
    print(tt.pivot(index="kriz", columns="olcu", values="son14_eksi_onceki").to_string())
    print(tt.pivot(index="kriz", columns="olcu", values="tur").to_string())
    gr = pd.DataFrame(granger)
    gr.to_csv(P / "h4_catisma_granger.csv", index=False)
    print("\nGranger p, en küçük değer (1–7 gün) ve 1. gün:")
    print(gr.groupby(["kriz", "olcu"]).p.agg(["min", "first"]).unstack().round(3).to_string())

    satir = []
    for x in OLCULER:
        hv = []
        for k, h in seriler.items():
            a = h[["saldiri", x]].copy()
            a["gecikmeli"] = a[x].shift(1).rolling(3).mean()
            a["ayni_gun"] = a[x]
            a["sonra"] = (a.index >= 0).astype(int)
            a["kriz"] = k
            a["tirmanan"] = int(tt[(tt.kriz == k) & (tt.olcu == x)].tur.iloc[0] == "tırmanan")
            hv.append(a)
        hv = pd.concat(hv).dropna()
        for ad, f, v, veri in [
            ("beş kriz, kontrollerle", "saldiri ~ gecikmeli + ayni_gun + sonra + C(kriz)", "gecikmeli", hv),
            ("etkileşim: gecikmeli × tırmanan", "saldiri ~ gecikmeli * tirmanan + ayni_gun + sonra + C(kriz)",
             "gecikmeli:tirmanan", hv),
            ("yalnız tırmanan krizler", "saldiri ~ gecikmeli + ayni_gun + sonra + C(kriz)", "gecikmeli",
             hv[hv.tirmanan == 1]),
            ("yalnız ani krizler", "saldiri ~ gecikmeli + ayni_gun + sonra + C(kriz)", "gecikmeli", hv[hv.tirmanan == 0]),
        ]:
            if veri.kriz.nunique() == 0 or veri.saldiri.sum() == 0:
                continue
            if veri.kriz.nunique() == 1:
                f = f.replace(" + C(kriz)", "")
            try:
                m = smf.glm(f, data=veri, family=sm.families.Poisson()).fit()
                ci = np.exp(m.conf_int().loc[v])
                satir.append(dict(olcu=x, model=ad, krizler=",".join(sorted(veri.kriz.unique())),
                                  irr=round(np.exp(m.params[v]), 2), ga_alt=round(ci[0], 2), ga_ust=round(ci[1], 2),
                                  p=round(m.pvalues[v], 4), saldiri=int(veri.saldiri.sum())))
            except Exception as e:
                satir.append(dict(olcu=x, model=ad, krizler="", irr=np.nan, p=np.nan, saldiri=int(veri.saldiri.sum()),
                                  ga_alt=np.nan, ga_ust=np.nan))
    r = pd.DataFrame(satir)
    r.to_csv(P / "h4_catisma_havuz.csv", index=False)
    print("\nHavuzlanmış Poisson (IRR: önceki 1–3 günün ölçüsü 1 SS arttığında):")
    print(r[["olcu", "model", "irr", "ga_alt", "ga_ust", "p", "saldiri", "krizler"]].to_string(index=False))

    fig, ax = plt.subplots(len(seriler), 1, figsize=(10, 12), sharex=True)
    for a, (k, h) in zip(ax, seriler.items()):
        a.plot(h.index, h.catisma_yogunlugu.rolling(3, center=True).mean(), label="Çatışma yoğunluğu (z)", color="#c0392b")
        a.plot(h.index, h.endeks_goldstein_ton.rolling(3, center=True).mean(), label="Goldstein + ton endeksi (z)",
               color="#7f8c8d", alpha=.8)
        for gun in h.index[h.saldiri > 0]:
            a.axvline(gun, color="#2c3e50", lw=.8, ls=":")
        a.axvline(0, color="black", lw=1.2)
        a.set_title(k, fontsize=10, loc="left")
    ax[0].legend(fontsize=8, loc="upper left")
    ax[-1].set_xlabel("Kriz tarihine göre gün (noktalı çizgi: karşı tarafla ilgili saldırı günü)")
    fig.tight_layout()
    fig.savefig(OUT / "h4_catisma_olcusu.png", dpi=150)


if __name__ == "__main__":
    main()
