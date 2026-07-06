# Nya och avancerade förbättringsförslag för Forge v2 (Nästa iteration)

Utför följande optimeringar, arkitektoniska förändringar och nya funktioner i Forge-motorn för att göra den redo för produktionsliknande miljöer.

---

## 1. Arkitektur & Modularisering

### A. Splitta `engine.py`
* **Problem**: [forge/core/engine.py](file:///c:/Users/hund/stydeOS/forge/core/engine.py) är nu nästan 400 rader lång och blandar manifest-hantering, blueprint-laddning, LLM-provider-abstraktioner och valideringslogik.
* **Åtgärd**:
  - Flytta alla LLM-providers (`_call_openai`, `_call_anthropic` etc.) och `call_llm` till en ny modul: `forge/core/llm.py`.
  - Flytta blueprint-specifik logik (`load_blueprint`, `validate_blueprint`) till en ny modul: `forge/core/blueprint.py`.
  - Håll `forge/core/engine.py` fokuserad på manifest I/O och hantering av run-kataloger.

### B. Etablera en robust testsvit med `pytest`
* **Problem**: De nuvarande inline `_demo()`-funktionerna körs manuellt och kräver riktiga API-nycklar. Det saknas en automatiserad, mockad testsvit.
* **Åtgärd**:
  - Skapa katalogen `tests/` i projektets rot.
  - Skriv enhetstester för `spawner.py`, `evaluator.py`, `teacher.py` och CLI-kommandona.
  - Använd `unittest.mock` för att mocka API-anrop till OpenAI, Anthropic och Gemini så att hela testsviten kan köras blixtsnabbt offline.

---

## 2. Dynamisk Exekvering & Sandbox (Tools impl)

### A. Ersätt statisk mockning med `tools_impl.py`
* **Problem**: Statisk mockning via `mock_responses.yaml` kan inte hantera dynamiska verktyg (t.ex. att `file_read` faktiskt läser en fil från disken, eller att sökningar ändras dynamiskt baserat på parametrar).
* **Åtgärd**:
  - Om en blueprint-katalog innehåller en Python-fil vid namn `tools_impl.py`, ska systemet ladda den dynamiskt (med `importlib`).
  - Om agenten anropar ett verktyg (t.ex. `file_read`), ska motsvarande Python-funktion i `tools_impl.py` anropas med de parametrar som agenten skickade med.
  - Fall tillbaka till `mock_responses.yaml` om filen saknas.

---

## 3. Git-integration & Versionskontroll

### A. Spåra kodändringar i Runs
* **Problem**: När Teacher-agenten modifierar regler i `persona.md` och kör loopar sparas inte historiken i git, vilket gör det svårt att spåra exakt vilken kod/persona-ändring som ledde till vilken poäng.
* **Åtgärd**:
  - Vid varje `spawn` eller `loop`-iteration, läs in aktuell git commit-hash (med hjälp av `subprocess` och `git rev-parse HEAD`).
  - Läs även in om det finns lokala uncommitted ändringar (`git diff`).
  - Spara commit-hash och diff-status i `eval.json` samt i `forge.json` manifestet under varje run-post.

---

## 4. CLI Förbättringar

### A. Kommando för historik: `forge history`
* **Åtgärd**:
  - Skapa ett CLI-kommando `forge history` som läser `forge.json` och visar en vacker färgkodad tabell (med ANSI escape-koder för terminalfärger) över alla runs, deras status (PASSED/FAILED), datum, modeller och slutpoäng.
