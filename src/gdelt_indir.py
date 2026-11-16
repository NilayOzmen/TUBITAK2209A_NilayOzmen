"""GDELT 1.0 günlük olay dosyalarından Türkiye'nin taraf olduğu olayları çeker.

Kullanım: python3 src/gdelt_indir.py
Her kriz için kriz tarihinin ±60 günü indirilir; yalnızca Actor1 veya Actor2'si
TUR olan ve olay tarihi (SQLDATE) indirilen günle aynı olan satırlar saklanır.
"""
import csv, io, sys, zipfile, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/gdelt"
OUT.mkdir(parents=True, exist_ok=True)

KRIZLER = {"rusya_2015": date(2015, 11, 24), "hollanda_2017": date(2017, 3, 11),
           "barispinari_2019": date(2019, 10, 9), "brunson_2018": date(2018, 8, 10)}
PENCERE = 60
# GDELT 1.0 sütun indeksleri
I = dict(id=0, sqldate=1, a1=7, a2=17, root=28, quad=29, goldstein=30,
         mentions=31, sources=32, articles=33, tone=34, url=57)
csv.field_size_limit(10**8)


def gun_isle(gun: date):
    hedef = OUT / f"{gun:%Y%m%d}.csv"
    if hedef.exists():
        return gun, "var"
    url = f"http://data.gdeltproject.org/events/{gun:%Y%m%d}.export.CSV.zip"
    for deneme in range(3):
        try:
            veri = urllib.request.urlopen(url, timeout=120).read()
            break
        except Exception as e:  # ağ hatasında tekrar dene
            hata = e
    else:
        return gun, f"HATA {hata}"
    sd = f"{gun:%Y%m%d}"
    satirlar = []
    with zipfile.ZipFile(io.BytesIO(veri)) as z:
        with z.open(z.namelist()[0]) as f:
            for r in csv.reader(io.TextIOWrapper(f, "utf-8", errors="replace"), delimiter="\t"):
                if len(r) < 58 or r[I["sqldate"]] != sd:
                    continue
                if "TUR" not in (r[I["a1"]], r[I["a2"]]):
                    continue
                satirlar.append([r[I[k]] for k in I])
    gecici = hedef.with_suffix(".tmp")
    with open(gecici, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(I))
        w.writerows(satirlar)
    gecici.rename(hedef)
    return gun, len(satirlar)


def main():
    gunler = sorted({k + timedelta(days=d) for k in KRIZLER.values()
                     for d in range(-PENCERE, PENCERE + 1)})
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, (gun, sonuc) in enumerate(ex.map(gun_isle, gunler), 1):
            print(f"[{i}/{len(gunler)}] {gun} -> {sonuc}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
