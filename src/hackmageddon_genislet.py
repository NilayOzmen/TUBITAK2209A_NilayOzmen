"""Sağlamlık analizi (±90 gün) için Hackmageddon verisini genişletir.

hackmageddon_indir.py ±60 günlük pencereler için gereken ayları indirir. ±90 gün için eksik kalan dönemler
(Şubat 2016, Mayıs–Haziran 2017, Ocak 2020) burada indirilir ve mevcut tabloyla birleştirilir.
Çıktı: data/processed/hackmageddon_genis.csv (ana veri setini değiştirmez)
"""
import pandas as pd
import hackmageddon_indir as h

h.AYLAR = ["2016/02", "2016/03", "2017/05", "2017/06", "2017/07", "2020/01", "2020/02"]


def main():
    mevcut = pd.read_csv(h.OUT / "hackmageddon_kriz_donemleri.csv")
    bilinen = set(mevcut.kaynak_yazi.dropna())
    yeni_urller = [u for u in h.yazi_listesi() if u not in bilinen]
    print(f"{len(yeni_urller)} yeni zaman çizelgesi yazısı")
    tum = []
    for u in yeni_urller:
        try:
            s = h.tablo_cek(u)
            tum += s
            print(f"  {len(s):4d} satır  {u}")
        except Exception as e:
            print(f"  HATA {u}: {e}")
    yeni = pd.DataFrame(tum)
    yeni["tarih"] = pd.to_datetime(yeni["Date"], format="%d/%m/%Y", errors="coerce")
    df = pd.concat([mevcut, yeni], ignore_index=True)
    df = df.drop_duplicates(subset=["Date", "Author", "Target", "Description"])
    df.to_csv(h.OUT / "hackmageddon_genis.csv", index=False)
    print(f"Toplam {len(df)} olay ({len(df) - len(mevcut)} yeni)")


if __name__ == "__main__":
    main()
