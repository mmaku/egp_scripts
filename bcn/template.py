from __future__ import annotations
import argparse, csv, hashlib, hmac, html, json, math, re, sys, unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple

csv.field_size_limit(sys.maxsize)
COLUMNS = [
    "ticket_type",
    "ticket_id",
    "related_id",
    "service",
    "initial_priority",
    "title",
    "reporting_unit",
    "company",
    "assignment_group",
    "priority",
    "status",
    "created_date",
    "accepted_date",
    "due_date",
    "modified_date",
    "flag",
    "reporter_lastname",
    "reporter",
    "resolver_lastname",
    "resolver",
    "description",
    "additional_field",
    "resolution_date",
    "resolution_flag",
    "solution",
    "resolution_status",
    "category",
    "final_field",
]
NULLS = {"", "NULL", "NONE", "N/A", "NAN", "(NOT SPECIFIED)"}
MODULE_RULES = [
    (
        "UPRAWNIENIA",
        (
            "uprawnien",
            "brak dostep",
            "nadanie roli",
            "rola referencyjna",
            "autoryzac",
            "reset mfa",
        ),
    ),
    (
        "KOMUNIKACJA_RYNKOWA",
        ("ape", "pdoc", "komunikacj rynkow", "brak zwrotki", "origami"),
    ),
    (
        "BILLING",
        ("billing", "biling", "faktur", "rozliczen", "ea19", "ea20", "ebf", "easibi"),
    ),
    ("FICA", ("fica", "fp04", "fpt", "windykac", "nalezn", "saldo", "odsetk")),
    (
        "UIP",
        ("uip", "urzadzen", "licznik", "montaz", "demontaz", "eg42", "eg30", "ec51"),
    ),
    ("ODCZYTY_POMIARY", ("odczyt", "pomiar", "obis", "pmax", "el28", "profil pomiar")),
    ("CRM", ("crm", "partner handlow", "sprawa crm", "umowa crm", "oferta", "aneks")),
    ("MIGRACJA", ("migrac", "domigrac", "fabok", "hmax")),
    (
        "DANE_PODSTAWOWE",
        ("dane podstawow", "teryt", "adres", "pesel", "nip", "es32", "instalac"),
    ),
    ("PNO", ("pno",)),
    ("EKANCELARIA", ("ekancelaria", "e-kancelaria")),
    ("RAPORTOWANIE", ("raport", "excel", "spool", "zisu_")),
    ("FIORI", ("fiori", "/ui2/flp", "launchpad", "kafelk")),
    ("KSEF", ("ksef",)),
    (
        "INFRASTRUKTURA",
        ("http 401", "serwer", "wydajnosc", "wolne dzialanie", "vdi", "vpn", "abap"),
    ),
]
SYMPTOM_RULES = [
    ("BRAK_KOMUNIKATU", ("brak komunikatu", "nie wygenerowano komunikatu")),
    ("BRAK_ZWROTKI", ("brak zwrotki", "brak komunikatu zwrotnego")),
    (
        "STATUS_ERROR",
        ("status error", "status err", "pojawil sie error", "zakonczyl sie bledem"),
    ),
    (
        "BLAD_FAKTUROWANIA",
        ("blad fakturow", "nie mozna zafakturow", "problem z fakturow"),
    ),
    (
        "BLAD_ROZLICZENIA",
        ("blad rozliczen", "nie mozna rozlicz", "problem z rozliczen"),
    ),
    ("BLEDNY_ODCZYT", ("bledny odczyt", "nieprawidlowy odczyt", "brak odczyt")),
    (
        "BLAD_URZADZENIA",
        (
            "blad licznika",
            "bledny licznik",
            "blad urzadzen",
            "rekord informacyjny urzadzen",
        ),
    ),
    ("BRAK_UPRAWNIEN", ("brak uprawnien", "brak dostepu", "nie mam dostepu")),
    (
        "NIEPRAWIDLOWY_STATUS_UMOWY",
        ("status umowy", "umowa nieaktyw", "umowa niezawarta"),
    ),
    ("BLAD_ADRESU_TERYT", ("teryt", "bledny adres", "nieprawidlowy adres")),
    ("BRAK_DANYCH", ("brak danych", "data incomplete", "niekompletne dane")),
    ("TIMEOUT", ("timeout", "time-out", "waiting time too long", "przekroczono czas")),
    ("WOLNE_DZIALANIE", ("wolne dzialanie", "dziala wolno", "wydajnosc")),
    (
        "DUPLIKAT",
        ("duplikat", "dubel", "ticket reported twice", "zgloszenie zdublowane"),
    ),
]
CAUSE_RULES = [
    ("BLAD_UZYTKOWNIKA", ("blad uzytkownika", "nieprawidlowe dzialanie uzytkownika")),
    (
        "BRAK_USTERKI",
        ("brak bledu systemowego", "brak usterki", "system dziala prawidlowo"),
    ),
    (
        "BLAD_DANYCH",
        ("bledne dane", "nieprawidlowe dane", "korekta danych", "poprawiono dane"),
    ),
    ("BRAK_DANYCH", ("brak danych", "data incomplete", "dane niekompletne")),
    (
        "PROBLEM_INTEGRACJI",
        ("problem komunikacji", "komunikacja udrozniona", "integrac", "brak zwrotki"),
    ),
    ("PROBLEM_UPRAWNIEN", ("brak uprawnien", "nadano uprawnienia")),
    ("PROBLEM_KONFIGURACJI", ("konfigurac", "parametryzac")),
    ("PROBLEM_WYDAJNOSCIOWY", ("wydajnosc", "timeout", "wolne dzialanie")),
    (
        "BLAD_SYSTEMU",
        ("poprawka programistyczna", "blad programu", "blad systemu", "transport"),
    ),
]
RESOLUTION_RULES = [
    ("DUPLIKAT", ("ticket reported twice", "duplikat", "dubel", "prace tocza sie w")),
    ("ODRZUCENIE", ("odrzucono", "odrzucony", "revocation")),
    ("BRAK_DANYCH", ("data incomplete", "brak danych", "brak odpowiedzi")),
    (
        "NADANIE_UPRAWNIEN",
        ("nadano uprawnienia", "uprawnienia zostaly nadane", "dodano role"),
    ),
    ("WORKAROUND", ("solved by workaround", "obejscie", "workaround")),
    ("REPROCESOWANIE", ("przeprocesow", "ponownie przetworz", "ponownie uruchom")),
    (
        "KOREKTA_DANYCH",
        ("skorygowano dane", "poprawiono dane", "korekta danych", "zmieniono dane"),
    ),
    (
        "ZMIANA_KONFIGURACJI",
        ("zmiana konfiguracji", "skonfigurowano", "zmieniono ustawienia"),
    ),
    (
        "NAPRAWA_SYSTEMOWA",
        (
            "poprawka programistyczna",
            "wdrozono poprawke",
            "transport",
            "successful permanently",
        ),
    ),
    ("BLAD_UZYTKOWNIKA", ("blad uzytkownika", "nieprawidlowe dzialanie uzytkownika")),
    ("BRAK_USTERKI", ("brak usterki", "brak bledu systemowego", "dziala prawidlowo")),
    ("INFORMACJA", ("udzielono informacji", "wyjasniono", "przekazano instrukcje")),
    ("PRZEKAZANIE", ("przekazano do", "hp alm", "przekierowano")),
    ("ANULOWANIE", ("anulowano", "zamknieto na prosbe")),
]
TECH_RE = re.compile(
    r"\b(?:NCBO|NCBD|CRDP|APE|KSEF|FIORI|SAP|IS-?U|SOP\d*|SDP\d*|SOT\d*|SDE\d*|SDT\d*|SOE\d*|CRM|OBIS|EBF|EASIBI|COMPR_IZW|ORIGAMI)\b",
    re.I,
)
TRANS_RE = re.compile(
    r"\b(?:EA\d+|ES\d+|EG\d+|EL\d+|EC\d+[A-Z]?|FP\d+|FPT\d+|SM\d+|FAGL[A-Z0-9]+|/UI2/FLP|Z[A-Z0-9_]{4,})\b",
    re.I,
)
PROCESS_RE = re.compile(
    r"(?<!\d)(?:1\.1|1\.3|1\.5|2\.2|2\.7|2\.8|4\.1(?:\.1\.1)?|4\.2|6\.2|6\.3|8\.1|8\.2|9\.1)(?!\d)"
)
ERROR_RE = re.compile(
    r"\b(?:CE\d{3}|HTTP\s*\d{3}|Z\d{2,4}|[A-Z]{2,10}[-_]\d{2,10})\b", re.I
)
TICKET_RE = re.compile(r"\b(?:I|C|SR)-\d{6,10}\b", re.I)


