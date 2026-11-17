"""Kriz dışı karşılaştırma (Temmuz 2015 – Kasım 2024).

Önerideki taahhüt: "Kriz dışı karşılaştırma için 2015–2025 genel siber olay verileri kullanılacak."
Haber taraması yalnızca kriz pencereleri için yapıldığından bu analiz yalnızca veri tabanı kaynaklarıyla
(EuRepoC + Hackmageddon) yapılır. On yıllık veri elle kodlanamayacağı için kriz ve kriz dışı dönemler aynı
otomatik kurallarla kodlanır (birlestir.py'deki kurallar): yalnızca hacktivist, gün düzeyinde tarihli ve
Türkiye'nin saldırgan ya da hedef olduğu olaylar sayılır.

Dönem: Hackmageddon 2015'in ilk yarısında tabloları resim olarak yayımladığı için 1 Temmuz 2015'te başlar;
Aralık 2024 zaman çizelgeleri indirme sırasında henüz eksik olduğundan 30 Kasım 2024'te biter.
2020'de sunucu hatası ya da biçim farkı nedeniyle alınamayan beş yarım aylık zaman çizelgesinin günleri dışarıda bırakılır.

Analizler
  0. Doğrulama: otomatik kodlamanın kriz pencerelerindeki sayıları, elle kodlanmış v03 veri tabanı kayıtlarıyla.
  1. Taban oran: günlük olay sayısı ~ dönem (kriz öncesi / kriz sonrası / kriz dışı) + yıl sabit etkisi (Poisson).
  2. Plasebo testi: rastgele seçilen "sahte kriz" tarihlerinde (sonra 60 gün − önce 60 gün) farkının dağılımı;
     gerçek üç krizin toplam farkı bu dağılımla karşılaştırılır (10.000 çekiliş).
  3. H3 kriz dışı karşılaştırma: Türkiye kaynaklı hacktivist saldırıların tek bir yabancı hedef ülkede
     yoğunlaşması (en çok saldırı alan ülkenin payı), kriz sonrası 61 gün ile rastgele 61 günlük kriz dışı
     pencereler karşılaştırılarak.
Çıktılar: data/processed/kriz_disi_*.csv, outputs/kriz_disi_plasebo.png
"""
import re
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import birlestir as b

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
OUT = ROOT / "outputs"
BAS, BIT = pd.Timestamp("2015-07-01"), pd.Timestamp("2024-11-30")
KRIZ = {"rusya_2015": pd.Timestamp("2015-11-24"), "hollanda_2017": pd.Timestamp("2017-03-11"),
        "barispinari_2019": pd.Timestamp("2019-10-09")}
KARSI = {"rusya_2015": "RU", "hollanda_2017": "NL", "barispinari_2019": "US"}
EKSIK = [("2020-07-16", "2020-07-31"), ("2020-08-01", "2020-08-15"), ("2020-09-01", "2020-09-15"),
         ("2020-10-01", "2020-10-15"), ("2020-12-01", "2020-12-15")]
W = 60
# birlestir.py'deki liste + kriz pencerelerinde elle kodlanan olaylarda görülen Türk grupları
TURK_SALDIRGAN = (b.TURK_GRUP + r"|Anka|Ak[ıi]nc[ıi]la|WKPF|RedHack|Turkz|Skorsky|Cyber.?Warrior|Sipahi|Root.?Ay[yi]+ld[ıi]z|"
                  r"Turkish hackers|THT\b")
CEKILIS = 10_000
rng = np.random.default_rng(2209)


def hackmageddon():
    d = pd.read_csv(P / "hackmageddon_2015_2024.csv", low_memory=False)
    olus = pd.to_datetime(d.Date, format="%d/%m/%Y", errors="coerce")
    bildirim = pd.to_datetime(d.get("Date Reported"), format="%d/%m/%Y", errors="coerce")
    olus = olus.where(olus >= "2000-01-01")          # boş tarih alanları 1970 olarak okunabiliyor
    d["tarih"] = olus.fillna(bildirim)
    d["Description"] = d["Description"].fillna(d.get("Event  Description"))
    metin = d.Author.fillna("") + " | " + d.Target.fillna("") + " | " + d.Description.fillna("")
    ulke = d.Country.fillna("").astype(str).str.replace("\n", ";")
    turkiye = ulke.str.contains(r"\bTR\b") | metin.str.contains(b.TURK_GRUP + r"|Turkey|Türkiye", case=False)
    h = d[turkiye & d["Attack Class"].fillna("").astype(str).str.strip().str.startswith("H") & d.tarih.notna()]
    # Türkiye kaynaklı: yalnızca saldırgan alanına bakılır (açıklamada "Turkish" geçmesi hedefi de anlatabilir)
    tr = h.Author.fillna("").str.contains(TURK_SALDIRGAN, case=False)
    return pd.DataFrame(dict(tarih=h.tarih.dt.normalize(), kaynak="hackmageddon", saldirgan=h.Author.fillna("?"),
                             tr_kaynakli=tr, hedef_ulke=ulke[h.index]))


