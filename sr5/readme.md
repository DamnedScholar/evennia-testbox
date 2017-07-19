# sr5/

This is a self-contained module that contains the functions and typeclasses necessary to run a game using the fifth edition Shadowrun rules, authored by Sammi.

To install this module, download it into your game folder and make the following additions to the pre-existing files:

1. In `commands/default_cmdsets.py`, `from sr5.command import CmdSheet` and add `self.add(CmdSheet())` to `PlayerCmdSet`.
2. In `typeclasses/characters.py`, `from sr5.character import DefaultShadowrunner` and change the `Character` parent to `DefaultShadowrunner`.

# Explanation

Here are my thoughts behind what I'm working on and why I feel that this is a good approach.

## Modular design

There are three major reasons why I believe every Evennia package should be built with full concern for modularity:

1. When a novice game runner is starting a new game, they might be ready and willing to dig into Python, but any packages that require more than three or four modifications to game files become daunting at worst and a source of accidental bugs at best. The ideal is to be able to install a package and *only* modify `settings.py` (which could even be done via a script).
2. When a piece of software has discrete components sorted into their own directories, it is much easier to debug. When you can pull out whole components without breaking the whole and then put them back in as they were, it makes problem-solving so much easier.
3. There's a nonzero chance that a user might want to include multiple game systems on a single installation, such as a MUSH used to run tabletop games. With Evennia's Account/Character separation, this is really easy to do. Packages that provide game systems for Evennia should accommodate that, and the best way to do so is by making each game system self-sufficient and separated from the code for the specific Evennia instance as much as possible. The ideal situation would be to have every `God Machine Chronicles` package be identical to every other one and store house rules and custom stats in a separate location.

## Character creation

Some people prefer the experience of going into a dedicated chargen room and walking through the process. It's very tangible that way, if a little slower. Some people prefer entering all the chargen commands from anywhere (this is especially relevant for plot-runners who want to create statted NPCs); I make characters by writing every single command into a text file and pasting them into the MUSH all at once. In the immediate future (should be right now, but we as a community have been slacking), people will demand fully web-accessible interfaces with mobile-first design.

To meet the needs of all three of these groups, chargen *cannot* be a series of commands attached to rooms. It has to be a command set with logic functions positioned in such a way that Django has access to them. The best solution I've found is to place a persistent [Script](https://github.com/evennia/evennia/wiki/Scripts) on the user. This has several objectives:

* The Script holds the logic for chargen functions, so chargen commands can always access it via `self.caller.cg`.
* The Script can easily give the user access to the `ChargenCmdSet` and revoke access when it is ended.
* Many RPGs have values that are important throughout chargen and unimportant afterwards. In D\&D, you have to know the difference between your base attribute and the bonus you get from your race, but that stops mattering once chargen is complete. Keeping stats on a Script and then writing them onto the Character when the Script is closed out is an efficient way to clean up these extra values, performing any modifications that are necessary and then deleting everything that is no longer needed.
* A Script can also be expanded to handle respeccing, for games that want to permit that. With the Script architecture, a player could go back through chargen while keeping all of their current stats, and cancelling the respec would be as simple as telling the Script to cancel itself.
* A player will always have access to their own chargen Script and a future Django integration would not have to do anything weird to locate the Script for the Character account that is currently logged in to the web site.

## Storing the rules

Every game system needs a datastore of all the values that the player can access. When these are hardcoded, it is prohibitively difficult for non-developers to access and modify them. Data stored in [a Google Sheet](https://docs.google.com/spreadsheets/d/1IgOcna1hLMRZwl0Zy6lC_XArWmQIMEvZNDmbOwGBaw4), however, is easy to pull out algorithmically and store in [`.py` files](https://github.com/DamnedScholar/evennia-testbox/blob/master/sr5/data/skills.py) where the game has access to them.

## Characters and stats

Since the Character and the chargen Script will have many similar stats, the functions used to validate and sanitize stat inputs can be stored on a mixin. This is not implemented in my code, because the stats and methods on `DefaultShadowrunner` were version `1.0` of my stat thinking and what's on `ChargenScript` is version `1.5`. As `ChargenScript` nears completion, its methods can be pulled out into a separate `class` and from there added into the default Character.

## Buying things

Whether you're buying a sword for 100 gold or a spell for 10 XP, there's not fundamentally much difference between these transactions. The results might be represented differently in code, but they're alike enough to both use a channel that's constructed to be wide and open-ended enough to support them.

## Non-stat things

For the sake of this argument, "stat" will refer to character sheet entities that are purely numerical. You can find out what Strength 4 does just by looking at the number. How you roll that, whether it's low or high, all that depends on the game system, but the number itself doesn't carry any additional information. However, many game systems have mechanical features that do carry additional meaning. Sometimes these mechanics change from character to character. The World of Darkness has many Merits (which are also stats) where the player chooses between multiple options, and several that are completely open-ended. In Shadowrun, cyberware augmentations sometimes come with their own stats and all have varying qualities. RPGs with magic are all over the place on this.

It is my belief that all (or at least most) non-stat character sheet entities can be represented through an additional typeclass parent (which I've called [Extra](https://github.com/DamnedScholar/evennia-testbox/blob/master/sr5/objects.py#L148)) with different children for each game system. Extras would allow for objects on the Character, but not necessarily represented as inventory like Objects are (although they could be), to store this information that is separate from the character sheet itself but necessary for the proper operation of the character.

Well-designed Extras [would be stored](https://github.com/DamnedScholar/evennia-testbox/blob/master/sr5/data/ware.py) similarly to stats, in the container designated for game system rules, with a series of prototypes that can be spawned with any custom information required for their use.

Since many non-stat entities reflect special abilities that other characters don't possess, certain Extras could give access to additional commands. As Objects contained by the Character, they could act as keys. Since their stats would be stored separately from the Character, it would be easy to tell the difference between values that are intrinsic to the character and ones that may be external or circumstantial.

## Dice and modifiers

Modifiers are hard. RPG systems are chock full of circumstantial bonuses and penalties. Some stack, some don't. It's nice when a dice roller factors in modifiers, but that's often not possible to accomplish with any level of fidelity. The superior writeability and processing of Python offers us a solution. Extras can have [modifiers](https://github.com/DamnedScholar/evennia-testbox/blob/master/sr5/data/ware.py#L73) stored on themselves that then get aggregated into a master list (which can be cached, as these rarely change on the fly) and then made accessible for the player to incorporate into rolls without having to consult the books in the middle of a fight.

My thinking on how modifiers should be represented and interpreted by the game is still in early stages, and thus may change, but fundamentally what needs to happen is for the game to be told which stat or function the Extra modifies, the value of the modifier, and the circumstances under which it applies. For unconditional modifiers, the game needs to know whether or not they're expected to stack. Some game systems have clearer rules about this than others. In any case, the user should be able to override what the game thinks should be applied.
