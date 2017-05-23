"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from evennia import default_cmds
from evennia.utils import evtable
import math
import string

class ChargenRoom(DefaultRoom):
    """
    This is a room designed to hold chargen instructions, with a responsive desc that can help guide the player through the process of setting up their character. In this implementation, a ChargenRoom is also available via a special command.
    """
    # A complete chargen system can be contained in one class definition, with individual room objects in the game being set with variables that define which one they are.

    # Steps
    # 1. Assign priorities A through E to the categories Metatype, Attributes, Magic/Resonance, Skills, and Resources.
    # 2. Pick a Metatype from the available list. The game should mention how many special attribute points are available at the chosen priority level. After the Metatype is chosen, these points will be available for setting.
    # 3. Distribute normal attribute points among mental and physical attributes. Characters may have no more than one attribute at its natural maximum limit.
    # 4. Magic or Resonance. Skip if this is Priority E.
    #   * Each of the top four priority levels has different options, and they're complex options that give skill choices and stuff. The M/R step has to be several mini chargens in a way, and keep whatever is set there separate from the skills overall until chargen is over so that the player has the option of resetting it individually. Probably do display it on the +sheet, though, which means the +sheet will have to be sensitive to however those skills get stored.
    # 5. Purchase qualities. Hard limit of 25 points of positive and 25 points of negative qualities.
    # 6. Purchase skills.
    #   * Exotic Melee Weapon and Pilot Exotic Aircraft have no specializations and need specific categories. The categories can be coded in or staff can review them.
    # 7. Select lifestyle and purchase gear. The gear can happen at any point if the system is automated.
    # 8. Background?
    # 9. Leftover Karma and contacts.

    room_types = ["priority", "metatype", "attributes", "mag_res", "qualities", "skills", "money", "background", "karma"]

    def return_appearance(self, looker):
        """
        This overrides the default function for chargen rooms specifically, and will return dynamic details about the player's progress.
        """
        pass

    pass

class CmdPriorities(default_cmds.MuxCommand):
    """
    Sets your priorities in chargen. You must set each of priorities A through E to one of 'Metatype', 'Attributes', 'Magic/Resonance', 'Skills', and 'Resources'. The command will autocomplete, and both "Magic" and "Resonance" are valid names for the third column.

    Usage:
        priority a = metatype
        priority b = mag
        priority b = reson
        priority e = resources
    """

    key = "priority"
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
