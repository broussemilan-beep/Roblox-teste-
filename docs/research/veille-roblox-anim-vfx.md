# Veille : animateurs et artistes VFX Roblox (TSB, Jujutsu Shenanigans, Blox Fruits, jeux « One Piece »)

Faite le 2026-10-29 par recherche web publique. Étiquettes : **[lu]** page ouverte et lue, **[extrait]** extrait de résultat de recherche seulement (page non ouverte), **[non vérifié]** source faible ou unique.

## 0. Ce que je n'ai pas pu atteindre (limites honnêtes)

- Reddit : bloqué pour mes outils (aucun fil Reddit lu). Les fils DevForum, plus techniques, ont servi de substitut.
- YouTube (pages de lecture, transcriptions) : CAPTCHA. Je n'ai que des titres et des chaînes, aucun contenu de vidéo.
- TikTok, X (Twitter), Fandom, ArtStation : fermés aux robots. Les publications X citées viennent d'extraits de recherche.
- Il n'existe **aucune liste officielle de crédits** pour TSB, Jujutsu Shenanigans ou Blox Fruits. Les crédits ci-dessous sont des auto-déclarations d'artistes (posts, portfolios) ou une ligne de description de jeu.
- « Real Sea » : aucun jeu de combat de ce nom trouvé (« Real Seas » est un jeu maritime). À préciser par toi : Real Piece, Rogue Piece, Haze Piece, King Legacy, GPO ?

## 1. Les personnes (par jeu)

### The Strongest Battlegrounds (studio : Yielding Arts [lu], propriétaire 22freshfrenchfries [extrait])

| Qui | Rôle | Travaux crédités | Méthode connue | Source |
|---|---|---|---|---|
| **Ultik** (@KirvKirv1) | animateur 3D | séries d'animations TSB postées par lui (Serious Punch, atomic samurai, 2023-2024) ; également crédité animateur de Jujutsu Shenanigans | bio : Maya et Blender [extrait, attribution ambiguë avec Snaliel] | x.com/KirvKirv1 [extrait] |
| **Veil** (@VeilUnbound) | animateur | animations d'une mise à jour TSB (oct. 2023, VFX ILoveMrCool), juin 2024 (#moonanimator #blender), déc. 2024 (VFX qid1k) ; crédité animateur de Jujutsu Shenanigans | Moon Animator + Blender (hashtags) [extrait] | x.com/VeilUnbound [extrait] |
| **Snaliel** | VFX + 3D | « more work I did for tsb, VFX by me » (déc. 2024) | non indiqué | x.com/Snaliel [extrait] |
| **ILoveMrCool** (Mr.Cool) | VFX + code | « Lapse Blue » pour TSB (VFX seulement) | explosion Megumin : « over 600 lines », tous les mesh flipbooks et la plupart des beams faits par lui ; pour l'impact frame animé : « drawing those frames took forever » | x.com/ILoveMrCool [extrait] |
| **qid / qid1k** | VFX | mise à jour TSB déc. 2024 (selon Veil) | aucune | [extrait] |
| **Pew** (pewpewagent) | VFX | « RUNUP VFX breakdown » (inspiré du dropkick 20-20-20 de KJ/TSB), pack mesh flipbooks open source | voir §2 : c'est la source la plus précise | devforum.roblox.com/t/runup-vfx-breakdown-part-4/3669430 [lu] |
| **DaSassyOwl** | animateur de la série KJ | personnage KJ à l'origine du dropkick | aucune | fandom TSB [extrait] |

### Jujutsu Shenanigans (développeur Tze, studio Tze's Shenanigans)

- Ligne de crédit de la description du jeu [lu, via Medal.tv] : « script / vfx guy - Tze ; animate guy - Tze, Ultik, Veil, ALTROILL, Frostholl ; sound guy - oiledmyster, EscDevv ; map guy - Skyrimmyz ». Donc **Ultik et Veil animent aussi Jujutsu Shenanigans**.
- **Bean / 3k3x** (@beanie_not) : « GPO & JJS VFX developer », VFX d'« Ultimate Being » pour JJS [extrait]. Méthode [lu, DevForum] : flipbooks, mesh flipbooks et slashes faits **de façon procédurale dans After Effects (bruit fractal)**, Blender pour l'animation, Photoshop ; un de ses posts compte 57 beams, 750 lignes de code et 15 textures/flipbooks pour un seul effet [extrait].
- Le jeu a un « Skill Builder » en jeu (assembler VFX + animations + hitbox + vitesse) [lu].

