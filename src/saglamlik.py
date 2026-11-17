"""Sağlamlık analizleri: H1 ve H2 sonuçlarının pencere uzunluğuna ve kriz tarihine duyarlılığı.

Yöntem bölümündeki taahhüt: analizler 30 ve 90 günlük pencerelerle ve kriz tarihi bir hafta öne ve geriye
kaydırılarak tekrarlanacak.

Senaryolar
  1. Pencere uzunluğu: ±30, ±45, ±60 gün (ana veri seti olaylar_v04.csv, ±60 günü kapsar).
  2. Kriz tarihi kaydırma: −7, 0, +7 gün. Kaydırınca pencere veri dışına taşmasın diye ±53 gün kullanılır.
  3. ±90 gün: Haber taraması yalnızca ±60 gün için yapıldığından bu senaryoda
     yalnızca veri tabanı kaynakları (EuRepoC + Hackmageddon) kullanılır ve aynı kaynaklarla ±60 gün sonucu
     yanına konur. 60–90 gün arasındaki olaylar olaylar_bant_60_90.csv dosyasında elle kodlanmıştır.
  4. Krizi teker teker dışarıda bırakma (±60 gün).
  5. Tek kaynaklı olaylar hariç (±60 gün): öneri metnine göre hedefin reddettiği ya da tek kaynakta geçen
     olaylar yalnızca duyarlılık analizinde kullanılır. Tek kaynaklı olaylar tek_kaynak.csv dosyasında
     gerekçeleriyle listelenir (veri tabanı kayıtları derlenmiş kaynak sayılır; haberden gelen bir olay, Türkçe ve
     İngilizce taramada yalnızca bir haber sitesinde geçiyorsa tek kaynaklıdır).

H1: Poisson GLM, günlük olay sayısı ~ kriz sonrası + kriz sabit etkisi. Kriz öncesinde hiç olay yoksa
    (tam ayrışma) kesin koşullu binom testi kullanılır.
H2: Türkiye kaynaklı hacktivist saldırılarda karşı tarafı hedef alanların oranı, önce/sonra, Fisher (tek yönlü).
Çıktı: data/processed/saglamlik.csv
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import binomtest, fisher_exact

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
KRIZLER = ["rusya_2015", "hollanda_2017", "barispinari_2019"]


def panel(s, w, kaydir=0, krizler=KRIZLER):
    g = s.gun_farki - kaydir
    satir = []
    for k in krizler:
        gk = g[s.kriz == k]
        ik = s.loc[s.kriz == k, "kriz_ikilisi"]
        for gun in range(-w, w + 1):
            m = gk == gun
            satir.append(dict(kriz=k, gun=gun, sonra=int(gun >= 0), olay=int(m.sum()),
                              ikili=int((m & (ik == "evet")).sum())))
    return pd.DataFrame(satir)


def h1(p, y):
    d = p[p.groupby("kriz")[y].transform("sum") > 0]
    once, sonra = int(d[d.sonra == 0][y].sum()), int(d[d.sonra == 1][y].sum())
    if once + sonra == 0:
        return once, sonra, np.nan, np.nan
    if once == 0:
        # Tam ayrışma; öncesi w gün, sonrası w+1 gün → beklenen pay (w+1)/(2w+1)
        w = int(d.gun.max())
        pay = (w + 1) / (2 * w + 1)
        return once, sonra, np.inf, binomtest(sonra, sonra, pay, alternative="greater").pvalue
    m = smf.glm(f"{y} ~ sonra + C(kriz)", data=d, family=sm.families.Poisson()).fit()
    return once, sonra, float(np.exp(m.params["sonra"])), float(m.pvalues["sonra"])


def h2(s, w, kaydir=0):
    x = s[(s.aktor_turu == "hacktivist") & s.saldirgan_ulke.fillna("").str.contains("TR")]
    g = x.gun_farki - kaydir
    once, sonra = x[(g < 0) & (g >= -w)], x[(g >= 0) & (g <= w)]
    a, b = int((once.kriz_ikilisi == "evet").sum()), len(once)
    c, d = int((sonra.kriz_ikilisi == "evet").sum()), len(sonra)
    p = fisher_exact([[c, d - c], [a, b - a]], alternative="greater")[1] if b and d else np.nan
    return f"{a}/{b}", f"{c}/{d}", p


def satir_yaz(ad, s, w, kaydir=0, krizler=KRIZLER):
    s = s[s.kriz.isin(krizler)]
    pn = panel(s, w, kaydir, krizler)
    o1, s1, irr1, p1 = h1(pn, "olay")
    o2, s2, irr2, p2 = h1(pn, "ikili")
    h2o, h2s, p3 = h2(s, w, kaydir)
    return dict(senaryo=ad, pencere=w, kaydirma=kaydir, olay_once=o1, olay_sonra=s1,
                irr_olay=round(irr1, 2), p_olay=round(p1, 4),
                ikili_once=o2, ikili_sonra=s2, irr_ikili=round(irr2, 2), p_ikili=round(p2, 4),
                h2_once=h2o, h2_sonra=h2s, p_h2=round(p3, 4))


def bant_olaylari():
    b = pd.read_csv(P / "olaylar_bant_60_90.csv")
    b = b[~b.islem.str.startswith("birlestir")]
    return b[b.sayima_dahil == "evet"]


def main():
    d = pd.read_csv(P / "olaylar_v04.csv")
    s = d[d.sayima_dahil == "evet"].copy()
    sonuc = []
    for w in [30, 45, 60]:
        sonuc.append(satir_yaz(f"Pencere ±{w}", s, w))
    for k in [-7, 0, 7]:
        sonuc.append(satir_yaz(f"Kriz tarihi {k:+d} gün (±53)", s, 53, k))
    vt = s[~s.kaynak.str.contains("haber")]
    vt90 = pd.concat([vt, bant_olaylari()], ignore_index=True)
    sonuc.append(satir_yaz("Yalnız veri tabanları ±60", vt, 60))
    sonuc.append(satir_yaz("Yalnız veri tabanları ±90", vt90, 90))
    for k in KRIZLER:
        sonuc.append(satir_yaz(f"{k} hariç (±60)", s, 60, krizler=[x for x in KRIZLER if x != k]))
    tek = set(pd.read_csv(P / "tek_kaynak.csv").olay_id)
    sonuc.append(satir_yaz("Tek kaynaklı olaylar hariç (±60)", s[~s.olay_id.isin(tek)], 60))
    t = pd.DataFrame(sonuc)
    t.to_csv(P / "saglamlik.csv", index=False)
    pd.set_option("display.width", 250)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
