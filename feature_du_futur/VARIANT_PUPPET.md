**Objectif**
- Pouvoir changer, par frame, l’apparence de certains membres (mains, bouche, yeux) via des “variantes” discrètes (step), tout en gardant l’interpolation continue pour rotations/positions.

**Approche**
- Ajouter une “channel” discrète par membre ciblé: `variant` (valeur string).
- Optionnel plus tard: des channels continues (ex. `eye_open: 0..1`, `mouth_open: 0..1`) pour interpolation fluide.

**Modèle de données**
- `Keyframe.puppets[puppet_name][member_name]` étendu:
  - Existant: `rotation: float` (+ `pos` pour les racines).
  - Nouveau: `variant: str | None` (ex: `"poing"`, `"main_ouverte"`, `"A"`, `"E"`, `"blink"`, `"open"`).
  - Futur (optionnel): `attrs: {eye_open: 0..1, mouth_open: 0..1, ...}` pour des interpolations numériques.
- `core/puppet_model.py`: ajouter un `VARIANT_MAP` décrivant les variantes autorisées par membre:
  - Exemple:
    - `main_gauche: {"poing": "main_gauche_poing", "ouverte": "main_gauche_ouverte"}`
    - `bouche: {"A": "bouche_A", "E": "bouche_E", "O": "bouche_O", "fermée": "bouche_close"}`
    - `yeux: {"ouverts": "yeux_open", "mi-clos": "yeux_half", "fermés": "yeux_closed"}`
  - Les valeurs pointent vers des `elementId` dans le SVG du pantin.

**Application (runtime)**
- `PuppetPiece`: ajouter `set_variant_key(key: str)` qui:
  - résout la clé via `VARIANT_MAP[member][key]` → `elementId`,
  - appelle `self.setElementId(elementId)` (le pivot ne bouge pas),
  - puis `update_handle_positions()` pour rester cohérent.
- `StateApplier.apply_puppet_states`:
  - Si `variant` présent dans le kf précédent: l’appliquer.
  - En interpolation entre 2 kf:
    - si `variant` identique → rien de spécial,
    - si différent → comportement step: garder la variante du kf précédent jusqu’au passage au kf suivant (pas d’interpolation).
  - Si plus tard on a `attrs` numériques, on lerp simplement ces valeurs.

**Règles d’interpolation**
- Rotations/positions: inchangées (déjà interpolées).
- Variantes: step (discrètes).
- Attributs continus (futur): lerp.

**Organisation des assets (SVG)**
- Dans le SVG du pantin, créer des groupes distincts par variante avec des `id` stables, alignés au même pivot:
  - `main_gauche_poing`, `main_gauche_ouverte`
  - `bouche_A`, `bouche_E`, `bouche_O`, `bouche_close`
  - `yeux_open`, `yeux_half`, `yeux_closed`
- Dans `PIVOT_MAP`, conserver une référence cohérente (le pivot reste celui de la pièce principale).
- Dans `PARENT_MAP`, s’assurer que `bouche`/`yeux` existent comme membres (enfants de `tete`) pour qu’ils aient leurs propres `PuppetPiece` (sinon on les ajoute).

**Sérialisation**
- JSON: `variant` et (plus tard) `attrs` sont sérialisés tels quels dans `keyframes[*].puppets`.
- Backward compatible: s’ils manquent, on garde le rendu actuel.

**Étapes d’implémentation (itératif)**
1) Ajouter `VARIANT_MAP` et les membres `bouche`/`yeux` si absents dans `PARENT_MAP`.
2) `PuppetPiece.set_variant_key()` + stockage de la variante courante.
3) `StateApplier`: appliquer `variant` (step) en plus de rotation/pos.
4) Sérialisation: inclure `variant` dans export/import.
5) (Plus tard) UI Inspecteur: combobox variantes pour `main_*`, `bouche`, `yeux`, avec thumbnails; insertion de keyframes “channel-only”.

Option d’évolution
- Lip-sync: canal `bouche.variant` piloté par une piste audio (visèmes “A,E,I,O,U,FV,MBP,…”).
- Yeux: auto-blink en générant des kf sur `yeux.variant`.

