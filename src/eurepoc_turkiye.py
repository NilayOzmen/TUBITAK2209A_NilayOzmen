"""EuRepoC verisinden Türkiye'yi içeren siber olayları çıkarır ve kriz pencerelerini özetler."""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/eurepoc/eurepoc_global_dataset_1_3.csv"
OUT = ROOT / "data/processed"
OUT.mkdir(parents=True, exist_ok=True)

KRIZLER = {
    "2015 Rusya uçak krizi": "2015-11-24",
    "2017 Türkiye–Hollanda krizi": "2017-03-11",
    "2019 Barış Pınarı Harekâtı": "2019-10-09",
}
PENCERE = 60
TR = "Turkey|Türkiye|Turkiye"


def aktor_turu(row) -> str:
    """Devlet destekli / hacktivist / diğer ayrımı (1.1.1'deki tanıma göre)."""
    cat = str(row["initiator_category"])
    sub = str(row["initiator_subcategory"])
    if "State" in cat:  # State, State affiliated actor
        return "devlet_destekli"
    if "Hacktivist" in sub or "hacktivist" in sub.lower():
        return "hacktivist"
    if "Non-state" in cat:
        return "devlet_disi_diger"
    return "belirsiz"


def main():
    g = pd.read_csv(RAW, low_memory=False)
    g["start"] = pd.to_datetime(g["start_date"], format="%d.%m.%Y", errors="coerce")
    tr_hedef = g["receiver_country"].fillna("").str.contains(TR)
    tr_saldirgan = g["initiator_country"].fillna("").str.contains(TR)
    t = g[tr_hedef | tr_saldirgan].copy()
    t["turkiye_rolu"] = (
        tr_hedef[t.index].map({True: "hedef", False: ""})
        + tr_saldirgan[t.index].map({True: "+saldirgan", False: ""})
    ).str.strip("+")
    t["aktor_turu"] = t.apply(aktor_turu, axis=1)

    cols = ["incident_id", "name", "start", "receiver_country", "initiator_name",
            "initiator_country", "initiator_category", "initiator_subcategory",
            "incident_type", "turkiye_rolu", "aktor_turu", "offline_conflict_name"]
    t[cols].sort_values("start").to_csv(OUT / "eurepoc_turkiye.csv", index=False)

    print(f"Toplam olay (EuRepoC): {len(g)}  |  Türkiye'yi içeren: {len(t)}")
    print("\nYıllara göre Türkiye olayları:")
    print(t["start"].dt.year.value_counts().sort_index().to_string())
    print("\nAktör türü:")
    print(t["aktor_turu"].value_counts().to_string())

    print("\nKriz pencereleri (±60 gün):")
    satirlar = []
    for ad, tarih in KRIZLER.items():
        k = pd.Timestamp(tarih)
        once = t[(t.start >= k - pd.Timedelta(days=PENCERE)) & (t.start < k)]
        sonra = t[(t.start >= k) & (t.start <= k + pd.Timedelta(days=PENCERE))]
        satirlar.append({"kriz": ad, "once": len(once), "sonra": len(sonra),
                         "sonra_hacktivist": int((sonra.aktor_turu == "hacktivist").sum()),
                         "sonra_devlet": int((sonra.aktor_turu == "devlet_destekli").sum())})
        for _, r in pd.concat([once, sonra]).iterrows():
            print(f"   {ad[:4]} | {r.start.date()} | {r.aktor_turu:16} | {r.turkiye_rolu:15} | {str(r['name'])[:70]}")
    ozet = pd.DataFrame(satirlar)
    ozet.to_csv(OUT / "kriz_pencere_ozeti_eurepoc.csv", index=False)
    print("\n" + ozet.to_string(index=False))


if __name__ == "__main__":
    main()
