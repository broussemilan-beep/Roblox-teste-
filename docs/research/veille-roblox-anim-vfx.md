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