class HTMLText(HTMLParser):
    BLOCK = {
        "p",
        "div",
        "br",
        "li",
        "tr",
        "table",
        "section",
        "article",
        "h1",
        "h2",
        "h3",
    }
    CELL = {"td", "th"}
    SKIP = {"style", "script", "head", "title"}

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.parts = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP:
            self.depth += 1
        elif not self.depth and tag in self.BLOCK:
            self.parts.append("\n")
        elif not self.depth and tag in self.CELL:
            self.parts.append("\t")

    def handle_endtag(self, tag):
        tag = tag.lower()

    if tag in self.SKIP and self.depth:
        self.depth -= 1
    elif not self.depth and tag in self.BLOCK:
        self.parts.append("\n")
    elif not self.depth and tag in self.CELL:
        self.parts.append("\t")

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)

    def text(self):
        return "".join(self.parts)


def nonnull(v):
    v = "" if v is None else str(v).strip()
    return "" if v.upper() in NULLS else v


def simplify(v):
    v = unicodedata.normalize("NFKD", v.casefold())
    return re.sub(
        r"\s+", " ", "".join(c for c in v if not unicodedata.combining(c))
    ).strip()


def detect_encoding(path):
    raw = path.read_bytes()[:200000]
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        raw.decode("utf-8")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "cp1250"


