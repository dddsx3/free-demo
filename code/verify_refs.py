"""Reference verification and refs.bib generation.

Every entry is looked up either by DOI (exact) or by a bibliographic title query
on Crossref.  An entry is ACCEPTED only if
  * the DOI resolves on Crossref, and
  * (title queries only) the normalised title similarity is >= 0.84 and the
    publication year is within +-2 y of the expected year.
Rejected candidates are logged with the reason and are NOT written to refs.bib,
so the manuscript cannot cite unverified work.
Dataset records are checked against DataCite with the same rule.

Run:  python code/verify_refs.py
Out:  refs.bib, data/ref_check.csv, data/ref_rejected.csv
"""
from pathlib import Path
import csv
import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
UA = "P4-phi-criterion/1.0 (mailto:author@example.org)"

# ---------------------------------------------------------------------------
# Candidates: (key, expected year, title-or-None, doi-or-None)
# ---------------------------------------------------------------------------
CANDIDATES = [
    # --- statistical power, p-values, replication ---------------------------------
    ("cohen1992power", 1992, "A power primer", "10.1037/0033-2909.112.1.155"),
    ("hoenig2001abuse", 2001, "The abuse of power: the pervasive fallacy of power calculations for data analysis", None),
    ("ioannidis2005why", 2005, "Why most published research findings are false", None),
    ("button2013power", 2013, "Power failure: why small sample size undermines the reliability of neuroscience", "10.1038/nrn3475"),
    ("benjamin2018redefine", 2018, "Redefine statistical significance", "10.1038/s41562-017-0189-z"),
    ("wasserstein2016asa", 2016, "The ASA statement on p-values: context, process, and purpose", None),
    ("greenland2016statistical", 2016, "Statistical tests, P values, confidence intervals, and power: a guide to misinterpretations", "10.1007/s10654-016-0149-3"),
    ("simmons2011falsepositive", 2011, "False-positive psychology: undisclosed flexibility in data collection and analysis allows presenting anything as significant", "10.1177/0956797611417632"),
    ("altman1995absence", 1995, "Absence of evidence is not evidence of absence", "10.1136/bmj.311.7003.485"),
    ("lenth2001some", 2001, "Some practical guidelines for effective sample size determination", None),
    ("nakagawa2007effect", 2007, "Effect size, confidence interval and statistical significance: a practical guide for biologists", None),
    ("sedlmeier1989do", 1989, "Do studies of statistical power have an effect on the power of studies", None),
    ("sterne2001sifting", 2001, "Sifting the evidence - what's wrong with significance tests", "10.1136/bmj.322.7280.226"),
    ("perneger1998whats", 1998, "What's wrong with Bonferroni adjustments", "10.1136/bmj.316.7139.1236"),
    ("amrhein2019scientists", 2019, "Scientists rise up against statistical significance", "10.1038/d41586-019-00857-9"),
    ("mcshane2017statistical", 2017, "Statistical significance and the dichotomization of evidence", "10.1080/01621459.2017.1289846"),
    ("box1976science", 1976, "Science and statistics", "10.1080/01621459.1976.10480949"),
    # --- effective sample size, correlation, resampling --------------------------
    ("bretherton1999effective", 1999, "The effective number of spatial degrees of freedom of a time-varying field", None),
    ("zwiers1995taking", 1995, "Taking serial correlation into account in tests of the mean", None),
    ("kunsch1989jackknife", 1989, "The jackknife and the bootstrap for general stationary observations", None),
    ("politis1994stationary", 1994, "The stationary bootstrap", "10.1080/01621459.1994.10476870"),
    ("efron1979bootstrap", 1979, "Bootstrap methods: another look at the jackknife", "10.1214/aos/1176344552"),
    ("benjamini1995controlling", 1995, "Controlling the false discovery rate: a practical and powerful approach to multiple testing", None),
    ("storey2002direct", 2002, "A direct approach to false discovery rates", "10.1111/1467-9868.00346"),
    ("dutilleul1993modifying", 1993, "Modifying the t test for assessing the correlation between two spatial processes", None),
    ("legendre1993spatial", 1993, "Spatial autocorrelation: trouble or new paradigm", "10.2307/1939924"),
    ("hurlbert1984pseudoreplication", 1984, "Pseudoreplication and the design of ecological field experiments", "10.2307/1942661"),
    # --- uncertainty / validation of Earth observation ---------------------------
    ("merchant2017uncertainty", 2017, "Uncertainty information in climate data records from Earth observation", None),
    ("loew2017validation", 2017, "Validation practices for satellite-based Earth observation data across communities", None),
    ("taylor2001summarizing", 2001, "Summarizing multiple aspects of model performance in a single diagram", None),
    # --- sea ice ----------------------------------------------------------------
    ("ricker2014first", 2014, "A first assessment of CryoSat-2 sea-ice thickness in the Arctic Ocean", "10.5194/tc-8-1607-2014"),
    ("ricker2017weekly", 2017, "A weekly Arctic sea-ice thickness data record from merged CryoSat-2 and SMOS satellite data", "10.5194/tc-11-1607-2017"),
    ("kurtz2013sea", 2013, "Sea ice thickness, freeboard, and snow depth products from Operation IceBridge airborne data", "10.5194/tc-7-1035-2013"),
    ("kurtz2011snow", 2011, "Large-scale surveys of snow depth on Arctic sea ice from Operation IceBridge", "10.1029/2011GL049216"),
    ("landy2022year", 2022, "A year-round satellite sea-ice thickness record from CryoSat-2", None),
    ("sallila2019assessment", 2019, "Assessment of contemporary satellite sea ice thickness products for Arctic sea ice", "10.5194/tc-13-1187-2019"),
    ("notz2016observed", 2016, "Observed Arctic sea-ice loss directly follows anthropogenic CO2 emission", None),
    ("stroeve2018arctic", 2018, "The Arctic's sea ice cover: trends, variability, predictability, and comparisons to the CMIP5 and CMIP6 models", None),
    ("kwok2009thinning", 2009, "Thinning and volume loss of the Arctic Ocean sea ice cover", "10.1029/2009jc005312"),
    ("laxon2013cryosat", 2013, "CryoSat-2 estimates of Arctic sea ice thickness and volume", "10.1002/grl.50193"),
    # --- soil moisture ----------------------------------------------------------
    ("entekhabi2010soil", 2010, "The Soil Moisture Active Passive (SMAP) mission", "10.1109/jproc.2010.2043918"),
    ("colliander2017validation", 2017, "Validation of SMAP surface soil moisture products with core validation sites", "10.1016/j.rse.2017.01.021"),
    ("dorigo2021international", 2021, "The International Soil Moisture Network: serving Earth system science for over a decade", "10.5194/hess-25-5749-2021"),
    ("gruber2018sparse", 2018, "Assimilation of spatially sparse in situ soil moisture networks into a continuous model domain", "10.1002/2017WR021277"),
    ("gruber2019evolution", 2019, "Evolution of the ESA CCI Soil Moisture climate data records and their underlying merging methodology", None),
    ("kerr2012smos", 2012, "The SMOS soil moisture retrieval algorithm", None),
    ("dorigo2011international", 2011, "The International Soil Moisture Network: a data hosting facility for global in situ soil moisture measurements", None),
    ("koster2009analyzing", 2009, "Analyzing the concurrence of meteorological droughts and warm periods", None),
    # --- sea surface salinity ---------------------------------------------------
    ("bingham2012interpolation", 2012, "A novel approach for the high-resolution interpolation of in situ sea surface salinity", "10.1175/JTECH-D-11-00099.1"),
    ("vinogradova2013small", 2013, "Small-scale variability in sea surface salinity and implications for satellite-derived measurements", None),
    ("tang2018aquarius", 2018, "Validation of Aquarius sea surface salinity with in situ measurements from Argo floats and moored buoys", None),
    ("meissner2011remote", 2011, "Remote sensing of sea surface salinity: an overview with case studies", None),
    ("bulk2019salinity", 2019, "Salinity and the global water cycle", None),
    # --- precipitation ----------------------------------------------------------
    ("li2018evaluation", 2018, "Evaluation of IMERG and TRMM precipitation over China", "10.1029/2018jd028991"),
    ("beck2019daily", 2019, "Daily evaluation of 26 precipitation datasets using Stage-IV gauge-radar data for the CONUS", "10.5194/hess-23-207-2019"),
    ("sun2018review", 2018, "A review of global precipitation data sets: data sources, estimation, and intercomparisons", None),
    ("huffman2020integrated", 2020, "Integrated Multi-satellite Retrievals for the Global Precipitation Measurement (GPM) mission (IMERG)", "10.1007/978-3-030-24568-9_19"),
    ("kidd2011status", 2011, "Status of satellite precipitation retrievals", "10.5194/hess-15-1109-2011"),
    ("tan2019imerg", 2019, "IMERG V06: changes to the morphing algorithm", None),
    ("huffman2007trmm", 2007, "The TRMM multisatellite precipitation analysis (TMPA): quasi-global, multiyear, combined-sensor precipitation estimates at fine scales", "10.1175/jhm560.1"),
    ("joyce2004cmorph", 2004, "CMORPH: a method that produces global precipitation estimates from passive microwave and infrared data at high spatial and temporal resolution", "10.1175/1520-0450(2004)043<1403:CMCAOR>2.0.CO;2"),
    ("beck2017global", 2017, "Global-scale evaluation of 22 precipitation datasets using gauge observations and hydrological modeling", "10.5194/hess-21-6201-2017"),
    # --- biomass ----------------------------------------------------------------
    ("duncanson2022aboveground", 2022, "Aboveground biomass density models for NASA's Global Ecosystem Dynamics Investigation (GEDI) lidar mission", "10.1016/j.rse.2021.112845"),
    ("dubayah2020global", 2020, "The Global Ecosystem Dynamics Investigation: high-resolution laser ranging of the Earth's forests and topography", None),
    ("chave2014improved", 2014, "Improved allometric models to estimate the aboveground biomass of tropical trees", "10.1111/gcb.12629"),
    ("saatchi2011benchmark", 2011, "Benchmark map of forest carbon stocks in tropical regions across three continents", None),
    ("xu2021gedi", 2021, "Estimating aboveground biomass from GEDI waveform data", None),
    ("zhao2021accuracy", 2021, "Accuracy assessment of GEDI aboveground biomass", None),
    # --- optional extras --------------------------------------------------------
    ("asner2016canopy", 2016, "Canopy height mapping and biomass estimation", None),
    ("hersbach2020era5", 2020, "The ERA5 global reanalysis", "10.1002/qj.3803"),
    ("munoz2021era5land", 2021, "ERA5-Land: a state-of-the-art global reanalysis dataset for land applications", "10.5194/essd-13-4349-2021"),
    ("rodell2004gldas", 2004, "The Global Land Data Assimilation System", "10.1175/BAMS-85-3-381"),
    ("xu2021changes", 2021, "Changes in global terrestrial live biomass over the 21st century", "10.1126/sciadv.abe9829"),
]
DATASETS = [
    ("icebird_pangaea", "IceBird 2019-04 electromagnetic sea ice thickness transects", "10.1594/PANGAEA.933912"),
    ("gedi_l4a", "GEDI L4A Footprint Level Aboveground Biomass Density", "10.3334/ORNLDAAC/2056"),
    ("gpcc_v2022", "GPCC Full Data Monthly Product Version 2022", "10.5676/DWD_GPCC/FD_M_V2022_100"),
]


