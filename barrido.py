#!/usr/bin/env python3
"""Barrido de portadas: extrae titular, seccion, autor y enlace de las noticias de 7 periodicos.
Salida: JSON {fecha, periodicos:{id:[{t,s,u,a?,op?}]}} en stdout o en el fichero indicado."""
import json, re, sys, datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36",
      "Accept-Language": "es-ES,es;q=0.9"}

# id, nombre, portada, dominio, patron de URL de noticia
SITES = [
    ("elmundo", "El Mundo", ["https://www.elmundo.es/", "https://www.elmundo.es/espana.html", "https://www.elmundo.es/internacional.html", "https://www.elmundo.es/economia.html", "https://www.elmundo.es/cultura.html", "https://www.elmundo.es/deportes.html", "https://www.elmundo.es/ciencia-y-salud.html"], "elmundo.es", r"/20\d\d/\d\d/\d\d/[0-9a-f]{24}[^/]*\.html$"),
    ("elpais", "El País", ["https://elpais.com/espana/", "https://elpais.com/internacional/", "https://elpais.com/economia/", "https://elpais.com/sociedad/", "https://elpais.com/cultura/", "https://elpais.com/deportes/", "https://elpais.com/opinion/"], "elpais.com", r"/20\d\d-\d\d-\d\d/[^/]+\.html$"),
    ("abc", "ABC", ["https://www.abc.es/", "https://www.abc.es/espana/", "https://www.abc.es/internacional/", "https://www.abc.es/economia/", "https://www.abc.es/sociedad/", "https://www.abc.es/cultura/", "https://www.abc.es/deportes/"], "abc.es", r"-\d{14}-n(ts?|i)\.html$"),
    ("larazon", "La Razón", "https://www.larazon.es/", "larazon.es", r"_20\d{6}[0-9a-f]+\.html$"),
    ("elespanol", "El Español", "https://www.elespanol.com/", "elespanol.com", r"/\d{8}/[^/]+/\d+_\d+\.html$"),
    ("eldiario", "elDiario.es", "https://www.eldiario.es/", "eldiario.es", r"_1_\d+\.html$"),
    ("elconfidencial", "El Confidencial", ["https://www.elconfidencial.com/", ("https://www.elconfidencial.com/opinion/", 25, "op")], "elconfidencial.com", r"/20\d\d-\d\d-\d\d/[^/]+_\d+/?$"),
]

MAX_ITEMS = 100
SKIP_SECTIONS = {"podcasts", "juegos", "loterias", "horoscopo", "promociones", "suscripcion", "servicios", "tiempo", "el tiempo", "us", "america", "mexico", "argentina", "chile", "colombia"}

def section_of(url, domain):
    p = urlparse(url)
    host = p.netloc.split(":")[0]
    segs = [s for s in p.path.split("/") if s]
    sub = host.replace("www.", "").replace(domain, "").strip(".")
    first = segs[0] if segs and not re.match(r"^\d", segs[0]) else ""
    sec = first or sub
    return sec.replace("-", " ").strip()

# periodicos cuya portada no muestra la firma: se lee la etiqueta <meta name="author"> de cada noticia
AUTHOR_FROM_ARTICLE = {"elpais", "abc"}
AU_RX = re.compile(r"(author|autor|firma|byline|signature|signing|writer)", re.I)

def clean_author(t):
    t = clean(t)
    t = re.sub(r"(^|\s)(Redacci[oó]n|Por)\s*:\s*", " ", t, flags=re.I).strip()
    t = re.sub(r"^Por\s+", "", t)
    t = re.sub(r"\s*\d{1,2}:\d{2}.*$", "", t)          # hora al final
    t = re.sub(r"\s+\d+$", "", t)                       # contador de comentarios
    t = re.sub(r"\s+[—–-]\s+[^—–-]+$", "", t)           # " — Madrid" (ciudad)
    t = t.replace(" | ", ", ").strip(" -—|·,")
    # firmas en mayusculas seguidas de ciudad (El Mundo): "DANIEL VIAÑA Dublín Redacción: ÁNGELA MARTIALAY Madrid"
    caps = re.findall(r"(?:\b[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ.'-]+(?:\s+|$)){2,}", t.replace(",", " ,"))
    if caps and sum(len(c) for c in caps) >= len(t) * 0.5:
        t = ", ".join(c.strip().title() for c in caps)
    return t if 2 < len(t) <= 80 and not re.search(r"https?://", t) else ""

