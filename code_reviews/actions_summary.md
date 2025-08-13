# Synthèse des actions à mener

## Priorité 1
- **Refactoriser les modules volumineux** (`ui/main_window.py`, `ui/object_manager.py`, `ui/timeline_widget.py`) pour isoler les responsabilités et faciliter la maintenance.
- **Introduire des types explicites** et éliminer l'usage répété de `Any` en définissant des protocoles ou classes dédiées.
- **Sécuriser l'I/O JSON** dans `core/scene_model.py` et `ui/scene_io.py` par une validation plus stricte et une gestion d'erreurs détaillée.

## Priorité 2
- **Adopter des `dataclasses`** pour les structures de données (`SceneObject`, `Keyframe`, `PuppetMember`) afin de clarifier les attributs.
- **Centraliser les constantes de thème et de chemins** (`ui/icons.py`, `ui/styles.py`, chemins d'assets) pour simplifier la configuration.
- **Améliorer la couverture de tests** pour les interactions majeures (lecture de keyframes, onion skin, drag & drop, sauvegarde/chargement).

## Priorité 3
- **Documenter systématiquement** les fonctions et classes manquantes de docstrings.
- **Prévoir l'internationalisation** des libellés et messages UI.
- **Optimiser le nettoyage et la gestion des ressources Qt** (suppression d'overlays, teardown des tests).
