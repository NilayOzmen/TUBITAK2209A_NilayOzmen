"""Tırmanan kriz örnekleri: 2018 ABD–Türkiye (Brunson) ve 2020 Türkiye–Yunanistan (Doğu Akdeniz) krizleri.

brunson.py'nin genelleştirilmiş hali. İki tırmanan kriz için aynı yöntem uygulanır ve beş krizin tamamı
havuzlanmış H4 modeline alınır. Ana veri hattı (birlestir.py, olaylar_v03.csv) değiştirilmez; olaylar
*_kodlama.csv dosyalarında kaynak bağlantıları ve gerekçeleriyle elle kodlanır.

Krizler
  brunson_2018       ana tarih 10.08.2018 (gümrük vergileri), alternatif 01.08.2018 (bakanlara yaptırım); karşı taraf ABD
  dogu_akdeniz_2020  ana tarih 10.08.2020 (Oruç Reis'in gönderilmesi), alternatif 12.08.2020 (fırkateyn çarpışması);
                     karşı taraf Yunanistan. Hackmageddon'ın Temmuz–Ekim 2020 zaman çizelgelerinin bir kısmı sitede
                     kaldırılmış ve EuRepoC'de dönemde Türkiye kaydı yok; olaylar neredeyse tamamen haberlerden geliyor.

Duyarlılık: tirmanan_sonuc.csv'de ana tarih için tek kaynaklı olaylar (tek_kaynak.csv) hariç tutulan satır da var.

Kriz türü: kriz öncesi 14 günde gerginlik eğimi anlamlı pozitifse ya da gerginlik önceki döneme göre ≥ 1 SS
yüksekse "tırmanan", değilse "ani".
Çıktılar: data/processed/olaylar_<kriz>.csv, tirmanan_sonuc.csv, tirmanan_h4_granger.csv,
          h4_kriz_turu_bes_kriz.csv, h4_havuz_bes_kriz.csv, gerginlik_endeksi_<kriz>.csv
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
W = 60
KRIZLER = {
    "brunson_2018": dict(tarih="2018-08-10", alternatif="2018-08-01", kodlama="brunson_kodlama.csv",
                         gdelt="gdelt_gunluk_2018_USA.csv", karsi="ABD"),
    "dogu_akdeniz_2020": dict(tarih="2020-08-10", alternatif="2020-08-12", kodlama="dogu_akdeniz_kodlama.csv",
                              gdelt="gdelt_gunluk_2020_GRC.csv", karsi="Yunanistan"),
}
ANI = {"rusya_2015": "gerginlik_endeksi_rusya_2015.csv", "hollanda_2017": "gerginlik_endeksi_hollanda_2017.csv",
       "barispinari_2019": "gerginlik_endeksi_barispinari_2019.csv"}


def z(x):
    return (x - x.mean()) / x.std()


def gdelt_serisi(k, c):
    """Türkiye–karşı taraf günlük Goldstein/ton serisi; yoksa ham GDELT dosyalarından üretilir."""
    yol = P / c["gdelt"]
    if not yol.exists():
        import gdelt_gerginlik as g
        t = pd.Timestamp(c["tarih"])
        s = g.gunluk_seri(g.yukle(t - pd.Timedelta(days=W), t + pd.Timedelta(days=W)), [c["gdelt"][-7:-4]])
        s["gun"] = (s.index - t).days
        s.to_csv(yol)
    return pd.read_csv(yol)[["gun", "goldstein", "ton", "catisma_orani"]]


def olaylar(k, c):
    d = pd.read_csv(P / c["kodlama"], parse_dates=["tarih"])
    d["gun_farki"] = (d.tarih - pd.Timestamp(c["tarih"])).dt.days
    d = d.sort_values("tarih").reset_index(drop=True)
    d.insert(0, "olay_id", [f"{k[0].upper()}{i + 1:02d}" for i in range(len(d))])
    d.to_csv(P / f"olaylar_{k}.csv", index=False)
    return d


def h1_h2(k, d, c):
    s = d[d.sayima_dahil == "evet"]
    satir = []
    for ad, t in [("ana", c["tarih"]), ("alternatif", c["alternatif"])]:
        t = pd.Timestamp(t)
        g = (s.tarih - t).dt.days
        x = s[(g >= -W) & (g <= W)]
        gx = (x.tarih - t).dt.days
        once, sonra = x[gx < 0], x[gx >= 0]
        pay = (W + 1) / (2 * W + 1)
        p1 = binomtest(len(sonra), len(x), pay, alternative="greater").pvalue if len(x) else np.nan
        io, isn = int((once.kriz_ikilisi == "evet").sum()), int((sonra.kriz_ikilisi == "evet").sum())
        p2 = binomtest(isn, io + isn, pay, alternative="greater").pvalue if io + isn else np.nan
        tr = x[(x.aktor_turu == "hacktivist") & x.saldirgan_ulke.fillna("").str.contains("TR")]
        gt = (tr.tarih - t).dt.days
        a, b = int(((gt < 0) & (tr.kriz_ikilisi == "evet")).sum()), int((gt < 0).sum())
        cc, e = int(((gt >= 0) & (tr.kriz_ikilisi == "evet")).sum()), int((gt >= 0).sum())
        p3 = fisher_exact([[cc, e - cc], [a, b - a]], alternative="greater")[1] if b and e else np.nan
        satir.append(dict(kriz=k, kriz_tarihi=f"{ad} ({t.date()})", olay_once=len(once), olay_sonra=len(sonra),
                          p_olay=round(p1, 4), ikili_once=io, ikili_sonra=isn, p_ikili=round(p2, 4),
                          h2_once=f"{a}/{b}", h2_sonra=f"{cc}/{e}",
                          p_h2=round(p3, 4) if p3 == p3 else "test edilemez"))
    return satir


def gerginlik(k, d, c):
    g = gdelt_serisi(k, c)
    y = (d[(d.sayima_dahil == "evet") & (d.kriz_ikilisi == "evet")].groupby("gun_farki").size()
         .reindex(range(-W, W + 1), fill_value=0).rename("saldiri"))
    h = g.set_index("gun").join(y, how="right").interpolate().bfill().rename_axis("gun")
    h["endeks"] = (z(-h.goldstein) + z(-h.ton)) / 2
    h[["saldiri", "goldstein", "ton", "catisma_orani", "endeks"]].to_csv(P / f"gerginlik_endeksi_{k}.csv")
    return h


def kriz_turu(h, etiket):
    on = h.loc[-14:-1]
    e = smf.ols("endeks ~ gun", data=on.reset_index()).fit()
    fark = on.endeks.mean() - h.loc[-W:-15, "endeks"].mean()
    tir = (e.params["gun"] > 0 and e.pvalues["gun"] < 0.05) or fark >= 1
    return dict(kriz=etiket, egim_gunluk=round(e.params["gun"], 3), p_egim=round(e.pvalues["gun"], 4),
                son14_eksi_onceki=round(fark, 2), tur="tırmanan" if tir else "ani")


def main():
    pd.set_option("display.width", 220)
    sonuc, granger, tur, havuz = [], [], [], []
    for k, dosya in ANI.items():
        h = pd.read_csv(P / dosya, index_col=0).rename_axis("gun")
        tur.append(kriz_turu(h, k))
        havuz.append((k, h[["saldiri", "endeks"]]))
    for k, c in KRIZLER.items():
        d = olaylar(k, c)
        print(f"\n[{k}] karşı taraf: {c['karsi']}")
        print(d[["olay_id", "tarih", "gun_farki", "saldirgan", "hedef_ulke", "kriz_ikilisi", "sayima_dahil"]]
              .to_string(index=False))
        sonuc += h1_h2(k, d, c)
        # Duyarlılık: tek kaynaklı olaylar hariç (tek_kaynak.csv; olay numaraları tarih sırasına göre yeniden
        # verildiği için eşleştirme kaynak bağlantısıyla yapılır)
        tek = set(pd.read_csv(P / "tek_kaynak.csv").kaynak_url)
        for r in h1_h2(k, d[~d.kaynak_url.isin(tek)], c):
            if r["kriz_tarihi"].startswith("ana"):
                r["kriz_tarihi"] = r["kriz_tarihi"].replace("ana", "ana, tek kaynaklılar hariç")
                sonuc.append(r)
        h = gerginlik(k, d, c)
        tur.append(kriz_turu(h, k))
        havuz.append((k, h[["saldiri", "endeks"]]))
        if (h.saldiri > 0).sum() >= 2:
            for lag, r in grangercausalitytests(h[["saldiri", "endeks"]], maxlag=7).items():
                f, p = r[0]["ssr_ftest"][:2]
                granger.append(dict(kriz=k, gecikme=lag, F=round(f, 2), p=round(p, 4)))
    t = pd.DataFrame(sonuc)
    t.to_csv(P / "tirmanan_sonuc.csv", index=False)
    print("\nH1 ve H2 (kesin testler):\n" + t.to_string(index=False))
    g = pd.DataFrame(granger)
    g.to_csv(P / "tirmanan_h4_granger.csv", index=False)
    print("\nH4 Granger (endeks → karşı tarafa saldırı):\n" + g.pivot(index="gecikme", columns="kriz", values="p").to_string())
    tt = pd.DataFrame(tur)
    tt.to_csv(P / "h4_kriz_turu_bes_kriz.csv", index=False)
    print("\nKriz türü:\n" + tt.to_string(index=False))

    hv = []
    for k, x in havuz:
        x = x.copy()
        x["gecikme_1_3"] = x.endeks.shift(1).rolling(3).mean()
        x["sonra"] = (x.index >= 0).astype(int)
        x["kriz"] = k
        x["tirmanan"] = int(tt.set_index("kriz").loc[k, "tur"] == "tırmanan")
        hv.append(x)
    hv = pd.concat(hv).dropna()
    rows = []
    for ad, f, v in [("gecikmeli + kriz sabit etkisi", "saldiri ~ gecikme_1_3 + C(kriz)", "gecikme_1_3"),
                     ("+ aynı gün + kriz sonrası", "saldiri ~ gecikme_1_3 + endeks + sonra + C(kriz)", "gecikme_1_3"),
                     ("+ etkileşim: gecikmeli × tırmanan", "saldiri ~ gecikme_1_3 * tirmanan + endeks + sonra + C(kriz)",
                      "gecikme_1_3:tirmanan")]:
        m = smf.glm(f, data=hv, family=sm.families.Poisson()).fit()
        ci = np.exp(m.conf_int().loc[v])
        rows.append(dict(model=ad, katsayi=v, irr=round(np.exp(m.params[v]), 2), ga_alt=round(ci[0], 2),
                         ga_ust=round(ci[1], 2), p=round(m.pvalues[v], 4), n_gun=int(m.nobs), saldiri=int(hv.saldiri.sum())))
    # Yalnız tırmanan krizler / yalnız ani krizler
    for ad, alt in [("yalnız tırmanan krizler", hv[hv.tirmanan == 1]), ("yalnız ani krizler", hv[hv.tirmanan == 0])]:
        m = smf.glm("saldiri ~ gecikme_1_3 + endeks + sonra + C(kriz)", data=alt, family=sm.families.Poisson()).fit()
        ci = np.exp(m.conf_int().loc["gecikme_1_3"])
        rows.append(dict(model=ad + " (+ aynı gün + kriz sonrası)", katsayi="gecikme_1_3",
                         irr=round(np.exp(m.params["gecikme_1_3"]), 2), ga_alt=round(ci[0], 2), ga_ust=round(ci[1], 2),
                         p=round(m.pvalues["gecikme_1_3"], 4), n_gun=int(m.nobs), saldiri=int(alt.saldiri.sum())))
    r = pd.DataFrame(rows)
    r.to_csv(P / "h4_havuz_bes_kriz.csv", index=False)
    print("\nHavuzlanmış Poisson, beş kriz (IRR: önceki 1–3 günün gerginliği 1 SS arttığında):\n" + r.to_string(index=False))


if __name__ == "__main__":
    main()