def author_near(a, rx, base):
    """Busca la firma en la tarjeta de la noticia, sin salir de una tarjeta con una sola noticia."""
    node = a
    for _ in range(6):
        node = node.parent
        if node is None:
            return ""
        urls = {urljoin(base, x["href"]).split("#")[0].split("?")[0] for x in node.find_all("a", href=True)}
        if sum(1 for x in urls if rx.search(x)) > 1:
            return ""
        el = node.find(attrs={"class": AU_RX}) or node.find(attrs={"itemprop": "author"}) or node.find(attrs={"rel": "author"})
        if el:
            return clean_author(el.get_text(" "))
    return ""

def author_from_article(u):
    try:
        r = requests.get(u, headers=UA, timeout=12)
        m = BeautifulSoup(r.text, "lxml").find("meta", attrs={"name": "author"})
        a = clean_author(m.get("content", "")) if m else ""
        return "" if a.lower() in {"el país", "el pais", "abc", "abc.es"} else a
    except Exception:
        return ""

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

def scrape(site):
    sid, name, homes, domain, pat = site
    if isinstance(homes, str):
        homes = [homes]
    # cada fuente: (url, tope de noticias o None, etiqueta o None)
    homes = [h if isinstance(h, tuple) else (h, None, None) for h in homes]
    reserved = sum(h[1] for h in homes if h[1])
    rx = re.compile(pat)
    seen, out = {}, []
    ok = 0
    home_first = len(homes) > 1 and urlparse(homes[0][0]).path in ("", "/")
    for idx, (home, cap, tag) in enumerate(homes):
        if cap:
            per_home = cap
        elif len(homes) == 1 or (home_first and idx == 0):
            per_home = MAX_ITEMS - reserved
        else:
            rest = sum(1 for h in homes[idx:] if not h[1])
            per_home = max(1, -(-(MAX_ITEMS - reserved - len(out)) // rest))
        n_home = 0
        try:
            r = requests.get(home, headers=UA, timeout=30)
            r.raise_for_status()
        except Exception:
            if len(homes) == 1:
                raise
            continue
        ok += 1
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a", href=True):
            u = urljoin(r.url, a["href"]).split("#")[0].split("?")[0]
            host = urlparse(u).netloc
            if domain not in host or not rx.search(u):
                continue
            if a.find_parent(["nav", "footer"]) or a.find_parent(attrs={"class": re.compile(r"(^|[-_ ])(nav|menu|trending|tags?|topics?|footer|ticker)([-_ ]|$)", re.I)}):
                continue
            h = a.find(["h1", "h2", "h3", "h4"]) or a.find_parent(["h1", "h2", "h3", "h4"])
            t = clean(h.get_text(" ") if h else a.get_text(" "))
            if not t or len(t) < 30 or t.startswith("Noticias de"):
                t2 = clean(a.get("title") or a.get("aria-label"))
                if len(t2) >= 30 and not t2.startswith("Noticias de"):
                    t = t2
                else:
                    continue
            au = author_near(a, rx, r.url)
            if u in seen:
                # misma noticia enlazada varias veces: conservar su posicion pero quedarse con el titular mas completo
                prev = seen[u]
                if len(t) > len(prev["t"]) and len(t) <= 300:
                    prev["t"] = t
                if au and not prev.get("a"):
                    prev["a"] = au
                if tag == "op":
                    prev["op"] = 1
                continue
            sec = section_of(u, domain)
            if sec in SKIP_SECTIONS or sec.split(" ")[0] in SKIP_SECTIONS:
                continue
            item = {"t": t[:300], "s": sec, "u": u}
            if au:
                item["a"] = au
            if tag == "op" or sec.startswith("opinion"):
                item["op"] = 1
            seen[u] = item
            out.append(item)
            n_home += 1
            if len(out) >= MAX_ITEMS:
                break
            if n_home >= per_home:
                break
        if len(out) >= MAX_ITEMS:
            break
    if not ok:
        raise RuntimeError("no se pudo leer ninguna pagina")
    if sid in AUTHOR_FROM_ARTICLE:
        falta = [x for x in out if not x.get("a")]
        with ThreadPoolExecutor(8) as ex:
            for x, au in zip(falta, ex.map(lambda x: author_from_article(x["u"]), falta)):
                if au:
                    x["a"] = au
    return out

def main():
    res = {"fecha": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "periodicos": {}, "errores": {}}
    for s in SITES:
        try:
            res["periodicos"][s[0]] = scrape(s)
        except Exception as e:
            res["periodicos"][s[0]] = []
            res["errores"][s[0]] = str(e)[:200]
    js = json.dumps(res, ensure_ascii=False)
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8").write(js)
    else:
        print(js)

if __name__ == "__main__":
    main()
