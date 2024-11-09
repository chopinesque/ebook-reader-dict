"""Greek language."""

import re
from collections import defaultdict

from ...user_functions import extract_keywords_from, italic, term, uniq
from .langs import langs

# Float number separator
float_separator = ","

# Thousands separator
thousands_separator = "."

# Markers for sections that contain interesting text to analyse.
head_sections = ("{{-el-}}",)
etyl_section = ("{{ετυμολογία}}",)
section_patterns = ("#", r"\*")
sections = (
    *head_sections,
    *etyl_section,
    "{{ουσιαστικό}",
    "{{ουσιαστικό|el}",
    "{{ρήμα}",
    "{{ρήμα|el}",
    "{{επίθετο}",
    "{{επίθετο|el}",
    "{{επίρρημα}",
    "{{επίρρημα|el}",
    "{{σύνδεσμος}",
    "{{σύνδεσμος|el}",
    "{{συντομομορφή}",
    "{{συντομομορφή|el}",
    "{{αριθμητικό}",
    "{{αριθμητικό|el}",
    "{{άρθρο}",
    "{{άρθρο|el}",
    "{{μετοχή}",
    "{{μετοχή|el}",
    "{{μόριο}",
    "{{μόριο|el}",
    "{{αντωνυμία}",
    "{{αντωνυμία|el}",
    "{{επιφώνημα}",
    "{{επιφώνημα|el}",
    "{{ρηματική έκφραση}",
    "{{επιρρηματική έκφραση}",
    "{{φράση}",
    "{{φράση|el}",
    "{{έκφραση}",
    "{{έκφραση|el}",
    "{{παροιμία}",
    "{{παροιμία|el}",
)

# Some definitions are not good to keep (plural, gender, ... )
definitions_to_ignore = (
    "{{μορφή ουσιαστικού}",
    "{{μορφή ουσιαστικού|el}",
    "{{μορφή ρήματος}",
    "{{μορφή ρήματος|el}",
    "{{μορφή επιθέτου}",
    "{{μορφή επιθέτου|el}",
    "{{εκφράσεις}",
    "{{εκφράσεις|el}",
)

# Templates to ignore: the text will be deleted.
templates_ignored = (
    "el-κλίσ",
    "!",
    "R:TELETERM",
    "κλείδα-ελλ",
    "λείπει η ετυμολογία",
    "περίοδος",
    "από",
    "ετυ+",
    "λείπει ο ορισμός",
)

# Templates more complex to manage.
templates_multi: dict[str, str] = {
    # {{resize|Βικιλεξικό|140}}
    "resize": "f'<span style=\"font-size:{parts[2]}%;\">{parts[1]}</span>'",
    # {{ετικ|γαστρονομία|τρόφιμα|γλυκά}}
    "ετικ": "'(' + ', '.join(italic(p) for p in parts[1:]) + ')'",
    # {{κνε}}
    "κνε": "italic('κοινή νεοελληνική')",
    # {{νε}}
    "νε": "italic('νέα ελληνική')",
}

# Templates that will be completed/replaced using custom style.
templates_other = {
    "*": "<big>*</big>",
}

# Release content on GitHub
# https://github.com/BoboTiG/ebook-reader-dict/releases/tag/el
release_description = """\
Αριθμός λέξεων: {words_count}
Εξαγωγή Βικιλεξικού: {dump_date}

Full version:
{download_links_full}

Etymology-free version:
{download_links_noetym}

<sub>Ημερομηνία δημιουργίας: {creation_date}</sub>
"""

# Dictionary name that will be printed below each definition
wiktionary = "Βικιλεξικό (ɔ) {year}"


_genders = {
    "θ": "θηλυκό",
    "α": "αρσενικό",
    "αθ": "αρσενικό ή θηλυκό",
    "αθο": "αρσενικό, θηλυκό, ουδέτερο",
    "ακλ": "άκλιτο",
    "καθ": "(καθαρεύουσα)",
    "ο": "ουδέτερο",
    "θο": "θηλυκό ή ουδέτερο",
    "αο": "αρσενικό ή ουδέτερο",
    "ακρ": "ακρωνύμιο",
}