def normalize(v):
    v = nonnull(v)
    if re.search(r"</?[a-z][^>]*>", v, re.I):
        p = HTMLText()
        try:
            p.feed(v)
            v = p.text()
        except Exception:
            v = re.sub(r"<[^>]+>", " ", v)
        v = html.unescape(v)
        v = unicodedata.normalize("NFKC", v)
        v = (
            v.translate(str.maketrans({"¦": "Ś", "¶": "ś", "±": "ą", "ˇ": "ż"}))
            .replace("\u00a0", " ")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
        v = re.sub(r"<!--.*?-->", " ", v, flags=re.S)
        v = re.sub(r"\b(?:P|SPAN|DIV)\s*\{[^{}]{0,2000}\}", " ", v, flags=re.I)
        v = re.sub(
            r"\b(?:mso-[\w-]+|font-family|font-size|margin(?:-[\w-]+)?|color)\s*:[^;\n]+;?",
            " ",
            v,
            flags=re.I,
        )
        v = re.sub(r"[ \t]+", " ", v)
        v = "\n".join(x.strip(" \t|") for x in v.splitlines())
        return re.sub(r"\n{3,}", "\n\n", v).strip()


MAIL_RE = re.compile(r"(?im)^\s*(?:from|od|sent|wysłano|to|do|cc|dw|subject|temat)\s*:")


def prepare(v):
    v = normalize(v)
    pos = [m.start() for m in MAIL_RE.finditer(v)]

    for marker in (
        "wiadomość ta może zawierać informacje poufne",
        "the information transmitted is intended only",
    ):
        p = v.lower().find(marker)
    if p >= 0:
        pos.append(p)
    return normalize(v[: min(pos)] if pos else v)


@dataclass
class Pseudonymizer:
    key: bytes
    maps: (Dict)[str, Dict[str, str]] = field(default_factory=dict)
    people: Set[str] = field(default_factory=set)

    def token(self, k, raw):
        raw = re.sub(r"\s+", " ", raw.strip())
        canon = raw.casefold()
        bucket = self.maps.setdefault(k, {})

    if canon not in bucket:
        bucket[canon] = "[{}_{}]".format(
            k,
            hmac.new(self.key, (k + "|" + canon).encode("utf-8"), hashlib.sha256)
            .hexdigest()[:10]
            .upper(),
        )
    return bucket[canon]

    def add_person(self, v):
        v = re.sub(r"\s+\d{6,10}\s*$", "", nonnull(v)).strip()
        if len(v.split()) >= 2:
            self.people.add(v)

    def anonymize(self, text):
        for k, p in [
            ("EMAIL", r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b"),
            ("URL", r"\b(?:https?|ftp)://[^\s<>\]\)\"']+"),
            ("IP", r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b"),
            ("PESEL", r"(?<!\d)\d{11}(?!\d)"),
        ]:
            text = re.sub(
                p, lambda m, kind=k: self.token(kind, m.group(0)), text, flags=re.I
            )
        labeled = [
            ("NIP", r"NIP", r"\d(?:[\s-]?\d){9}"),
            ("PPE", r"(?:kod\s*)?PPE", r"(?:19XPG[A-Z0-9]+|\d{12,20})"),
            ("PDOC", r"PDOC", r"[A-Z0-9][A-Z0-9._/-]{4,}"),
            ("PH", r"(?:PH|partner(?:a)?\s+handlowego)", r"\d{5,15}"),
            ("KU", r"(?:KU|konto\s+umowy)", r"\d{5,15}"),
            (
                "LOGIN",
                r"(?:login(?:\s+domenowy)?|użytkownik|user)",
                r"[A-Z0-9._\\-]{5,}",
            ),
            (
                "KOMPUTER",
                r"(?:nazwa\s+komputera|komputer|host|hostname)",
                r"[A-Z0-9][A-Z0-9._-]{4,}",
            ),
        ]
        for k, l, val in labeled:
            p = re.compile(
                r"(?P<label>\b{}\b\s*[:=#-]?\s*)(?P<value>{})".format(l, val), re.I
            )
            text = p.sub(
                lambda m, kind=k: m.group("label") + self.token(kind, m.group("value")),
                text,
            )
        for person in sorted(self.people, key=len, reverse=True):
            text = re.sub(
                r"(?<!\w){}(?!\w)".format(re.escape(person)),
                lambda m: self.token("OSOBA", m.group(0)),
                text,
                flags=re.I,
            )
        return normalize(text) @ dataclass


class Ticket:
    ticket_id: str
    related: List[str]
    source: str
    ticket_type: str
    system: str
    environment: str
    module: str
    processes: List[str]
    symptoms: List[str]
    errors: List[str]
    error_message: str
    transactions: List[str]
    terms: List[str]
    objects: List[str]
    title: str
    description: str
    cause: str
    resolution_type: str
    quality: str
    resolution: str
    duplicate: str
    duplicate_of: str
    search_text: str
    resolution_date: str
    fingerprint: str


def labels(text, rules):
    s = simplify(text)
    return [label for label, words in rules if any(simplify(w) in s for w in words)]


def first(text, rules, default):
    found = labels(text, rules)
    return found[0] if found else default


def system_of(text):
    upper = text.upper()


for x in ("NCBO", "NCBD", "CRDP", "PNO", "KSEF"):
    if x in upper:
        return x
return "NCB"


def environment_of(text):
    m = re.search(r"\b(?:SOP|SDP|SDE|SDT|SOT|SOE)\s*M?\s*\d{0,3}\b", text.upper())
    if m:
        return re.sub(r"\s+", "", m.group(0))
    s = simplify(text)
    if "preprod" in s:
        return "PREPROD"
    if "test" in s:
        return "TEST"
    if "produkc" in s or " prod" in s:
        return "PROD"
    return "NIEUSTALONE"


def object_types(text):
    rules = [
        ("PPE", r"\bPPE\b"),
        ("PDOC", r"\bPDOC\b"),
        ("PH", r"\bPH\b|partner handlow"),
        ("KU", r"\bKU\b|konto umowy"),
        ("UMOWA_CRM", r"umowa crm"),
        ("UMOWA_ISU", r"umowa isu"),
        ("INSTALACJA", r"instalac"),
        ("LICZNIK", r"licznik|GERNR"),
        ("FAKTURA", r"faktur"),
        ("EBF", r"\bEBF\b"),
        ("OT", r"zlecenie OT|\bOT\b"),
        ("OFERTA", r"ofert"),
        ("ANEKS", r"aneks"),
        ("ADRES", r"adres|TERYT"),
    ]
    return [k for k, p in rules if re.search(p, text, re.I)]


def quality(sol):
    if not sol:
        return "BRAK"
    if len(sol) < 35 or simplify(sol).strip(" .!") in {
        "rozwiazano",
        "problem zostal rozwiazany",
        "udzielono informacji",
        "poprawiono",
    }:
        return "NISKA"
    return "WYSOKA" if len(sol) >= 120 else "SREDNIA"


def display(v):
    return "; ".join(v) if v else "brak"


def make_ticket(row, source, pseudo):
    tid = nonnull(row["ticket_id"])
    if not tid:
        return None
    title = pseudo.anonymize(prepare(row["title"]))
    desc = pseudo.anonymize(prepare(row["description"]))
    sol = pseudo.anonymize(prepare(row["solution"]))
    combined = " ".join(
        (
            title,
            desc,
            sol,
            prepare(row["service"]),
            prepare(row["assignment_group"]),
            prepare(row["category"]),
        )
    )
    typ = (
        "WNIOSEK"
        if "wniosek" in simplify(row["ticket_type"] + " " + title)
        else (
            "INCYDENT"
            if "incydent" in simplify(row["ticket_type"] + " " + title)
            else "INNE"
        )
    )
    processes = sorted(set(PROCESS_RE.findall(combined)))
    symptoms = labels(title + " " + desc, SYMPTOM_RULES)
    errors = sorted(set(x.upper().replace(" ", "") for x in ERROR_RE.findall(combined)))
    trans = sorted(set(x.upper() for x in TRANS_RE.findall(combined)))
    terms = sorted(set(x.upper() for x in TECH_RE.findall(combined)))
    objects = object_types(combined)
    cause = first(sol + " " + desc, CAUSE_RULES, "NIEUSTALONA")
    rtype = first(sol + " " + row["resolution_status"], RESOLUTION_RULES, "INNE")
    q = quality(sol)
    related = sorted(
        set(
            x
            for x in TICKET_RE.findall(
                " ".join((nonnull(row["related_id"]), desc, sol))
            )
            if x.casefold() != tid.casefold()
        )
    )
    dup = "TAK" if rtype == "DUPLIKAT" or "DUPLIKAT" in symptoms else "NIE"
    dupof = related[0] if dup == "TAK" and related else ""
    errmsg = next(
        (
            line[:600]
            for line in desc.splitlines()
            if re.search(r"(?i)blad|błąd|error|exception|komunikat", line)
        ),
        "",
    )
    system = system_of(combined)
    env = environment_of(combined)
    module = first(combined, MODULE_RULES, "INNE")
    dline = re.sub(r"\n+", " ", desc)[:2200]
    search = "\n".join(
        [
            "Typ: " + typ,
            "System: " + system,
            "Srodowisko: " + env,
            "Modul: " + module,
            "Procesy: " + display(processes),
            "Symptomy: " + display(symptoms),
            "Kody bledow: " + display(errors),
            "Transakcje: " + display(trans),
            "Terminy: " + display(terms),
            "Obiekty: " + display(objects),
            "Tytul: " + title,
            "Przyczyna: " + cause,
            "Problem: " + dline,
        ]
    )
    fp = hashlib.sha256(
        simplify(" ".join((title, desc, sol))).encode("utf-8")
    ).hexdigest()
    return Ticket(
        tid,
        related,
        source.name,
        typ,
        system,
        env,
        module,
        processes,
        symptoms,
        errors,
        errmsg,
        trans,
        terms,
        objects,
        title,
        desc,
        cause,
        rtype,
        q,
        sol,
        dup,
        dupof,
        normalize(search),
        nonnull(row["resolution_date"]),
        fp,
    )


def iter_rows(path, encoding):
    with path.open("r", encoding=encoding, newline="", errors="replace") as f:
        for n, row in enumerate(csv.reader(f, delimiter=";", quotechar='"'), 1):
            if not row or not any(x.strip() for x in row):
                continue
        yield n, (
            dict(zip(COLUMNS, row))
            if len(row) == len(COLUMNS)
            else {"_error": "{}: rekord {}: {} kolumn".format(path.name, n, len(row))}
        )


def inputs_of(items, input_dir, pattern):
    files = list(items) + (list(input_dir.glob(pattern)) if input_dir else [])
    out = []
    seen = set()

    for p in sorted(files, key=lambda x: x.name.casefold()):
        if p.is_file() and p.resolve() not in seen:
            seen.add(p.resolve())
            out.append(p)
    return out


def render(t):
    fields = [
        ("ID_ZGLOSZENIA", t.ticket_id),
        ("ID_POWIAZANE", display(t.related)),
        ("TYP_ZGLOSZENIA", t.ticket_type),
        ("SYSTEM", t.system),
        ("SRODOWISKO", t.environment),
        ("MODUL", t.module),
        ("PROCESY", display(t.processes)),
        ("SYMPTOMY", display(t.symptoms)),
        ("KODY_BLEDOW", display(t.errors)),
        ("KOMUNIKAT_BLEDU", t.error_message or "brak"),
        ("TRANSAKCJE", display(t.transactions)),
        ("TERMINY_TECHNICZNE", display(t.terms)),
        ("OBIEKTY_BIZNESOWE", display(t.objects)),
        ("TYTUL", t.title or "brak"),
        ("OPIS_PROBLEMU", t.description or "brak"),
        ("PRZYCZYNA", t.cause),
        ("TYP_ROZWIAZANIA", t.resolution_type),
        ("JAKOSC_ROZWIAZANIA", t.quality),
        ("ROZWIAZANIE", t.resolution or "brak"),
        ("CZY_DUPLIKAT", t.duplicate),
        ("DUPLIKAT_ZGLOSZENIA", t.duplicate_of or "brak"),
        ("SEARCH_TEXT", t.search_text),
    ]
    body = "\n\n".join(k + "\n" + v for k, v in fields)
    return (
        "=" * 72
        + "\nBEGIN_TICKET\n"
        + "=" * 72
        + "\n\n"
        + normalize(body)
        + "\n\n"
        + "=" * 72
        + "\nEND_TICKET\n"
        + "=" * 72
        + "\n"
    )


def write_text(path, text):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def split_even(items, count):
    count = max(1, min(count, len(items)))
    size = int(math.ceil(len(items) / float(count)))
    return [items[i : i + size] for i in range(0, len(items), size)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="*", type=Path)
    p.add_argument("--input-dir", type=Path)
    p.add_argument("--pattern", default="NCBReportSolution*.csv")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--max-files", type=int, default=50)
    p.add_argument(
        "--encoding", choices=["auto", "utf-8-sig", "cp1250"], default="auto"
    )
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--include-review", action="store_true")
    a = p.parse_args()

    if a.max_files < 1:
        p.error("--max-files musi byc > 0")
    files = inputs_of(a.inputs, a.input_dir, a.pattern)
    if not files:
        p.error("Nie znaleziono plikow CSV")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    enc = {
        x.name: detect_encoding(x) if a.encoding == "auto" else a.encoding
        for x in files
    }
    pseudo = Pseudonymizer(a.key.encode("utf-8"))
    structural = []
    for path in files:
        for _, row in iter_rows(path, enc[path.name]):
            if "_error" in row:
                structural.append(row["_error"])
            else:
                pseudo.add_person(row["reporter"])
                pseudo.add_person(row["resolver"])
    stats = Counter()
    byid = {}
    fps = {}
    dups = []
    processed = 0
    stop = False
    for path in files:
        if stop:
            break
    for _, row in iter_rows(path, enc[path.name]):
        if "_error" in row:
            continue
        if a.limit and processed >= a.limit:
            stop = True
            break
            processed += 1
            stats["rekordy_wejsciowe"] += 1
            t = make_ticket(row, path, pseudo)
        if not t:
            continue
        key = t.ticket_id.casefold()
        if key in byid:
            stats["duplikaty_id"] += 1
            dups.append(t.ticket_id)
            continue
        if t.fingerprint in fps:
            stats["duplikaty_tresci"] += 1
            dups.append(t.ticket_id)
            continue
        byid[key] = t
        fps[t.fingerprint] = t.ticket_id
        stats["jakosc_" + t.quality.lower()] += 1
    main = [
        t
        for t in byid.values()
        if t.quality not in ("BRAK", "NISKA") and t.duplicate != "TAK"
    ]
    review = [t for t in byid.values() if t not in main]
    selected = main + (review if a.include_review else [])
    groups = defaultdict(list)
    for t in selected:
        groups[(t.system, t.module)].append(t)
    while len(groups) > a.max_files:
        key = min(groups, key=lambda k: len(groups[k]))
        vals = groups.pop(key)
        target = (key[0], "INNE") if key[1] != "INNE" else ("NCB", "INNE")
        groups[target].extend(vals)
    keys = list(groups)
    allocation = {k: 1 for k in keys}
    remaining = a.max_files - len(keys)
    total = float(sum(len(groups[k]) for k in keys) or 1)
    while remaining > 0 and keys:
        key = max(keys, key=lambda k: len(groups[k]) / float(allocation[k]))
        allocation[key] += 1
        remaining -= 1
    generated = []
    index = []
    num = 0
    for key in sorted(keys):
        tickets = sorted(groups[key], key=lambda t: (t.resolution_date, t.ticket_id))
    for batch in split_even(tickets, allocation[key]):
        num += 1
        name = "NCB_{:02d}_{}_{}.txt".format(num, key[0], key[1])
        content = (
            "BAZA WIEDZY NCB\nSYSTEM: {}\nMODUL: {}\nLICZBA_ZGLOSZEN: {}\n\n".format(
                key[0], key[1], len(batch)
            )
            + "\n\n".join(render(t) for t in batch)
        )
        write_text(a.output_dir / name, content)
        generated.append(name)
    for t in batch:
        index.append(
            {
                "ticket_id": t.ticket_id,
                "source_csv": t.source,
                "package_file": name,
                "ticket_type": t.ticket_type,
                "system": t.system,
                "environment": t.environment,
                "module": t.module,
                "processes": display(t.processes),
                "symptoms": display(t.symptoms),
                "error_codes": display(t.errors),
                "resolution_type": t.resolution_type,
                "quality": t.quality,
                "title": t.title,
            }
        )
    fields = [
        "ticket_id",
        "source_csv",
        "package_file",
        "ticket_type",
        "system",
        "environment",
        "module",
        "processes",
        "symptoms",
        "error_codes",
        "resolution_type",
        "quality",
        "title",
    ]
    with (a.output_dir / "_ticket_index.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(index)
    stats.update(
        {
            "unikalne_tickety": len(byid),
            "main": len(main),
            "review": len(review),
            "wyeksportowane": len(index),
            "wygenerowane_pliki_txt": len(generated),
        }
    )
    report = {
        "input_files": [str(x) for x in files],
        "encodings": enc,
        "max_files": a.max_files,
        "generated_txt_files": len(generated),
        "statistics": dict(stats),
        "structural_errors_count": len(structural),
        "structural_errors_sample": structural[:100],
        "duplicates_sample": dups[:1000],
        "pseudonym_counts": {k: len(v) for k, v in pseudo.maps.items()},
        "generated_files": generated,
    }
    write_text(
        a.output_dir / "_audit_report.json",
        json.dumps(report, ensure_ascii=False, indent=2),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if structural else 0


if __name__ == "__main__":
    raise SystemExit(main())
