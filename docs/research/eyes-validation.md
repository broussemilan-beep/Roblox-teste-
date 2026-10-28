# Les « yeux » : ce qu'ils lisent bien, ce qu'ils lisent mal (validation du 2026-10-28)

Question de l'utilisateur : construire des yeux qui voient, lisent et comprennent, parce que je confondais par exemple un coup
transformé en VFX pour faire un effet de multi-coups ultra rapide avec de vrais coups. « Dis-moi quand c'est bon. »

**Verdict : pas « bon » pour la lecture des poses. Bon pour une partie des faits mesurables, avec un protocole qui m'empêche de
conclure sans avoir regardé.**

## Outils

| Outil | Rôle |
|---|---|
| `tsb_engine/perception.py` | lit un clip : ponctuation noire/blanche, scène vide, mur de VFX, mouvement de caméra (ajustement affine sur le fond), coupes, flashs, réaction de la victime ; étiquettes `MULTIHIT_VFX`, `REAL_COMBO`, `SINGLE_HIT_SMEAR`, `HELD_WITH_VFX`, `VICTIM_CYCLING` |
| `tsb_engine/reading.py` | registre de lecture : je note par plan ce que j'ai regardé et vu ; le validateur signale les contradictions avec les mesures et les images jamais regardées |
| `examples/eyes_bench.py` + `tools/eyes_bench.py` | banc d'essai : clips du moteur dont le contenu est connu (10 classes × 3 variantes aléatoires, 1 320 images) ; `--reference DIR` note aussi l'outil contre ma propre lecture de la vidéo de référence |
| `tools/eyes.py read / check / hot` | timeline des événements, toutes les images autour des pics de mouvement, modèle `reading.json`, contrôle des contradictions |

## Résultats

### Banc d'essai (28/30)

| Classe (vérité connue) | Résultat |
|---|---|
| ponctuation noir/blanc, scène vide, mur de traits, coupe franche, caméra seule (pan/orbite/travelling), cycle de victime avec héros tenu | 3/3 chacune |
| faux multi-coups (un bras strobe + flash sur chaque image), coup unique avec smear, vrai enchaînement de 4 coups | 3/3 chacune |
| effets sans réaction (flashs, traînées, encre, victime immobile) | **1/3** : de l'encre sombre qui recouvre la victime la fait paraître « en réaction » → lu `REAL_COMBO` ou `MULTIHIT_VFX` |

Le banc a été durci en cours de route (sa première version était trop facile : flashs trop espacés, victime qui ne réagissait pas). Les
seuils de décision ont été calibrés **sur ce banc** : 28/30 est donc un score d'entraînement, pas de généralisation.

### Vidéo de référence (ma lecture image par image = vérité)

* **Fiable** (7/7 attendus, aucune fausse détection) : image vide 14-18, impact frame blanc 166-168, mur de traits 195-238, images noires 257-258
  et 282, impact frame blanc 284-286, mouvement de caméra 268-275.
* **Pas fiable** : `CUT` (55 détectés, trop ; la caméra bouge avec parallaxe et les relances de mise en page ressemblent à des coupes) ;
  `REAL_COMBO` détecté 2 fois dans une période où le héros s'accroupit (faux) ; `SINGLE_HIT_SMEAR` une fois (plausible, non vérifié).
* **Raté** : le jonglage 97-132 (héros tenu, victime qui change de pose toutes les 1-2 images) n'est pas reconnu : la caméra bouge fort et
  l'encre sombre recouvre le héros.

## Pourquoi (limites de fond)

1. **Noir sur noir.** Le bras noir se confond avec le manteau noir : la silhouette du héros ne dit presque rien d'un strobe de bras. Ce qui se
   voit, ce sont les flashs, traînées blanches et la réaction de la victime blanche. Un strobe sans VFX ni victime visible n'est pas lisible.
2. **L'encre est sombre aussi.** Les traînées noires du style de référence ressemblent aux membres noirs : le lecteur ne les sépare pas.
3. **Fort mouvement de caméra + parallaxe** : le modèle de caméra (similitude 2D) ne les explique pas, donc fausses « coupes ».
4. Les réglages ont été trouvés sur du synthétique (rendu du viewer) : une vidéo réelle compressée, avec d'autres couleurs, sera plus dure.

## Protocole qui en découle (ce que je dois faire à chaque vidéo)