def find_genders(
    code: str,
    pattern: re.Pattern[str] = re.compile(r"{{([^{}]*)}}"),
    line_pattern: str = "'''{{PAGENAME}}''' ",
) -> list[str]:
    """
    >>> find_genders("")
    []
    >>> find_genders("'''{{PAGENAME}}''' {{αθ}}")
    ['αρσενικό ή θηλυκό']
    >>> find_genders("'''{{PAGENAME}}''' {{αθ}}, {{ακλ|αθ}}")
    ['αρσενικό ή θηλυκό', 'άκλιτο']
    >>> find_genders("'''{{PAGENAME}}''' {{ακλ|αθ}}, {{αθ}}")
    ['άκλιτο', 'αρσενικό ή θηλυκό']
    >>> find_genders("'''{{PAGENAME}}''' {{θο}} {{ακλ}}")
    ['θηλυκό ή ουδέτερο', 'άκλιτο']
    >>> find_genders("'''{{PAGENAME}}''' {{αο}} {{ακλ}} {{ακρ}}")
    ['αρσενικό ή ουδέτερο', 'άκλιτο', 'ακρωνύμιο']
    >>> find_genders("'''{{PAGENAME}}''' {{α}} ({{ετ|ιδιωματικό|0=-}}, Κάλυμνος)")
    ['αρσενικό']
    """
    return [
        g
        for line in code.splitlines()
        for gender in pattern.findall(line[len(line_pattern) :])
        if line.startswith(line_pattern) and (g := _genders.get(gender.split("|")[0]))
    ]


def find_pronunciations(
    code: str,
    pattern: re.Pattern[str] = re.compile(r"{ΔΦΑ(?:\|γλ=el)?(?:\|el)?\|([^}\|]+)"),
) -> list[str]:
    """
    >>> find_pronunciations("")
    []
    >>> find_pronunciations("{{ΔΦΑ|tɾeˈlos|γλ=el}}")
    ['/tɾeˈlos/']
    >>> find_pronunciations("{{ΔΦΑ|γλ=el|ˈni.xta}}")
    ['/ˈni.xta/']
    >>> find_pronunciations("{{ΔΦΑ|el|ˈni.ði.mos}}")
    ['/ˈni.ði.mos/']
    """
    return [f"/{p}/" for p in uniq(pattern.findall(code))]


def text_language(lang_donor_iso: str, myargs: dict[str, str] = defaultdict(str)) -> str:
    """
    see https://el.wiktionary.org/w/index.php?title=Module:%CE%B5%CF%84%CF%85%CE%BC%CE%BF%CE%BB%CE%BF%CE%B3%CE%AF%CE%B1&oldid=6368956 link_language function
    """
    lang: dict[str, str | bool] = langs[lang_donor_iso]
    lang_donor = str(lang["name"])  # neuter plural γαλλικά (or fem.sing. μέση γερμανκή)
    lang_donor_frm = str(lang["frm"])  # feminine accusative singular γαλλική
    if lang_donor != "" and lang_donor_frm != "":
        # feminine article + accusative singular τη γαλλική
        lang_donor_apo = str(lang["apo"])
        # προέλευσης από +apota -- FOR FAMILIES: σημιτικής προέλευσης
        lang_donor_from = str(lang["from"])
        if myargs["root"] == "1" or myargs["ρίζα"] == "1":
            mytext = f"{italic(lang_donor_frm)} <i>ρίζα</i>"
        elif lang["family"]:
            mytext = italic(lang_donor_from)
        elif myargs["text"] == "1" or myargs["κειμ"] == "1":
            mytext = italic(lang_donor_apo)
        else:
            mytext = italic(lang_donor_frm)

    return mytext


def labels_output(text_in: str, args: dict[str, str] = defaultdict(str)) -> str:
    """
    from https://el.wiktionary.org/w/index.php?title=Module:labels&oldid=5634715
    """
    from .aliases import aliases
    from .labels import labels as data

    mytext = ""

    label = args.get("label") or args.get("topic") or args.get("ετικέτα") or ""

    alias = ""
    if label in aliases:
        alias = label
        label = aliases[alias]

    text = text_in or args["1"]
    term = args["όρος"] or args["term"] or ""
    show = args["εμφ"] or args["show"] or ""
    noparenthesis = args["0"]
    if not label or label is None:
        return ""
    nodisplay = args["nodisplay"] or args["000"]

    if not nodisplay:
        if term != "":
            mytext = term
        elif text != "":
            mytext = text
        elif all_labels := data.get(label):
            if isinstance(all_labels, list):
                all_labels = all_labels[0]
            if all_labels.get("link") not in {None, "πατρότητα"}:
                mytext = show or f'{italic(all_labels["linkshow"])}'
        mytext = mytext if noparenthesis else f"({mytext})"
    return mytext


