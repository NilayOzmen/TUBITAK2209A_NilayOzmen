"""Çeviri katmanı taramasının çıktısını süzer: başlığında siber saldırıya özgü ifade geçen tekil haberler.

Ayrıca günlük Türkçe siber haber yoğunluğu serisini üretir (kriz öncesi/sonrası karşılaştırma için).
"""
import html, json, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/gkg_ceviri"
P = ROOT / "data/processed"
KRIZ = pd.Timestamp("2019-10-09")
# Başlıkta aranacak, gerçek saldırıya işaret eden ifadeler (Türkçe + İngilizce)
GUCLU = re.compile(r"hack|hacker|siber saldır|siber atak|ddos|deface|tahrif|çökert|ele geçir|"
                   r"cyber.?attack|cyberattack|siber ordu|siber savaş|siber tim", re.I)
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
                d["baslik"] = html.unescape(d["baslik"])
                if GUCLU.search(d["baslik"]) and not HARIC.search(d["baslik"]):
                    aday.append(d)
    m = pd.DataFrame(meta)
    m["tarih"] = pd.to_datetime(m.zaman.str[:8])
    g = m.groupby("tarih")[["turkce_haber", "turkce_siber"]].sum()
    g["gun"] = (g.index - KRIZ).days
    g.to_csv(P / "gkg_ceviri_gunluk.csv")
    a = pd.DataFrame(aday)
    a["tarih"] = pd.to_datetime(a.tarih)
    a["gun"] = (a.tarih - KRIZ).dt.days
    a["anahtar"] = a.baslik.str.lower().str.replace(r"[^a-zçğıöşü0-9 ]", "", regex=True).str[:70]
    t = (a.sort_values("tarih").groupby("anahtar")
         .agg(gun=("gun", "min"), n=("url", "size"), dil=("dil", "first"), baslik=("baslik", "first"), url=("url", "first"))
         .sort_values("gun"))
    t.to_csv(P / "gkg_ceviri_adaylar.csv", index=False)
    print(f"Taranan dosya: {len(m)} | Türkçe haber: {int(m.turkce_haber.sum())} | aday kayıt: {len(a)} | tekil başlık: {len(t)}")
    once, sonra = g[g.gun < 0].turkce_siber.mean(), g[g.gun >= 0].turkce_siber.mean()
    print(f"Günlük Türkçe 'siber' temalı haber ort.: önce {once:.1f} → sonra {sonra:.1f}")
    for _, r in t.iterrows():
        print(f"{int(r.gun):+4d} x{r.n:<3d} [{r.dil}] {r.baslik[:110]}")


if __name__ == "__main__":
    main()
