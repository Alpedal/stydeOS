# Master Prompt: Forge v2 — Doctor Scans, Checkpoints & Cost Telemetry (För DeepSeek v4 Pro/Flash)

Implementera följande tre nya moduler och integrationer i Forge v2 för att bygga in hälsoanalys, felsäker återställning och kostnadsspårning.

---

## Modul A: Blueprint Doctor (`forge doctor`)
Skapa ett nytt diagnostiskt verktyg som granskar alla blueprints i katalogen och varnar för konfigurationsfel eller filavvikelser före körning.

1. **Nytt CLI-kommando**: `python -m forge.cli.main doctor`
2. **Diagnostiska kontroller per blueprint**:
   - Kontrollera att filerna `persona.md` och `blueprint.yaml` existerar.
   - Varna om `persona.md` eller `blueprint.yaml` är 0 byte eller misstänkt korta (< 50 tecken).
   - Validera YAML-syntaxen i `blueprint.yaml` och verifiera att obligatoriska fält finns (`id`, `name`, `threshold`, `model`).
   - Kontrollera om blueprinten är inaktiv/stale (inga körningar i `forge.json` de senaste 7 dagarna).
3. **Visning**: Presentera en CP1252-säker ASCII-rapport uppdelad på `Healthy`, `Warnings` och `Critical Issues`.

---

## Modul B: Checkpoints & Återställning (`forge checkpoint` / `recover`)
Implementera ett system för att spara och återställa systemtillståndet (`forge.json`) för att förhindra förlust av träningshistorik eller konfigurationer.

1. **Kommandon**:
   - `python -m forge.cli.main checkpoint <name>`: Sparar en kopia av nuvarande `forge.json` till `.forge_checkpoints/checkpoint_<name>.json`.
   - `python -m forge.cli.main checkpoint --list`: Listar alla sparade checkpoints med skapandetid och storlek.
   - `python -m forge.cli.main recover <name>`: Återställer `forge.json` från den sparade checkpointen.
2. **Säkerhet**: Skapa `.forge_checkpoints/`-mappen automatiskt. Gör en `.bak`-kopia av `forge.json` innan en återställning utförs för att förhindra oavsiktlig överskrivning.

---

## Modul C: Telemetry & Kostnadsspårning (Token Tracker)
Integrera automatisk beräkning av token-användning och API-kostnader för att förhindra skenande kostnader under loop-körningar.

1. **Tokenspårning**:
   - Uppdatera run-strukturen i `forge.json` så att varje körning sparar `prompt_tokens`, `completion_tokens` och `estimated_usd_cost`.
   - I `llm.py`, om mock-svar returneras, generera estimerade tokens (t.ex. 1 tecken = 0.25 tokens). Om ett live API-anrop görs, läs ut de faktiska token-värdena från API-responsen.
2. **Kostnadskalkylator**:
   - Beräkna kostnad baserat på modell och leverantör (t.ex. $2.50/M input tokens och $10.00/M output tokens för standardmodeller, och lägre priser för flash-modeller).
3. **Rapportering**:
   - Uppdatera `forge status` och `forge history` för att visa den ackumulerade kostnaden för blueprinten och totalt för hela systemet.