1. `eyes.py ref VIDEO DIR` (30 fps ; `--fps 60` si le clip est animé en 60).
2. `eyes.py read DIR OUT --mask-right 0.17` : timeline, `hot_windows.png` (toutes les images autour des pics), `reading.json`.
3. **Regarder** les fenêtres `hot_windows.png` et les planches de chaque plan (12 images par planche, numérotées), puis remplir `reading.json` :
   `viewed` (plages d'images réellement regardées), `camera`, `punct`, `hits`, `vfx_multihit`, `victim`.
4. `eyes.py check DIR reading.json` : chaque contradiction ou plage non regardée est une raison de rouvrir les images, **pas** une preuve que j'ai tort.
5. Seulement alors, écrire l'analyse. Les classes marquées « pas fiable » ne sont jamais citées comme faits sans lecture visuelle.

## Pour aller plus loin (non fait)

* Mode « vérité moteur » pour **mes propres films** : rendre la même scène sans effets donne les poses exactes (cinématique), ce qui supprime le
  problème noir sur noir ; non implémenté pour l'instant.
* Un lecteur appris (suivi de points type CoTracker, segmentation SAM 2) pour séparer encre et membres : lourd, non essayé ici.
* Plus de vidéos de référence annotées à la main : le seuil actuel repose sur une seule vidéo.


---

## Addendum (2026-10-28, v3): un modèle de vision appris, SAM 2.1, branché en « je désigne, il suit »

Après le verdict ci-dessus (les seuils classiques ne lisent pas les poses noir sur noir), recherche d'un vrai modèle de vision :
Hugging Face et PyPI sont accessibles depuis ce conteneur (pas le miroir PyTorch ni GitHub), 4 CPU / 15 Go. Retenu : **SAM 2.1 tiny** de Meta
(`facebook/sam2.1-hiera-tiny`, segmentation promptable + suivi vidéo, via `transformers`), ~1-2 s par image sur CPU. Écartés : CoTracker
(code sur GitHub, inaccessible), flux optique profond (inutile ici), VLM de description (non essayé : trop peu fiable pour des poses de blocs).

### Principe
`tools/eyes.py propose DIR FRAME OUT.png` numérote des objets candidats sur une image ; **je regarde l'image, je dis « le 5, c'est le mannequin, le 19, la
jambe »**, puis `eyes.py track DIR OUT --obj nom=image:x,y ...` suit chaque objet sur toute la vidéo (masques exacts), mesure sa portée vers
l'adversaire, juge la **fiabilité du suivi** (score d'existence de l'objet fourni par le modèle) et classe le mouvement :
`strobe` (bascule entre deux extensions à chaque image : un seul geste + VFX), `cycling` (change sans cesse de pose), `moving` (balayage lisse),
`steady` (tenu).

### Mesures sur le banc (18 bras suivis, masque vrai fourni par le moteur)
* IoU moyen **0,25** : le masque exact est souvent faux (petits membres noirs collés au corps, cuffs/manteau ajoutés par le modèle). À ne **pas** utiliser
  pour des surfaces.
* **Fiabilité** (médiane du score d'existence hors image du prompt) : bon suivi ≥ 7, perdu < 5. Le score s'effondre exactement quand l'IoU s'effondre
  (bras gauche du combo : ~10 → ~2 à l'image 4).
* **Type de mouvement** : sur les suivis jugés *fiables* (8 cas), le type mesuré = le type réel **8/8** (strobe retrouvé : 22 inversions sur 22 ;
  coups en balayage ; bras tenus). Sur les suivis *douteux/perdus* (10 cas), 7/10 : à ne pas croire sans regarder la superposition.

### Sur la vidéo de référence (jonglage 97-132, lu à l'œil avant)
Le mannequin est suivi à travers toutes ses poses (debout, penché, horizontal, replié) : `cycling`. Cheveux/chapeau et jambe du héros : `steady`. C'est
la lecture « héros tenu, victime en cycle » que les seuils classiques ratent. *Première version* du test de strobe (comptage d'inversions) a faussement
annoncé un strobe sur la jambe tenue ; remplacée par un test de période 2 (|x[t]−x[t−2]| ≪ |x[t]−x[t−1]|), validé sur le banc et sur ce cas.

### Limites restantes
* Il faut **un point d'appui par objet, choisi par moi** ; l'extraction automatique (`propose`) donne des candidats bruités.
* Un objet petit, noir, caché derrière le corps, ou foreshortené (bras qui pointe vers la caméra) n'est pas suivi : la mesure « portée » est alors vraie *et* nulle
  (cas du banc : le strobe existe mais n'a aucune extension à l'écran).
* Calibré sur 4 + 18 suivis du banc et un jonglage ; pas de statistique sur beaucoup de vidéos. Coût : ~3 min pour 30 images et 2-3 objets.

---

## Addendum v4 (2026-10-28): lecture de la 2ᵉ vidéo, négatifs et victime

Relue image par image (`reference-analysis-2.md`), la 2ᵉ référence a mis trois trous à nu :
1. **Images négatives** (luminance inversée, cyan/violet) non vues : ajout de `PUNCT_NEGATIVE` (anti-corrélation avec l'image précédente + corrélation avec son inverse,
   durée ≤ 6). 5 des 6 négatifs lus à l'œil sont retrouvés (257-259 manquant). Garde-fou : sans le plafond de durée, les coupes franches du banc étaient lues « négatif ».
2. **Pas de victime, mais des étiquettes de coup** : `_compact_blob` exige un corps clair compact (ni ligne, ni anneau) avant tout verdict de coup.
   Les étiquettes entre 102 et 268 disparaissent ; 3 fausses étiquettes subsistent (voir la section 5 de l'analyse).
3. Banc : toujours **28/30** (les 2 échecs : encre sombre sur la victime). Le banc ne contient pas de négatifs ni de clip sans victime : ces deux ajouts sont validés
   sur **une seule** vidéo (la 2ᵉ référence) et sur un test unitaire synthétique, rien de plus.

