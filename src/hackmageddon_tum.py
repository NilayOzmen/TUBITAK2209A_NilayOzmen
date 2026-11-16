"""Kriz dışı karşılaştırma için Hackmageddon'ın 2015–2024 arasındaki bütün zaman çizelgelerini indirir.

hackmageddon_indir.py yalnızca kriz pencerelerine ait ayları indirir. Bu betik aynı yöntemi bütün döneme uygular.
Çıktı: data/processed/hackmageddon_2015_2024.csv (yeniden dağıtılmaz; .gitignore'da)
"""
import time
import pandas as pd
from bs4 import BeautifulSoup
import hackmageddon_indir as h

# Bir döneme ait yazılar sonraki ay da yayımlanabildiği için Ocak 2025 de taranır
h.AYLAR = [f"{y}/{m:02d}" for y in range(2015, 2025) for m in range(1, 13)] + ["2025/01", "2025/02"]


def yeni_bicim(url):
    """2021 ve sonrası: istemci taraflı tablo; tarih sütunları 'Date Reported' / 'Date Occurred'.
    Saldırının gerçekleştiği tarih (Date Occurred) esas alınır, yoksa bildirildiği tarih kullanılır."""
    dosya = h.RAW / (url.rstrip("/").split("/")[-1] + ".html")
    soup = BeautifulSoup(dosya.read_text(), "lxml")
    satirlar = []
    for tb in soup.find_all("table", class_="wpDataTable"):
        basliklar = [th.get_text(" ", strip=True) for th in tb.find("thead").find_all("th")]
        if "Date Reported" not in basliklar:
            continue
        for tr in tb.find("tbody").find_all("tr"):
            hucre = tr.find_all("td")
            if len(hucre) != len(basliklar):
                continue
            d = dict(zip(basliklar, [c.get_text(" ", strip=True) for c in hucre]))
            olus = d.get("Date Occurred", "")
            d["Date"] = olus if olus and olus != "-" else d["Date Reported"]
            a = hucre[basliklar.index("Link")].find("a", href=True) if "Link" in basliklar else None
            d["Link"] = a["href"] if a else ""
            d["kaynak_yazi"] = url
            satirlar.append(d)
    return satirlar


def cek(url):
    for deneme in range(3):
        try:
            s = h.tablo_cek(url)
            return s if s else yeni_bicim(url)
        except Exception as e:
            hata = e
            time.sleep(5)
    raise hata


def main():
    urller = h.yazi_listesi()
    print(f"{len(urller)} zaman çizelgesi yazısı bulundu", flush=True)
    tum, hata = [], []
    for i, u in enumerate(urller, 1):
        try:
            s = cek(u)
            tum += s
            print(f"[{i}/{len(urller)}] {len(s):4d} satır  {u}", flush=True)
        except Exception as e:
            hata.append(u)
            print(f"[{i}/{len(urller)}] HATA {u}: {e}", flush=True)
    df = pd.DataFrame(tum)
    df["tarih"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df = df.drop_duplicates(subset=["Date", "Author", "Target", "Description"])
    df.to_csv(h.OUT / "hackmageddon_2015_2024.csv", index=False)
    print(f"Toplam {len(df)} olay, tarih okunamayan: {df.tarih.isna().sum()}, hatalı yazı: {len(hata)}")
    for u in hata:
        print("  hata:", u)


if __name__ == "__main__":
    main()
