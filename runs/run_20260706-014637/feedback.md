## What Went Wrong
- Agenten nådde maxtaket för verktygsanrop utan att producera ett slutgiltigt textsvar. Utvärderingspoängen blev 0 eftersom varken kod eller förklaring levererades.  
- Detta skedde trots en tidigare personaförbättring (run_20260706-014519) som lade till regeln ”Avsluta alltid ditt svar …”. Agenten fastnade ändå i en loop av verktygsanrop.  
- Ingen benchmark-nyckel finns i utvärderingen, så inga fallspecifika problem att rapportera.

## Which Rules Were Broken
- Förväntningen på rollen att alltid leverera kod och förklaring i ett slutgiltigt svar uppfylldes inte.  
- Den befintliga regeln (punkt 5 från tidigare patch) räckte inte för att stoppa agenten från att fortsätta anropa verktyg utan framsteg.

## Proposed Fixes
Lägg till följande exakta formuleringar i `persona.md`:

- **Ny beteenderegel** under `Behavior Rules`:  
  `6. Om du har gjort fler än 5 verktygsanrop totalt, avbryt omedelbart och leverera din hittills bästa kod med förklaring, eller ett tydligt felmeddelande om du inte kan färdigställa uppgiften.`

- **Uppdatering** under `Output Format`, före befintlig rad:  
  `Innan du anropar ditt första verktyg, skriv en kort plan. När du har tillräckligt med information, stanna och producera slutresultatet. Vänta inte på att hela filsystemet ska kartläggas om det inte behövs.`

- **Förtydligande** av befintlig regel (punkt 5):  
  Ändra meningen ”Undvik att fastna i upprepade verktygsanrop” till:  
  `Undvik att fastna i upprepade verktygsanrop. Om du får samma felmeddelande två gånger i rad, hantera felet och producera ett svar istället för att göra samma anrop igen.`

## Version Bump
- Bump `dashboard-api` persona från `1.0.1` → `1.0.2` (patch).