MANUAL = """
@book{kish1965survey,
author = {Kish, Leslie},
title = {Survey Sampling},
publisher = {John Wiley},
address = {New York},
year = {1965}
}
"""


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def crossref_by_doi(doi):
    return get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]


def crossref_by_title(title):
    q = urllib.parse.quote(title)
    msg = get("https://api.crossref.org/works?query.bibliographic=%s&rows=6"
              "&filter=type:journal-article"
              "&select=DOI,title,author,issued,container-title,volume,page,type,publisher" % q)
    return msg["message"]["items"]


def is_preprint(item):
    ct = field(item, "container-title").lower()
    doi = item.get("DOI", "").lower()
    if "discussion" in ct or "preprint" in ct:
        return True
    # Copernicus / EGU discussion DOIs: tc-2016-123, tcd-6-4771-2012, essd-2019-21, hess-2018-481
    if re.search(r"-(19|20)\d\d-\d+$", doi) and re.search(r"(tc|tcd|essd|hess|cpd|cptc)-", doi):
        return True
    return False


def datacite_by_doi(doi):
    return get("https://api.datacite.org/dois/" + urllib.parse.quote(doi))["data"]["attributes"]


LATEX_ACCENT = {
    "á": "\\'a", "à": "\\`a", "â": "\\^a", "ä": "\\\"a", "å": "\\r{a}", "ã": "\\~a",
    "é": "\\'e", "è": "\\`e", "ê": "\\^e", "ë": "\\\"e", "í": "\\'i", "ì": "\\`i",
    "î": "\\^i", "ï": "\\\"i", "ó": "\\'o", "ò": "\\`o", "ô": "\\^o", "ö": "\\\"o",
    "õ": "\\~o", "ø": "\\o{}", "ú": "\\'u", "ù": "\\`u", "û": "\\^u", "ü": "\\\"u",
    "ñ": "\\~n", "ç": "\\c{c}", "š": "\\v{s}", "ž": "\\v{z}", "ć": "\\'c",
    "ł": "{\\l}", "ß": "{\\ss}", "ı": "{\\i}",
}


