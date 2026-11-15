"""Elle kodlamayı uygular, son veri setini üretir ve kriz öncesi/sonrası ilk karşılaştırmayı yapar.

Önce/sonra pencereleri eşit uzunlukta (60'ar gün) olduğundan, iki dönemin olay sayıları
Poisson oranlarının eşitliği için koşullu binom testiyle karşılaştırılır:
toplam n olay verildiğinde, oranlar eşitse sonraki dönemdeki olay sayısı ~ Binom(n, 0.5).
"""
from pathlib import Path
import pandas as pd
from scipy.stats import binomtest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
KRIZ_AD = {"rusya_2015": ("2015 Rusya", "RUS"), "hollanda_2017": ("2017 Hollanda", "NLD"),
           "barispinari_2019": ("2019 Barış Pınarı", "USA")}


def son_veri_seti():
    d = pd.read_csv(P / "olaylar_aday.csv", parse_dates=["tarih"]).set_index("satir")
    e = pd.read_csv(P / "elle_kodlama.csv", dtype=str).set_index("satir")
    e.index = e.index.astype(int)
    d["sayima_dahil"], d["not"] = "evet", ""
    birlestirilen = []
    for i, r in e.iterrows():
        if r.islem.startswith("birlestir_"):
            hedef = int(r.islem.split("_")[1])
            d.loc[hedef, "kaynak"] = "+".join(sorted({d.loc[hedef, "kaynak"], d.loc[i, "kaynak"]}))
            birlestirilen.append(i)
            continue
        for c in ["aktor_turu", "kriz_ikilisi", "saldirgan_ulke", "hedef_ulke", "sayima_dahil", "not"]:
            if c in r and pd.notna(r[c]) and r[c] != "":
                d.loc[i, c] = "" if r[c] == "-" else r[c]   # "-" alanı boşaltır
        if "tarih" in r and pd.notna(r["tarih"]) and r["tarih"] != "":
            yeni = pd.Timestamp(r["tarih"])
            d.loc[i, "gun_farki"] += (yeni - d.loc[i, "tarih"]).days
            d.loc[i, "tarih"] = yeni
    d = d.drop(index=birlestirilen)
    # Haberlerden elle kodlanan olaylar (EuRepoC/Hackmageddon'da bulunmayanlar)
    h = pd.read_csv(P / "haber_kodlama.csv", parse_dates=["tarih"])
    tarihler = {"rusya_2015": "2015-11-24", "hollanda_2017": "2017-03-11", "barispinari_2019": "2019-10-09"}
    h["gun_farki"] = [(t - pd.Timestamp(tarihler[k])).days for t, k in zip(h.tarih, h.kriz)]
    d = pd.concat([d, h], ignore_index=True)
    d.loc[d.aktor_turu == "suc", "sayima_dahil"] = "hayir"
    d = d.drop(columns=[c for c in ["mukerrer_aday", "karsi"] if c in d.columns])
    d = d.sort_values(["kriz", "tarih"]).reset_index(drop=True)
    d.insert(0, "olay_id", [f"{k[:3].upper()}-{n:02d}" for n, k in enumerate(d.kriz, 1)])
    d.to_csv(P / "olaylar_v02.csv", index=False)
    return d


def main():
    d = son_veri_seti()
    s = d[d.sayima_dahil == "evet"]
    print(f"Son veri seti: {len(d)} kayıt | sayıma dahil: {len(s)} | haber kodlaması dahil\n")
    print("Sayıma dahil olayların aktör türü:", s.aktor_turu.value_counts().to_dict(), "\n")
    satir = []
    for k, (ad, _) in KRIZ_AD.items():
        x = s[s.kriz == k]
        for etiket, alt in [("tüm olaylar", x), ("yalnız kriz ikilisi", x[x.kriz_ikilisi == "evet"])]:
            once, sonra = int((alt.gun_farki < 0).sum()), int((alt.gun_farki >= 0).sum())
            n = once + sonra
            p = binomtest(sonra, n, 0.5, alternative="greater").pvalue if n else float("nan")
            satir.append(dict(kriz=ad, kapsam=etiket, once=once, sonra=sonra, p_tek_yonlu=round(p, 4)))
    # Üç krizin birleşik testi
    for etiket, alt in [("tüm olaylar", s), ("yalnız kriz ikilisi", s[s.kriz_ikilisi == "evet"])]:
        once, sonra = int((alt.gun_farki < 0).sum()), int((alt.gun_farki >= 0).sum())
        p = binomtest(sonra, once + sonra, 0.5, alternative="greater").pvalue
        satir.append(dict(kriz="Üç kriz birlikte", kapsam=etiket, once=once, sonra=sonra, p_tek_yonlu=round(p, 4)))
    t = pd.DataFrame(satir)
    t.to_csv(P / "pilot_once_sonra_testi.csv", index=False)
    print(t.to_string(index=False))

    # Haftalık grafik: olay sayısı (çubuk) + GDELT Goldstein (çizgi)
    fig, axes = plt.subplots(3, 1, figsize=(9, 8.5), sharex=True)
    for ax, (k, (ad, karsi)) in zip(axes, KRIZ_AD.items()):
        x = s[s.kriz == k].copy()
        x["hafta"] = (x.gun_farki // 7)
        hafta = pd.Series(0, index=range(-9, 9))
        ikili = hafta.copy()
        hafta = hafta.add(x.groupby("hafta").size(), fill_value=0)
        ikili = ikili.add(x[x.kriz_ikilisi == "evet"].groupby("hafta").size(), fill_value=0)
        ax.bar(hafta.index, hafta.values, color="#c9d6e8", width=0.8, label="Türkiye ile ilgili hacktivist/devlet olayı")
        ax.bar(ikili.index, ikili.values, color="#2f6db3", width=0.8, label="bunlardan kriz ikilisiyle ilgili olanlar")
        ax.set_ylabel("olay / hafta")
        ax.set_ylim(0, 5)
        ax.axvline(-0.5, color="crimson", ls="--", lw=1)
        ax.set_title(f"{ad} krizi", loc="left", fontsize=10)
        g = pd.read_csv(P / f"gdelt_gunluk_{k.split('_')[1]}_{karsi}.csv")
        gh = g.assign(hafta=g.gun // 7).groupby("hafta").goldstein.mean()
        ax2 = ax.twinx()
        ax2.plot(gh.index, gh.values, color="#444", lw=1.4, marker="o", ms=3, label="GDELT Goldstein (haftalık ort.)")
        ax2.axhline(0, color="#999", lw=0.5)
        ax2.set_ylim(-4, 4)
        ax2.set_ylabel("Goldstein", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
    h1, l1 = axes[0].get_legend_handles_labels()
    h2, l2 = axes[0].get_figure().axes[3].get_legend_handles_labels()
    axes[0].legend(h1 + h2, l1 + l2, fontsize=7, loc="upper left")
    axes[-1].set_xticks(range(-9, 9))
    axes[-1].set_xlabel("Kriz haftasına göre hafta (0 = kriz haftası)")
    fig.suptitle("Pilot: kriz öncesi ve sonrası siber olaylar ve diplomatik gerginlik", fontsize=12)
    fig.tight_layout()
    fig.savefig(ROOT / "outputs/pilot_haftalik.png", dpi=150)


if __name__ == "__main__":
    main()
