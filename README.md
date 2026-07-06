# stydeOS — Forge v2

Forge v2 = closed-loop agent training. Spawna agent från blueprint → evaluera → teacher förbättrar → loopa tills godkänd.

## Mappstruktur
```
.
├── benchmarks/        # Testfall i JSON för evaluering
├── blueprints/        # Agent-blueprints och mallar
├── forge/             # Core logik och CLI wrappers
├── products/          # Sparade slutprodukter från Forge
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
