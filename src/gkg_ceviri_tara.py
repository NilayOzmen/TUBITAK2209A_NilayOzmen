"""GDELT 2.0 çeviri (Translingual) GKG dosyalarından Türkiye ile ilgili siber saldırı haberlerini çeker.

Kapsam: seçilen krizin ±GUN günü (varsayılan 14; önerideki 121 günlük pencere için 60), 15 dakikalık dosyalar.
Kullanım: python3 src/gkg_ceviri_tara.py [barispinari_2019|rusya_2015|hollanda_2017|brunson_2018|dogu_akdeniz_2020] [GUN]
Daha önce indirilmiş dosyalar atlanır; pencere genişletildiğinde yalnızca yeni günler indirilir.
Bir kayıt saklanır, eğer:
  - siber: temalarda CYBER_ATTACK var YA DA sayfa başlığında hack/siber/ddos/deface/cyber geçiyor, VE
  - Türkiye ile ilgili: haber Türkçe (srclc:tur) YA DA konumlarda Türkiye (FIPS: TU) var.
Ayrıca her dosya için toplam Türkçe haber ve Türkçe siber haber sayısı kaydedilir (yoğunluk serisi için).
"""
import csv, io, json, re, sys, zipfile, urllib.request
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KRIZLER = {"barispinari_2019": datetime(2019, 10, 9), "rusya_2015": datetime(2015, 11, 24),
           "hollanda_2017": datetime(2017, 3, 11), "brunson_2018": datetime(2018, 8, 10),
           "dogu_akdeniz_2020": datetime(2020, 8, 10)}
KRIZ_AD = sys.argv[1] if len(sys.argv) > 1 else "barispinari_2019"
KRIZ_T = KRIZLER[KRIZ_AD]
# Barış Pınarı'nın ilk taraması data/raw/gkg_ceviri altında; diğerleri kriz adıyla alt klasörde
OUT = ROOT / "data/raw/gkg_ceviri" / ("" if KRIZ_AD == "barispinari_2019" else KRIZ_AD)
OUT.mkdir(parents=True, exist_ok=True)
GUN = int(sys.argv[2]) if len(sys.argv) > 2 else 14
BAS, BIT = KRIZ_T - timedelta(days=GUN), KRIZ_T + timedelta(days=GUN + 1)   # BIT hariç
SIBER = re.compile(r"hack|siber|ddos|deface|cyber|tahrif|bilişim saldır", re.I)
# Ön süzgeç için SIBER ifadesindeki kelimeler (küçük harf, bayt) + tema kodu
ANAHTAR_B = [k.encode() for k in SIBER.pattern.split("|")] + [b"cyber_attack"]
csv.field_size_limit(10**9)


def baslik(extras):
    m = re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", extras)
    return m.group(1) if m else ""


def tu_konum(*alanlar):
    for alan in alanlar:
        for loc in alan.split(";"):
            p = loc.split("#")
            if len(p) > 2 and p[2] == "TU":
                return True
    return False


def dosya_isle(t):
    ad = t.strftime("%Y%m%d%H%M%S")
    hedef = OUT / f"{ad}.jsonl"
    if hedef.exists():
        return ad, "var"
    url = f"http://data.gdeltproject.org/gdeltv2/{ad}.translation.gkg.csv.zip"
    for _ in range(3):
        try:
            veri = urllib.request.urlopen(url, timeout=120).read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                hedef.write_text(json.dumps({"_meta": True, "dosya": ad, "eksik": True}) + "\n")
                return ad, "404"
            hata = e
        except Exception as e:
            hata = e
    else:
        return ad, f"HATA {hata}"
    n_tur = n_tur_siber = 0
    kayitlar = []
    with zipfile.ZipFile(io.BytesIO(veri)) as z:
        ham = z.read(z.namelist()[0])
    # Türkçe haber sayısı: TranslationInfo alanı her satırda bir kez geçer
    n_tur = ham.count(b"srclc:tur")
    # Hızlı ön süzgeç: siber izi taşıyan satırların yerleri tüm dosyada tek geçişte bulunur, yalnızca onlar ayrıştırılır
    kucuk = ham.lower()
    baslar = set()
    for kelime in ANAHTAR_B:
        i = kucuk.find(kelime)
        while i != -1:
            bas = ham.rfind(b"\n", 0, i) + 1
            baslar.add(bas)
            son = ham.find(b"\n", i)
            i = kucuk.find(kelime, son if son != -1 else len(ham))
    for bas in sorted(baslar):
        son = ham.find(b"\n", bas)
        satir = ham[bas:son if son != -1 else len(ham)]
        r = next(csv.reader([satir.decode("utf-8", "replace").rstrip("\r")], delimiter="\t"), [])
        if len(r) < 27:
            continue
        tur = "srclc:tur" in r[25]
        temalar = r[7] + ";" + r[8]
        b = baslik(r[26])
        siber = "CYBER_ATTACK" in temalar or bool(SIBER.search(b))
        if not siber:
            continue
        n_tur_siber += tur
        if tur or tu_konum(r[9], r[10]):
            kayitlar.append({"tarih": r[1][:8], "kaynak": r[3], "url": r[4], "baslik": b[:300],
                             "dil": re.search(r"srclc:(\w+)", r[25]).group(1) if "srclc:" in r[25] else "",
                             "ton": r[15].split(",")[0], "cyber_tema": "CYBER_ATTACK" in temalar})
    gecici = hedef.with_suffix(".tmp")
    with open(gecici, "w") as fh:
        fh.write(json.dumps({"_meta": True, "dosya": ad, "turkce_haber": n_tur, "turkce_siber": n_tur_siber}) + "\n")
        for k in kayitlar:
            fh.write(json.dumps(k, ensure_ascii=False) + "\n")
    gecici.rename(hedef)
    return ad, f"tr={n_tur} tr_siber={n_tur_siber} aday={len(kayitlar)}"


def main():
    zamanlar = []
    t = BAS
    while t < BIT:
        zamanlar.append(t)
        t += timedelta(minutes=15)
    with ProcessPoolExecutor(max_workers=int(__import__("os").environ.get("ISCI", 16))) as ex:
        for i, (ad, s) in enumerate(ex.map(dosya_isle, zamanlar), 1):
            if i % 48 == 0 or "HATA" in s:
                print(f"[{i}/{len(zamanlar)}] {ad} -> {s}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
