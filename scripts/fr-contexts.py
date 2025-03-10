import re

from scripts_utils import get_content


def clean_lua(text: str) -> str:
    text = text.replace("local ", "")
    text = text.replace("end", "")
    text = text.replace("true", "True")
    text = text.replace("false", "False")
    text = text.replace("--", "#")
    return text


def process_display(display: str) -> str:
    if "[[" in display:
        display = re.sub(r"\[\[[^\|\]]*\|(^\])*", "", display)
        display = display.replace("]]", "")
        display = display.replace("[[", "")
    return display


def get_contexts() -> dict[str, str]:
    text = clean_lua(get_content("https://fr.wiktionary.org/wiki/Module:contexte/data?action=raw"))
    repl = (
        "alias",
        "cat",
        "glossaire",
        "id",
        "invisible",
        "label",
        "lien",
        "nom",
        "type",
    )
    text = re.sub(rf"\s+({'|'.join(repl)})[\s]*=", r'    "\1":', text)
    text = re.sub(r"^\s+\['([^']+)']\s*=", r'    "\1":', text, flags=re.MULTILINE)

    code = text[: text.find("# Prépare tous les labels")]

    _locals: dict[str, dict[str, dict[str, str | set[str]]]] = {}
    exec(code, None, _locals)

    contexts = _locals.get("c", {})

    all_contexts = {}
    for top_values in contexts.values():
        for key, values in top_values.items():
            display = process_display(values.get("label") or values.get("nom") or key)  # type: ignore[union-attr]
            all_contexts[key] = display
            for alias in values.get("alias", set()):  # type: ignore[union-attr]
                all_contexts[alias] = display

    return all_contexts


contexts = get_contexts()
print("contexts = {")
for key, value in sorted(contexts.items()):
    print(f'    "{key}": "{value[0].capitalize()}{value[1:]}",')
print(f"}}  # {len(contexts):,}")
