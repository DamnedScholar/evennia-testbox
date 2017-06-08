"""
Room

Rooms are simple containers that has no location of their own.

"""

import math
import string
from evennia import CmdSet
from evennia import default_cmds
from evennia import DefaultRoom
from evennia import DefaultScript
from evennia.utils import evtable
from sr5.data.skills import Skills

class ChargenScript(DefaultScript):
    """
    This script is placed on a character object when it is created. It holds variables relevant to the chargen process that need to be cleaned up after and it inherits the data that is important for the chargen process.
    """
    cg_steps = ["priority", "vitals", "metatype", "attributes", "magic",
                "resonance", "qualities", "skills", "resources", "background",
                "karma"]
    data_skills = Skills
    categories = ["metatype", "attributes", "magic", "resonance", "skills",
                  "resources"]
    metatypes = {"a": [("human", 9, 0), ("elf", 8, 0), ("dwarf", 7, 0), ("ork", 7, 0), ("troll", 5, 0)],
                 "b": [("human", 7, 0), ("elf", 6, 0), ("dwarf", 4, 0), ("ork", 4, 0), ("troll", 0, 0)],
                 "c": [("human", 5, 0), ("elf", 3, 0), ("dwarf", 1, 0), ("ork", 0, 0)],
                 "d": [("human", 3, 0), ("elf", 0, 0)],
                 "e": [("human", 1, 0)]}
    attr = {"a": 24, "b": 20, "c": 16, "d": 14, "e": 12}
    magic = {
        "a": {"magician": {"magic": 6, "skills": (2, 5), "spells": 10},
              "mystic adept": {"magic": 6, "skills": (2, 5), "spells": 10}},
        "b": {"magician": {"magic": 4, "skills": (2, 4), "spells": 7},
              "mystic adept": {"magic": 4, "skills": (2, 4), "spells": 7},
              "aspected magician": {"magic": 5, "group": (1, 4)},
              "apprentice": {"magic": 5, "group": (1, 4)},
              "adept": {"magic": 6, "skills": (1, 4)}},
        "c": {"magician": {"magic": 3, "skills": (2, 5), "spells": 5},
              "mystic adept": {"magic": 3, "skills": (2, 5), "spells": 5},
              "aspected magician": {"magic": 3, "group": (1, 2)},
              "apprentice": {"magic": 3, "group": (1, 2)},
              "adept": {"magic": 4, "skills": (1, 2)},
              "enchanter": {"magic": 5, "group": (1, 4)}},
              "explorer": {"magic": 5, "skills": (2, 6)},
        "d": {"aspected magician": {"magic": 3, "group": (1, 2)},
              "adept": {"magic": 4, "skills": (1, 2)},
              "aware": {"magic": 3, "skills": (1, 4)}}
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
        # Evennia stuff
        self.key = "chargen"
        self.desc = "Handles Character Creation"

    def reset_all(self):
        "Resets chargen."
        # Preliminary chargen stuff
        self.db.tier = "experienced"
        self.db.priorities = {"a": "", "b": "", "c": "",
                              "d": "", "e": ""}


    def reset_all(self):
        "Resets chargen."
        # Metatype
        self.db.metatype, self.db.metakarma = "", 0
        self.db.specattr = {"edge": 1, "magic": 0, "resonance": 0}

        # Attributes
        self.db.attr = {'body': 0, 'agility': 0, 'reaction': 0, 'strength': 0,
        'willpower': 0, 'logic': 0, 'intuition': 0, 'charisma': 0}
        self.db.metaattr = {'body': 1, 'agility': 1, 'reaction': 1, 'strength': 1,
        'willpower': 1, 'logic': 1, 'intuition': 1, 'charisma': 1}

    def at_start(self):
        """
        This initializes the back-reference and chargen cmdset on a character
        """
        self.obj.cg = self.obj.scripts.get("chargen")[0]
        self.obj.cmdset.add("sr5.chargen.ChargenCmdSet")

    def cgview(self, step, priority):
        self.priority = "You've set the following priorities:\n\n" \
                        "A: {a}\nB: {b}\nC: {c}\nD: {d}\nE: {e}".format(
                            a=self.db.priorities["a"].title(),
                            b=self.db.priorities["b"].title(),
                            c=self.db.priorities["c"].title(),
                            d=self.db.priorities["d"].title(),
                            e=self.db.priorities["e"].title()
                        )

        # def getkey(item):
        #     return item[0]
        # options = sorted(self.metatypes[priority], key=getkey)
        options = self.metatypes[priority]
        self.metatype = "At priority {0}, you have the following choices:\n\n".format(priority.title())
        self.metatype += "\t|h{left:<20}{right:>30}|n\n".format(left="Command to Set", right="Metatype (Attributes, Karma)")
        for i in range(0, len(options)):
            option = options[i]
            left = "\t> meta {command}".format(command=option[0])
            right = "{name} ({sa} SA, {karma} Karma)\n".format(name=option[0].title(), sa=option[1], karma=option[2])
            self.metatype += "{left:<20}{right:>30}".format(left=left, right=right)

        self.metatype += "\nYou can look at a metatype's stats with \"stat <metatype>\"."

        return getattr(self, step, "We're not finding that step.")

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


    def return_appearance(self, looker):
        """
        This overrides the default function for chargen rooms specifically, and will return dynamic details about the player's progress.
        """
        pass

    pass

class CmdSetPriority(default_cmds.MuxCommand):
    """
    Sets your priorities in chargen. You must set each of priorities A through E to one of 'Metatype', 'Attributes', 'Magic', 'Resonance', 'Skills', and 'Resources'. The command will match partials, and both "Magic" and "Resonance" are valid names for the third column.

    Usage:
        priority a = metatype
        priority b = mag
        priority b reson
        pri e resources
        pri a = unset
    """

    key = "priority"
    aliases = ["pri"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def parse(self):
        self.args = self.args.strip()
        self.args = self.args.replace('=', ' ')
        self.input = self.args.split(' ')

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        # Break apart self.input and return errors if things aren't what they're supposed to be.
        self.priority = self.input[0].lower()
        self.category = self.input[len(self.input) - 1].lower()
        match, occupied, success = '', '', False
        if self.priority not in "abcde":
            caller.msg(tag + "Please enter 'a', 'b', 'c', 'd', or 'e'.")
            return False

        for i in range(0,len(cg.categories)):
          if self.category in cg.categories[i]:
            match = True
            self.category = cg.categories[i]
        if not match:
            caller.msg(tag + 'Please enter a valid category. Valid choices are "Metatype", "Attributes", "Magic", "Resonance", "Skills", and "Resources".')
            return False
        # Check to see if something's already in that priority slot.
        if cg.db.priorities[self.priority] and cg.db.priorities[self.priority] is not self.category:
            occupied = ' and category "' + cg.db.priorities[self.priority].title() + '" removed'

        # Check to see if the category's on the list. "Magic" and "Resonance" are synonymous for this step, so they remove each other.
        self.existing = cg.db.priorities.items()
        for i in range(0,len(self.existing)):
            if self.category in self.existing[i][1] or self.category in "magic" and self.existing[i][1] in "resonance" or self.category in "resonance" and self.existing[i][1] in "magic":
                self.operation = "replace"
                cg.db.priorities[self.existing[i][0]] = ''
                cg.db.priorities[self.priority] = self.category
                success = True
        # If not, then don't remove anything.
        if not success:
            self.operation = "add"
            cg.db.priorities[self.priority] = self.category
        # Display a message according to the operation.
        if self.operation == "add":
            caller.msg(tag + 'Category "' + self.category.title() + '" set as priority ' + self.priority.title() + occupied + '.')
        elif self.operation == "replace":
            caller.msg(tag + 'Category "' + self.category.title() + '" changed to priority ' + self.priority.title() + occupied + '.')

class CmdCGRoom(default_cmds.MuxCommand):
    """
    Displays a page with data relevant to a particular stage of character creation. This is identical to standing in the respective chargen room and using "look". The stage will match partials. "Magic" and "Resonance" are synonymous here. The options you are shown for either of these will be based on which one is in your priorities list.

    Usage:
        chargen metatype
        chargen ski
        cg attributes
        cg mag
    """

    key = "chargen"
    aliases = ["cg"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        step, match, priority = '', False, ''

        # Check if the args match a CG step.
        for i in range(0,len(cg.cg_steps)):
            if self.args in cg.cg_steps[i]:
                match = True
                step = cg.cg_steps[i]

        if not match:
            caller.msg(tag + "Please select a valid step of CG.")
            return False

        # Check if a priority has been set for that CG step.
        if step in cg.db.priorities.values():
            priority = cg.db.priorities.keys()[cg.db.priorities.values().index(step)]
        elif step == "priority":
            priority = "a"
        else:
            caller.msg(tag + "You have to set a priority for it first.")
            return False

        caller.msg(cg.cgview(step, priority))

class CmdSetMetatype(default_cmds.MuxCommand):
    """
    Sets your metatype. The metatype field will match partials. You must set a priority before using this command.

    Usage:
    > metatype human
    > meta hobgo
    """

    key = "metatype"
    aliases = ["meta"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")
class CmdSetSpecAttr(default_cmds.MuxCommand):
    """
    Sets your special attributes. The attribute field will match partials.

    Usage:
    > sa magic 2
    > specattr mag = 2
    """

    key = "specattr"
    aliases = ["sa"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")

class CmdSetAttr(default_cmds.MuxCommand):
    """
    Sets your attributes. The attribute field will match partials. You must set a priority before using this command.

    Usage:
    > attribute bod = 3
    > attr bod 3
    """

    key = "attribute"
    aliases = ["attr"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")

class CmdSetMagicType(default_cmds.MuxCommand):
    """
    Sets your magical type. The type field will match partials. You must set a priority before using this command.

    Usage:
    > magic magician
    > mag mystic adept
    """

    key = "magic"
    aliases = ["mag"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")
class CmdBuySpell(default_cmds.MuxCommand):
    """
    Purchase a spell in character creation. The name field will match partials (so be careful). You must set a magical type before using this command.

    Usage:
    > spell manaball
    > sp manaball
    """

    key = "spell"
    aliases = ["sp"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")
class CmdBuyPower(default_cmds.MuxCommand):
    """
    Purchase a power in character creation. The name field will match partials (so be careful). You must set a magical type before using this command.

    Usage:
    > power killing hands
    > pow killing hands
    """

    key = "power"
    aliases = ["pow"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")
class CmdBuyForm(default_cmds.MuxCommand):
    """
    Purchase a complex form in character creation. The name field will match partials (so be careful).

    Usage:
    > form puppeteer
    > form resonance veil
    """

    key = "form"
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")

class CmdSetSkill(default_cmds.MuxCommand):
    """
    Sets your skills. The skill field will match partials. You must set a priority before using this command.

    Usage:
    > skill archery = 3
    > sk archery 3
    """

    key = "skill"
    aliases = ["sk"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")
class CmdSetSpecialization(default_cmds.MuxCommand):
    """
    Sets your specializations. The specialization field will match partials. You must set a priority before using this command.

    Usage:
    > specialize archery = horseback
    > spec archery horseback
    > spec archery.horseback
    """

    key = "specialize"
    aliases = ["spec"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")

class CmdSetLifestyle(default_cmds.MuxCommand):
    """
    Sets your lifestyle. The lifestyle field will match partials. You must set a priority before using this command.

    Usage:
    > lifestyle great
    > life poor
    """

    key = "lifestyle"
    aliases = ["life"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")
class CmdBuyAugment(default_cmds.MuxCommand):
    """
    Buy augments in character creation. This system needs to be figured out.

    Usage:
    > augment dermal plating
    > aug dermal plating
    """

    key = "augment"
    aliases = ["aug"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")

class CmdSetQualities(default_cmds.MuxCommand):
    """
    Sets your qualities. The quality field will match partials. If you enter a number above the maximum level for the quality, the highest level of the quality will be entered. Qualities with multiple forms are most likely split into individual entries, so make sure to check them first.

    Usage:
    > quality addiction (common) 4
    > qual bad luck
    """

    key = "quality"
    aliases = ["qual"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        tag = "|Rsr5 > |n"

        caller.msg("This command isn't in place yet.")

class ChargenCmdSet(CmdSet):
    """
    This is the cmdset available to the Player at all times. It is
    combined with the `CharacterCmdSet` when the Player puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """
    key = "Chargen"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdSetPriority())           # key: priority, pri
        self.add(CmdCGRoom())                # key: chargen, cg
        # Metatype Room
        self.add(CmdSetMetatype())           # key: metatype, meta
        self.add(CmdSetSpecialAttr())        # key: specattr, sa
        # Attribute Room
        self.add(CmdSetAttr())               # key: attribute, attr
        # Magic/Resonance Room
        self.add(CmdSetMagicType())          # key: magic, mag
        self.add(CmdBuySpell())              # key: spell, sp
        self.add(CmdBuyPower())              # key: power, pow
        self.add(CmdBuyForm())               # key: form
        # Skill Room
        self.add(CmdSetSkill())              # key: skill, sk
        self.add(CmdSetSpecialization())     # key: specialize, spec
        # Resources Room
        self.add(CmdSetLifestyle())          # key: lifestyle, life
        self.add(CmdBuyAugment())            # key: augment, aug
        # Qualities Room
        self.add(CmdSetQualities())          # key: quality, qual
