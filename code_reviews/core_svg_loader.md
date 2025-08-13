# Revue de code: core/svg_loader.py

## Analyse
Charge et manipule des fichiers SVG pour extraire des groupes, obtenir des bounding boxes et calculer des pivots. Utilise `QSvgRenderer` et `xml.etree` pour l'analyse.

## Recommandations
- Valider l'existence du fichier avant le parsing pour fournir des messages d'erreur explicites.
- Documenter les méthodes publiques, notamment `get_pivot` et `extract_group`.
- Mutualiser les conversions de types pour réduire la duplication dans `translate_path`.
- Ajouter des tests couvrant les cas d'échec (groupe absent, viewBox manquante).