def last_template_handler(template: tuple[str, ...], locale: str, word: str = "") -> str:
    """
    Will be call in utils.py::transform() when all template handlers were not used.

        >>> last_template_handler(["γραπτηεμφ", "1889"], "el")
        '<i>(η λέξη μαρτυρείται από το 1889)</i>'
        >>> last_template_handler(["γραπτηεμφ", "1889", "0=-"], "el")
        'η λέξη μαρτυρείται από το 1889'

        >>> last_template_handler(["λενδ", "el", "fr"], "el")
        'λόγιο ενδογενές δάνειο:'
        >>> last_template_handler(["λενδ", "el", "fr", "0=-"], "el")
        'λόγιο ενδογενές δάνειο'

        >>> last_template_handler(["λδδ", "grc", "el", "νήδυμος"], "el")
        '(διαχρονικό δάνειο) <i>αρχαία ελληνική</i> νήδυμος'
        >>> last_template_handler(["λδδ", "grc-koi", "el"], "el")
        '(διαχρονικό δάνειο) <i>ελληνιστική κοινή</i>'
        >>> last_template_handler(["λδδ", "0=-", "grc-koi", "el", "τεχνικός"], "el")
        '<i>ελληνιστική κοινή</i> τεχνικός'

        >>> last_template_handler(["λ", "ἡδύς", "grc"], "el")
        'ἡδύς'
        >>> last_template_handler(["λ"], "el", word="Ινδία")
        'Ινδία'

        >>> last_template_handler(["ετ"], "el")
        ''
        >>> last_template_handler(["ετ", "ιατρική"], "el")
        '(<i>ιατρική</i>)'
        >>> last_template_handler(["ετ", "ιατρική", "0=-"], "el")
        '<i>ιατρική</i>'

        >>> last_template_handler(["λόγιο"], "el")
        '(<i>λόγιο</i>)'

        >>> last_template_handler(["ουσ"], "el")
        '(<i>ουσιαστικοποιημένο</i>)'

        >>> last_template_handler(["ετυμ", "ine-pro"], "el")
        '<i>πρωτοϊνδοευρωπαϊκή</i>'
        >>> last_template_handler(["ετυμ", "gkm"], "el")
        '<i>μεσαιωνική ελληνική</i>'
        >>> last_template_handler(["ετυμ", "μσν"], "el")
        '<i>μεσαιωνική ελληνική</i>'
        >>> last_template_handler(["ετυμ", "grc", "el", "ἔλαιον"], "el")
        '<i>αρχαία ελληνική</i> ἔλαιον'

        >>> last_template_handler(["γρ", "τραπεζομάντιλο"], "el")
        '<i>άλλη γραφή του</i> <b>τραπεζομάντιλο</b>'
        >>> last_template_handler(["γρ", "ελαιόδενδρο", "μορφή"], "el")
        '<i>άλλη μορφή του</i> <b>ελαιόδενδρο</b>'
        >>> last_template_handler(["γρ", "ελαιόδενδρο", "πολυ", "εμφ=ελαιόδενδρο(ν)"], "el")
        '<i>πολυτονική γραφή του</i> <b>ελαιόδενδρο(ν)</b>'
        >>> last_template_handler(["γρ", "ποιέω", "ασυν", "grc"], "el")
        '<i>ασυναίρετη μορφή του</i> <b>ποιέω</b>'
        >>> last_template_handler(["γρ", "ποιέω", "ασυν", "grc", "εμφ=ποι-έω"], "el")
        '<i>ασυναίρετη μορφή του</i> <b>ποι-έω</b>'
        >>> last_template_handler(["γρ", "colour", "", "en"], "el")
        '<i>άλλη γραφή του</i> <b>colour</b>'
        >>> last_template_handler(["γρ", "colour", "freestyle text", "en"], "el")
        '<i>freestyle text</i> <b>colour</b>'

        >>> last_template_handler(["πρόσφ", "μαλλί", "-ης"], "el")
        'μαλλί + -ης'
        >>> last_template_handler(["πρόσφ", "μαλλί", ".1=μαλλ(ί)", "-ης"], "el")
        'μαλλ(ί) + -ης'

        >>> last_template_handler(["αρχ"], "el")
        '<i>αρχαία ελληνική</i>'
        >>> last_template_handler(["αρχ", "ὅπου"], "el")
        '<i>αρχαία ελληνική</i> ὅπου'

        >>> last_template_handler(["μσν"], "el")
        '<i>μεσαιωνική ελληνική</i>'
        >>> last_template_handler(["μσν", "ὅπου"], "el")
        '<i>μεσαιωνική ελληνική</i> ὅπου'

        >>> last_template_handler(["fr"], "el")
        'γαλλικά'
    """
    from ...user_functions import concat, italic, strong
    from .. import defaults
    from .langs import langs
    from .template_handlers import lookup_template, render_template

    if lookup_template(template[0]):
        return render_template(word, template)

    tpl, *parts = template
    data = extract_keywords_from(parts)

    if tpl == "γραπτηεμφ":
        phrase = f"η λέξη μαρτυρείται από το {parts[0]}"
        if not data["0"]:
            phrase = term(phrase)
        return phrase

    if tpl == "λενδ":
        phrase = "λόγιο ενδογενές δάνειο"
        if not data["0"]:
            phrase += ":"
        return phrase

    if tpl == "μτφρ":
        phrase = "μεταφορικά"
        if not data["0"]:
            phrase = term(phrase)
        return phrase

    if tpl == "αρχ":
        phrase = italic("αρχαία ελληνική")
        if parts:
            phrase += f" {parts[0]}"
        return phrase

    if tpl == "μσν":
        phrase = italic("μεσαιωνική ελληνική")
        if parts:
            phrase += f" {parts[0]}"
        return phrase

    if tpl == "μτβ":
        phrase = "μεταβατικό"
        if not data["0"]:
            phrase = term(phrase)
        return phrase

    if tpl == "αμτβ":
        phrase = "αμετάβατο"
        if not data["0"]:
            phrase = term(phrase)
        return phrase

    if tpl == "βλφρ":
        phrase = italic("δείτε την έκφραση")
        if not data["0"]:
            phrase += ":"
        return phrase

    if tpl == "κτεπε":
        phrase = "κατʼ επέκταση"
        if not data["0"]:
            phrase = term(phrase)
        return phrase

    if tpl in ["λδδ", "dlbor"]:
        phrase = "" if data["0"] else "(διαχρονικό δάνειο) "
        phrase += text_language(parts[0], data)
        if rest := data["1"] or parts[2] if len(parts) > 2 else "":
            phrase += f" {rest}"
        return phrase

    if tpl in ["λ", "l", "link"]:
        return parts[0] if parts else word

    if tpl in ["ετ", "ετικέτα"]:
        if not parts:
            return ""
        data["label"] = parts[0]
        return labels_output(data.get("text", ""), data)

    if tpl == "ετυμ":
        text = italic(str(langs[parts[0]]["frm"]))
        if len(parts) > 2:
            text += f" {parts[2]}"
        return text

    if tpl == "λόγιο":
        data["label"] = tpl
        return labels_output("", data)

    if tpl == "ουσ":
        text = italic("ουσιαστικοποιημένο")
        return text if data["0"] else f"({text})"

    if text := {
        "νεολ": "νεολογισμός",
        "μπφ": "μέση-παθητική φωνή του ρήματος",
        "μτβ+αμτβ": "μεταβατικό και αμετάβατο",
        "μτγν": "ελληνιστική",
        "μτγρ": "μεταγραφή",
        "μτχα": "μετοχή παθητικού αορίστου",
        "μτχπα": "μετοχή παθητικού αορίστου",
        "μτχε": "μετοχή παθητικού ενεστώτα",
        "μτχπε": "μετοχή παθητικού ενεστώτα",
        "μτχεα": "μετοχή ενεργητικού αορίστου",
        "μτχεε": "μετοχή ενεργητικού ενεστώτα",
        "μτχεμ": "μετοχή ενεργητικού μέλλοντα",
        "μτχεπ": "μετοχή ενεργητικού παρακειμένου",
        "μτχμα": "μετοχή μέσου αορίστου",
        "μτχπ": "μετοχή παρακειμένου",
        "μτχπμ": "μετοχή παθητικού μέλλοντα",
        "μτχπp": "μετοχή παθητικού παρακειμένου",
        "μτχππ": "μετοχή παθητικού παρακειμένου",
        "μτχππαναδ": "μετοχή παθητικού παρακειμένου",
        "μτχχρ": "μετοχή παθητικού παρακειμένου",
        "μυθολ": "μυθολογία",
        "παρετυμολογία": "παρετυμολογία",
    }.get(template[0], ""):
        text = italic(text)
        return text if data["0"] else f"({text})"

    if tpl == "γρ":
        desc = parts[1] if len(parts) > 1 else ""
        desc = {
            "": "άλλη γραφή του",
            "απλοπ": "απλοποιημένη γραφή του",
            "μη απλοπ": "απλοποιημένη γραφή του",
            "ασυν": "ασυναίρετη μορφή του",
            "ετυμ": "ετυμολογική γραφή του",
            "μονο": "μονοτονική γραφή του",
            "μορφή": "άλλη μορφή του",
            "πολυ": "πολυτονική γραφή του",
            "πολ": "πολυτονική γραφή του",
            "παρωχ": "παρωχημένη γραφή του",
            "σνρ": "συνηρημένη μορφή του",
            "συνων": "συνώνυμο του",
        }.get(desc, desc)
        return f"{italic(desc)} {strong(data['εμφ'] or parts[0])}"

    if tpl in {"πρόσφ", "προσφ"}:
        words = []
        for idx, part in enumerate(parts, 1):
            words.append(data[f".{idx}"] or part)
        return concat(words, sep=" + ")

    # This is a country in the current locale
    if lang := langs.get(tpl):
        return str(lang["name"])

    return defaults.last_template_handler(template, locale, word=word)
