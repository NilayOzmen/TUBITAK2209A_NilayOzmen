"""GKG'den çekilen Türkiye + CYBER_ATTACK haberlerini süzer ve kodlanacak aday listesini üretir.

Gürültüyü azaltmak için bir haber ancak URL'sinde siber saldırıya özgü bir kelime geçiyorsa aday sayılır.
Aynı URL birden fazla gün geçiyorsa ilk görüldüğü gün tutulur. Ayrıca günlük
"Türkiye ile ilgili siber saldırı haberi" sayısı (siber haber yoğunluğu) serisi üretilir.
"""
import json, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/gkg"
P = ROOT / "data/processed"
KRIZLER = {"rusya_2015": "2015-11-24", "hollanda_2017": "2017-03-11", "barispinari_2019": "2019-10-09"}
SIBER = re.compile(r"hack|cyber|siber|ddos|deface|tahrif|anonymous|ayyildiz|redhack|turkhack", re.I)
GURULTU = re.compile(r"thanksgiving|turkey-(recipe|dinner|day)|roast|stuffing", re.I)


def kriz_bul(t):
    for k, tarih in KRIZLER.items():
        g = (t - pd.Timestamp(tarih)).days
        if -60 <= g <= 60:
            return k, g
    return None, None


def main():
    satirlar, gunluk = [], []
    for f in sorted(RAW.glob("*.jsonl")):
        with open(f) as fh:
            meta = json.loads(fh.readline())
            tarih = pd.Timestamp(meta["tarih"])
            n_tr = 0
            for line in fh:
                d = json.loads(line)
                n_tr += 1
                for url in d["urller"].split("<UDIV>"):
                    if SIBER.search(url) and not GURULTU.search(url):
                        satirlar.append({"tarih": tarih, "url": url, "ton": d["ton"],
                                         "numarts": int(d["numarts"] or 1)})
            gunluk.append({"tarih": tarih, "tum_siber_haber": meta["toplam_siber_haber"],
                           "turkiye_siber_haber": n_tr})
    a = pd.DataFrame(satirlar).sort_values("tarih").drop_duplicates("url")
    a[["kriz", "gun_farki"]] = a.tarih.apply(lambda t: pd.Series(kriz_bul(t)))
    a["baslik_tahmini"] = a.url.str.rstrip("/").str.split("/").str[-1].str.replace(r"[-_]", " ", regex=True).str[:110]
    a.to_csv(P / "gkg_adaylar.csv", index=False)
    g = pd.DataFrame(gunluk)
    g[["kriz", "gun_farki"]] = g.tarih.apply(lambda t: pd.Series(kriz_bul(t)))
    g.to_csv(P / "gkg_gunluk_siber_haber.csv", index=False)
    print(f"Aday haber (URL filtresi sonrası, tekil): {len(a)}")
    print(a.groupby("kriz").size().to_string())


if __name__ == "__main__":
    main()
