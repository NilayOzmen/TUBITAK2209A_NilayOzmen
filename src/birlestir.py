"""EuRepoC ve Hackmageddon'daki Türkiye olaylarını kodlama kılavuzuna göre tek veri setinde birleştirir.

Çıktı: data/processed/olaylar_aday.csv  (otomatik kodlama + mükerrer adayları)
Elle düzeltmeler data/processed/elle_kodlama.csv dosyasında tutulur ve son veri setine uygulanır.
"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
KRIZLER = {"rusya_2015": ("2015-11-24", "RU"), "hollanda_2017": ("2017-03-11", "NL"),
           "barispinari_2019": ("2019-10-09", "US")}
TURK_GRUP = r"Turk|Türk|Ayyildiz|Ayyıldız|Aslan Neferler|Börteçine|Borte"
ULKE = {"Turkey": "TR", "Russia": "RU", "Netherlands": "NL", "United States": "US", "Iran": "IR",
        "Israel": "IL", "Armenia": "AM", "Azerbaijan": "AZ", "Germany": "DE", "Austria": "AT"}


def kriz_bul(t):
    for k, (tarih, karsi) in KRIZLER.items():
        g = (t - pd.Timestamp(tarih)).days
        if -60 <= g <= 60:
            return k, g, karsi
    return None, None, None


def sektor(s):
    s = str(s).lower()
    for anahtar, deger in [("financ", "finans"), ("bank", "finans"), ("gov", "kamu"), ("military", "kamu"),
                           ("defen", "kamu"), ("diplomat", "kamu"), ("media", "medya"), ("news", "medya"),
                           ("energy", "kritik_altyapi"), ("telecom", "kritik_altyapi"), ("infrastructure", "kritik_altyapi"),
                           ("registrar", "kritik_altyapi"), ("individual", "bireyler"), ("education", "diger")]:
        if anahtar in s:
            return deger
    return "diger"


def saldiri(s):
    s = str(s).lower()
    for anahtar, deger in [("ddos", "ddos"), ("denial", "ddos"), ("deface", "tahrifat"), ("leak", "veri_sizintisi"),
                           ("data theft", "veri_sizintisi"), ("hijack", "hesap_ele_gecirme"), ("account", "hesap_ele_gecirme"),
                           ("espionage", "casusluk"), ("targeted", "casusluk"), ("malware", "diger")]:
        if anahtar in s:
            return deger
    return "diger"


def eurepoc():
    e = pd.read_csv(P / "eurepoc_turkiye.csv", parse_dates=["start"])
    g = pd.read_csv(ROOT / "data/raw/eurepoc/eurepoc_global_dataset_1_3.csv", low_memory=False,
                    usecols=["incident_id", "receiver_category", "source_url"])
    e = e.merge(g.drop_duplicates("incident_id"), on="incident_id", how="left")
    rows = []
    for _, r in e.iterrows():
        k, gun, karsi = kriz_bul(r.start)
        if k is None:
            continue
        sal_ulke = ";".join(sorted({ULKE.get(x.strip(), x.strip()) for x in str(r.initiator_country).split(";")}))
        hed_ulke = ";".join(sorted({ULKE.get(x.strip(), x.strip()) for x in str(r.receiver_country).split(";")}))
        tur = {"devlet_destekli": "devlet_destekli", "hacktivist": "hacktivist"}.get(r.aktor_turu, "belirsiz")
        if "Criminal" in str(r.initiator_subcategory):
            tur = "suc"
        rows.append(dict(kaynak="eurepoc", kaynak_id=r.incident_id, tarih=r.start.date(),
                         tarih_kesinligi="ay" if r.start.day == 1 else "gun", kriz=k, gun_farki=gun,
                         saldirgan=r.initiator_name, saldirgan_ulke=sal_ulke, hedef=r["name"],
                         hedef_ulke=hed_ulke, hedef_sektor=sektor(r.receiver_category), aktor_turu=tur,
                         saldiri_turu=saldiri(r.incident_type), karsi=karsi,
                         kaynak_url=str(r.source_url).split(";")[0]))
    return rows


def hackmageddon():
    d = pd.read_csv(P / "hackmageddon_kriz_donemleri.csv", parse_dates=["tarih"])
    d["Description"] = d["Description"].fillna(d.get("Event  Description"))
    metin = d.Author.fillna("") + " | " + d.Target.fillna("") + " | " + d.Description.fillna("")
    secim = d.Country.fillna("").str.contains(r"\bTR\b") | metin.str.contains(TURK_GRUP + r"|Turkey", case=False)
    rows = []
    for _, r in d[secim].iterrows():
        if pd.isna(r.tarih):
            continue
        k, gun, karsi = kriz_bul(r.tarih)
        if k is None:
            continue
        sinif = str(r["Attack Class"]).strip()
        turk_saldirgan = bool(re.search(TURK_GRUP, f"{r.Author} {r.Description}", re.I))
        if sinif.startswith("H"):
            tur = "hacktivist"
        elif sinif.startswith(("CE", "CW")):
            tur = "devlet_destekli" if re.search(r"state|government-backed|sponsored|APT", str(r.Description), re.I) else "belirsiz"
        elif sinif.startswith("CC"):
            tur = "suc"
        else:
            tur = "belirsiz"
        rows.append(dict(kaynak="hackmageddon", kaynak_id=r.get("ID"), tarih=r.tarih.date(),
                         tarih_kesinligi="gun", kriz=k, gun_farki=gun, saldirgan=r.Author,
                         saldirgan_ulke="TR" if turk_saldirgan else "", hedef=r.Target,
                         hedef_ulke=str(r.Country).replace("\n", ";"), hedef_sektor=sektor(r["Target Class"]),
                         aktor_turu=tur, saldiri_turu=saldiri(r.Attack), karsi=karsi, kaynak_url=r.Link,
                         aciklama=str(r.Description)[:300]))
    return rows


def main():
    df = pd.DataFrame(eurepoc() + hackmageddon())
    df["tarih"] = pd.to_datetime(df["tarih"])
    taraflar = df.saldirgan_ulke.fillna("") + ";" + df.hedef_ulke.fillna("")
    df["kriz_ikilisi"] = [("TR" in t and karsi in t) for t, karsi in zip(taraflar, df.karsi)]
    df["kriz_ikilisi"] = df.kriz_ikilisi.map({True: "evet", False: "hayir"})
    df = df.sort_values(["kriz", "tarih"]).reset_index(drop=True)
    # Mükerrer adayı: farklı kaynak, ≤3 gün fark, aynı kriz ve hedef ülke kesişimi
    df["mukerrer_aday"] = ""
    for i, a in df.iterrows():
        for j, b in df.iloc[i + 1:].iterrows():
            if a.kaynak != b.kaynak and a.kriz == b.kriz and abs((a.tarih - b.tarih).days) <= 3:
                if set(str(a.hedef_ulke).split(";")) & set(str(b.hedef_ulke).split(";")):
                    df.loc[j, "mukerrer_aday"] = f"{df.loc[j, 'mukerrer_aday']} {i}".strip()
    df.to_csv(P / "olaylar_aday.csv", index_label="satir")
    print(df[["kriz", "gun_farki", "kaynak", "tarih_kesinligi", "aktor_turu", "kriz_ikilisi",
              "saldirgan", "hedef", "mukerrer_aday"]].to_string(max_colwidth=32))


if __name__ == "__main__":
    main()
