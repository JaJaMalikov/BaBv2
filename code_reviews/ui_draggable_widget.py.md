# Revue de code : ui/draggable_widget.py

## Aperçu
Fournit des overlays et entêtes déplaçables/redimensionnables pour les panneaux flottants.

## Points forts
- Gestion intuitive du déplacement par clic droit et du redimensionnement par glisser sur les bords.
- Effet d'ombre conditionnel pour améliorer l'interface.

## Points à améliorer
- Pas de docstrings pour expliquer le comportement attendu.
- La classe `DraggableOverlay` expose `_drag_start_position` sans protection ; risque de manipulation externe.
- Le code de détection des bords pourrait être factorisé pour lisibilité.

## Recommandations
1. Ajouter des docstrings et commentaires pour clarifier les interactions utilisateur.
2. Préfixer les attributs internes par `_` et fournir des propriétés si nécessaire.
3. Extraire la logique de calcul de `_get_edge` dans une fonction utilitaire commune.
