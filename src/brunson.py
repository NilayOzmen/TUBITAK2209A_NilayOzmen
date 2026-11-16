"""Tırmanan kriz örneği: 2018 ABD–Türkiye (Brunson) krizi.

Neden: Rusya, Hollanda ve Barış Pınarı krizlerinin öncesinde gerginlik belirgin biçimde tırmanmadığından (ani krizler)
H4'ün erken uyarı mantığı bu krizlerde test edilemiyordu. Brunson krizinde gerginlik haftalar içinde tırmandı:
26 Temmuz yaptırım tehdidi, 1 Ağustos bakanlara yaptırım, 3 Ağustos Türkiye'nin karşılığı, 10 Ağustos gümrük
vergilerinin ikiye katlanması ve liranın çöküşü.

Kriz tarihi: 10 Ağustos 2018 (tırmanmanın tepe noktası); 1 Ağustos 2018 alternatif olarak raporlanır.
Karşı taraf: ABD. Pencere: ±60 gün (Türkçe haber taraması ±14 gün, diğer krizlerle aynı).
Ana veri hattı (birlestir.py, olaylar_v03.csv) değiştirilmez; olaylar brunson_kodlama.csv dosyasında elle kodlanır.

Çıktılar: data/processed/olaylar_brunson_2018.csv, brunson_sonuc.csv, brunson_h4_granger.csv,
          h4_kriz_turu_dort_kriz.csv, h4_havuz_dort_kriz.csv, gerginlik_endeksi_brunson_2018.csv
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import binomtest, fisher_exact
from statsmodels.tsa.stattools import grangercausalitytests

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
TARIH = {"10 Ağustos 2018": pd.Timestamp("2018-08-10"), "1 Ağustos 2018 (alternatif)": pd.Timestamp("2018-08-01")}
W = 60


def z(x):
    return (x - x.mean()) / x.std()


def olaylar():
    d = pd.read_csv(P / "brunson_kodlama.csv", parse_dates=["tarih"])
    d["gun_farki"] = (d.tarih - TARIH["10 Ağustos 2018"]).dt.days
    d = d.sort_values("tarih").reset_index(drop=True)
    d.insert(0, "olay_id", [f"B{i + 1:02d}" for i in range(len(d))])
    d.to_csv(P / "olaylar_brunson_2018.csv", index=False)
    return d


def h1_h2(d):
    s = d[d.sayima_dahil == "evet"]
    satir = []
    for ad, t in TARIH.items():
        g = (s.tarih - t).dt.days
        icinde = s[(g >= -W) & (g <= W)]
        gi = g[(g >= -W) & (g <= W)]
        once, sonra = icinde[gi < 0], icinde[gi >= 0]
        pay = (W + 1) / (2 * W + 1)          # öncesi 60, sonrası 61 gün
        p1 = binomtest(len(sonra), len(once) + len(sonra), pay, alternative="greater").pvalue if len(icinde) else np.nan
        io, isn = int((once.kriz_ikilisi == "evet").sum()), int((sonra.kriz_ikilisi == "evet").sum())
        p2 = binomtest(isn, io + isn, pay, alternative="greater").pvalue if io + isn else np.nan
        tr = icinde[(icinde.aktor_turu == "hacktivist") & icinde.saldirgan_ulke.fillna("").str.contains("TR")]
        gt = (tr.tarih - t).dt.days
        a, b = int(((gt < 0) & (tr.kriz_ikilisi == "evet")).sum()), int((gt < 0).sum())
        c, e = int(((gt >= 0) & (tr.kriz_ikilisi == "evet")).sum()), int((gt >= 0).sum())
        p3 = fisher_exact([[c, e - c], [a, b - a]], alternative="greater")[1] if b and e else np.nan
        satir.append(dict(kriz_tarihi=ad, olay_once=len(once), olay_sonra=len(sonra), p_olay=round(p1, 4),
                          ikili_once=io, ikili_sonra=isn, p_ikili=round(p2, 4),
                          h2_once=f"{a}/{b}", h2_sonra=f"{c}/{e}", p_h2=round(p3, 4) if p3 == p3 else "test edilemez"))
    return pd.DataFrame(satir)


def gerginlik(d):
    g = pd.read_csv(P / "gdelt_gunluk_2018_USA.csv")[["gun", "goldstein", "ton", "catisma_orani"]]
    y = (d[(d.sayima_dahil == "evet") & (d.kriz_ikilisi == "evet")].groupby("gun_farki").size()
         .reindex(range(-W, W + 1), fill_value=0).rename("saldiri"))
    h = g.set_index("gun").join(y, how="right").interpolate().bfill().rename_axis("gun")
    h["endeks"] = (z(-h.goldstein) + z(-h.ton)) / 2
    h[["saldiri", "goldstein", "ton", "catisma_orani", "endeks"]].to_csv(P / "gerginlik_endeksi_brunson_2018.csv")
    return h


def kriz_turu(h, etiket):
    on = h.loc[-14:-1]
    e = smf.ols("endeks ~ gun", data=on.reset_index()).fit()
    fark = on.endeks.mean() - h.loc[-W:-15, "endeks"].mean()
    # Tırmanan kriz: kriz öncesi 14 günde gerginlik ya anlamlı biçimde artıyor ya da önceki döneme göre
    # en az 1 standart sapma yüksek seyrediyor
    tir = (e.params["gun"] > 0 and e.pvalues["gun"] < 0.05) or fark >= 1
    return dict(kriz=etiket, egim_gunluk=round(e.params["gun"], 3), p_egim=round(e.pvalues["gun"], 4),
                son14_eksi_onceki=round(fark, 2), tur="tırmanan" if tir else "ani")


def main():
    d = olaylar()
    pd.set_option("display.width", 220)
    print(d[["olay_id", "tarih", "gun_farki", "saldirgan", "hedef_ulke", "aktor_turu", "kriz_ikilisi", "sayima_dahil"]]
          .to_string(index=False))
    t = h1_h2(d)
    t.to_csv(P / "brunson_sonuc.csv", index=False)
    print("\nH1 ve H2 (kesin binom testi; kriz öncesi olay sayısı sıfır olabildiği için):\n" + t.to_string(index=False))

    h = gerginlik(d)
    satir = []
    for x in ["endeks"]:
        if h.saldiri.sum() >= 2:
            for lag, r in grangercausalitytests(h[["saldiri", x]], maxlag=7).items():
                f, p = r[0]["ssr_ftest"][:2]
                satir.append(dict(kriz="brunson_2018", gosterge=x, gecikme=lag, F=round(f, 2), p=round(p, 4)))
    gr = pd.DataFrame(satir)
    gr.to_csv(P / "brunson_h4_granger.csv", index=False)
    print("\nH4 Granger (TR–USA endeksi → karşı tarafa saldırı):\n" + gr.to_string(index=False))

    # Kriz türü: dört kriz aynı ölçütle
    tur = []
    for etiket, dosya in [("rusya_2015", "gerginlik_endeksi_rusya_2015.csv"),
                          ("hollanda_2017", "gerginlik_endeksi_hollanda_2017.csv"),
                          ("barispinari_2019", "gerginlik_endeksi_barispinari_2019.csv")]:
        tur.append(kriz_turu(pd.read_csv(P / dosya, index_col=0).rename_axis("gun"), etiket))
    tur.append(kriz_turu(h, "brunson_2018"))
    tt = pd.DataFrame(tur)
    tt.to_csv(P / "h4_kriz_turu_dort_kriz.csv", index=False)
    print("\nKriz türü (eğim anlamlı pozitif ya da seviye farkı ≥ 1 SS ise tırmanan):\n" + tt.to_string(index=False))

    # Havuzlanmış model: dört kriz; gecikmeli gerginliğin etkisi tırmanan krizlerde farklı mı?
    havuz = []
    for etiket, dosya in [("rusya_2015", "gerginlik_endeksi_rusya_2015.csv"),
                          ("hollanda_2017", "gerginlik_endeksi_hollanda_2017.csv"),
                          ("barispinari_2019", "gerginlik_endeksi_barispinari_2019.csv"),
                          ("brunson_2018", "gerginlik_endeksi_brunson_2018.csv")]:
        x = pd.read_csv(P / dosya, index_col=0)[["saldiri", "endeks"]]
        x["gecikme_1_3"] = x.endeks.shift(1).rolling(3).mean()
        x["sonra"] = (x.index >= 0).astype(int)
        x["kriz"] = etiket
        x["tirmanan"] = int(tt.set_index("kriz").loc[etiket, "tur"] == "tırmanan")
        havuz.append(x)
    hv = pd.concat(havuz).dropna()
    sonuc = []
    for ad, f in [("gecikmeli", "saldiri ~ gecikme_1_3 + C(kriz)"),
                  ("gecikmeli + aynı gün + kriz sonrası", "saldiri ~ gecikme_1_3 + endeks + sonra + C(kriz)")]:
        m = smf.glm(f, data=hv, family=sm.families.Poisson()).fit()
        ci = np.exp(m.conf_int().loc["gecikme_1_3"])
        sonuc.append(dict(model=ad, irr_1ss=round(np.exp(m.params["gecikme_1_3"]), 2), ga_alt=round(ci[0], 2),
                          ga_ust=round(ci[1], 2), p=round(m.pvalues["gecikme_1_3"], 4), n_gun=int(m.nobs),
                          saldiri=int(hv.saldiri.sum())))
    ht = pd.DataFrame(sonuc)
    ht.to_csv(P / "h4_havuz_dort_kriz.csv", index=False)
    print("\nHavuzlanmış Poisson, dört kriz (IRR = önceki 1–3 günün gerginliği 1 SS arttığında):\n" + ht.to_string(index=False))


if __name__ == "__main__":
    main()
