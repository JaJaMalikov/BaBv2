# Revue de code: ui/scene_io.py

## Analyse
Gère la sauvegarde et le chargement des scènes au format JSON ainsi que la création d'une scène vierge. Interagit étroitement avec `MainWindow` et `ObjectManager`.

## Recommandations
- Factoriser les chemins de fichiers par défaut (ex. pantin « manu ») dans une constante configurables.
- Éviter la logique UI dans les fonctions d'I/O pour permettre une utilisation en ligne de commande.
- Ajouter des validations supplémentaires sur la structure de `puppets_data` lors de l'import.
- Couvrir par des tests les cas d'erreur de lecture/écriture et de compatibilité de version.
