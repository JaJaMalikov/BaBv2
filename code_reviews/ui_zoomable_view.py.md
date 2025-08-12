# Revue de code : ui/zoomable_view.py

## Aperçu
Vue graphique personnalisée offrant des outils de zoom, de gestion des poignées et de dépôt d'objets depuis la bibliothèque.

## Points forts
- Utilisation d'overlays pour regrouper les outils sans encombrer la scène.
- Gestion intuitive du zoom (molette + Ctrl) et du pan (bouton du milieu).
- Support du glisser-déposer avec sérialisation JSON.

## Points à améliorer
- Les méthodes `_build_overlay` et `_build_main_tools_overlay` sont longues et contiennent du code répétitif pour créer des boutons.
- Certaines méthodes manipulent des attributs non définis si des erreurs surviennent (ex. `_main_tools_overlay`).

## Recommandations
1. Factoriser la création de boutons dans une fonction utilitaire partagée.
2. Ajouter des vérifications/exceptions pour s'assurer que les attributs optionnels existent avant leur utilisation.
3. Documenter la logique de positionnement des overlays pour faciliter les ajustements futurs.
