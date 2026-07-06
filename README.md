# stydeOS — Forge v2

Forge v2 = closed-loop agent training. Spawna agent från blueprint → evaluera → teacher förbättrar → loopa tills godkänd.

## Mappstruktur
```
.
├── benchmarks/        # Testfall i JSON för evaluering
├── blueprints/        # Original-blueprints och mallar
├── done-blueprints/   # Arkiverade blueprints som är redo för produktion
├── forge/             # Core logik och CLI wrappers
├── production/        # Sparade slutprodukter från Forge
├── refinery/          # Blueprints under aktiv förbättring
├── runs/              # Automatiska körningar (runs)
└── workspace/         # Temporära arbetsytor och scratch
```

## CLI
Kör Forge CLI med:
`uv run python -m forge.cli.main init | spawn | eval | improve | loop`

## Regler
- Rör aldrig filer i `runs/` manuellt.
- `forge.json` är systemets source of truth.
- Inga nya externa dependencies utan godkännande (använd stdlib i första hand).