def eurepoc():
    e = pd.read_csv(P / "eurepoc_turkiye.csv", parse_dates=["start"])
    e = e[(e.aktor_turu == "hacktivist") & (e.start.dt.day != 1)]
    ulke = lambda s: ";".join(sorted({b.ULKE.get(x.strip(), x.strip()) for x in str(s).split(";")}))
    return pd.DataFrame(dict(tarih=e.start.dt.normalize(), kaynak="eurepoc", saldirgan=e.initiator_name,
                             tr_kaynakli=e.initiator_country.fillna("").str.contains("Turkey")
                             | e.initiator_name.fillna("").str.contains(TURK_SALDIRGAN, case=False),
                             hedef_ulke=e.receiver_country.map(ulke)))


def olaylar():
    h, e = hackmageddon(), eurepoc()
    # Mükerrer: EuRepoC kaydı, ≤3 gün içinde hedef ülkesi örtüşen bir Hackmageddon kaydıyla aynı sayılır
    tut = []
    for _, r in e.iterrows():
        yakin = h[(h.tarih - r.tarih).abs().dt.days <= 3]
        ortak = any(set(str(r.hedef_ulke).split(";")) & set(str(x).split(";")) for x in yakin.hedef_ulke)
        tut.append(not ortak)
    d = pd.concat([h, e[tut]], ignore_index=True)
    # Kılavuz 6: Türkiye'ye özgü olmayan (üçten fazla hedef ülkeli) kampanyalar sayılmaz
    d = d[d.hedef_ulke.fillna("").str.split(";").str.len() <= 3]
    return d[(d.tarih >= BAS) & (d.tarih <= BIT)].sort_values("tarih").reset_index(drop=True)


def gunluk(d):
    gun = pd.DataFrame(index=pd.date_range(BAS, BIT, freq="D"))
    gun["olay"] = d.groupby("tarih").size().reindex(gun.index, fill_value=0)
    gun["tr_olay"] = d[d.tr_kaynakli].groupby("tarih").size().reindex(gun.index, fill_value=0)
    gun["eksik"] = False
    for a, z in EKSIK:
        gun.loc[a:z, "eksik"] = True
    gun["donem"] = "kriz_disi"
    for t in KRIZ.values():
        gun.loc[t - pd.Timedelta(days=W):t - pd.Timedelta(days=1), "donem"] = "kriz_oncesi"
        gun.loc[t:t + pd.Timedelta(days=W), "donem"] = "kriz_sonrasi"
    gun["yil"] = gun.index.year
    return gun


def dogrulama(d):
    v = pd.read_csv(P / "olaylar_v04.csv")
    v = v[(v.sayima_dahil == "evet") & ~v.kaynak.str.contains("haber") & (v.aktor_turu == "hacktivist")]
    satir = []
    for k, t in KRIZ.items():
        g = (d.tarih - t).dt.days
        oto = d[(g >= -W) & (g <= W)]
        el = v[v.kriz == k]
        satir.append(dict(kriz=k, otomatik_once=int(((oto.tarih - t).dt.days < 0).sum()),
                          otomatik_sonra=int(((oto.tarih - t).dt.days >= 0).sum()),
                          elle_once=int((el.gun_farki < 0).sum()), elle_sonra=int((el.gun_farki >= 0).sum())))
    return pd.DataFrame(satir)


def taban_oran(gun):
    x = gun[~gun.eksik]
    sonuc = []
    for y in ["olay", "tr_olay"]:
        m = smf.glm(f"{y} ~ C(donem, Treatment('kriz_disi')) + C(yil)", data=x, family=sm.families.Poisson()).fit()
        disp = m.pearson_chi2 / m.df_resid
        if disp > 1.5:     # aşırı yayılım varsa negatif binom
            m = smf.glm(f"{y} ~ C(donem, Treatment('kriz_disi')) + C(yil)", data=x,
                        family=sm.families.NegativeBinomial(alpha=1.0)).fit()
        for d_ in ["kriz_oncesi", "kriz_sonrasi"]:
            ad = f"C(donem, Treatment('kriz_disi'))[T.{d_}]"
            ci = np.exp(m.conf_int().loc[ad])
            sonuc.append(dict(seri=y, donem=d_, gunluk_ort=round(x[x.donem == d_][y].mean(), 3),
                              kriz_disi_ort=round(x[x.donem == "kriz_disi"][y].mean(), 3),
                              irr=round(np.exp(m.params[ad]), 2), ga_alt=round(ci[0], 2), ga_ust=round(ci[1], 2),
                              p=round(m.pvalues[ad], 4), asiri_yayilim=round(disp, 2)))
    return pd.DataFrame(sonuc)


def fark(gun, t, y):
    once = gun.loc[t - pd.Timedelta(days=W):t - pd.Timedelta(days=1), y].sum()
    sonra = gun.loc[t:t + pd.Timedelta(days=W - 1), y].sum()
    return sonra - once


