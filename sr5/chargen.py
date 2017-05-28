"""
Room

Rooms are simple containers that has no location of their own.

"""

import math
import string
from evennia import default_cmds
from evennia import DefaultRoom
from evennia import DefaultScript
from evennia.utils import evtable

class ChargenScript(DefaultScript):
    """
    This script is placed on a character object when it is created. It holds variables relevant to the chargen process that need to be cleaned up after and it inherits the data that is important for the chargen process.
    """
    test = "It works."
    metatype = {"a": {"human": 9, "elf": 8, "dwarf": 7, "ork": 7, "troll": 5},
                "b": {"human": 7, "elf": 6, "dwarf": 4, "ork": 4, "troll": 0},
                "c": {"human": 5, "elf": 3, "dwarf": 1, "ork": 0},
                "d": {"human": 3, "elf": 0},
                "e": {"human": 1}}
    attr = {"a": 24, "b": 20, "c": 16, "d": 14, "e": 12}
    magic = {
        "a": {"magician": {"magic": 6, "skills": (2, 5), "spells": 10},
              "mystic adept": {"magic": 6, "skills": (2, 5), "spells": 10}},
        "b": {"magician": {"magic": 4, "skills": (2, 4), "spells": 7},
              "mystic adept": {"magic": 4, "skills": (2, 4), "spells": 7},
              "aspected magician": {"magic": 5, "group": (1, 4)},
              "adept": {"magic": 6, "skills": (1, 4)}},
        "c": {"magician": {"magic": 3, "skills": (2, 5), "spells": 5},
              "mystic adept": {"magic": 3, "skills": (2, 5), "spells": 5},
              "aspected magician": {"magic": 3, "group": (1, 2)},
              "adept": {"magic": 4, "skills": (1, 2)}},
        "d": {"aspected magician": {"magic": 3, "group": (1, 2)},
              "adept": {"magic": 4, "skills": (1, 2)}}
    }
    resonance = {"a": {"resonance": 6, "skills": (2, 5), "forms": 5},
                 "b": {"resonance": 4, "skills": (2, 4), "forms": 2},
                 "c": {"resonance": 3, "skills": (0, 0), "forms": 1}}
    skills = {"a": {"points": 46, "group": 10},
              "b": {"points": 36, "group": 5},
              "c": {"points": 28, "group": 2},
              "d": {"points": 22, "group": 0},
              "e": {"points": 18, "group": 0}}
    resources = {"a": {"street": 75000, "experienced": 450000, "prime": 500000},
                 "b": {"street": 50000, "experienced": 275000, "prime": 325000},
                 "c": {"street": 25000, "experienced": 140000, "prime": 210000},
                 "d": {"street": 15000, "experienced": 50000, "prime": 150000},
                 "e": {"street": 6000, "experienced": 6000, "prime": 100000}}

    def at_script_creation(self):
        self.tier = "experienced"
        self.priorities = {"a": "", "b": "", "c": "",
                           "d": "", "e": ""}
        self.key = "chargen"
        self.desc = "Handles Character Creation"
        pass

    def at_start(self):
        self._init_character(self.obj.name)

    def _init_character(self, character):
        """
        This initializes the back-reference
        and chargen cmdset on a character
        """
        self.obj.chargen = self.obj.scripts.get("chargen")[0]
        #character.cmdset.add("sr5.chargen.ChargenCmdSet")

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

    # When in a chargen room, the here.cg_step attribute will be checked and the desc will change based on that. When the +chargen command is invoked, this list will serve as the list of viable arguments. I'm still not quite sure where to put this.
    cg_steps = ["priority", "vitals", "metatype", "attributes", "magic", "resonance", "qualities", "skills", "money", "background", "karma"]

    def return_appearance(self, looker):
        """
        This overrides the default function for chargen rooms specifically, and will return dynamic details about the player's progress.
        """
        pass

    pass

class CmdPriorities(default_cmds.MuxCommand):
    """
    Sets your priorities in chargen. You must set each of priorities A through E to one of 'Metatype', 'Attributes', 'Magic', 'Resonance', 'Skills', and 'Resources'. The command will autocomplete, and both "Magic" and "Resonance" are valid names for the third column.

    Usage:
        priority a = metatype
        priority b = mag
        priority b reson
        priority e resources
        priority a = unset
    """

    key = "priority"
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        #cgscript = caller.scripts
