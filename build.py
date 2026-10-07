#!/usr/bin/env python3
"""Builds kalimatisland.com from src.html (one bilingual source, data-l="ar"/"en" on every text):

    /index.html      Arabic (the default, x-default), lang=ar dir=rtl
    /en/index.html   English, lang=en dir=ltr

Each page carries only its own language (nothing hidden for search engines), its own title, description, canonical,
hreflang alternates, Open Graph and JSON-LD (MobileApplication, WebSite, Organization, FAQPage built from the page's
own questions). Also writes sitemap.xml and robots.txt.

    python3 build.py        (needs beautifulsoup4)
"""
import json
import pathlib
import re

from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent
SITE = "https://kalimatisland.com"
APP = "https://apps.apple.com/app/id6816729943"
TODAY = "2026-10-07"

META = {
    "ar": {
        "title": "جزيرة الكلمات | لعبة تعليمية للأطفال لتعلّم الكلام والنطق والحروف العربية",
        "description": "جزيرة الكلمات لعبة أطفال تعليمية ثلاثية الأبعاد للآيفون والآيباد: ٥٠ لعبة في ١٥ جزيرة يتعلّم فيها طفلك الكلام والنطق والحروف والأرقام والألوان وهو يلعب. للأطفال من ٣ إلى ٦ سنوات، بلا إعلانات، وتعمل بلا إنترنت.",
        "keywords": "لعبة تعليمية للأطفال، ألعاب أطفال، تعليم الكلام للأطفال، تعليم النطق، تأخر الكلام عند الأطفال، تعليم الحروف العربية، تعليم الأرقام للأطفال، تعليم الألوان، ألعاب أطفال بدون إنترنت، لعبة أطفال ٣ سنوات، لعبة أطفال ٤ سنوات، العاب تعليمية عربية، جزيرة الكلمات",
        "og_title": "جزيرة الكلمات: يلعب… يضحك… ويتعلّم الكلام!",
        "og_locale": "ar_AR",
        "path": "/",
    },
    "en": {
        "title": "Kalimat Island | Arabic Learning Game for Kids: Words, Letters & Speech",
        "description": "Kalimat Island is a 3D educational game for iPhone and iPad: 50 games across 15 islands where kids aged 3 to 6 learn to say Arabic words, letters, numbers and colours while they play. No ads, and it works offline.",
        "keywords": "Arabic learning game for kids, learn Arabic for kids, Arabic alphabet app, Arabic words for toddlers, kids speech game, educational games for kids, Arabic letters tracing, Kalimat Island",
        "og_title": "Kalimat Island: play, laugh… and learn to talk!",
        "og_locale": "en_US",
        "path": "/en/",
    },
}