def plasebo(gun):
    # Sahte kriz tarihi: ±60 günlük penceresi dönem içinde kalan, eksik günlere ve gerçek kriz pencerelerine
    # (±120 gün, pencereler örtüşmesin diye) değmeyen günler
    aday = []
    for t in gun.index[W:-W]:
        p = gun.loc[t - pd.Timedelta(days=W):t + pd.Timedelta(days=W - 1)]
        if p.eksik.any() or any(abs((t - k).days) < 2 * W for k in KRIZ.values()):
            continue
        aday.append(t)
    aday = pd.DatetimeIndex(aday)
    sonuc, dagilim = [], {}
    for y in ["olay", "tr_olay"]:
        tek = np.array([fark(gun, t, y) for t in aday])
        gozlenen = {k: fark(gun, t, y) for k, t in KRIZ.items()}
        toplam = sum(gozlenen.values())
        cek = tek[rng.integers(0, len(tek), size=(CEKILIS, 3))].sum(axis=1)
        dagilim[y] = (cek, toplam)
        sonuc.append(dict(seri=y, kriz="üçü birlikte", gozlenen_fark=toplam, plasebo_ort=round(cek.mean(), 2),
                          p_tek_yonlu=round((cek >= toplam).mean(), 4), aday_gun=len(aday)))
        for k, g in gozlenen.items():
            sonuc.append(dict(seri=y, kriz=k, gozlenen_fark=g, plasebo_ort=round(tek.mean(), 2),
                              p_tek_yonlu=round((tek >= g).mean(), 4), aday_gun=len(aday)))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for a, (y, baslik) in zip(ax, [("olay", "Tüm hacktivist olaylar"), ("tr_olay", "Türkiye kaynaklı")]):
        cek, toplam = dagilim[y]
        a.hist(cek, bins=40, color="#9aa7b8")
        a.axvline(toplam, color="#c0392b", lw=2, label=f"Gerçek krizler: {toplam:+d}")
        a.set_title(baslik)
        a.set_xlabel("3 tarihte toplam (sonraki 60 gün − önceki 60 gün)")
        a.legend()
    ax[0].set_ylabel("Plasebo çekilişi")
    fig.suptitle("Plasebo testi: rastgele 'sahte kriz' tarihleri ile gerçek krizler")
    fig.tight_layout()
    fig.savefig(OUT / "kriz_disi_plasebo.png", dpi=150)
    return pd.DataFrame(sonuc)


def yogunlasma(x, karsi=None):
    """Türkiye kaynaklı saldırılarda en çok saldırı alan yabancı ülkenin payı (TR hedefler hariç)."""
    hedef = x.hedef_ulke.fillna("").str.split(";").explode().str.strip()
    hedef = hedef[(hedef != "") & (hedef != "TR") & (hedef != ">1")]
    if len(hedef) < 3:
        return None, None, len(hedef)
    say = hedef.value_counts()
    return say.index[0], say.iloc[0] / len(hedef), len(hedef)


def h3_kriz_disi(d, gun):
    tr = d[d.tr_kaynakli]
    satir = []
    for k, t in KRIZ.items():
        x = tr[(tr.tarih >= t) & (tr.tarih <= t + pd.Timedelta(days=W))]
        ulke, pay, n = yogunlasma(x)
        satir.append(dict(pencere=k, en_cok_hedef=ulke, pay=pay, hedef_sayisi=n))
    rastgele = []
    adaylar = [t for t in gun.index[:-W] if not gun.loc[t:t + pd.Timedelta(days=W)].eksik.any()
               and all(abs((t - k).days) > W for k in KRIZ.values())]
    for t in rng.choice(adaylar, size=2000, replace=False):
        t = pd.Timestamp(t)
        x = tr[(tr.tarih >= t) & (tr.tarih <= t + pd.Timedelta(days=W))]
        ulke, pay, n = yogunlasma(x)
        if pay is not None:
            rastgele.append(pay)
    rastgele = np.array(rastgele)
    for s in satir:
        if s["pay"] is not None:
            s["kriz_disi_ort_pay"] = round(rastgele.mean(), 3)
            s["p_tek_yonlu"] = round((rastgele >= s["pay"]).mean(), 4)
            s["pay"] = round(s["pay"], 3)
        s["kriz_disi_pencere"] = len(rastgele)
    return pd.DataFrame(satir)


def main():
    d = olaylar()
    gun = gunluk(d)
    d.to_csv(P / "kriz_disi_olaylar.csv", index=False)
    pd.set_option("display.width", 220)
    print(f"Dönem {BAS.date()} – {BIT.date()}: {len(d)} hacktivist olay "
          f"({d.kaynak.value_counts().to_dict()}), Türkiye kaynaklı {int(d.tr_kaynakli.sum())}; "
          f"dışarıda bırakılan gün: {int(gun.eksik.sum())}")
    for ad, f in [("dogrulama", lambda: dogrulama(d)), ("taban_oran", lambda: taban_oran(gun)),
                  ("plasebo", lambda: plasebo(gun)), ("h3", lambda: h3_kriz_disi(d, gun))]:
        t = f()
        t.to_csv(P / f"kriz_disi_{ad}.csv", index=False)
        print(f"\n== {ad} ==\n{t.to_string(index=False)}")


if __name__ == "__main__":
    main()
