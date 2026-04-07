# Survival Horror Research Reading Map for a TTRPG Designer

## Executive take

Your current shelf already has a real point of view. It is not “horror in general”; it is specifically interested in:

- puzzles as **tension pacing**, not just obstacle tax
- survival horror as a **knowledge game** and a **route-planning game**
- map structure, recursive unlocking, and controlled backtracking
- fear as something you **build, release, and re-arm**
- the idea that horror is often stronger when combat is constrained, awkward, or undesirable

That is a strong shelf. It is also a *partial* shelf.

The biggest things you are currently underweight on are:

1. **safe rooms / save systems / checkpoint design**
2. **stalker AI / pursuer logic / “the monster is hunting you” systems**
3. **inventory as a horror economy**
4. **audio and diegetic information design**
5. **the back-half problem** — i.e. how horror stops working once the player has learned the trick
6. **the tabletop translation layer** — how to steal survival-horror structure without just making a bad videogame imitation with paper bookkeeping

That is where I would push the next pass.

---

## What your current list is already teaching you well

Your current list already hits several foundational truths:

- **Puzzles are there to modulate emotional rhythm.** Frictional’s old puzzle series is still excellent on this point: puzzle segments can calm the player down, create vulnerability, and set up the next scare, but unclear action spaces and incoherent puzzle logic will absolutely kill immersion.  
  Sources: [Puzzles in horror games Part 1](https://frictionalgames.com/2009-08-puzzles-in-horror-games-part-1/), [Part 2](https://frictionalgames.com/2009-08-puzzles-in-horror-games-part-2/), [Part 3](https://frictionalgames.com/2009-08-puzzles-in-horror-games-part-3/), [Part 4](https://frictionalgames.com/2009-09-puzzles-in-horror-games-part-4/)

- **World-coherent puzzles matter more than “clever” puzzles.** The missing follow-up here is Frictional’s Part 5, which makes that point explicitly.  
  Source: [Puzzles in horror games Part 5](https://frictionalgames.com/2009-09-puzzles-in-horror-games-part-5/)

- **Resident Evil-style space is not fake nonlinear space; it is tightly controlled traversal wearing a nonlinear mask.** Chris Pruett’s “Recursive Unlocking” is one of the best articles on survival-horror spatial structure on the internet.  
  Source: [Recursive Unlocking: Analyzing Resident Evil’s Map Design with Data Visualization](https://horror.dreamdawn.com/?p=81213)

- **Survival horror often works as a knowledge game.** Daniel Primed’s *Code Veronica* puzzle-box series is useful precisely because it looks at chapter function, mental-model teaching, and when the game asks the player to revise what they think the game is.  
  Source: [Cracking the Resident Evil Puzzle Box](https://danielprimed.com/old_site/2017/01/cracking-the-resident-evil-puzzle-box-chapter-overview/index.html)

- **Fear is not one note.** “Fight or Flight” is useful because it reminds you that horror design is partly an exercise in manipulating anticipation, uncertainty, and stress physiology.  
  Source: [Fight or Flight: The Neuroscience of Survival Horror](https://www.gamedeveloper.com/design/fight-or-flight-the-neuroscience-of-survival-horror)

So the base is good. The next move is not “more general horror articles.” It is to fill the specific design holes that survival horror depends on.

---

## Other resources you will probably like

## 1) The Dreamdawn archive is your best immediate expansion pack

If I had to pick one place to push deeper based on your current shelf, it would be Chris Pruett’s old Dreamdawn / *Chris’s Survival Horror Quest* archive. It is probably the single best survival-horror-specific design archive still publicly accessible.

### Read these next

- **Tracing the Tendrils of Item Management**  
  This is the obvious follow-up to *Recursive Unlocking*. It gets into item combination, synchronization points, dependency chains, and why inventory systems are not just inconvenience but part of the puzzle grammar.  
  Source: [Tracing the Tendrils of Item Management](https://horror.dreamdawn.com/?p=14800056)

- **Data Mining Resident Evil**  
  A shorter companion piece, but useful because it states the core claim cleanly: Resident Evil funnels the player through space at a controlled pace rather than letting them thrash randomly around the map.  
  Source: [Data Mining Resident Evil](https://horror.dreamdawn.com/?p=8070)

- **Ingredients of Horror: Two-Factor and Horror Game Design**  
  Useful for thinking about horror as combinations of pressure systems instead of just “monster + darkness = scary.”  
  Source: [Ingredients of Horror: Two-Factor and Horror Game Design](https://horror.dreamdawn.com/?p=7979)

- **The Prehistory of Survival Horror**  
  Worth it because it connects survival horror to older adventure-game interaction models instead of pretending the genre emerged fully formed out of a spooky PlayStation coffin.  
  Source: [The Prehistory of Survival Horror](https://horror.dreamdawn.com/?p=74151)

- **GDC: Akira Yamaoka and the Atmosphere of Silent Hill**  
  A nice complement to the Resident Evil-heavy parts of the archive, especially if your game wants psychological or environmental dread instead of pure pursuit horror.  
  Source: [GDC: Akira Yamaoka and the Atmosphere of Silent Hill](https://horror.dreamdawn.com/?p=1715)

### Why I think this matters for you

Your current list is already halfway into the Dreamdawn worldview. The missing Dreamdawn pieces are exactly the missing joints in your shelf: **inventory**, **save-room logic**, **structure beyond puzzles**, and **survival horror as a whole system instead of isolated tricks**.

---

## 2) Frictional has more for you than just the puzzle posts

The old puzzle series is great, but if you stop there you miss the broader Frictional theory of horror.

### Read these next

- **9 Years, 9 Lessons on Horror**  
  One of the best broad craft essays on horror-game design. The key value here is that it is written by a studio that actually shipped influential horror games and had to debug their failures in public.  
  Source: [9 Years, 9 Lessons on Horror](https://frictionalgames.com/2019-10-9-years-9-lessons-on-horror/)

- **The Five Foundational Design Pillars of SOMA**  
  Extremely useful if your horror game needs to keep puzzles, movement, interaction, and story from feeling like separate layers glued together after the fact.  
  Source: [The Five Foundational Design Pillars of SOMA](https://frictionalgames.com/2013-12-the-five-foundational-design-pillars-of-soma/)

- **4-Layers, A Narrative Design Approach**  
  Not survival-horror-specific, but very useful if your game needs narrative and interaction to reinforce each other instead of alternating like awkward stage cues.  
  Source: [4-Layers, A Narrative Design Approach](https://frictionalgames.com/2014-04-4-layers-a-narrative-design-approach/)

- **Choices, Consequences and the Ability to Plan**  
  This matters because survival horror lives or dies on the player believing that choices have legible consequences and that planning matters.  
  Source: [Choices, Consequences and the Ability to Plan](https://frictionalgames.com/2017-06-choices-consequences-and-the-ability-to-plan/)

- **The SSM Framework of Game Design**  
  Broader framework piece, but useful for keeping “systems, story, mental model” aligned.  
  Source: [The SSM Framework of Game Design](https://frictionalgames.com/2017-05-the-ssm-framework-of-game-design/)

### Why I think this matters for you

Your current shelf is a little over-indexed on **local problems** (“how should puzzles work?”) and under-indexed on **global coherence** (“how do the game’s rules, interaction model, and emotional goals stop stepping on each other?”). Frictional is very good on the second question.

---

## 3) Alien: Isolation is mandatory if you care about pursuit horror

If your game has *any* stalker / hunter / apex-predator energy, then *Alien: Isolation* is not optional reading. It is the cleanest case study in how to make a monster feel unfair, intelligent, and alive without actually letting it become arbitrary mush.

### Read / watch these

- **Building Fear in Alien: Isolation**  
  The cleanest top-level statement of the game’s design goal: one alien, meaningful encounters, underpowered player, strong audiovisual atmosphere.  
  Sources: [GDC Vault session](https://gdcvault.com/play/1021852/Building-Fear-in-Alien), [Game Developer summary](https://www.gamedeveloper.com/audio/video-building-fear-in-i-alien-isolation-i-)

- **The Perfect Organism: The AI of Alien: Isolation**  
  This is the famous breakdown of the alien’s AI stack, including the split between “director” knowledge and creature-level behavior.  
  Source: [The Perfect Organism: The AI of Alien: Isolation](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)

- **Revisiting the AI of Alien: Isolation**  
  Useful because it revisits the first article and expands on the system rather than leaving it as myth.  
  Source: [Revisiting the AI of Alien: Isolation](https://www.gamedeveloper.com/design/revisiting-the-ai-of-alien-isolation)

### Why I think this matters for you

Your current shelf is very good on **puzzle pressure** but thin on **predator pressure**.

A lot of survival horror becomes interesting the moment the player is not solving a room, but solving a route under pursuit.

That is a different design problem. *Alien: Isolation* is one of the best resources on that problem.

---

## 4) You need more Capcom, not less

Same point you made about D&D, but for survival horror: do not let internet taste flatten the canon into “indie good / AAA bad.” Capcom is half the genre’s textbook.

### Read these

- **Postmortem: Capcom’s Resident Evil 4 (2005)**  
  Important because it shows that RE4 did not just “add action.” It rebuilt the fear model around smarter enemies, pressure, mobility, and a new relationship to combat.  
  Source: [Postmortem: Capcom’s Resident Evil 4 (2005)](https://www.gamedeveloper.com/design/postmortem-i-resident-evil-4-i-)

- **Reliving the Horror: Taking Resident Evil 7 Forward by Looking Back**  
  Useful because it is explicit about taking the series somewhere new while trying to remain true to original survival-horror concepts.  
  Source: [Reliving the Horror: Taking ‘Resident Evil 7’ Forward by Looking Back](https://www.gdcvault.com/play/1024559/Reliving-the-Horror-Taking-Resident)

- **The Sound of Horror: Resident Evil 7**  
  Very useful if you care about the idea that horror is not just visual design plus mechanics; sound is doing a huge amount of emotional labor.  
  Sources: [GDC session](https://www.gdcvault.com/play/1024696/The-Sound-of-Horror-Resident), [slides PDF](https://media.gdcvault.com/gdc2017/Presentations/Usami_Ken_The_Sound_of.pdf)

- **Resident Evil Village: Our Approach to Game Design, Art Direction, and Graphics**  
  The key reason to read this is the explicit talk about **player acclimation to fear** and a logic architecture of **tension and relief**. That is back-half-problem gold.  
  Source: [Resident Evil Village: Our Approach to Game Design, Art Direction, and Graphics](https://gdcvault.com/play/1027542/-Resident-Evil-Village-Our)

- **Revealing Resident Evil Revelations**  
  Useful because it explicitly frames the project as a return to survival-horror roots with improved controls and playability.  
  Source: [Revealing Resident Evil Revelations](https://gdcvault.com/play/1016370/Revealing-Resident-Evil-Revelations)

### Why I think this matters for you

Capcom is where you go if you want to study the genre **actually trying to survive contact with large audiences**. That matters. “Pure” survival-horror theory is nice. Shipping games that millions of people can still navigate is nicer.

---

## 5) Dead Space is your UI / information-design case study

If your game is tabletop, you obviously cannot copy a diegetic hologram UI. But you **can** learn from Dead Space’s information philosophy.

### Read these

- **Designing Dead Space’s immersive user interface**  
  The key idea is removing the “wall of safety” between player and game by integrating information into the world.  
  Source: [Designing Dead Space’s immersive user interface](https://www.gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface)

- **Crafting Destruction: The Evolution of the Dead Space User Interface**  
  The more complete GDC treatment of how and why the interface evolved.  
  Source: [Crafting Destruction: The Evolution of the Dead Space User Interface](https://gdcvault.com/play/1017723/Crafting-Destruction-The-Evolution-of)

### Why I think this matters for you

For a TTRPG, “diegetic UI” becomes:

- how the sheet exposes risk
- how maps, handouts, trackers, clocks, and inventory communicate pressure
- how much the player can safely know at a glance
- whether the play surface itself helps create tension or accidentally becomes a comfort blanket

This is exactly why your instinct about the Mothership character sheet is right. Survival-horror information design is not decoration. It is mechanics wearing typography.

---

## 6) Silent Hill / Akira Yamaoka is your “other grammar of horror”

Resident Evil is not the only design language in the genre. If your game wants dread, sadness, ambiguity, absence, or “the environment is wrong in a way I cannot quite name,” Silent Hill matters.

### Read these

- **Postcard From GDC 2005: Akira Yamaoka on Silent Hill, Fear, and Audio For Games**  
  Very useful on the distinction between different fear traditions and the importance of sound.  
  Source: [Postcard From GDC 2005: Akira Yamaoka on Silent Hill, Fear, and Audio For Games](https://www.gamedeveloper.com/audio/postcard-from-gdc-2005-akira-yamaoka-on-i-silent-hill-i-fear-and-audio-for-games)

- **GameSpot’s recap of “The Day and Night of Silent Hill”**  
  A second useful recap of the same general territory, especially around the difference between American and Japanese horror emphases.  
  Source: [GDC Session: The dark spirit of Silent Hill](https://www.gamespot.com/articles/gdc-session-the-dark-spirit-of-silent-hill/1100-6120347/)

- **Classic Postmortem: Silent Hill 4: The Room**  
  Worth reading because *The Room* is such a strong case study in claustrophobia, sanctuary, domestic space, and the danger of overusing a “safe place.”  
  Source: [Classic Postmortem: Silent Hill 4: The Room (2004)](https://www.gamedeveloper.com/audio/classic-postmortem-i-silent-hill-4-the-room-i-)

### Why I think this matters for you

If Resident Evil is the masterclass in **lock/key/resource route pressure**, Silent Hill is often the masterclass in **psychological atmosphere, sadness, estrangement, and the wrongness of place**. You probably want both languages available.

---

## 7) Signalis is your modern recombination study

Not because it invented everything, but because it recombines older survival-horror grammar with unusual confidence.

### Read these

- **SIGNALIS presskit**  
  This is useful because it states the game’s puzzle and resource philosophy very plainly: code-breaking, radio, object combination, scarce ammo, enemies not easily defeated.  
  Source: [SIGNALIS Presskit](https://rose-engine.org/press/Presskit_SIGNALIS.html)

- **Official site**  
  A shorter official overview, but still a clean statement of the design target.  
  Source: [SIGNALIS official site](https://rose-engine.org/signalis/)

### Why I think this matters for you

If you are making a new TTRPG, you probably do not want to make “RE1 but with dice.” *Signalis* is a good study in how to **inherit old forms without becoming museum glass**.

---

## 8) Tabletop horror / survival-horror translation resources

This is where your shelf most obviously needs reinforcement.

### The best next reads

- **Environmental Horror Design — Sean McCoy**  
  This is maybe the most directly useful single tabletop article for translating survival-horror videogame thinking into scenario design. The core point — unanswered environmental questions create tension — is dead-on.  
  Source: [Environmental Horror Design](https://seanmccoy.substack.com/p/environmental-horror-design)

- **Violent Encounters — Sean McCoy**  
  Useful because it explicitly warns against treating tabletop violence like videogame combat. Survival horror at the table needs violent situations, not just initiative minigames.  
  Source: [Violent Encounters](https://seanmccoy.substack.com/p/violent-encounters)

- **The Trajectory of Fear — Ash Law**  
  Extremely practical tabletop horror pacing tool: unease, dread, terror, horror. Maybe a little schematic, but in a good way.  
  Source: [The Trajectory of Fear (PDF)](https://nerdsonearth.com/wp-content/uploads/2020/03/Trajectory-of-Fear.pdf)

- **Give a Clue — Robin D. Laws / GUMSHOE**  
  If your survival horror has investigation, mystery, or “what happened here?” energy, then clue bottlenecks will kill your game. GUMSHOE remains one of the best cures for that.  
  Source: [See Page XX: Give a Clue – Giving Out Clues in GUMSHOE](https://pelgranepress.com/2020/09/16/see-page-xx-give-a-clue-giving-out-clues-in-gumshoe/)

- **Fear Itself 2nd Edition / Designer’s Notes**  
  Great because it is explicitly about ordinary people against unremitting horror, and the designer notes are honest about one-shot / mini-series / campaign structure, hiding, fleeing, clue use, and short-form horror support.  
  Sources: [Fear Itself 2nd Edition](https://pelgranepress.com/product/fear-itself-2nd-edition/), [Designer’s Notes](https://pelgranepress.com/2016/04/01/fear-itself-designers-notes/)

- **Mothership: Warden’s Operations Manual**  
  You already like Mothership, and you are right to like it. The WOM is one of the best practical books on running horror procedures at the table, including prep, tension, scenario generation, and campaign growth.  
  Sources: [Warden’s Operations Manual](https://www.tuesdayknightgames.com/products/mothership-wardens-operations-manual), [Mothership resources / Warden Educational System](https://www.tuesdayknightgames.com/pages/mothership-resources-downloads)

- **Delta Green: Handler’s Guide**  
  Strong for long-form investigative horror, scenario seeds, unnatural-threat construction, and the way institutions, secrecy, and personal collapse support dread.  
  Sources: [Handler’s Guide](https://shop.arcdream.com/products/delta-green-handlers-guide-hardback), [Retail details / overview](https://shop.arcdream.com/pages/retailer-information)

- **Ten Candles**  
  Not survival horror, exactly — more tragic horror — but enormously useful as an example of mechanics, mood, and physical play all pointing in one direction.  
  Sources: [Ten Candles info](https://cavalrygames.com/ten-candles-info), [product page](https://cavalrygames.com/ten-candles)

- **Trophy Dark**  
  Useful because it formalizes doomed descent and environmental hostility in a very table-forward way.  
  Sources: [Trophy RPG](https://trophyrpg.com/), [Trophy system reference](https://trophyrpg.com/system/)

- **Cthulhu Dark**  
  Still one of the cleanest examples of a horror game that understands “fighting the monster” is often the wrong fantasy.  
  Sources: [Cthulhu Dark PDF](https://catchyourhare.com/files/Cthulhu%20Dark.pdf), [DriveThru product page](https://www.drivethrurpg.com/en/product/341997/index.html)

- **Dread**  
  Useful because the physical resolution method actually creates bodily tension at the table instead of merely describing it.  
  Sources: [About Dread](https://dreadthegame.wordpress.com/about-dread-the-game/), [DriveThru page](https://www.drivethrurpg.com/en/product/83854/index.html)

### Why I think this matters for you

You are not just making a horror game. You are making a **tabletop** horror game inspired by **survival horror**.

That means you need techniques for:

- investigation without stalls
- violent situations without wargame bloat
- sanctuary / respite without boredom
- physical or procedural tension that players actually *feel*
- campaign structures that do not instantly dissolve the fear

That is a different shelf than “best horror videogame essays.”

---

## What gaps you are currently missing

## 1) Save rooms, save systems, and checkpoint logic

This is the biggest obvious gap.

Classic survival horror does not just have “places to save.” It has **sanctuaries**. Sanctuaries are pacing tools. They define the pulse of the whole game.

Relevant reads:

- *Alien: Isolation*’s save terminals make the player linger in vulnerability rather than quicksaving from safety.  
  Sources: [Building Fear in Alien: Isolation](https://gdcvault.com/play/1021852/Building-Fear-in-Alien), [Alien: Isolation AI article](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)

- Dreamdawn’s Silent Hill 4 and Resident Evil commentary is useful on what happens when sanctuary becomes too available, too convenient, or too detached from mounting pressure.  
  Sources: [Chris’s Survival Horror Quest archive](https://horror.dreamdawn.com/), [Ingredients of Horror: Two-Factor and Horror Game Design](https://horror.dreamdawn.com/?p=7979)

### Why this matters for your TTRPG

A tabletop “safe room” does not have to be literally a room. It can be:

- a guaranteed breather scene
- a refuge location with specific services
- a time-boxed camp phase
- a record / regroup / inventory / clue-sorting procedure
- a sanctuary that later becomes compromised

But if your game wants survival-horror cadence, it probably needs *something* like this.

---

## 2) Stalker logic and pursuit design

Your current shelf talks more about puzzles than hunters.

If your game has a monster, killer, bio-weapon, relentless enemy, or even just “something that keeps showing up where it should not,” you need a shelf on how pursuit works.

Best resources:

- [Building Fear in Alien: Isolation](https://gdcvault.com/play/1021852/Building-Fear-in-Alien)
- [The Perfect Organism: The AI of Alien: Isolation](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)
- [Revisiting the AI of Alien: Isolation](https://www.gamedeveloper.com/design/revisiting-the-ai-of-alien-isolation)

### Why this matters for your TTRPG

At the table, “stalker AI” usually means:

- the GM needs **procedures**
- the hunter should have **limited but dangerous knowledge**
- the game needs to distinguish between **searching**, **tracking**, **closing**, **ambushing**, and **cooldown / reset**
- the creature cannot just be omniscient GM spite or it stops being frightening and becomes arbitrary

That is a gap worth filling on purpose.

---

## 3) Inventory as a horror economy

You have some puzzle writing and some Resident Evil structure, but not enough on inventory itself.

The big insight here is that inventory is not a side system. It is one of the genre’s primary **decision engines**.

Best resources:

- [Tracing the Tendrils of Item Management](https://horror.dreamdawn.com/?p=14800056)
- [Pack-Ratting in Video Games: Do Players Have to Have It All?](https://www.gamedeveloper.com/design/pack-ratting-in-video-games-do-players-have-to-have-it-all-)
- [SIGNALIS Presskit](https://rose-engine.org/press/Presskit_SIGNALIS.html)

### Why this matters for your TTRPG

Inventory pressure becomes interesting when it creates:

- route choices
- sacrifice
- preparation
- return trips
- short-term vs long-term tradeoffs
- “I can carry the gun or the thing that lets me solve the next room, but not both”

If it just creates accounting, it sucks. If it creates planning, it sings.

---

## 4) Audio and information design

This is another major gap.

Survival horror is not just map + monster + puzzle. A shocking amount of the emotional work is done by **what the player knows**, **when they know it**, and **how the world sounds while they know too little**.

Best resources:

- [The Sound of Horror: Resident Evil 7](https://www.gdcvault.com/play/1024696/The-Sound-of-Horror-Resident)
- [Designing Dead Space’s immersive user interface](https://www.gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface)
- [Crafting Destruction: The Evolution of the Dead Space User Interface](https://gdcvault.com/play/1017723/Crafting-Destruction-The-Evolution-of)
- [Postcard From GDC 2005: Akira Yamaoka on Silent Hill, Fear, and Audio For Games](https://www.gamedeveloper.com/audio/postcard-from-gdc-2005-akira-yamaoka-on-i-silent-hill-i-fear-and-audio-for-games)

### Why this matters for your TTRPG

At the table, this translates into:

- what is on the sheet
- what is hidden behind the screen
- whether maps are player-facing or not
- how clues and handouts are staged
- whether trackers and tokens create pressure or just admin
- whether information arrives as prose, diagrams, audio, cards, clocks, or environmental fragments

Again: not decoration. Mechanics wearing layout.

---

## 5) The back-half problem

Most horror games get weaker as they go. Once players understand the threat grammar, the emotional shape flattens.

Best resources:

- [The Back Half Problems of Horror Design](https://www.gamedeveloper.com/design/the-back-half-problems-of-horror-design)
- [Resident Evil Village: Our Approach to Game Design, Art Direction, and Graphics](https://gdcvault.com/play/1027542/-Resident-Evil-Village-Our)

### Why this matters for your TTRPG

You need a plan for what happens when the players learn:

- what the monster wants
- what the environment does
- what their best routines are
- where the safe places are
- which risks are fake

A survival-horror game needs a way to **mutate**, **escalate**, or **contaminate** the player’s learned procedures.

---

## What I think is closest to a “best resources” canon here

There is no official survival-horror-design Bible descending from the ceiling on a chain. But if I had to guess at the most useful, most recurring, most broadly valuable shelf for someone designing a survival-horror-inspired TTRPG, it would look something like this.

## A) Video game survival-horror canon

1. [Designing and Integrating Puzzles in Action-Adventure Games](https://www.gamedeveloper.com/design/designing-and-integrating-puzzles-in-action-adventure-games)  
2. [Puzzles in Horror Games, Parts 1–5](https://frictionalgames.com/2009-08-puzzles-in-horror-games-part-1/)  
3. [Recursive Unlocking](https://horror.dreamdawn.com/?p=81213)  
4. [Tracing the Tendrils of Item Management](https://horror.dreamdawn.com/?p=14800056)  
5. [Postmortem: Resident Evil 4](https://www.gamedeveloper.com/design/postmortem-i-resident-evil-4-i-)  
6. [Building Fear in Alien: Isolation](https://gdcvault.com/play/1021852/Building-Fear-in-Alien)  
7. [The Perfect Organism](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)  
8. [Revisiting the AI of Alien: Isolation](https://www.gamedeveloper.com/design/revisiting-the-ai-of-alien-isolation)  
9. [Designing Dead Space’s immersive user interface](https://www.gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface)  
10. [The Sound of Horror: Resident Evil 7](https://www.gdcvault.com/play/1024696/The-Sound-of-Horror-Resident)  
11. [9 Years, 9 Lessons on Horror](https://frictionalgames.com/2019-10-9-years-9-lessons-on-horror/)  
12. [Resident Evil Village: Our Approach to Game Design, Art Direction, and Graphics](https://gdcvault.com/play/1027542/-Resident-Evil-Village-Our)

### My blunt opinion

If you skip **Dreamdawn**, **Frictional**, **Alien: Isolation**, and **Capcom’s own postmortem / GDC material**, you are leaving giant holes in your understanding of the genre.

---

## B) Tabletop adaptation canon

1. [Environmental Horror Design](https://seanmccoy.substack.com/p/environmental-horror-design)  
2. [Violent Encounters](https://seanmccoy.substack.com/p/violent-encounters)  
3. [The Trajectory of Fear](https://nerdsonearth.com/wp-content/uploads/2020/03/Trajectory-of-Fear.pdf)  
4. [Give a Clue – Giving Out Clues in GUMSHOE](https://pelgranepress.com/2020/09/16/see-page-xx-give-a-clue-giving-out-clues-in-gumshoe/)  
5. [Fear Itself 2nd Edition](https://pelgranepress.com/product/fear-itself-2nd-edition/) + [Designer’s Notes](https://pelgranepress.com/2016/04/01/fear-itself-designers-notes/)  
6. [Mothership: Warden’s Operations Manual](https://www.tuesdayknightgames.com/products/mothership-wardens-operations-manual)  
7. [Delta Green: Handler’s Guide](https://shop.arcdream.com/products/delta-green-handlers-guide-hardback)  
8. [Ten Candles](https://cavalrygames.com/ten-candles)  
9. [Trophy Dark / Trophy](https://trophyrpg.com/)  
10. [Cthulhu Dark](https://catchyourhare.com/files/Cthulhu%20Dark.pdf)  
11. [Dread](https://dreadthegame.wordpress.com/about-dread-the-game/)

### My blunt opinion

If you want to make a survival-horror TTRPG and you do *not* study **how tabletop handles clues, sanctuary, pursuit, violent situations, and doomed descent**, you will end up reinventing a lot of mediocre wheels.

---

## If I were tailoring a study order specifically for your project

## Phase 1: Finish the missing joints in your current shelf

1. [Puzzles in Horror Games Part 5](https://frictionalgames.com/2009-09-puzzles-in-horror-games-part-5/)  
2. [Tracing the Tendrils of Item Management](https://horror.dreamdawn.com/?p=14800056)  
3. [Data Mining Resident Evil](https://horror.dreamdawn.com/?p=8070)  
4. [9 Years, 9 Lessons on Horror](https://frictionalgames.com/2019-10-9-years-9-lessons-on-horror/)  

## Phase 2: Study pursuit and pressure

5. [Building Fear in Alien: Isolation](https://gdcvault.com/play/1021852/Building-Fear-in-Alien)  
6. [The Perfect Organism](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)  
7. [Revisiting the AI of Alien: Isolation](https://www.gamedeveloper.com/design/revisiting-the-ai-of-alien-isolation)  

## Phase 3: Study the genre’s information layer

8. [Designing Dead Space’s immersive user interface](https://www.gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface)  
9. [The Sound of Horror: Resident Evil 7](https://www.gdcvault.com/play/1024696/The-Sound-of-Horror-Resident)  
10. [Postcard From GDC 2005: Akira Yamaoka on Silent Hill, Fear, and Audio For Games](https://www.gamedeveloper.com/audio/postcard-from-gdc-2005-akira-yamaoka-on-i-silent-hill-i-fear-and-audio-for-games)

## Phase 4: Translate it into tabletop form

11. [Environmental Horror Design](https://seanmccoy.substack.com/p/environmental-horror-design)  
12. [Give a Clue](https://pelgranepress.com/2020/09/16/see-page-xx-give-a-clue-giving-out-clues-in-gumshoe/)  
13. [The Trajectory of Fear](https://nerdsonearth.com/wp-content/uploads/2020/03/Trajectory-of-Fear.pdf)  
14. [Fear Itself Designer’s Notes](https://pelgranepress.com/2016/04/01/fear-itself-designers-notes/)  
15. [Mothership: Warden’s Operations Manual](https://www.tuesdayknightgames.com/products/mothership-wardens-operations-manual)

---

## The biggest design lesson to steal from all of this

Survival horror is not “a horror game with scarce ammo.”

It is usually the combination of:

- **a constrained action set**
- **a hostile or partially legible space**
- **route-planning under pressure**
- **limited but meaningful resources**
- **sanctuary punctuating danger**
- **threats that cannot be cleanly solved by force**
- **information arriving slowly enough to create dread**
- **late-game mutation so the learned solution does not kill the mood**

That is the real pattern.

---

## How I would translate this into a survival-horror TTRPG

This is the most “design-useful” part, so I’m being direct.

## 1) Make sanctuaries explicit

Give the game a formal breather procedure.

Not necessarily a literal safe room. But something like:

- regroup
- inventory adjust
- patch injuries
- review clues
- lower panic / stress in a limited way
- mark progress
- maybe save a finite resource

If you do not formalize sanctuary, your game loses one of the genre’s core pulses.

## 2) Treat inventory as choice architecture, not realism tax

Do not count batteries because “survival horror counts batteries.” Count them if doing so changes routes, priorities, or risk appetite.

The moment the inventory system stops forcing hard choices, it becomes spreadsheet mold.

## 3) Use puzzles that reveal world logic

Moon-logic “combine goose with wrench” nonsense is not the move.

The better model is:

- diagnose a situation
- discover how the place works
- notice patterns
- connect spaces
- interpret symbols, radio traffic, journals, or environmental clues
- make a plan under pressure

That is much closer to what survival horror is actually good at.

## 4) Your stalker needs procedures

If there is a persistent hunter, write procedures for it.

For example:

- what tells it the PCs are nearby?
- what makes it search?
- what makes it commit?
- what makes it back off?
- how does it escalate across the scenario?
- what are the signals that it is learning?

Do not leave this as pure GM mood. Pure GM mood becomes vibesy nonsense fast.

## 5) Guarantee clue flow

If your game includes mystery — and survival horror usually does — do not let failed rolls hard-stop the game.

Use GUMSHOE logic, or steal it shamelessly:

- core clues should be found if the players do the sensible thing
- rolls can gate speed, cost, safety, precision, or bonus information
- not existence

Nothing kills dread faster than “well, you all failed the check, I guess the scary house remains unexplained.”

## 6) Keep the monster offscreen longer than feels comfortable

Ash Law and Sean McCoy are both useful here for different reasons.

The strongest horror often comes from:

- signs
- aftermath
- implications
- unanswered environmental questions
- dread that rises before the reveal

The second you overexplain or overshow the threat, the pressure vents.

## 7) Plan the back half now, not later

You need to know how the game changes once the players understand it.

Good mutations include:

- the sanctuary stops being safe
- the map folds or corrupts
- a new threat tier appears
- old routes become contaminated
- inventory assumptions flip
- the stalker learns new behaviors
- the “what is happening?” mystery becomes “what are we willing to do to survive?”

If you do not design the back half early, the game will probably devolve into “same thing, but louder.”

---

## Final recommendation in one sentence

If you want the shortest version: **push deeper into Dreamdawn, Frictional beyond the puzzle posts, Alien: Isolation’s AI/pursuit material, Capcom’s own survival-horror GDC talks, Dead Space’s information design, and then cross-train that with McCoy, GUMSHOE, Fear Itself, Mothership, Delta Green, Ten Candles, Trophy Dark, Cthulhu Dark, and Dread so you can turn videogame survival-horror grammar into procedures that actually work at a table.**

---

## Appendix: link dump

### From your original list
- [Classic Game Postmortem: Alone in the Dark](https://www.youtube.com/watch?v=c2lgEyNaop4)
- [Designing and Integrating Puzzles in Action-Adventure Games](https://www.gamedeveloper.com/design/designing-and-integrating-puzzles-in-action-adventure-games)
- [Puzzles in Horror Games Part 1](https://frictionalgames.com/2009-08-puzzles-in-horror-games-part-1/)
- [Puzzles in Horror Games Part 2](https://frictionalgames.com/2009-08-puzzles-in-horror-games-part-2/)
- [Puzzles in Horror Games Part 3](https://frictionalgames.com/2009-08-puzzles-in-horror-games-part-3/)
- [Puzzles in Horror Games Part 4](https://frictionalgames.com/2009-09-puzzles-in-horror-games-part-4/)
- [Cracking the Resident Evil Puzzle Box](https://danielprimed.com/old_site/2017/01/cracking-the-resident-evil-puzzle-box-chapter-overview/index.html)
- [Recursive Unlocking](https://horror.dreamdawn.com/?p=81213)
- [Fight or Flight: The Neuroscience of Survival Horror](https://www.gamedeveloper.com/design/fight-or-flight-the-neuroscience-of-survival-horror)

### Best additions for this pass
- [Puzzles in Horror Games Part 5](https://frictionalgames.com/2009-09-puzzles-in-horror-games-part-5/)
- [Tracing the Tendrils of Item Management](https://horror.dreamdawn.com/?p=14800056)
- [Data Mining Resident Evil](https://horror.dreamdawn.com/?p=8070)
- [The Prehistory of Survival Horror](https://horror.dreamdawn.com/?p=74151)
- [Ingredients of Horror: Two-Factor and Horror Game Design](https://horror.dreamdawn.com/?p=7979)
- [9 Years, 9 Lessons on Horror](https://frictionalgames.com/2019-10-9-years-9-lessons-on-horror/)
- [The Five Foundational Design Pillars of SOMA](https://frictionalgames.com/2013-12-the-five-foundational-design-pillars-of-soma/)
- [4-Layers, A Narrative Design Approach](https://frictionalgames.com/2014-04-4-layers-a-narrative-design-approach/)
- [Choices, Consequences and the Ability to Plan](https://frictionalgames.com/2017-06-choices-consequences-and-the-ability-to-plan/)
- [The SSM Framework of Game Design](https://frictionalgames.com/2017-05-the-ssm-framework-of-game-design/)
- [Building Fear in Alien: Isolation](https://gdcvault.com/play/1021852/Building-Fear-in-Alien)
- [The Perfect Organism: The AI of Alien: Isolation](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)
- [Revisiting the AI of Alien: Isolation](https://www.gamedeveloper.com/design/revisiting-the-ai-of-alien-isolation)
- [Postmortem: Capcom’s Resident Evil 4 (2005)](https://www.gamedeveloper.com/design/postmortem-i-resident-evil-4-i-)
- [Reliving the Horror: Taking Resident Evil 7 Forward by Looking Back](https://www.gdcvault.com/play/1024559/Reliving-the-Horror-Taking-Resident)
- [The Sound of Horror: Resident Evil 7](https://www.gdcvault.com/play/1024696/The-Sound-of-Horror-Resident)
- [Resident Evil Village: Our Approach to Game Design, Art Direction, and Graphics](https://gdcvault.com/play/1027542/-Resident-Evil-Village-Our)
- [Revealing Resident Evil Revelations](https://gdcvault.com/play/1016370/Revealing-Resident-Evil-Revelations)
- [Designing Dead Space’s immersive user interface](https://www.gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface)
- [Crafting Destruction: The Evolution of the Dead Space User Interface](https://gdcvault.com/play/1017723/Crafting-Destruction-The-Evolution-of)
- [Postcard From GDC 2005: Akira Yamaoka on Silent Hill, Fear, and Audio For Games](https://www.gamedeveloper.com/audio/postcard-from-gdc-2005-akira-yamaoka-on-i-silent-hill-i-fear-and-audio-for-games)
- [GDC Session: The dark spirit of Silent Hill](https://www.gamespot.com/articles/gdc-session-the-dark-spirit-of-silent-hill/1100-6120347/)
- [Classic Postmortem: Silent Hill 4: The Room](https://www.gamedeveloper.com/audio/classic-postmortem-i-silent-hill-4-the-room-i-)
- [SIGNALIS Presskit](https://rose-engine.org/press/Presskit_SIGNALIS.html)
- [SIGNALIS official site](https://rose-engine.org/signalis/)
- [The Back Half Problems of Horror Design](https://www.gamedeveloper.com/design/the-back-half-problems-of-horror-design)

### Best tabletop translation reads
- [Environmental Horror Design](https://seanmccoy.substack.com/p/environmental-horror-design)
- [Violent Encounters](https://seanmccoy.substack.com/p/violent-encounters)
- [The Trajectory of Fear](https://nerdsonearth.com/wp-content/uploads/2020/03/Trajectory-of-Fear.pdf)
- [Give a Clue – Giving Out Clues in GUMSHOE](https://pelgranepress.com/2020/09/16/see-page-xx-give-a-clue-giving-out-clues-in-gumshoe/)
- [Fear Itself 2nd Edition](https://pelgranepress.com/product/fear-itself-2nd-edition/)
- [Fear Itself Designer’s Notes](https://pelgranepress.com/2016/04/01/fear-itself-designers-notes/)
- [Mothership: Warden’s Operations Manual](https://www.tuesdayknightgames.com/products/mothership-wardens-operations-manual)
- [Mothership Resources & Downloads](https://www.tuesdayknightgames.com/pages/mothership-resources-downloads)
- [Delta Green: Handler’s Guide](https://shop.arcdream.com/products/delta-green-handlers-guide-hardback)
- [Delta Green: Impossible Landscapes](https://shop.arcdream.com/products/delta-green-impossible-landscapes)
- [Ten Candles](https://cavalrygames.com/ten-candles)
- [Trophy RPG](https://trophyrpg.com/)
- [Trophy system reference](https://trophyrpg.com/system/)
- [Cthulhu Dark PDF](https://catchyourhare.com/files/Cthulhu%20Dark.pdf)
- [Dread](https://dreadthegame.wordpress.com/about-dread-the-game/)
