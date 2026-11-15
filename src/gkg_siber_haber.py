"""GDELT 1.0 günlük GKG dosyalarından Türkiye ile ilgili siber saldırı haberlerini çeker.

Bir haber kaydı şu koşullarda aday sayılır:
  - THEMES alanında CYBER_ATTACK teması var ve
  - LOCATIONS alanında Türkiye (ülke kodu TU) geçiyor ya da URL/ORGANIZATIONS'da "turk" geçiyor.
Her gün için ayrıca tüm CYBER_ATTACK haberlerinin sayısı saklanır (normalizasyon için).
"""
import csv, io, json, zipfile, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/gkg"
OUT.mkdir(parents=True, exist_ok=True)
KRIZLER = [date(2015, 11, 24), date(2017, 3, 11), date(2019, 10, 9)]
PENCERE = 60
csv.field_size_limit(10**9)
COLS = ["DATE", "NUMARTS", "COUNTS", "THEMES", "LOCATIONS", "PERSONS",
        "ORGANIZATIONS", "TONE", "CAMEOEVENTIDS", "SOURCES", "SOURCEURLS"]


def turkiye_mi(locs: str, orgs: str, urls: str) -> bool:
    # LOCATIONS: tip#ad#ülkeKodu#... kayıtları ';' ile ayrılır; Türkiye FIPS kodu "TU"
    for loc in locs.split(";"):
        p = loc.split("#")
        if len(p) > 2 and p[2] == "TU":
            return True
    s = (orgs + " " + urls).lower()
    return "turk" in s or "türk" in s


def gun_isle(gun: date):
    hedef = OUT / f"{gun:%Y%m%d}.jsonl"
    if hedef.exists():
        return gun, "var"
    url = f"http://data.gdeltproject.org/gkg/{gun:%Y%m%d}.gkg.csv.zip"
    hata = None
    for _ in range(3):
        try:
            veri = urllib.request.urlopen(url, timeout=180).read()
            break
        except Exception as e:
            hata = e
    else:
        return gun, f"HATA {hata}"
    toplam_siber, adaylar = 0, []
    with zipfile.ZipFile(io.BytesIO(veri)) as z:
        with z.open(z.namelist()[0]) as f:
            r = csv.reader(io.TextIOWrapper(f, "utf-8", errors="replace"), delimiter="\t")
            next(r, None)
            for row in r:
                if len(row) < 11 or "CYBER_ATTACK" not in row[3]:
                    continue
                toplam_siber += 1
                if turkiye_mi(row[4], row[6], row[10]):
                    d = dict(zip(COLS, row))
                    adaylar.append({"tarih": d["DATE"], "numarts": d["NUMARTS"],
                                    "ton": d["TONE"].split(",")[0],
                                    "temalar": d["THEMES"], "konumlar": d["LOCATIONS"],
                                    "kurumlar": d["ORGANIZATIONS"], "kaynaklar": d["SOURCES"],
                                    "urller": d["SOURCEURLS"]})
    gecici = hedef.with_suffix(".tmp")
    with open(gecici, "w") as f:
        f.write(json.dumps({"_meta": True, "tarih": f"{gun:%Y%m%d}",
                            "toplam_siber_haber": toplam_siber}) + "\n")
        for a in adaylar:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    gecici.rename(hedef)
    return gun, f"siber={toplam_siber} türkiye={len(adaylar)}"


def main():
    gunler = sorted({k + timedelta(days=d) for k in KRIZLER for d in range(-PENCERE, PENCERE + 1)})
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, (gun, s) in enumerate(ex.map(gun_isle, gunler), 1):
            print(f"[{i}/{len(gunler)}] {gun} -> {s}", flush=True)


if __name__ == "__main__":
    main()
