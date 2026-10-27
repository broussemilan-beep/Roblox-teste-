# Conversation Gemini vs notre méthode : où on était à côté, ce qu'on fait maintenant

Relecture ciblée du texte Gemini (`docs/gemini/gemini-roblox-vfx-conversation.txt`, numéros de lignes entre parenthèses),
comparée à la façon dont `examples/short.py` (première version) était construit, puis à la version refaite.
Rappel : les chiffres de Gemini sont des heuristiques (il ne voit pas les vidéos : l. 1867-1878, 6282-6285, 7732-7750),
seuls tes propres retours (l. 6294-6298 « trop rigide, robotique », 6857 « il manque déplacement et déboîtement des
membres », 7325 « le coup chargé est mal fait », 8612 « VFX pauvres, pas la matière ») sont des signaux fiables.

## 1. Ce que la méthode prescrit, et ce que faisait ma première version

| Méthode (Gemini + tes corrections) | Première version du court métrage | Verdict |
|---|---|---|
| Pose-à-pose, **la silhouette doit lire en Constant** avant tout easing (1446-1488) | Poses devinées à la main, non vérifiées une par une ; membres cachés derrière le torse sur presque tous les contacts | Raté |
| **Breakdown d'arc** juste avant l'impact (1472-1480) | Pas de breakdown : interpolation directe entre l'armé et le contact | Raté |
| **Chaîne cinétique / décalage des membres** : tête +2 à +3 frames, bras opposé en retard (1491-1497, 1640-1644) | Tout clé sur les mêmes frames (le linter TSB012 existe, mais le film l'enfreignait en esprit) | Raté |
| **Déboîtement** du bloc membre 1-2 frames, remboîté avec overshoot (tes remarques 6857, 7149-7227) | Absent du film | Raté |
| **Moving hold** pendant l'armé et les maintiens (1757-1765) | Seulement dans l'armé initial ; 70 frames figées dans la tempête, 80 sur le mannequin (TSB007) | Partiel |
| **Victime** : la partie touchée bouge d'abord, le reste traîne 2-3 frames, pliage en C (3380-3383) | Mannequin raide d'un bloc dès la frame 0 | Raté |
| Caméra : punch de FOV, shake, roll 3-5° à l'impact (1672-1680) | Présents, mais caméra de profil fixe trop loin : personnages à 20-40 % de la hauteur d'écran | Partiel |
| Pas de hitstop global, pas de shader (8620-8623) | Respecté (aucun hitstop ; les impact frames viennent de la **vidéo de référence**, signalés optionnels) | OK |
| Squash & stretch par Scale (3427-3437) | Impossible en `KeyframeSequence` (Gemini l'admet l. 6957) ; le déboîtement le remplace | N/A |

Ce que tu voyais (« mauvaises, mal modélisées ») était vrai : un personnage noir de 25 % de la hauteur d'écran, de profil,
avec un membre sur deux masqué, est une tache. Aucun effet ne rattrape ça.

## 2. Ce qui a changé (la boucle)

1. **Contacts calculés, plus devinés** : `tsb_engine/solver.py` (`aim_limb`, `reach_root`) place l'extrémité du membre sur un
   point du mannequin avec la même cinématique que le viewer (résidu ≤ 0,055 stud sur les contacts principaux du film). L'animateur
   façonne ensuite autour : armé, chaîne, overshoot.
2. **Chaîne et déboîtement** : `chain()` (tête +2, bras +1…), `dislocate()` (bloc membre décalé 2 frames puis remboîté avec
   un overshoot opposé), `moving_hold()`.
3. **Victime** : `react()` plie la zone touchée, la tête arrive 2 frames après, puis le corps se raidit (planche de la référence).
4. **Cadrage** : `autoframe()` garde les corps à un taux de remplissage fixé, angle 3/4 (la ligne de combat est l'axe Z ; une
   caméra proche de cet axe superpose les deux corps, d'où azimut 40-90°), suivi lissé.
5. **Mesure** : `tsb_engine/readability.py` (z-buffer numpy, caméra du viewer) donne hauteur à l'écran, visibilité de chaque
   membre, cadrage ; `tools/check_poses.py scène frames`. Résultat sur les contacts principaux : hauteur d'écran 0,23-0,47 → 0,27-0,80 (la plupart > 0,4).
6. **Boucle de travail** : poser (solveur) → rendre **deux vues** (3/4 et profil) → lire la métrique → bande d'images prises de 2 en 2
   pour juger le *mouvement* → corriger → linter. Le jugement final reste le tien.
7. **Fin refaite** (ton « bonne initiative, mal réalisée ») : le héros cueille le mannequin d'un coup de pied montant, s'envole
   avec lui, une seule taillade cyan, le mannequin éclate en **ses six blocs** (comme un `BreakJoints` Roblox, 100 %
   faisable avec des offsets de membres), les blocs tombent, le héros atterrit, plan final bas et serré avec le chapeau
   relevé, braises cyan, blocs au premier plan.

## 3. Ce qui reste hors de portée / non vérifié

* Je ne vois pas ton jeu : tout est jugé sur le viewer (imitation des primitives Roblox). Import Studio du `.rbxmx`
  jamais vérifié.
* Le mouvement secondaire (manteau, cheveux, chapeau) et les traînées d'encre ne s'exportent pas : accessoires, `Trail` et
  `Beam` à faire côté Roblox.
* Contradictions de Gemini à ne pas suivre : snap 1-2 frames illisible en 3D (11675-11679, M1 validé à ~4 frames, 12964) ;
  « Linear sur le coup » vs « Linear fait robot » (1698-1708 / 1949-1952) ; clones écartés par toi (11688).
* Dans le film, les poses de contact gardent encore un membre éloigné partiellement caché (limites d'un profil) : c'est
  mesuré par la colonne `limb` de `check_poses`, pas corrigé partout.

## 4. Deuxième relecture : la vidéo de référence (ajout)

Tu as signalé un problème de lecture de la vidéo. Relecture complète image par image (336 images à 30 fps, voir
`docs/research/reference-analysis.md` v2). Ce que ma première lecture avait faux ou laissé de côté :

| Ce que j'avais retenu | Ce que la vidéo montre vraiment |
|---|---|
| « Modélisation basique » = blocs R6 simples, donc un héros fin | Rig R6 simple **mais** silhouette riche : grand chapeau rond à ruban, grosse masse de cheveux blancs, manteau évasé, ceinture rayée, autocollant « … » sur le chapeau. La présence vient du volume |
| Contacts filmés en 3/4 pour mieux séparer les corps | Combat **de profil**, caméra serrée (héros 35-50 % de la hauteur), puis **au ras du sol** pour le jonglage (60-75 %) ; les poses sont dessinées pour cette caméra |
| Jonglage = le héros alterne deux coups | **Le héros est tenu dans une seule pose** ~30 images, seul le **mannequin change de pose toutes les 1-2 images**, avec de grands tourbillons d'encre sombre persistants |
| Traînées d'encre fines et translucides | Croissants noirs **opaques et affûtés, aussi longs que le héros**, tourbillons de la moitié de sa taille, étoile **noire à contour blanc** |
| Tempête de 33 images : traits 3D que j'amincissais pour garder la pose lisible | Les traits sont **énormes (15-25 % de la hauteur d'écran), blancs à bord cyan**, ils **ensevelissent** les corps entrevus entre les traits, relancés à chaque image (~5 mises en page) |
| Fin : un plan large du héros debout | **Macro statique de 48 images** sur le héros voûté : dôme du chapeau, manchette blanche, bras du mannequin gris en haut à droite |

Changements faits en conséquence : `reference_outfit()` (cylindres/ellipsoïdes dans le viewer), héros et mannequin en profil, héros
tenu + mannequin en cycle de 5 poses pendant le jonglage, encre 2× plus large et opaque, `screen_fx("strokes")` pour la tempête,
`burst(outline=...)` pour l'étoile noire, final en macro sur un héros accroupi, tête baissée.
