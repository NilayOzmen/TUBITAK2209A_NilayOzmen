"""Çeviri katmanı taramasının çıktısını süzer: başlığında siber saldırıya özgü ifade geçen tekil haberler.

Ayrıca günlük Türkçe siber haber yoğunluğu serisini üretir (kriz öncesi/sonrası karşılaştırma için).
"""
import html, json, re, sys, urllib.parse
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
KRIZLER = {"barispinari_2019": "2019-10-09", "rusya_2015": "2015-11-24", "hollanda_2017": "2017-03-11",
           "brunson_2018": "2018-08-10", "dogu_akdeniz_2020": "2020-08-10"}
KRIZ_AD = sys.argv[1] if len(sys.argv) > 1 else "barispinari_2019"
KRIZ = pd.Timestamp(KRIZLER[KRIZ_AD])
RAW = ROOT / "data/raw/gkg_ceviri" / ("" if KRIZ_AD == "barispinari_2019" else KRIZ_AD)
EK = "" if KRIZ_AD == "barispinari_2019" else "_" + KRIZ_AD
# Başlıkta aranacak, gerçek saldırıya işaret eden ifadeler (Türkçe + İngilizce)
GUCLU = re.compile(r"hack|hacker|siber.?sald[ıi]r|siber.?atak|ddos|deface|tahrif|[çc][öo]kert|ele.?ge[çc]ir|"
                   r"cyber.?attack|cyberattack|siber.?ordu|siber.?sava[şs]|siber.?tim", re.I)


def url_baslik(url):
    """2015-2017 dosyalarında PAGE_TITLE alanı yok; başlık yerine URL'deki metin (slug) kullanılır."""
    yol = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    parca = max(yol.strip("/").split("/"), key=len) if yol.strip("/") else ""
    return re.sub(r"[-_]+", " ", re.sub(r"\.(html?|php|aspx?)$", "", parca))
HARIC = re.compile(r"virüs|virus|covid|grip|kalp|hastal|tarım|meyve|futbol maç", re.I)


def main():
    meta, aday = [], []
    for f in sorted(RAW.glob("*.jsonl")):
        with open(f) as fh:
            m = json.loads(fh.readline())
            if m.get("eksik"):
                continue
            meta.append({"zaman": m["dosya"], "turkce_haber": m["turkce_haber"], "turkce_siber": m["turkce_siber"]})
            for line in fh:
                d = json.loads(line)
                d["baslik"] = html.unescape(d["baslik"]) or url_baslik(d["url"])
                if GUCLU.search(d["baslik"]) and not HARIC.search(d["baslik"]):
                    aday.append(d)
    m = pd.DataFrame(meta)
    m["tarih"] = pd.to_datetime(m.zaman.str[:8])
    g = m.groupby("tarih")[["turkce_haber", "turkce_siber"]].sum()
    g["gun"] = (g.index - KRIZ).days
    g.to_csv(P / f"gkg_ceviri_gunluk{EK}.csv")
    a = pd.DataFrame(aday)
    a["tarih"] = pd.to_datetime(a.tarih)
    a["gun"] = (a.tarih - KRIZ).dt.days
    a["anahtar"] = a.baslik.str.lower().str.replace(r"[^a-zçğıöşü0-9 ]", "", regex=True).str[:70]
    t = (a.sort_values("tarih").groupby("anahtar")
         .agg(gun=("gun", "min"), n=("url", "size"), dil=("dil", "first"), baslik=("baslik", "first"), url=("url", "first"))
         .sort_values("gun"))
    t.to_csv(P / f"gkg_ceviri_adaylar{EK}.csv", index=False)
    print(f"Taranan dosya: {len(m)} | Türkçe haber: {int(m.turkce_haber.sum())} | aday kayıt: {len(a)} | tekil başlık: {len(t)}")
    once, sonra = g[g.gun < 0].turkce_siber.mean(), g[g.gun >= 0].turkce_siber.mean()
    print(f"Günlük Türkçe 'siber' temalı haber ort.: önce {once:.1f} → sonra {sonra:.1f}")
    for _, r in t.iterrows():
        print(f"{int(r.gun):+4d} x{r.n:<3d} [{r.dil}] {r.baslik[:110]}")


if __name__ == "__main__":
    main()
