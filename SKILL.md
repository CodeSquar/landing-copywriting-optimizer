---
name: landing-copy-optimizer
description: Optimiza el copy de una landing page SaaS hacia la "landing perfecta" con Jev (Typesafe AI). Usa esta skill siempre que el usuario mencione landing page, landing copy, headlines, optimizar conversion con benchmarks, analizar copy con Jev/Typesafe, o pida acercarse al average que funciona, incluso si no dice la palabra "skill".
---

# Landing Copy Optimizer (Jev + average que funciona)

Optimizas una landing en loop corto: **escritura JSON → análisis Jev → MD de resultados → reescritura**,
hasta acercarte al average de `references/average.md`.

El input JSON puede tener **cualquier estructura**: se envía tal cual como `state` a Jev.
Jev no genera texto, solo devuelve decisiones estructuradas (choice/score + probabilidades + confianza).

## Landing Page Copy

- Usar un estilo principalmente **directo (36.7%)**, con apoyo **punchy (21.9%)** y **aspiracional (19.9%)**. Mantener el hype como recurso secundario (11.2%).
- Comunicar el valor principalmente desde el **resultado para el usuario (68.7% outcome-first)**; features (11.7%) y definición de categoría (11.6%) deben apoyar ese mensaje.
- Buscar **claridad muy alta**: 52.9% “very clear” + 40.7% “extremely explicit” (**3.34/4**). El visitante debe entender rápido qué hace el producto y por qué importa.
- Mantener una especificidad moderada (**1.79/4**): usar detalles concretos cuando aporten credibilidad, sin convertir todo el copy en explicación técnica.
- Ser **muy conciso** (**3.66/4**): 71.8% en el nivel máximo. Eliminar redundancia y hacer que casi cada frase aporte información o persuasión.
- Orientar el mensaje a outcomes, pero sin exagerarlo (**2.08/4**): combinar beneficios con qué hace el producto y con sus features.
- Usar un tono principalmente **confident (34.6%) + bold (30.8%) + aspirational (24.2%)**. Evitar depender de hype-heavy (7%), tono conversacional (2.9%) o técnico (0.3%).
- Mantener un carácter **aspirational/polished (30.3%)**, **clear/minimal (22.8%)** y familiar al marketing SaaS (22.3%), sin perder claridad.
- Headlines: **directos, cortos, claros y orientados al resultado**.
- Descripciones: **breves, específicas lo suficiente y centradas en el valor**, usando features solo para volver creíble la promesa.
- Evitar: textos largos, sobreexplicación, lenguaje técnico, hype excesivo, demasiados detalles y copy centrado únicamente en features o únicamente en outcomes.

La sección anterior es la regla central. En caso de duda entre dos rewrites, elige el que más se acerque a ella.

## Workflow (sigue este orden)

1. **Extrae el JSON tú mismo (no lo pidas).** localiza el copy en los archivos del proyecto del usuario (solo lectura, nunca edites) y construye el JSON del `state` a partir de lo que encuentres (hero, H1/sub, CTAs, secciones, pricing, FAQ, CTAs finales). Acepta cualquier forma: `{"hero": {...}}`, `{"state": {...}}`, `{"name":..., "state":...}`. Si viene con wrapper `state`, se usa ese campo; si no, el JSON entero es el `state`. Mira `references/example-landing.json` como ejemplo. Solo pide el JSON al usuario si tras buscar no encuentras copy en el proyecto. Evita pasos manuales.
2. **Analiza con el script (sin crear archivos).** Ejecuta (desde la carpeta de la skill) pasando el JSON inline; el MD sale por stdout:
   `python scripts/analyze_landing.py --input '{"hero": {...}}'`
   Requiere `TYPESAFE_API_KEY` en el entorno. Usa las mismas 8 questions del `script.py` original (fijas, no se pasan por CLI).
3. **Lee el MD resultante.** Tiene el formato de `references/average.md` (choice + score con probabilidades) más una línea `_Objetivo average:_` con delta / OK-DIFERENTE por métrica.
4. **Compara contra el average.** El objetivo es acercarse a: direct ~36.7%, outcome_first ~68.7%, clarity ~3.34, specificity ~1.79, conciseness ~3.66, outcome_orientation ~2.08, confident ~34.6%, aspirational_polished ~30.3%. No busques 100% en nada: el average es una mezcla.
5. **Reescribe solo lo necesario.** Aplica la regla central para corregir el desvío más grande primero (ver guía abajo). Genera un nuevo JSON con la misma estructura de entrada.
6. **Repite.** Vuelve al paso 2 con el nuevo JSON. Para después de 2–3 iteraciones si ya no hay mejora clara o si el copy empieza a sonar forzado.
7. **No toques la app/web del usuario.** Nunca edites archivos del proyecto del usuario (app, web, repo). Solo trabaja sobre el JSON del copy. Al finalizar, muestra el copy ganador en formato MD en el chat (no en archivo) y pregunta si quiere integrarlo antes de tocar nada.

## Cómo corregir según el MD (por qué importa)

- **dominant_style ≠ direct:** el visitante no entiende qué hace el producto. Reescribe el H1 en una frase plana que diga producto + para quién + resultado. Guarda punchy/aspiracional para H2s y CTA final.
- **value_framing ≠ outcome_first:** lideras con features o categoría. Mueve el beneficio al frente ("Logra X en Y") y deja la feature como prueba ("con Z").
- **clarity < 3.0:** hay vaguedad. Concreta verbo + objeto en hero y una sección. Pregúntate: ¿un visitante nuevo entiende en 5 segundos qué hace y por qué importa?
- **specificity muy alta (>2.5):** te volviste técnico. Quita mecanismo y deja solo el detalle que da credibilidad (número, tiempo, entrega concreta).
- **specificity muy baja (<1.0):** suenas genérico. Agrega 1–2 detalles concretos (qué recibe, cuánto tarda, qué incluye).
- **conciseness < 3.0:** hay redundancia. Corta frases que no agregan información o persuasión; fusiona hero/sub si dicen lo mismo.
- **outcome_orientation muy alto (>3.0):** prometes sin sostener. Agrega qué hace el producto + 1 feature creíble por sección.
- **outcome_orientation muy bajo (<1.5):** describes sin vender. Agrega el resultado del usuario a cada H2.
- **tone → hype_heavy / conversacional / técnico:** recalibra a confident+bold+aspiracional: afirmaciones fuertes pero verificables, sin superlativos vacíos ni jerga.
- **overall_character → generic_marketing:** es intercambiable con otro SaaS. Mantén la forma SaaS familiar pero con 1 promesa propia y 1 detalle propio.

## CLI del script

```bash
# Requiere: pip install requests + TYPESAFE_API_KEY
python scripts/analyze_landing.py --input landing.json --out resultado.md
python scripts/analyze_landing.py --input '{"hero":{"h1":"Crea skins en segundos"}}' --name "test-rapido"
python scripts/analyze_landing.py --input landing.json --no-compare   # solo valores, sin línea de objetivo
python scripts/analyze_landing.py --input landing.json --json-out raw.json
python scripts/analyze_landing.py --dry-run   # prueba formato MD sin gastar API
```

El script retorna el MD por stdout y, si pasas `--out`, lo guarda en archivo.
Lee `references/average.md` para el objetivo y `references/example-landing.json` para el formato de entrada.

## Notas Jev (Typesafe AI)

- Cada respuesta trae probabilidades calibradas + confianza: úsalas como señal, no como verdad absoluta; si la confianza es baja, prioriza tu juicio y la regla central.
