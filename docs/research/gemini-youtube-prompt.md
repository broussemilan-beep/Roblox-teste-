# Commandes à coller dans Gemini (qui peut regarder YouTube / la vidéo)

Je (Claude) ne peux pas regarder une vidéo : seulement lire du texte et des images fixes. Gemini peut. Voici deux commandes. Colle les réponses dans le chat, je les transforme en clés d'animation.

## 1. Décrire la vidéo de référence, seconde par seconde (joindre ScreenRecording_10-28-2026_18-58-08_1.mp4)

```
Tu es animateur Roblox. Regarde cette vidéo (un rig R6 de test aux faces colorées : FRONT rouge, BACK bleu, RIGHT vert, LEFT orange, TOP bleu clair, BOTTOM jaune, tête ronde claire ; caméra fixe de Roblox Studio). Le personnage va de la gauche vers la droite de l'écran, la boucle dure environ 5 secondes.
Fais-moi un découpage de toutes les 0,1 s (10 lignes par seconde) avec, pour chaque ligne :
- la direction du regard du personnage (vers la caméra / de dos / vers la droite / vers la gauche) ;
- le tronc (penché avant/arrière/côté, de combien à peu près, en degrés) ;
- chaque bras (levé devant, sur le côté, derrière, replié) et chaque jambe (devant, derrière, écartée, pliée) ;
- la hauteur : au sol / accroupi / en l'air (combien de longueurs de corps au-dessus du sol) ;
- l'action et l'effet visuel en même temps (aura violette, anneau de poussière, anneaux magenta, faisceau, etc.).
Puis résume les 8 grandes phases avec leur durée en secondes et dis, pour chacune, quel est le mouvement d'anticipation, le moment de l'impact, et ce qui bouge en dernier (suivi).
Réponds en tableau Markdown, sans phrases inutiles.
```

## 2. Aller chercher des tutoriels d'animation Roblox et en tirer des règles chiffrées

```
Cherche sur YouTube des tutoriels d'animation de combat Roblox en R6 (mots clés : "Roblox R6 combat animation tutorial", "Moon Animator 2 tutorial punch impact", "Roblox animation impact frames", "Roblox battlegrounds animation tutorial", "Roblox animation easing styles tutorial", "Roblox VFX shockwave ring tutorial", "Roblox VFX practice").
Regarde au moins 5 vidéos et, pour chacune, donne : le titre exact, la chaîne, le lien, puis les règles concrètes que l'animateur montre, avec des chiffres : nombre d'images (frames) ou secondes pour l'anticipation, la frappe, la récupération ; styles d'interpolation (Linear / Cubic / Constant / Elastic / Bounce, direction In / Out / InOut) utilisés pour chaque phase ; comment il fait un arrêt sur image à l'impact, un tremblement de caméra, un saut, une vrille, une roulade, un atterrissage ; quelles erreurs de débutant il corrige.
Termine par une liste de 15 règles courtes, classées par importance, que je peux appliquer à un combo (garde, charge, vrille, course, lancer, saut, plongeon, glissade, roulade).
```
