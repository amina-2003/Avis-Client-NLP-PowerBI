// Power Query (M) - requete fonction generique. NON TESTE dans Power BI Desktop.
// 1) Accueil > Obtenir des donnees > Requete vide > Editeur avance > coller ce code, nommer la requete "fnCSV".
// 2) Creer un parametre texte "Dossier" (ex. C:\projet12\powerbi\ , avec le \ final).
// 3) Pour chaque table : requete vide > = fnCSV("FactReviews")  (puis FactSales, FactReviewThemes, DimDate, DimReviewDate, ...)
let
    fnCSV = (nom as text) as table =>
        let
            Source  = Csv.Document(File.Contents(Dossier & nom & ".csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
            Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
            // Culture fixe en-US : evite les erreurs de decimales (point) sur un Power BI en francais
            Types   = Table.TransformColumnTypes(Entetes, List.Transform(Table.ColumnNames(Entetes), each {_, type any}), "en-US")
        in
            Types
in
    fnCSV
// Apres chargement : typer les colonnes (Date -> Date, SentimentScore/ListPrice/SalesAmount -> Nombre decimal,
// cles -> Nombre entier, ReviewText -> Texte). Masquer les colonnes techniques (cles) dans le modele.
