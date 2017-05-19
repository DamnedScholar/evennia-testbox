# sr5/

This is a self-contained module that contains the functions and TypeClasses necessary to run a game using the fifth edition Shadowrun rules, authored by Sammi.

To install this module, download it into your game folder and make the following additions to the pre-existing files:

1. In `commands/default_cmdsets.py`, `from sr5.command import CmdSheet` and add `self.add(CmdSheet())` to `PlayerCmdSet`.
2. In `typeclasses/characters.py`, `from sr5.character import DefaultShadowrunner` and change the `Character` parent to `DefaultShadowrunner`.
