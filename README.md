# Landing Copy Optimizer

Makes your landing copy read like the ones that convert. That's it.

## The only thing you need

```powershell
pip install requests
$env:TYPESAFE_API_KEY="your-key-here"
```

No key, no work. No exceptions.

## How to use (don't think, just do this)

**Option 1 — The easy one (recommended):**

Tell your agent / Claude:

> optimize my landing with this skill

Done. It finds your copy, analyzes it, rewrites it, and shows you the winner. You touch nothing.

**Option 2 — Manual (1 command):**

```bash
python scripts/analyze_landing.py --input '{"hero":{"h1":"Your headline here"}}' --name "my-landing"
```

Have a file? Even better:

```bash
python scripts/analyze_landing.py --input landing.json --out resultado.md
```
