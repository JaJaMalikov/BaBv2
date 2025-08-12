# Code Review : tests/test_object_keyframe_states.py

## Points positifs
- Vérifie que les états des objets sont correctement enregistrés dans les keyframes et restaurés.
- Utilise `pytest` et `QApplication` avec un fixture pour gérer le contexte Qt.

## Points d'amélioration
- L'environnement offscreen n'est pas forcé (contrairement à d'autres tests), ce qui peut poser problème en CI sans serveur X.
- Le test crée une `MainWindow` mais ne la ferme jamais explicitement; risque de fuites de ressources.
- `sys.path.append` utilisé pour gérer l'import; préférer une configuration de package ou `PYTHONPATH`.

## Recommandations
- Ajouter `os.environ["QT_QPA_PLATFORM"] = "offscreen"` en haut du fichier ou dans le fixture `app`.
- Fermer explicitement la fenêtre (`win.close()`) à la fin du test pour libérer les ressources.
- Configurer les imports via `pytest.ini` ou l'installation du package pour éviter la manipulation de `sys.path`.
