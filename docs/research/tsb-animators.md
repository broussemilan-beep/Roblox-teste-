# Who animated The Strongest Battlegrounds? (research notes)

Question: learn from the animators who worked on TSB, to build a skill and a tool that
animates "like them".

## What I found (web searches, this session)

- TSB is developed by the studio **Yielding Arts**; the game launched in August 2022 and won
  two Roblox Innovation Awards in 2024 (Best Strategy, Best Fighting Experience).
  <https://rowatcher.com/news/the-strongest-battlegrounds-how-one-punch-man-sparked-roblox-s-anime-fighter-revolution>
- **Santino** (Roblox user `22freshfrenchfries`) is the owner/lead developer. An in-game
  title lists "Owner" and a generic "Animators" role without naming anyone.
  <https://techwiser.com/titles-the-strongest-battlegrounds/>
- A fan playlist recreates TSB moves ("The moves in TSB, recreated by me!") — not official.
  <https://www.youtube.com/playlist?list=PLk9iqqBYvZheh185KZodZGs_dOEmmOB14>

## What I did NOT find

- No public credit list naming TSB's animators or VFX artists.
- No interview, devlog or DevForum post where the team explains its animation pipeline,
  frame counts or tools.
- Therefore the Gemini conversation's claims about "the Santino / Yielding Arts methodology"
  (event-driven timeline, Skill Builder internals, "Pocket Room" at Y = 5000, exact
  frame data) are **unverified**. They may come from videos the user watched (Skill Builder
  UI screenshots), but they are not documented anywhere I could reach.
- The tutorial authors cited in that conversation (Devgrams, Niski, distovi, Twist VFX, etc.)
  are YouTube educators, not TSB staff.

## Consequence for the project

We cannot copy a documented studio method, because none is public. What we can do:

1. Encode **observable craft rules** (anticipation, snap, overlap, contact hold, reaction,
   silhouette) from general animation practice and the user's references.
2. Turn them into **checks** (done: `tsb_engine` linter) and **explicit builders**.
3. Calibrate thresholds against **animations the user considers good** (their TSB/JJS
   captures, their own best takes). This needs data, not more prose.
4. Keep the user's eye as the final judge.

## How to get real signal about TSB animators

- In-game credits / the TSB Roblox group and Discord: the user can check who holds the
  "Animator" roles, then look for those people's public portfolios or tutorials.
- Share short clips (frame-accurate if possible: screen recordings at 60 fps) of the TSB
  moves to imitate; I can then extract measurable timings with a script (frame differences)
  instead of guessing.
- Ask the user which animators/channels they already follow; I can research those specifically.