### Blox Fruits (Gamer Robot Inc, fondateur mygame43)

- **TBGlitch** : « Head Animator @BloxFruits » [extrait].
- **Felku** : VFX du fruit Gravité (avr. 2025) [extrait].
- **ItsJustFir3** : VFX, liste Blox Fruits, GPO, Haze Piece, etc. ; 60k+ Robux par effet ; outils non indiqués [lu].
- **Yippy** (YIPPYFX) : liste Blox Fruits parmi ses jeux ; Roblox Studio ; à partir de 200 $ l'effet [lu].
- **Plebarae** : VFX (Combat Warriors, Anime Champions X, etc.), outils : particules Roblox, After Effects, Photoshop ; propose un tutoriel « BloxFruits-Style Beam Slash » [lu]. Sa structure d'un effet : **anticipation → apogée → dissipation rapide** ; il fixe timing et silhouette dès le blocage et respecte un budget de particules.
- **Neo Jittungtrong** (freelance, Blox Fruits et King Legacy) : Roblox Studio + Lua, After Effects pour les textures, Blender pour les meshes [lu].

### Grands créateurs d'animation (YouTube/TikTok)

Cités dans des résultats de recherche : Zillgo, Xoaterz, Drowsy, TopAtAnimations, PMDamiann, OoferGuide, CodysTooBig, Shadowmid [extrait, liste utilisateur TikTok et interview YouTube]. **Je n'ai trouvé aucune page vérifiable sur eux**, ni sur leurs méthodes : ne pas les prendre pour acquis.

## 2. Méthodes vérifiées (les plus utiles pour le style TSB)

D'après la décomposition de Pew [lu] et ses réponses DevForum :

1. **Anneaux animés** : on clone un mesh en version « Start » et version « End » et on interpole (tween) de l'un à l'autre. C'est ce que Pew décrit pour TSB (sa croyance, pas une confirmation du studio).
2. **Deux rigs dans Moon Animator** (attaquant + victime) animés dans un seul fichier, exportés via « Export Rigs » et joués ensemble.
3. **Caméra de cinématique** : Moon exporte CFrame + FOV de la caméra ; un script les rejoue en caméra Scriptable à pas fixe de 1/60 s sur RenderStepped. Les effets, projectiles et sous-titres ne s'exportent pas : à coder à la main.
4. **Faux mesh en 3D avec des beams empilés** et une texture qui défile (plus simple que les mesh flipbooks).
5. **Sphère de distorsion** : objet verre avec transparence > 1 et un Highlight désactivé pour qu'il s'affiche encore.
6. **Mesh flipbooks** : pas natifs dans Roblox ; un module boucle sur des textures séparées appliquées à un mesh ; VortexFX peut émettre ces meshes comme particules. Pack open source de Pew avec shockwaves et dissolves.
7. **Impact frames** : redessinées image par image (Mr.Cool). Méthode intégrée : ColorCorrection avec saturation −1 et contraste ±25000 pendant environ 0,1 s [module ParadoxSoftwork, lu]. Autres voies : retouche Photopea (capture, désaturer, filtre Sketch/Torn Edges, inverser), ou deux ColorCorrection.
8. **Arrêt sur image (hit-stop)** : `AdjustSpeed(0)` sur toutes les pistes en cours puis retour à 1 ; ne pas placer le marqueur sur la dernière clé [lu, DevForum]. Aucun nombre d'images n'est donné nulle part.
9. **Secousse de caméra** : EZ Camera Shake (port de Sleitnick) ou version maison : intensité environ 3, durée 0,1 s, décroissance linéaire [lu].
10. **Poussière et débris** : lancer un rayon vers le bas depuis la racine, apparaître un petit bloc avec rotation aléatoire et la couleur du sol touché [lu]. Aucun fil sur les anneaux de fissure ni l'aura.
11. **Particules** : taux 0 et `:Emit(30)` au bon moment, durée de vie ajustée [lu].
12. **Flipbooks** : plafond de lecture Roblox de 30 images/s [extrait, outil VFX Lab].