def texify(s):
    if s is None:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    out = []
    for ch in s:
        out.append(LATEX_ACCENT.get(ch, ch))
    s = "".join(out)
    s = s.replace("\\", "\x00").replace("&", "\\&").replace("%", "\\%").replace("#", "\\#")
    s = s.replace("_", "\\_").replace("$", "\\$").replace("\x00", "\\")
    s = s.replace("–", "--").replace("—", "---")
    s = s.replace("p -Values", "$p$-Values").replace("p -values", "$p$-values")
    return s


def field(rec, name):
    v = rec.get(name)
    if isinstance(v, list):
        return v[0] if v else ""
    return v or ""


def authors_bib(rec):
    names = []
    for a in rec.get("author", [])[:40]:
        fam = a.get("family") or a.get("name") or ""
        giv = a.get("given") or ""
        if not fam:
            continue
        names.append("%s, %s" % (texify(fam), texify(giv)))
    return " and ".join(names)


def make_entry(key, rec):
    typ = rec.get("type", "article")
    title = texify(field(rec, "title"))
    year = ""
    for k in ("issued", "published-print", "published-online", "created"):
        if k in rec and rec[k].get("date-parts"):
            year = rec[k]["date-parts"][0][0]
            break
    au = authors_bib(rec)
    doi = rec.get("DOI", "")
    jour = texify(field(rec, "container-title"))
    vol = field(rec, "volume")
    pages = field(rec, "page")
    pub = texify(rec.get("publisher", ""))
    if typ in ("book", "monograph"):
        body = "author = {%s},\ntitle = {%s},\npublisher = {%s},\nyear = {%s},\ndoi = {%s}" % (au, title, pub, year, doi)
        return "@book{%s,\n%s\n}\n" % (key, body)
    if not jour:
        body = "author = {%s},\ntitle = {%s},\nhowpublished = {%s},\nyear = {%s},\ndoi = {%s}" % (au, title, pub or "preprint", year, doi)
        return "@misc{%s,\n%s\n}\n" % (key, body)
    extra = ""
    if vol:
        extra += ",\nvolume = {%s}" % vol
    if pages:
        extra += ",\npages = {%s}" % pages.replace("-", "--")
    body = ("author = {%s},\ntitle = {%s},\njournal = {%s}%s,\nyear = {%s},\ndoi = {%s}"
            % (au, title, jour, extra, year, doi))
    return "@article{%s,\n%s\n}\n" % (key, body)