def build(lang: str) -> str:
    other = "en" if lang == "ar" else "ar"
    m = META[lang]
    soup = BeautifulSoup((ROOT / "src.html").read_text(), "html.parser")
    for el in soup.select(f'[data-l="{other}"]'):
        el.decompose()
    for el in soup.select("[data-l]"):
        del el["data-l"]
    html = soup.html
    html["lang"] = lang
    html["dir"] = "rtl" if lang == "ar" else "ltr"

    head = soup.head
    head.title.string = m["title"]
    for name in ("description", "keywords"):
        tag = head.find("meta", attrs={"name": name}) or soup.new_tag("meta", attrs={"name": name})
        tag["content"] = m[name]
        head.append(tag)
    for prop, val in (("og:title", m["og_title"]), ("og:description", m["description"]), ("og:url", SITE + m["path"]),
                      ("og:locale", m["og_locale"]), ("og:site_name", "جزيرة الكلمات · Kalimat Island")):
        tag = head.find("meta", attrs={"property": prop}) or soup.new_tag("meta", attrs={"property": prop})
        tag["content"] = val
        head.append(tag)
    for old in head.find_all("link", rel=lambda r: r and ("canonical" in r or "alternate" in r)):
        old.decompose()
    head.append(soup.new_tag("link", rel="canonical", href=SITE + m["path"]))
    for hl, path in (("ar", "/"), ("en", "/en/"), ("x-default", "/")):
        head.append(soup.new_tag("link", rel="alternate", hreflang=hl, href=SITE + path))

    # the parents' questions, as structured data from the page itself
    faq = []
    for d in soup.select("details[data-faq]"):
        q = d.summary.get_text(" ", strip=True)
        a = d.p.get_text(" ", strip=True)
        faq.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
        del d["data-faq"]
    shots = [SITE + "/a/shot_%s_%d.webp" % (lang, i) for i in range(1, 9)]
    graph = [
        {"@type": "MobileApplication", "@id": SITE + "/#app",
         "name": "جزيرة الكلمات" if lang == "ar" else "Kalimat Island",
         "alternateName": ["Kalimat Island", "جزيرة الكلمات", "Kalimat Island: Arabic Words"],
         "description": m["description"], "url": SITE + m["path"], "image": SITE + "/a/og.jpg",
         "screenshot": shots, "operatingSystem": "iOS, iPadOS", "applicationCategory": "EducationalApplication",
         "applicationSubCategory": "Kids learning game", "inLanguage": ["ar", "en"], "contentRating": "4+",
         "isFamilyFriendly": True,
         "audience": {"@type": "PeopleAudience", "suggestedMinAge": 3, "suggestedMaxAge": 6},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "category": "free with a one-time in-app purchase"},
         "downloadUrl": APP, "installUrl": APP, "publisher": {"@id": SITE + "/#org"}},
        {"@type": "Organization", "@id": SITE + "/#org", "name": "Kalimat Island", "alternateName": "جزيرة الكلمات",
         "url": SITE + "/", "logo": SITE + "/a/logo.png", "email": "xfanezz.developer@gmail.com",
         "sameAs": [APP]},
        {"@type": "WebSite", "@id": SITE + "/#site", "name": "جزيرة الكلمات · Kalimat Island", "url": SITE + "/",
         "inLanguage": lang, "publisher": {"@id": SITE + "/#org"}},
        {"@type": "FAQPage", "@id": SITE + m["path"] + "#faq", "inLanguage": lang, "mainEntity": faq},
    ]
    ld = soup.new_tag("script", type="application/ld+json")
    ld.string = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    head.append(ld)

    # the language switch becomes a link between the two pages; the script no longer switches languages itself
    btn = soup.find(id="lang")
    link = soup.new_tag("a", attrs={"class": "lang", "href": "/en/" if lang == "ar" else "/", "hreflang": other,
                                    "lang": other})
    link.string = "English" if lang == "ar" else "العربية"
    btn.replace_with(link)
    out = str(soup)
    out = re.sub(r"  function setLang\(l\) \{.*?document\.getElementById\(\"lang\"\)\.addEventListener\([^\n]*\n", "", out,
                 flags=re.S)
    if lang == "en":  # one folder down
        out = re.sub(r'(src|href|poster)="(a/|fonts/|privacy/|support/)', r'\1="../\2', out)
        out = out.replace("url(fonts/", "url(../fonts/").replace("url(a/", "url(../a/")
    # the sound button's two labels, written by the script
    if lang == "ar":
        out = out.replace("""'<span data-l="ar">🔊 شغّل الصوت</span><span data-l="en">🔊 Sound on</span>'""", "'🔊 شغّل الصوت'")
        out = out.replace("""'<span data-l="ar">🔇 اكتم الصوت</span><span data-l="en">🔇 Mute</span>'""", "'🔇 اكتم الصوت'")
    else:
        out = out.replace("""'<span data-l="ar">🔊 شغّل الصوت</span><span data-l="en">🔊 Sound on</span>'""", "'🔊 Sound on'")
        out = out.replace("""'<span data-l="ar">🔇 اكتم الصوت</span><span data-l="en">🔇 Mute</span>'""", "'🔇 Mute'")
    return "<!doctype html>\n" + out.replace("<!DOCTYPE html>", "").lstrip()


def main():
    (ROOT / "index.html").write_text(build("ar"))
    (ROOT / "en").mkdir(exist_ok=True)
    (ROOT / "en" / "index.html").write_text(build("en"))
    alt = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{SITE}{p}"/>'
                  for h, p in (("ar", "/"), ("en", "/en/"), ("x-default", "/")))
    urls = [(p, alt) for p in ("/", "/en/")] + [(p, "") for p in ("/support/", "/privacy/", "/privacy/android/")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p, a in urls:
        sm.append(f"<url><loc>{SITE}{p}</loc><lastmod>{TODAY}</lastmod>{a}</url>")
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print("built: index.html, en/index.html, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
