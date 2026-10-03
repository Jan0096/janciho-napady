// =====================================================================
//  Kilometrovník dopravcu – dotazy Power Query pre Power BI Desktop
//  Každý blok nižšie vlož ako SAMOSTATNÝ prázdny dotaz
//  (Domov → Transformovať údaje → Nový zdroj → Prázdny dotaz → Rozšírený editor).
//  Názov dotazu nastav presne podľa riadku "NÁZOV DOTAZU".
// =====================================================================


// ---------------------------------------------------------------------
// NÁZOV DOTAZU: PriecinokDat
// Parameter s cestou k priečinku, kam ukladáš CSV z appky.
// Cesta MUSÍ končiť spätnou lomkou \
// ---------------------------------------------------------------------
"C:\Kilometrovnik\" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]


// ---------------------------------------------------------------------
// NÁZOV DOTAZU: Jazdy
// ---------------------------------------------------------------------
let
    Zdroj = Csv.Document(
        File.Contents(PriecinokDat & "jazdy.csv"),
        [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Hlavicky = Table.PromoteHeaders(Zdroj, [PromoteAllScalars = true]),
    Typy = Table.TransformColumnTypes(
        Hlavicky,
        {
            {"id", type text}, {"datum", type date}, {"firma", type text}, {"trasa", type text},
            {"vozidlo_id", type text}, {"vozidlo", type text}, {"stav", type text},
            {"zaplatena", Int64.Type},
            {"km_naklad", type number}, {"km_prazdne", type number}, {"km_spolu", type number}, {"dni", type number},
            {"trzba", Currency.Type}, {"naklady", Currency.Type}, {"variabilne_naklady", Currency.Type},
            {"fixne_naklady", Currency.Type}, {"diety", Currency.Type}, {"myto", Currency.Type},
            {"ine_naklady", Currency.Type}, {"zisk", Currency.Type},
            {"marza_pct", type number}, {"zisk_den", Currency.Type},
            {"splatnost_dni", type number}, {"datum_splatnosti", type date}
        },
        "en-US"   // CSV používa desatinnú bodku a dátumy RRRR-MM-DD
    ),
    // Čitateľný stav pre slicery a legendy
    StavText = Table.AddColumn(Typy, "Stav jazdy",
        each if [stav] = "zrealizovana" then "Zrealizovaná" else "Len ponuka", type text),
    Uhrada = Table.AddColumn(StavText, "Úhrada",
        each if [stav] <> "zrealizovana" then "Nefakturované"
             else if [zaplatena] = 1 then "Zaplatená"
             else if [datum_splatnosti] <> null and [datum_splatnosti] < Date.From(DateTime.LocalNow()) then "Po splatnosti"
             else "Čaká na úhradu",
        type text)
in
    Uhrada


// ---------------------------------------------------------------------
// NÁZOV DOTAZU: Firmy
// ---------------------------------------------------------------------
let
    Zdroj = Csv.Document(
        File.Contents(PriecinokDat & "firmy.csv"),
        [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Hlavicky = Table.PromoteHeaders(Zdroj, [PromoteAllScalars = true]),
    Typy = Table.TransformColumnTypes(Hlavicky, {{"firma", type text}}),
    BezDuplicit = Table.Distinct(Typy, {"firma"})
in
    BezDuplicit


// ---------------------------------------------------------------------
// NÁZOV DOTAZU: Vozidla
// ---------------------------------------------------------------------
let
    Zdroj = Csv.Document(
        File.Contents(PriecinokDat & "vozidla.csv"),
        [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Hlavicky = Table.PromoteHeaders(Zdroj, [PromoteAllScalars = true]),
    Typy = Table.TransformColumnTypes(
        Hlavicky,
        {
            {"id", type text}, {"nazov", type text},
            {"fixne_mesacne", Currency.Type}, {"diety_den", Currency.Type},
            {"km_mesacne", type number}, {"dni_mesacne", type number},
            {"variabilne_km", type number}, {"fixne_km", type number}, {"naklad_km", type number},
            {"ciel_zisk_pct", type number}
        },
        "en-US"
    )
in
    Typy


// ---------------------------------------------------------------------
// NÁZOV DOTAZU: Faktury
// Nákladové faktúry zo záložky 6 (už zaradené do skupín nákladov).
// ---------------------------------------------------------------------
let
    Zdroj = Csv.Document(
        File.Contents(PriecinokDat & "faktury.csv"),
        [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Hlavicky = Table.PromoteHeaders(Zdroj, [PromoteAllScalars = true]),
    Typy = Table.TransformColumnTypes(
        Hlavicky,
        {
            {"id", type text}, {"datum", type date}, {"dodavatel", type text}, {"popis", type text},
            {"suma", Currency.Type}, {"kategoria_kod", type text}, {"kategoria", type text},
            {"vozidlo_id", type text}, {"vozidlo", type text}, {"sposob_zaradenia", type text}
        },
        "en-US"
    )
in
    Typy


// ---------------------------------------------------------------------
// NÁZOV DOTAZU: PlanNakladov
// Plánované mesačné náklady každého auta po skupinách (z nastavení vozidla).
// ---------------------------------------------------------------------
let
    Zdroj = Csv.Document(
        File.Contents(PriecinokDat & "plan_nakladov.csv"),
        [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Hlavicky = Table.PromoteHeaders(Zdroj, [PromoteAllScalars = true]),
    Typy = Table.TransformColumnTypes(
        Hlavicky,
        {
            {"vozidlo_id", type text}, {"vozidlo", type text}, {"kategoria_kod", type text},
            {"kategoria", type text}, {"plan_mesacne", Currency.Type}
        },
        "en-US"
    )
in
    Typy
