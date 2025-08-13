# Revue de code: macronotron.py

## Analyse
Point d'entrée de l'application, crée une `QApplication`, applique la feuille de style puis instancie et affiche `MainWindow`.

## Recommandations
- Ajouter une fonction `main()` pour faciliter les tests unitaires et l'import du module.
- Prévoir une gestion d'exceptions autour de l'initialisation de l'application.
- Externaliser la sélection du thème pour permettre une configuration plus flexible.