Côté animation pure (fils DevForum de critique) :
- la frappe doit être **bien plus rapide que la charge** ; clés régulièrement espacées = plat ;
- **Back Out** sur le coup ; l'épaule mène, le bras suit ; arrêt net avec un petit tremblement ; les jambes poussent dans le coup ;
- une pause de quelques images entre deux coups d'un combo ; enchaîner sans trou entre les animations.

## 3. Ce que je retiens pour ton combo (et ce qui manque encore à ma version)

Déjà appliqué dans `practice` : facilités par segment, décalage tête/bras, tremblement après lancer et impact.
Pas encore appliqué (à faire selon ton feu vert) :
- **arrêt sur image réel** à l'impact (geler 2-3 images du corps pendant que les effets continuent) ;
- **images d'impact** (flash noir/blanc, négatif) à l'impact et au lancer, comme dans TSB ;
- **anneaux en Start/End interpolés** au lieu de mes anneaux actuels ;
- **secousse de caméra** à l'impact (ma caméra est fixe comme la référence : ce serait un ajout de style, pas une copie).

## 4. Pistes à suivre avec un vrai navigateur (ou ton Gemini)

- Comptes X : @KirvKirv1, @VeilUnbound, @Snaliel, @ILoveMrCool, @qid1k, @beanie_not, @TBGlitch, @Felku_.
- Chaînes YouTube : Alrech (« ROBLOX VFX Tutorial »), Kyuzu (« The Strongest Battlegrounds Trailer Animation | Raw ver. »), nateyox (« SCRAPPED MOVES, VFX & MORE! »), LanceStuffs (« The Best ANIMATIONs in The Strongest Battlegrounds »), tutoriels Moon Animator : « Learning IMPACT FRAMES In Roblox Moon Animator! » (A_1uFlVrumM), « (Moon Animator) Impact Frames: Advanced Tutorial Part 1 » (tTCPbe9jQn8), « How to make Smear Frames (Moon Animator tutorial) » (Gxt-JFnB1ic), « Moon Animator Tutorial! General Keyframes, and Easing! » (gG3HFjnExqw).
- À corriger : l'identifiant YouTube 1VWTLn_7hPA correspond à « Inside The World of Roblox Animation » (PurpleFloplop), pas à « The Truth About Roblox Animation YouTubers ».
- Fils DevForum riches : devforum.roblox.com/t/runup-vfx-breakdown-part-4/3669430, …/serious-punch-recreation-creation-overview-part-3/3630207, …/mesh-flipbooks-particle-flipbooks-animations-and-movesets/2204359, …/advanced-impact-frames/2468478, …/open-source-impactframe-module/2963136.

## 5. Réponses de Gemini (reçues le 2026-10-29) et leur vérification

