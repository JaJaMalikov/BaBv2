# Revue de code : ui/draggable_widget.py

## Aperçu
Fournit des widgets superposés (`DraggableOverlay`, `PanelOverlay`, `DraggableHeader`) permettant le drag & resize des panneaux.

## Points positifs
- Gestion du redimensionnement avec détection des bords via `_get_edge`.
- Effet d'ombre ajoutant de la profondeur aux overlays.
- Réutilisable pour différents panneaux (bibliothèque, inspecteur, etc.).

## Points à améliorer
- Le module n'importe pas `QWidget` bien qu'il soit utilisé (provoquera une erreur d'exécution).
- Duplication de logique de drag dans `DraggableOverlay` et `DraggableHeader`.
- Peu de commentaires expliquant les valeurs magiques (ex: largeur minimale 200).

## Suggestions
- Ajouter `from PySide6.QtWidgets import QWidget` au début du fichier.
- Factoriser la logique de déplacement commun entre `DraggableOverlay` et `DraggableHeader`.
- Documenter les constantes liées au redimensionnement et permettre leur configuration.
