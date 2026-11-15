"""İndirilen GDELT satırlarından ülke çifti bazında günlük gerginlik serisi üretir."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/gdelt"
OUT = ROOT / "data/processed"
FIG = ROOT / "outputs"

# Barış Pınarı'nda en sert tepkiyi veren ana karşı taraf olarak ABD alındı;
# AB ülkeleri ikinci analizde eklenebilir.
KRIZLER = {
    "2015 Rusya uçak krizi": ("2015-11-24", ["RUS"]),
    "2017 Türkiye–Hollanda krizi": ("2017-03-11", ["NLD"]),
    "2019 Barış Pınarı Harekâtı": ("2019-10-09", ["USA"]),
}


def yukle(baslangic, bitis):
    gunler = pd.date_range(baslangic, bitis)
    parcalar = [pd.read_csv(RAW / f"{g:%Y%m%d}.csv", dtype=str) for g in gunler
                if (RAW / f"{g:%Y%m%d}.csv").exists()]
    df = pd.concat(parcalar, ignore_index=True)
    for c in ["goldstein", "tone", "mentions"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["quad"] = pd.to_numeric(df["quad"], errors="coerce")
    df["tarih"] = pd.to_datetime(df["sqldate"], format="%Y%m%d")
    return df


def gunluk_seri(df, karsi):
    m = ((df.a1 == "TUR") & df.a2.isin(karsi)) | ((df.a2 == "TUR") & df.a1.isin(karsi))
    d = df[m].copy()
    d["w_gold"] = d.goldstein * d.mentions
    d["w_tone"] = d.tone * d.mentions
    d["catisma"] = d.quad.isin([3, 4]).astype(int)  # sözlü/maddi çatışma
    s = d.groupby("tarih").agg(olay=("id", "size"), anma=("mentions", "sum"),
                               w_gold=("w_gold", "sum"), w_tone=("w_tone", "sum"),
                               catisma=("catisma", "sum"))
    s["goldstein"] = s.w_gold / s.anma          # anma sayısıyla ağırlıklı ortalama
    s["ton"] = s.w_tone / s.anma
    s["catisma_orani"] = s.catisma / s.olay
    return s[["olay", "anma", "goldstein", "ton", "catisma_orani"]]


def main():
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharey=False)
    ozet = []
    for ax, (ad, (tarih, karsi)) in zip(axes, KRIZLER.items()):
        k = pd.Timestamp(tarih)
        df = yukle(k - pd.Timedelta(days=60), k + pd.Timedelta(days=60))
        s = gunluk_seri(df, karsi)
        s["gun"] = (s.index - k).days
        s.to_csv(OUT / f"gdelt_gunluk_{tarih[:4]}_{'-'.join(karsi)}.csv")
        once, sonra = s[s.gun < 0], s[s.gun >= 0]
        ozet.append({"kriz": ad, "karsi_taraf": ",".join(karsi), "gun_sayisi": len(s),
                     "olay_once_ort": round(once.olay.mean(), 1), "olay_sonra_ort": round(sonra.olay.mean(), 1),
                     "goldstein_once": round(once.goldstein.mean(), 2), "goldstein_sonra": round(sonra.goldstein.mean(), 2),
                     "ton_once": round(once.ton.mean(), 2), "ton_sonra": round(sonra.ton.mean(), 2)})
        ax.plot(s.gun, s.goldstein.rolling(3, center=True).mean(), lw=1.6, label="Goldstein (3 günlük ort.)")
        ax.plot(s.gun, s.ton.rolling(3, center=True).mean(), lw=1.6, label="Ton (3 günlük ort.)")
        ax.axvline(0, color="crimson", ls="--", lw=1)
        ax.axhline(0, color="grey", lw=0.6)
        ax.set_title(f"{ad} — Türkiye ↔ {', '.join(karsi)}", fontsize=10, loc="left")
        ax.set_xlim(-60, 60)
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8, loc="lower left")
    axes[-1].set_xlabel("Kriz tarihine göre gün")
    fig.suptitle("GDELT: kriz öncesi ve sonrası diplomatik gerginlik", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "gdelt_gerginlik_pilot.png", dpi=150)
    o = pd.DataFrame(ozet)
    o.to_csv(OUT / "kriz_pencere_ozeti_gdelt.csv", index=False)
    print(o.to_string(index=False))


if __name__ == "__main__":
    main()