**Tableau « 0,1 s » de la vidéo de référence : non utilisé.** Vérifié contre ma mesure de la trajectoire réelle (`tools/measure_track.py`, `docs/research/reference-poses/practice_track.json`) :
- Gemini décrit des courses en arc, un « dash vers la gauche » à 1,9 s et plusieurs retours au centre. Mesuré : le personnage avance vers la droite presque tout le temps (+609 px au total, 14 images seulement vers la gauche).
- Gemini place le grand saut à 3,3–4,1 s, haut de « 2,5 corps ». Mesuré : le grand saut est à 2,7 s et monte à 2,5 studs (moins d'un demi-corps).
- Les anneaux magenta sont à 2,0 s mesurés contre 2,4–2,5 s annoncés ; l'impact au sol est à 3,0 s mesuré contre 4,1 s annoncé.
Conclusion : le tableau est une description plausible mais inexacte ; seule la mesure fait foi.

**Les 7 tutoriels et les 15 règles : utilisés** (cohérents avec les fils DevForum et les tutoriels lus par ailleurs). Je n'ai pas pu regarder les vidéos moi-même ; les chiffres sont ceux de Gemini :
- timeline en paliers de 5 images (60 fps) : départ, anticipation, drag, milieu de frappe, exagération, amorti (« wiggle ») ;
- ratio anticipation:frappe:récupération de 3:1:2, soit 10-15 / 2-4 / 8-12 images à 60 fps ;
- drag des bras et de la tête de 2 à 5 images ; dépassement de 10 à 15° après l'impact (ou Back Out) ;
- arrêt sur image de 2 à 4 images (copier la pose d'impact quelques images plus loin, ou clé en Constant) avec une micro-torsion d'environ 2° ;
- In sur les élans et chutes, Out sur les atterrissages et freinages ;
- anneau de choc : deux beams, CurveSize = rayon × 4/3 (une approximation de Bézier d'un demi-cercle, ce qui est mathématiquement juste) ;
- flash d'impact : durée de vie 0,1-0,2 s, éclats Speed 50 / Drag 3.
Appliqué dans `examples/practice_keys.py` : décalage tête/bras de 2 images, Back Out sur le lancer, l'impact et l'atterrissage de la vrille, arrêt sur image de 3 images au lancer (108) et à l'impact (137) avec rattrapage de l'horloge de pose sur 8 images pour rester sur le minutage de la référence.
Non appliqué : abaisser le torse en garde (les jambes R6 sont rigides, il faudrait enfoncer les pieds dans le sol), tremblement de caméra et FOV (la caméra de la référence est fixe), impact frames noir/blanc (absentes de la référence).

## 6. Deuxième passe, mots-clés pointus (2026-10-29)

Accès : je ne contourne pas les blocages anti-robot (CAPTCHA YouTube, 403 Reddit, protections TikTok). Voies légitimes : clé de l'API YouTube Data de l'utilisateur (titres, descriptions, chapitres, commentaires ; pas les sous-titres), application Reddit de l'utilisateur (OAuth), vidéos téléchargées par l'utilisateur sur son ordinateur, ou Gemini. X fonctionne avec `yt-dlp` (clips téléchargés en dossier temporaire, non versionnés).

**Série « Creation Overview » de Pew (DevForum, avril-mai 2025)** [lu] : Part 1 (Stoic Bomb de KJ), Part 2 (VFX physiques, orbite de débris), Part 3 (Serious Punch, cinématique + mesh flipbooks), Part 4 (RUNUP). Points précis :
- Tous les émetteurs de particules dans une seule pièce soudée à la racine par un Motor6D et animée comme un membre ; les effets sont déclenchés par des événements d'animation (`KeyframeReached`), pas par des délais.
- Boucle de flipbook : `Duration = 1`, `Framerate = 60`, une attente de `Duration / Framerate` par image ; les images doivent rester chargées (decals sous une pièce) pour éviter le clignotement.
- Orbite de débris : `dist = 10`, `speed = 10`, phase aléatoire entre −180° et 180°, position `sin(t·speed+phase)·dist`, `cos(...)·dist`, hauteur 2.
- Caméra de cinématique : une pièce soudée animée comme caméra, ou l'export de rigs de Moon avec FOV ; remettre FOV à 70 à la fin.
- Retours de la communauté sur son « Serious Punch » : « le coup pourrait avoir plus d'accélération en y entrant » (cela confirme l'usage d'un In sur l'élan) ; secousse de caméra suggérée à l'impact.
- Il dit lui-même ne pas être bon en animation : sa série est surtout un modèle pour les VFX.

**Autres pages lues** : fil sur les impact frames (plein écran ImageLabel, vidéo dans un ScreenGui, Krita ; « aucun jeu ne fait de vraies impact frames en temps réel » : elles sont déclenchées par script), fil « Drawn Impact Frames » (ImageLabel animé dans un BillboardGui car certains ColorCorrection cachent les particules), guide Moon Animator 2 non officiel de 2020 (touche + pour insérer une clé, regrouper des clés « pour faire une pause », Mirror, Looper, Time Stretch, Wiggler ; conseil R6 : ne pas lever trop haut un bras, descendre la pièce plutôt que « plier » le R6), rig Blender R6 IK/FK, pipeline Blender vers Roblox à 60 images/s (1 s = 60 images), réglages d'export FBX (Bake Animation, Add Leaf Bones désactivé, Apply Scalings = FBX Unit Scale).

**Données de jeu TSB (site tiers seamou.studio, non vérifiable : le wiki Fandom répond 402)** : chaîne de 4 coups M1, les 3 premiers avec stun léger de 0,2 s, le 4e avec recul ou projection au sol ; recul d'un M1 raté de 0,2 s ; Side-Dash rechargé en 2 s, dash avant/arrière 5 s. Aucune page ne donne de nombre d'images de départ/actif/récupération pour un coup, ni d'angles R6 pour garde, élan, saut, atterrissage.

**Conclusion honnête** : cette deuxième passe confirme les règles déjà appliquées (accélération vers le coup, arrêt net, suivi décalé, arrêt sur image, événements d'animation pour synchroniser les VFX) mais n'apporte pas de nouveaux chiffres de poses. Les chiffres de poses n'existent pas en public ; il faut les mesurer sur des clips.

## 7. Troisième passe : interfaces publiques sans clé, recherche en masse, dépôts GitHub publics (2026-10-29)

**Politique d'accès** : je n'utilise aucune clé, aucun jeton ni aucun identifiant trouvé dans des dépôts, des fuites ou des pages publiques (ce sont ceux d'autres personnes). Seules les interfaces publiques sans clé sont utilisées, à cadence polie : l'API JSON publique du DevForum (`search.json`, `t/<id>.json`), le clonage anonyme en lecture seule de dépôts GitHub publics, `yt-dlp` sur des posts X publics. Bluesky (403), Wayback Machine (429), YouTube, Reddit et TikTok restent fermés.

**Recherche en masse DevForum** (30 requêtes, 705 sujets) : tri par recoupement. Les plus pertinents lus :
- « Best way to replicate VFX/Animations for a Battlegrounds game (TSB/JJS style architecture) » : architecture standard = le joueur envoie son intention au serveur, le serveur valide (état, recharge) puis la diffuse à tous les clients, chaque client rejoue l'animation sur l'attaquant et **déclenche les visuels et les sons sur les événements d'animation** ; hitboxes côté client avec contrôles serveur [lu].
- « How to Create a KJ 20 Dropkick Move » : réponses de la communauté : Moon Animator pour l'animation, **caméra cinématique de Moon + marqueurs pour les effets** ; un répondant estime que Blender est nécessaire (Moon « ne va pas assez loin ») [lu, réponses non vérifiées].
- « How would I make my combat feel more impactful » : secousse de caméra, recul (knockback), particules qui partent vers l'extérieur, **saturation qui monte puis redescend**, zoom de FOV, sons variés (vitesse de lecture légèrement différente à chaque coup), particules plus grosses et plus lumineuses, **les particules ne doivent jamais apparaître avant l'animation** [lu].
- « Camera following Torso movements » : dans TSB, la caméra suit le **Torse** pendant les animations (le sujet de la caméra est le torse) [lu].
- « How can I recreate this VFX effect » : un slash de grande épée = **un mesh en disque avec une texture en feuille de sprites animée par script**, avec l'éclat obtenu en poussant la couleur de la texture au-delà de 1 (Color3 de 400) ; alternative plus simple mais plus plate : un émetteur de particules avec flipbook orienté VelocityPerpendicular [lu].
- Offres d'emploi (Jujutsu Annals, Bonkland) : un animateur de combat est jugé sur « le poids, l'impact, l'anticipation et la douceur des facilités » (le critère est cité tel quel) ; un artiste VFX sur ParticleEmitters, Beams, Trails [lu].
- « Tips on smooth animation » : tourner une vidéo de soi-même comme référence ; la vitesse (nombre d'images) change tout en combat (comparaison 30 vs 45 images) [lu].

**Dépôts GitHub publics lus (clonés en lecture seule, hors du projet, code non exécuté)** :
- `Sleitnick/RbxCameraShaker` : vrais préréglages. `Bump` (un seul coup, secousse courte et douce) = magnitude 2,5, rugosité 4, montée 0,1 s, descente 0,75 s, influence de position 0,15, de rotation 1 ; `Explosion` = magnitude 5, rugosité 10, montée 0, descente 1,5 s, influence de rotation (4, 1, 1) ; `Vibration` (soutenue) = magnitude 0,4, rugosité 20. Utile si on ajoute un tremblement de caméra à l'impact.
- `NevelStudios/roblox-vfx-lab` (licence présente) : fabrique des flipbooks par shaders WGSL et les cuit en feuille PNG (grilles 2×2, 4×4, 8×8 ; Roblox lit un flipbook à 30 images/s au maximum) ; son guide contient un exemple d'anneau de choc blanc teintable (4×4, OneShot) et des règles de qualité : garder la forme à l'intérieur de l'image (sinon coupure dure), l'image 0 doit se lire seule, un cœur lumineux avec un corps plus faible lit mieux qu'un blanc plat, toutes les images doivent changer.
- Autres dépôts repérés, non lus : `VirtualButFake/vfx-editor`, `Mqxsyy/Lumina` (particules), `Srcrix/TweenPlus`, `g1mmethemoney/WCS` (cadre de combat), `Cautioned/Blender-Animations-Plugin`, `dextermorganfan/Blender-OAE`, `stardustdtm/combo`.

**Ce qui n'existe pas en public, malgré tout** : des angles de poses R6 ou des durées en images par coup. Seule la mesure sur de vrais clips peut les donner.

## 8. Analyse mesurée des 11 clips X téléchargés (2026-10-29)

Clips publics de Veil, Ultik, Snaliel, Mr.Cool et Felku, gardés hors du dépôt. Mesures faites par script (cv2) sur chaque image native ; lecture visuelle de trois fenêtres.

- **Cadence réelle** : 9 clips sur 11 mettent le contenu à jour à chaque image native (96 à 99 % d'images nouvelles) : 30 images/s (Mr.Cool, Ultik atomic samurai, Ultik « autres animations ») ou 60 images/s (Veil, Snaliel, Felku). Aucun n'est animé « sur 2 » ou « sur 3 » : l'animation de combat de TSB postée par ces artistes est lisse à la cadence native. Exception : « Omni-Directional Serious Punch » d'Ultik (60 images/s, 63 % d'images répétées, intervalles de 1 à 4 images). Sur la fenêtre regardée (24,3 s), c'est un survol caméra avec débris : je l'attribue à la capture ou à l'encodage, pas à un style, donc je n'en tire aucune règle.
- **Structure d'un impact lu image par image** (Veil, mise à jour TSB, 60 images/s, 15,2 à 16,0 s) : aura violet-noir pendant au moins 0,3 s (anticipation) → éclair blanc avec rayons sur quelques images (≈ 3 images) → cylindre blanc translucide qui s'étend puis s'efface en ≈ 0,1 à 0,2 s → gros blocs de débris et caméra qui s'enfonce parmi les blocs pendant ≈ 0,4 s. Cela correspond à la règle « anticipation, apogée, dissipation rapide » de Plebarae.
- **Présentation d'Ultik** : chaque animation est montrée sur un rig en plein cadre sous Studio, avec filigrane, et les animations sont enchaînées par des coupes sèches (environ 26 coupes en 55 s).
- **Ce que la mesure ne peut pas donner** : mes durées « anticipation / frappe / récupération » par clip sont inutilisables : l'énergie de mouvement de l'image entière mélange caméra, VFX et temps morts. Pour de vraies durées il faut suivre le personnage lui-même (SAM 2, `tools/eyes.py track`) et mesurer ses membres, clip par clip.

### 8 bis. Durées du mouvement du corps seul (Ultik, atomic samurai, 30 images/s)

Méthode : le rig blanc est isolé par couleur (faible saturation, forte luminosité) sur le sol bleu, dans la zone centrale ; l'énergie de mouvement est le nombre de pixels de masque qui changent d'une image à l'autre, divisé par la surface du rig ; 24 rafales de mouvement (fenêtres 15,2-33,5 s et 39,6-47,0 s, où le plan est fixe).
- Partie rapide d'un mouvement (au-dessus de 50 % du pic de la rafale) : **médiane 7 images (0,23 s), de 2 à 15 images (0,07 à 0,5 s)** ; la moitié des mouvements tient entre 4 et 11 images.
- Rafales entières : de 5 à 56 images (0,17 à 1,87 s) ; les plus longues contiennent des temps morts ou plusieurs gestes.
- La montée lente (anticipation) passe sous le seuil de détection : sa durée n'est pas mesurable avec cette méthode (médiane mesurée 0,5 image, ce qui est un artefact, pas une mesure).
- Limites : ce sont des animations d'épée d'un seul animateur, sans coup de poing ni saut ; échantillon de 24 gestes ; pas de séparation anticipation / frappe / récupération. À ne pas généraliser.
- Comparaison avec la séquence de ta référence : mes phases explosives sont de 2 à 3 images (lancer 106→108, vrille 65→68, saut 121→124), donc au bas de cette fourchette ; la durée des gestes de TA référence se lit sur ta vidéo, pas sur ces épées.
