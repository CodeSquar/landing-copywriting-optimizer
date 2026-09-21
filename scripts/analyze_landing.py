#!/usr/bin/env python3
"""
analyze_landing.py — version simple del benchmark SaaS.

Que hace:
  1. Recibe un JSON cualquiera por linea de comando (archivo o string).
  2. Lo manda como `state` a Typesafe AI Jev (POST /v1/systemone).
  3. Retorna en Markdown los valores resultantes del analisis.

Mismas 8 questions que script.py original:
  choice: dominant_style, value_framing, tone, overall_character
  score:  clarity, specificity, conciseness, outcome_orientation

Docs Jev (TypeSafe AI, modelo System One, sept 2026):
  - Endpoint: POST https://api.typesafe.ai/v1/systemone
  - Auth: Authorization: Bearer $TYPESAFE_API_KEY
  - Body: {"model": "jev-latest", "state": <str|obj|array>, "questions": {...}}
  - Todas las questions se evaluan en paralelo sobre el mismo state.
  - Choice retorna {choice, probabilities, confidence}.
  - Score retorna {score, probabilities, confidence}.
  - Output tokens gratis; input ~$0.042 / Mtok. Latencia tipica 70-500 ms.
  - Ver: https://docs.typesafe.ai/introduction/quickstart
         https://docs.typesafe.ai/api
         https://docs.typesafe.ai/concepts/system-one

Uso:
  set TYPESAFE_API_KEY=xxx
  python analyze_landing.py --input landing.json
  python analyze_landing.py --input landing.json --out resultado.md
  python analyze_landing.py --input "{\"hero\": {\"h1\": \"...\"}}" --name "Mi landing"
  python analyze_landing.py --input landing.json --json-out raw.json
  python analyze_landing.py --input landing.json --no-compare
  python analyze_landing.py --dry-run   (prueba formato MD sin llamar API)
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    requests = None

API_URL = os.getenv("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
MODEL_DEFAULT = os.getenv("TYPESAFE_MODEL", "jev-latest")

# ------------------------------------------------------------
# Mismas QUESTIONS que script.py original (no modificar
# sin actualizar SKILL.md + references/).
# ------------------------------------------------------------
QUESTIONS = {
    "dominant_style": {
        "type": "choice",
        "instructions": "What best describes the dominant copywriting style across this landing page?",
        "criteria": {
            "direct": "Direct, plain, explicit, says exactly what the product does.",
            "punchy": "Short, energetic, compressed, memorable statements.",
            "minimalist": "Very few words, restrained language, high information density.",
            "conversational": "Natural, casual, human, spoken-language feel.",
            "authoritative": "Confident, precise, expert, matter-of-fact.",
            "technical": "Product-specific, technical, mechanism-oriented language.",
            "aspirational": "Focused on desired future state, transformation, or ambition.",
            "playful": "Witty, informal, personality-heavy, clever.",
            "hype_driven": "Superlatives, exaggerated promises, excitement-heavy language."
        }
    },
    "value_framing": {
        "type": "choice",
        "instructions": "What is the primary way this landing page communicates value?",
        "criteria": {
            "outcome_first": "Leads with what the user gets or achieves.",
            "problem_first": "Leads with the pain, frustration, or problem being solved.",
            "feature_first": "Leads with product capabilities and features.",
            "mechanism_first": "Leads with how the product works.",
            "workflow_first": "Leads with the task or process the product simplifies.",
            "category_first": "Primarily explains what category or type of product this is."
        }
    },
    "clarity": {
        "type": "score",
        "instructions": "How immediately understandable is the copy to a qualified visitor who has never seen the product before?",
        "criteria": [
            "Ambiguous and difficult to understand.",
            "Partially understandable but requires interpretation.",
            "Generally clear with some vague wording.",
            "Very clear; product and value are quickly understood.",
            "Extremely explicit; what it does and why it matters are obvious almost instantly."
        ]
    },
    "specificity": {
        "type": "score",
        "instructions": "How specific and concrete is the copy rather than generic or interchangeable with another SaaS?",
        "criteria": [
            "Highly generic and interchangeable.",
            "Mostly generic with a few specific details.",
            "Balanced between generic and specific.",
            "Mostly specific and product-relevant.",
            "Extremely specific to the exact product, workflow, and outcome."
        ]
    },
    "conciseness": {
        "type": "score",
        "instructions": "How concise and information-dense is the copy?",
        "criteria": [
            "Very wordy or repetitive.",
            "Contains considerable unnecessary explanation.",
            "Balanced amount of copy.",
            "Concise with little wasted language.",
            "Extremely compressed and high-signal; nearly every phrase adds useful information."
        ]
    },
    "outcome_orientation": {
        "type": "score",
        "instructions": "How strongly does the copy focus on what the user accomplishes rather than merely describing the product or its features?",
        "criteria": [
            "Almost entirely product or feature focused.",
            "Mostly product focused.",
            "Balanced between product and outcomes.",
            "Mostly outcome focused.",
            "Strongly centered on concrete user results and accomplishments."
        ]
    },
    "tone": {
        "type": "choice",
        "instructions": "What best describes the overall tone of the landing page copy?",
        "criteria": {
            "restrained": "Calm, understated, neutral, avoids strong marketing language.",
            "confident": "Clear and assured without sounding aggressive.",
            "bold": "Assertive, energetic, and willing to make strong claims.",
            "conversational": "Informal, natural, approachable, spoken-language feel.",
            "technical": "Precise, factual, technical, and product-oriented.",
            "aspirational": "Polished and focused on an attractive future state.",
            "hype_heavy": "Aggressive, exaggerated, superlative-heavy marketing."
        }
    },
    "overall_character": {
        "type": "choice",
        "instructions": "Which description best captures the overall character of the landing page copy?",
        "criteria": {
            "clear_minimal": "Clear, restrained, concise, simple, and high-signal.",
            "concrete_direct": "Specific, explicit, practical, and outcome-oriented.",
            "bold_punchy": "Short, energetic, assertive, and memorable.",
            "explanatory_precise": "Explains enough to remove ambiguity while remaining precise.",
            "conversational_simple": "Human, approachable, informal, and easy to read.",
            "technical_precise": "Technical, exact, product-specific, and information-dense.",
            "aspirational_polished": "Outcome-driven, elevated, polished, and emotionally appealing.",
            "generic_marketing": "Broad benefits, familiar SaaS wording, and interchangeable claims."
        }
    }
}

# Objetivos extraidos de average.md (10 landings que "funcionan").
# Se muestran como linea de comparacion en el MD.
TARGETS = {
    "dominant_style": {"choice": "direct", "prob": 0.367},
    "value_framing": {"choice": "outcome_first", "prob": 0.687},
    "clarity": {"score": 3.34},
    "specificity": {"score": 1.79},
    "conciseness": {"score": 3.66},
    "outcome_orientation": {"score": 2.08},
    "tone": {"choice": "confident", "prob": 0.346},
    "overall_character": {"choice": "aspirational_polished", "prob": 0.303},
}

ORDER = ["dominant_style", "value_framing", "clarity", "specificity",
         "conciseness", "outcome_orientation", "tone", "overall_character"]

LABELS = {
    "dominant_style": "Dominant style",
    "value_framing": "Value framing",
    "clarity": "Clarity",
    "specificity": "Specificity",
    "conciseness": "Conciseness",
    "outcome_orientation": "Outcome orientation",
    "tone": "Tone",
    "overall_character": "Overall character",
}


def load_state(raw):
    """Acepta path a .json o string JSON crudo. Retorna (state, name_hint)."""
    raw = (raw or "").strip()
    if not raw:
        # Soporta pipe: echo {...} | python analyze_landing.py
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("Sin input. Usa --input <archivo.json | string JSON> o pipe por stdin.")

    # 1) Si es un archivo existente, cargarlo.
    if os.path.isfile(raw):
        with open(raw, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"El input no es path valido ni JSON valido: {e}")

    # 2) Aceptar wrappers comunes, el state es lo que va a Jev.
    #    - {"state": {...}} -> usa .state
    #    - {"name":..., "state":...} (formato LANDINGS original) -> usa .state
    #    - anything else -> el JSON entero ES el state (cualquiera).
    if isinstance(data, dict) and "state" in data:
        return data["state"], data.get("name")
    return data, (data.get("name") if isinstance(data, dict) else None)


def analyze(state, model, api_url, api_key, timeout=60):
    if requests is None:
        raise RuntimeError("Falta dependencia 'requests'. Instala con: pip install requests")
    if not api_key:
        raise ValueError("Set the TYPESAFE_API_KEY environment variable.")
    resp = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "state": state, "questions": QUESTIONS},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def _fmt_pct(x):
    try:
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return "?"


def to_markdown(result, name="landing", compare=True):
    """Convierte la respuesta Jev en MD estilo average.md (una sola landing)."""
    answers = result.get("answers", {})
    L = [f"# Landing Analysis — {name}", ""]
    L.append("## Choice questions")
    L.append("")
    for qid in ["dominant_style", "value_framing", "tone", "overall_character"]:
        a = answers.get(qid)
        if not a:
            continue
        winner = a.get("choice", "?")
        conf = a.get("confidence", 0)
        L.append(f"### {LABELS[qid]} → **{winner}** (conf. {_fmt_pct(conf)})")
        if compare and qid in TARGETS:
            t = TARGETS[qid]
            mark = "OK" if winner == t["choice"] else "DIFERENTE"
            L.append(f"_Objetivo average: **{t['choice']}** ({_fmt_pct(t['prob'])}) → {mark}_")
        L.append("| Opción | Prob. |")
        L.append("|---|---|")
        probs = a.get("probabilities", {})
        for opt, p in sorted(probs.items(), key=lambda x: x[1], reverse=True):
            L.append(f"| {opt} | {_fmt_pct(p)} |")
        L.append("")
    L.append("## Score questions (0–4)")
    L.append("")
    for qid in ["clarity", "specificity", "conciseness", "outcome_orientation"]:
        a = answers.get(qid)
        if not a:
            continue
        score = a.get("score", 0)
        conf = a.get("confidence", 0)
        L.append(f"### {LABELS[qid]} — **{float(score):.2f} / 4** (conf. {_fmt_pct(conf)})")
        if compare and qid in TARGETS:
            t = TARGETS[qid]["score"]
            delta = float(score) - t
            L.append(f"_Objetivo average: **{t:.2f} / 4** (delta {delta:+.2f})_")
        L.append("| Nivel | Prob. |")
        L.append("|---|---|")
        probs = a.get("probabilities", {})
        for lvl in sorted(probs.keys(), key=lambda x: int(x)):
            L.append(f"| {lvl} | {_fmt_pct(probs[lvl])} |")
        L.append("")
    usage = result.get("usage", {})
    if usage:
        L.append(f"_Tokens: {usage.get('input_tokens', '?')} input / {usage.get('output_tokens', '?')} output · model {result.get('model', '')}_")
        L.append("")
    return "\n".join(L).strip() + "\n"


MOCK_RESULT = {
    "model": "jev-latest (mock)",
    "answers": {
        "dominant_style": {"type": "choice", "choice": "direct",
                           "probabilities": {"direct": 0.4, "punchy": 0.25, "aspirational": 0.2, "hype_driven": 0.1, "authoritative": 0.05},
                           "confidence": 0.5},
        "value_framing": {"type": "choice", "choice": "outcome_first",
                          "probabilities": {"outcome_first": 0.7, "feature_first": 0.15, "category_first": 0.15},
                          "confidence": 0.65},
        "clarity": {"type": "score", "score": 3.2,
                    "probabilities": {"0": 0, "1": 0, "2": 0.1, "3": 0.6, "4": 0.3}, "confidence": 0.6},
        "specificity": {"type": "score", "score": 1.8,
                        "probabilities": {"0": 0.1, "1": 0.35, "2": 0.2, "3": 0.3, "4": 0.05}, "confidence": 0.5},
        "conciseness": {"type": "score", "score": 3.6,
                        "probabilities": {"0": 0, "1": 0, "2": 0.05, "3": 0.3, "4": 0.65}, "confidence": 0.75},
        "outcome_orientation": {"type": "score", "score": 2.1,
                               "probabilities": {"0": 0.05, "1": 0.3, "2": 0.2, "3": 0.38, "4": 0.07}, "confidence": 0.5},
        "tone": {"type": "choice", "choice": "confident",
                 "probabilities": {"confident": 0.35, "bold": 0.3, "aspirational": 0.25, "hype_heavy": 0.1},
                 "confidence": 0.5},
        "overall_character": {"type": "choice", "choice": "aspirational_polished",
                              "probabilities": {"aspirational_polished": 0.3, "clear_minimal": 0.25, "generic_marketing": 0.2, "bold_punchy": 0.15, "concrete_direct": 0.1},
                              "confidence": 0.4},
    },
    "usage": {"input_tokens": 0, "output_tokens": 0},
}


def main(argv=None):
    # Windows: consola cp1252 no soporta flechas/emdash del MD.
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description="Analiza un landing JSON con Jev y retorna MD (mismas questions que script.py).")
    ap.add_argument("--input", "-i", default="",
                    help="Path a .json o string JSON crudo. Tambien acepta stdin. Cualquier estructura vale: se envia como state.")
    ap.add_argument("--name", "-n", default="", help="Nombre para el titulo del MD (default: nombre archivo o 'landing').")
    ap.add_argument("--out", "-o", default="", help="Archivo .md de salida (default: solo stdout).")
    ap.add_argument("--json-out", default="", help="Opcional: guardar respuesta cruda Jev en JSON.")
    ap.add_argument("--model", default=MODEL_DEFAULT, help=f"Modelo Jev (default: {MODEL_DEFAULT}).")
    ap.add_argument("--api-url", default=API_URL, help="Endpoint SystemOne.")
    ap.add_argument("--no-compare", action="store_true", help="No mostrar linea de objetivo average.")
    ap.add_argument("--dry-run", action="store_true", help="No llama a la API; imprime MD de ejemplo.")
    args = ap.parse_args(argv)

    if args.dry_run:
        md = to_markdown(MOCK_RESULT, args.name or "landing (mock)", compare=not args.no_compare)
        print(md)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[dry-run] MD escrito en {args.out}", file=sys.stderr)
        return 0

    try:
        state, hint = load_state(args.input)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    name = args.name or hint or "landing"
    # Si el input fue un path, usar su basename como nombre por defecto.
    if not args.name and args.input and os.path.isfile(args.input.strip()):
        name = os.path.splitext(os.path.basename(args.input.strip()))[0]

    api_key = os.getenv("TYPESAFE_API_KEY", "")
    try:
        result = analyze(state, args.model, args.api_url, api_key)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        # Mostrar body de error HTTP si lo hay (como script.py original).
        body = getattr(getattr(e, "response", None), "text", "")
        print(f"ERROR llamando a Jev: {e}\n{body}", file=sys.stderr)
        return 1

    md = to_markdown(result, name, compare=not args.no_compare)
    print(md)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"MD escrito en {args.out}", file=sys.stderr)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"JSON escrito en {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
