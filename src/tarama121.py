"""Türkçe 121 günlük taramada bulunan olayları v03'e ekleyerek olaylar_v04.csv'yi üretir.

Girdi:  data/processed/olaylar_v03.csv          (değiştirilmez)
        data/processed/tarama121_kodlama.csv    (yeni olaylar ve birleştirmeler)
Çıktı:  data/processed/olaylar_v04.csv

Kurallar:
- v03'teki olay numaraları korunur (ikinci kodlayıcı formu bunlara dayanır); yeni olaylar her krizde
  sıradaki numarayı alır (ör. RUS-50).
- `birlestir` sütunu doluysa satır yeni olay olarak eklenmez; mükerrer kuralı (≤3 gün, aynı saldırgan ve
  hedef ülke) gereği belirtilen olaya bağlanır: tarih en erken güne çekilir, kaynak bağlantısı ve not eklenir.
- Suç kategorisindeki olaylar sayım dışıdır (kılavuz bölüm 3).
Kullanım: python3 src/tarama121.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
KRIZ_TARIHI = {"rusya_2015": "2015-11-24", "hollanda_2017": "2017-03-11", "barispinari_2019": "2019-10-09"}


def main():
    v3 = pd.read_csv(P / "olaylar_v03.csv", dtype={"kaynak_id": str})
    v3["tarih"] = pd.to_datetime(v3.tarih)
    y = pd.read_csv(P / "tarama121_kodlama.csv", dtype=str).fillna("")
    y["tarih"] = pd.to_datetime(y.tarih)
    y["gun_farki"] = [(t - pd.Timestamp(KRIZ_TARIHI[k])).days for t, k in zip(y.tarih, y.kriz)]

    d = v3.set_index("olay_id")
    for _, r in y[y.birlestir != ""].iterrows():
        h = r.birlestir
        if h not in d.index:
            raise SystemExit(f"Birleştirilecek olay bulunamadı: {h}")
        if r.tarih < d.loc[h, "tarih"]:
            d.loc[h, "gun_farki"] += (r.tarih - d.loc[h, "tarih"]).days
            d.loc[h, "tarih"] = r.tarih
        d.loc[h, "hedef"] = f"{d.loc[h, 'hedef']}; {r.hedef}"
        d.loc[h, "not"] = f"{d.loc[h, 'not']} | {r.tarih.date()}: {r['not']} ({r.kaynak_url})"
    d = d.reset_index()

    yeni = y[y.birlestir == ""].drop(columns="birlestir").copy()
    yeni.loc[yeni.aktor_turu == "suc", "sayima_dahil"] = "hayir"
    son_no = d.olay_id.str.split("-").str[1].astype(int).groupby(d.kriz).max()
    numara = []
    for k in yeni.kriz:
        son_no[k] += 1
        numara.append(f"{k[:3].upper()}-{son_no[k]:02d}")
    yeni.insert(0, "olay_id", numara)
    v4 = pd.concat([d, yeni], ignore_index=True).sort_values(["kriz", "tarih", "olay_id"]).reset_index(drop=True)
    v4["tarih"] = v4.tarih.dt.date
    v4.to_csv(P / "olaylar_v04.csv", index=False)

    s3, s4 = v3[v3.sayima_dahil == "evet"], v4[v4.sayima_dahil == "evet"]
    print(f"v03: {len(v3)} kayıt, {len(s3)} sayıma dahil  →  v04: {len(v4)} kayıt, {len(s4)} sayıma dahil")
    print(f"Yeni olay: {len(yeni)} | mevcut olaya bağlanan: {(y.birlestir != '').sum()}")
    for k in KRIZ_TARIHI:
        a, b = s4[s4.kriz == k], s3[s3.kriz == k]
        print(f"  {k:18s} önce {int((b.gun_farki < 0).sum())}→{int((a.gun_farki < 0).sum())}, "
              f"sonra {int((b.gun_farki >= 0).sum())}→{int((a.gun_farki >= 0).sum())}")


if __name__ == "__main__":
    main()