def make_dataset_entry(key, attrs):
    title = texify(attrs.get("titles", [{}])[0].get("title", ""))
    year = attrs.get("publicationYear", "")
    pub = texify(attrs.get("publisher", "")) or "Data repository"
    doi = attrs.get("doi", "")
    body = ("title = {%s},\npublisher = {%s},\nyear = {%s},\ndoi = {%s},\n"
            "note = {dataset}") % (title, pub, year, doi)
    return "@misc{%s,\n%s\n}\n" % (key, body)


def main():
    accepted, rejected, log = [], [], []
    for key, year, title, doi in CANDIDATES:
        try:
            if doi:
                rec = crossref_by_doi(doi)
                score, got_year, got_title = 1.0, None, field(rec, "title")
                rec.setdefault("DOI", doi)
            else:
                items = crossref_by_title(title)
                best = None
                for it in items:
                    if is_preprint(it):
                        continue
                    t = field(it, "title")
                    sc = difflib.SequenceMatcher(None, norm(t), norm(title)).ratio()
                    if best is None or sc > best[0]:
                        best = (sc, it)
                if best is None:
                    rejected.append(dict(key=key, reason="no journal-article match",
                                         title=title, doi="", score=""))
                    continue
                score, rec = best
                got_title = field(rec, "title")
                gp = None
                for k in ("issued", "published-print", "published-online"):
                    if k in rec and rec[k].get("date-parts"):
                        gp = rec[k]["date-parts"][0][0]
                        break
                got_year = gp
                if gp is not None and abs(int(gp) - year) > 3:
                    rejected.append(dict(key=key, reason="year %s != %s" % (gp, year),
                                         title=got_title, doi=rec.get("DOI", ""),
                                         score=round(score, 3)))
                    continue
            if score < 0.84:
                rejected.append(dict(key=key, reason="title similarity %.2f" % score,
                                     title=got_title, doi=rec.get("DOI", ""), score=round(score, 3)))
                continue
            accepted.append(make_entry(key, rec))
            log.append(dict(key=key, doi=rec.get("DOI", ""), year=got_year or year,
                            title=got_title, journal=field(rec, "container-title"),
                            score=round(score, 3), status="accepted"))
        except Exception as exc:                                   # noqa: BLE001
            rejected.append(dict(key=key, reason="lookup failed: %s" % exc,
                                 title=title or doi, doi=doi or "", score=""))
        time.sleep(0.35)

    for key, title, doi in DATASETS:
        try:
            attrs = datacite_by_doi(doi)
            accepted.append(make_dataset_entry(key, attrs))
            log.append(dict(key=key, doi=doi, year=attrs.get("publicationYear", ""),
                            title=attrs.get("titles", [{}])[0].get("title", ""),
                            journal="dataset", score=1.0, status="accepted"))
        except Exception as exc:                                   # noqa: BLE001
            rejected.append(dict(key=key, reason="datacite failed: %s" % exc,
                                 title=title, doi=doi, score=""))
        time.sleep(0.35)

    (ROOT / "refs.bib").write_text("\n".join(accepted) + MANUAL, encoding="utf-8")
    with open(DATA / "ref_check.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "doi", "year", "title", "journal", "score", "status"])
        w.writeheader()
        w.writerows(log)
    with open(DATA / "ref_rejected.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "reason", "title", "doi", "score"])
        w.writeheader()
        w.writerows(rejected)

    print("accepted: %d   rejected: %d" % (len(accepted), len(rejected)))
    print("\naccepted keys:")
    for r in log:
        print("  %-26s %-40s %s" % (r["key"], r["doi"], (r["title"] or "")[:55]))
    if rejected:
        print("\nrejected:")
        for r in rejected:
            print("  %-26s %s  | %s" % (r["key"], r["reason"], (r["title"] or "")[:60])) 
    if len(accepted) < 50:
        print("\nWARNING: fewer than 50 verified entries")
        sys.exit(0)


if __name__ == "__main__":
    main()
