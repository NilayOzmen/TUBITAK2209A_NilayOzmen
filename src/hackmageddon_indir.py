"""Hackmageddon siber saldırı zaman çizelgelerini (kriz dönemleri için) indirip tek tabloya dönüştürür.

Kaynak: https://www.hackmageddon.com — her ay iki "cyber attacks timeline" yazısı yayımlanır.
Sütunlar: ID, Date, Author, Target, Description, Attack, Target Class, Attack Class, Country, Link
Attack Class kodları: H = Hacktivizm, CE = Siber casusluk, CC = Siber suç, CW = Siber savaş
"""
import re, time, urllib.request
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/hackmageddon"
RAW.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "data/processed"
UA = {"User-Agent": "Mozilla/5.0 (akademik arastirma; kriz-siber projesi)"}
# Yazılar ilgili dönemden sonraki ayda da yayımlanabildiği için +1 ay taranır
AYLAR = ([f"2015/{m:02d}" for m in range(9, 13)] + ["2016/01", "2016/02"]
         + [f"2017/{m:02d}" for m in range(1, 7)]
         + [f"2019/{m:02d}" for m in range(8, 13)] + ["2020/01"])


def getir(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")


def yazi_listesi():
    urller = set()
    for ay in AYLAR:
        for sayfa in ("", "page/2/"):
            try:
                s = getir(f"https://www.hackmageddon.com/{ay}/{sayfa}")
            except Exception:
                continue
            urller |= set(re.findall(r'href="(https://www\.hackmageddon\.com/\d{4}/\d{2}/\d{2}/[^"]*cyber-attacks-timeline[^"]*/)"', s))
            time.sleep(0.5)
    return sorted(urller)


def wpdatatable_cek(url, html):
    """Sunucu taraflı sayfalanan wpDataTables tablolarının tüm satırlarını ajax ile çeker."""
    import http.cookiejar, json, urllib.parse
    m = re.search(r'wdtNonceFrontendServerSide_(\d+)" name="[^"]*" value="([^"]+)"', html)
    if not m:
        return None
    tablo_id = m.group(1)
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    taze = op.open(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "ignore")
    nonce = re.search(r'wdtNonceFrontendServerSide_\d+" name="[^"]*" value="([^"]+)"', taze).group(1)
    soup = BeautifulSoup(taze, "lxml")
    tb = soup.find("table", class_="wpDataTable")
    basliklar = [th.get_text(" ", strip=True) for th in tb.find("thead").find_all("th")]
    params = {"draw": 1, "start": 0, "length": 2000, "wdtNonce": nonce}
    for i in range(len(basliklar)):
        params[f"columns[{i}][data]"] = i
        params[f"columns[{i}][searchable]"] = "true"
        params[f"columns[{i}][search][value]"] = ""
    req = urllib.request.Request(
        f"https://www.hackmageddon.com/wp-admin/admin-ajax.php?action=get_wdtable&table_id={tablo_id}",
        data=urllib.parse.urlencode(params).encode(), headers={**UA, "Referer": url}, method="POST")
    veri = json.loads(op.open(req, timeout=60).read())
    satirlar = []
    for r in veri["data"]:
        d = dict(zip(basliklar, r))
        link = re.search(r'href="([^"]+)"', str(d.get("Link", "")))
        d["Link"] = link.group(1) if link else d.get("Link", "")
        d["kaynak_yazi"] = url
        satirlar.append(d)
    return satirlar


def tablo_cek(url):
    dosya = RAW / (url.rstrip("/").split("/")[-1] + ".html")
    if not dosya.exists():
        dosya.write_text(getir(url))
        time.sleep(0.5)
    html = dosya.read_text()
    ajax = wpdatatable_cek(url, html)
    if ajax is not None:
        return ajax
    soup = BeautifulSoup(html, "lxml")
    satirlar = []
    for tb in soup.find_all("table"):
        trs = tb.find_all("tr")
        if not trs:
            continue
        baslik = [c.get_text(" ", strip=True) for c in trs[0].find_all(["td", "th"])]
        if "Date" not in baslik or "Author" not in baslik:
            continue
        for tr in trs[1:]:
            hucre = tr.find_all(["td", "th"])
            if len(hucre) != len(baslik):
                continue
            d = dict(zip(baslik, [c.get_text(" ", strip=True) for c in hucre]))
            # Bazı dönemlerde ayrı "Link" sütunu yok; bağlantı açıklama hücresine gömülü
            link_hucre = hucre[baslik.index("Link")] if "Link" in baslik else tr
            a = link_hucre.find("a", href=True) or tr.find("a", href=True)
            d["Link"] = a["href"] if a and a.has_attr("href") else d.get("Link", "")
            d["kaynak_yazi"] = url
            satirlar.append(d)
    return satirlar


def main():
    urller = yazi_listesi()
    print(f"{len(urller)} zaman çizelgesi yazısı bulundu")
    tum = []
    for u in urller:
        try:
            s = tablo_cek(u)
            tum += s
            print(f"  {len(s):4d} satır  {u}")
        except Exception as e:
            print(f"  HATA {u}: {e}")
    df = pd.DataFrame(tum)
    df["tarih"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df = df.drop_duplicates(subset=["Date", "Author", "Target", "Description"])
    df.to_csv(OUT / "hackmageddon_kriz_donemleri.csv", index=False)
    print(f"Toplam {len(df)} olay, tarih okunamayan: {df.tarih.isna().sum()}")


if __name__ == "__main__":
    main()
