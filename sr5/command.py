"""
Commands

Commands describe the input the player can do to the game.

"""

import pyparsing as pp
from decimal import Decimal
import math
import string
import inspect
import evennia
from evennia import Command as BaseCommand
from evennia import default_cmds
from evennia.utils import evtable
from fuzzywuzzy import process
from sr5.data.base_stats import *
from sr5.data.metatypes import *
from sr5.data.skills import *
from sr5.data.qualities import *
from sr5.msg_format import mf
from sr5.utils import (a_n, itemize, flatten, LedgerHandler, SlotsHandler,
                       validate, ureg)
from sr5.system import Stats


class SemanticCommand(default_cmds.MuxCommand):
    """
    This is a replacement command parent that spits out a more semantically
    meaningful cluster of command parts. It should only override parse().
    """
    def parse(self):
        """
        This method is called by the cmdhandler once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from self.func() (see below)

        The following variables are available for our use when entering this
        method (from the command definition, and assigned on the fly by the
        cmdhandler):
           self.key - the name of this command ('look')
           self.aliases - the aliases of this cmd ('l')
           self.permissions - permission string for this command
           self.help_category - overall category of command

           self.caller - the object calling this command
           self.cmdstring - the actual command name used to call this
                            (this allows you to know which alias was used,
                             for example)
           self.args - the raw input; everything following self.cmdstring.
           self.cmdset - the cmdset from which this command was picked. Not
                         often used (useful for commands like 'help' or to
                         list all available commands etc)
           self.obj - the object on which this command was defined. It is often
                         the same as self.caller.

        A MUX command has the following possible syntax:

          name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]

        The 'name[ with several words]' part is already dealt with by the
        cmdhandler at this point, and stored in self.cmdname (we don't use
        it here). The rest of the command is stored in self.args, which can
        start with the switch indicator /.

        This parser breaks self.args into its constituents and stores them in the
        following variables:
          self.switches = [list of /switches (without the /)]
          self.raw = This is the raw argument input, including switches
          self.args = This is re-defined to be everything *except* the switches
          self.lhs = Everything to the left of = (lhs:'left-hand side'). If
                     no = is found, this is identical to self.args.
          self.rhs: Everything to the right of = (rhs:'right-hand side').
                    If no '=' is found, this is None.
          self.lhslist - [self.lhs split into a list by comma]
          self.rhslist - [list of self.rhs split into a list by comma]
          self.arglist = [list of space-separated args (stripped, including '=' if it exists)]

          All args and list members are stripped of excess whitespace around the
          strings, but case is preserved.
        """
        raw = self.args
        args = raw.strip()

        # split out switches
        switches = []
        if args and len(args) > 1 and raw[0] == "/":
            # we have a switch, or a set of switches. These end with a space.
            switches = args[1:].split(None, 1)
            if len(switches) > 1:
                switches, args = switches
                switches = switches.split('/')
            else:
                args = ""
                switches = switches[0].split('/')
        arglist = [arg.strip() for arg in args.split()]

        # check for arg1, arg2, ... = argA, argB, ... constructs
        lhs, rhs = args, None
        lhslist, rhslist = [arg.strip() for arg in args.split(',')], []
        if args and '=' in args:
            lhs, rhs = [arg.strip() for arg in args.split('=', 1)]
            lhslist = [arg.strip() for arg in lhs.split(',')]
            rhslist = [arg.strip() for arg in rhs.split(',')]

        # save to object properties:
        self.raw = raw
        self.switches = switches
        self.args = args.strip()
        self.arglist = arglist
        self.lhs = lhs
        self.lhslist = lhslist
        self.rhs = rhs
        self.rhslist = rhslist

        # if the class has the player_caller property set on itself, we make
        # sure that self.caller is always the player if possible. We also create
        # a special property "character" for the puppeted object, if any. This
        # is convenient for commands defined on the Player only.
        if hasattr(self, "player_caller") and self.player_caller:
            if utils.inherits_from(self.caller, "evennia.objects.objects.DefaultObject"):
                # caller is an Object/Character
                self.character = self.caller
                self.caller = self.caller.player
            elif utils.inherits_from(self.caller, "evennia.players.players.DefaultPlayer"):
                # caller was already a Player
                self.character = self.caller.get_puppet(self.session)
            else:
                self.character = None

        name_string = pp.Word(
            pp.alphanums + pp.punc8bit +
            pp.alphas8bit + "#$%&'()*+-.;<>!?@[\\]^_`|~ "
        )
        switch_string = pp.Word(
            pp.alphanums + pp.punc8bit +
            pp.alphas8bit + "#$%&'()*+-.;<>!?@[\\]^_`|~"
        )
        text_string = pp.Word(
            pp.alphanums + pp.punc8bit +
            pp.alphas8bit + "#$%&'()*+-.;/<>!?@[\\]^_`|~ "
        )
        s = pp.ZeroOrMore(" ")
        eq = pp.Suppress(pp.Word("="))
        switch = pp.Suppress("/") + name_string
        switches = pp.Optional(pp.OneOrMore(switch))
        phrase = pp.Suppress('"') + text_string + pp.Suppress('"')
        target = phrase("target") ^ name_string("target")
        # target = text_string("target")
        rating = pp.Word(pp.nums + ".,")
        balance = rating("rating") + switches("arg switches") ^ text_string("text")
        setting = switches("cmd switches") + s + target("lhs") + pp.Optional(s + eq + s + balance("rhs"))

        self.new_args = setting.parseString(self.args)
        # Sort command switches into a list.
        # self.switches = list(self.new_args.get('cmd switches', []))
        # Isolate target.
        self.target = self.new_args.get('target', None)
        # Convert rating to a number, making it a decimal if possible.
        self.rating = self.new_args.get('rating', None)
        if self.rating:
            self.rating = self.rating.replace(",", ".")
            self.rating = Decimal(self.rating)
        # The text or subject of the command.
        self.subject = None
        self.text = self.new_args.get('text', None)
        self.arg_switches = list(self.new_args.get('arg switches', []))
        if self.text:
            disassembly = self.text.split("/")
            self.subject = disassembly.pop(0)
            self.arg_switches += disassembly

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
         by the cmdhandler right after self.parser() finishes, and so has access
         to all the variables defined therein.
        """
        # a simple test command to show the available properties
        string = "-" * 50
        string += "\n|w%s|n - Command variables from evennia:\n" % self.key
        string += "-" * 50
        string += "\nname of cmd (self.key): |w%s|n\n" % self.key
        string += "cmd aliases (self.aliases): |w%s|n\n" % self.aliases
        string += "cmd locks (self.locks): |w%s|n\n" % self.locks
        string += "help category (self.help_category): |w%s|n\n" % self.help_category
        string += "object calling (self.caller): |w%s|n\n" % self.caller
        string += "object storing cmdset (self.obj): |w%s|n\n" % self.obj
        string += "command string given (self.cmdstring): |w%s|n\n" % self.cmdstring
        # show cmdset.key instead of cmdset to shorten output
        string += utils.fill("current cmdset (self.cmdset): |w%s|n\n" % self.cmdset)
        string += "\n" + "-" * 50
        string += "\nVariables from MuxCommand baseclass\n"
        string += "-" * 50
        string += "\nraw argument (self.raw): |w%s|n \n" % self.raw
        string += "cmd args (self.args): |w%s|n\n" % self.args
        string += "cmd switches (self.switches): |w%s|n\n" % self.switches
        string += "space-separated arg list (self.arglist): |w%s|n\n" % self.arglist
        string += "lhs, left-hand side of '=' (self.lhs): |w%s|n\n" % self.lhs
        string += "lhs, comma separated (self.lhslist): |w%s|n\n" % self.lhslist
        string += "rhs, right-hand side of '=' (self.rhs): |w%s|n\n" % self.rhs
        string += "rhs, comma separated (self.rhslist): |w%s|n\n" % self.rhslist
        string += "-" * 50
        self.caller.msg(string)


class CmdStatView(SemanticCommand, Stats):
    """
    Shows the details for a stat requested by the user.
    """

    key = "stat"
    help_category = "Shadowrun 5e"

    def func(self):
        "Active function."
        caller = self.caller
        # IDEA: Maybe the view could include the current rating possessed by
        # the caller.

        # Route the user to where they need to go.
        lists = {
            "Metatypes": (Metatypes.meta_attr.keys(), self.view_metatype),
            "Attributes": (
                Attr.names.keys() + SpecAttr.names.keys(), self.view_attr),
            "Skills": (
                Skills.active.keys() + Skills.knowledge.keys() +
                ["language"],
                self.view_skill),
            "Qualities": (
                PositiveQualities.names + NegativeQualities.names,
                self.view_quality),
            # "Spells": (Spells.names.keys(), self.view_spell),
            # "Forms": (Forms.names.keys(), self.view_form),
        }

        to_show = [(l, n[0])
                   for l, d in lists.items()
                   for n in process.extract(self.target, d[0])
                   if n[1] > 80]

        if len(to_show) > 1:
            caller.msg(mf.tag + self.view_disambiguation(to_show))

        view_method = []

    color = {
        "metatype": "h",
        "attr": "h",
        "skill": "h",
        "quality": "h",
        "spell": "h",
        "form": "h"
    }

    def colorize(self, text, cat):
        """
        Maybe you want each stat category to have a different color. This
        function makes that happen, as long as its companion dict (self.color)
        has an entry for that category.
        """
        return "|{}{}|n".format(self.color.get(cat, ""), text)

    def view_disambiguation(self, to_show):
        to_show = [
            self.colorize("{}: {}".format(l, n.title()), l)
            for l, n in to_show]
        return '"{}" looks like multiple entries in the system. Did you mean' \
               ' to search for one of the following? {}'.format(
                    self.target, itemize(to_show)
               )

    def view_metatype(self, caller):
        "Display attribute blurbs."
        pass

    def view_attr(self, caller):
        "Display attribute blurbs."
        pass

    def view_skill(self, caller):
        "Display skill blurbs."
        pass

    def view_quality(self, caller):
        "Display quality blurbs."
        pass

    def view_spell(self, caller):
        "Display spell blurbs."
        pass

    def view_form(self, caller):
        "Display form blurbs."
        pass

class CmdSheet(default_cmds.MuxCommand):
    """
    Displays your sheet, or initializes a blank sheet (for restarting chargen, hard-resetting in the case of bugs, or giving sheets to objects that don't have them).

    Usage:
        sheet
        sheet <target>
        sheet/blank
        sheet/blank <target>
        sheet/prove
        sheet/prove <target>
        sheet/show
        sheet/show <target>
    """

    key = "sheet"
    help_category = "Shadowrun 5e"

    def func(self):
        "Active function."
        caller = self.caller
        if self.args:
            target = self.args
        elif self.args:
            return caller.msg("I can't find a player by that name.")
        else:
            target = caller

        # If the target is in chargen, look at the chargen script for data instead of the character object.
        if target.cg:
            target = target.cg
            mode = "chargen"
        else:
            mode = "normal"

        if not self.switches:
            # Display the character sheet. If the object doesn't have a character sheet, display an error message.
            if not self.args:
                # Display the caller's sheet.
                vitals = evtable.EvTable(width=120, align="l")
                vitals.add_row("Full Name:", target.db.fullname,
                               "Birthdate:", target.db.birthdate)
                vitals.add_row("Metatype:", target.db.metatype,
                               "Ethnicity:", target.db.ethnicity)
                vitals.add_row("Height:", target.db.height,
                               "Weight:", target.db.weight)
                rep = evtable.EvTable(width=120, align="l")
                rep.add_row("Street Cred:", target.db.street_cred,
                            "Notoriety:", target.db.notoriety,
                            "Public Awareness:", target.db.public_awareness)
                karma = evtable.EvTable(width=120, align="l")
                karma.add_row("Karma:", target.db.karma["current"],
                               "Total:", target.db.karma["total"])
                caller.msg(vitals)
                caller.msg(rep)
                caller.msg(karma)

                attributes = evtable.EvTable(width=120, align="l")
                attributes.add_row("BOD:", target.get_bod(),
                                   "AGI:", target.get_agi(),
                                   "REA:", target.get_rea(),
                                   "STR:", target.get_str())
                attributes.add_row("WIL:", target.get_bod(),
                                   "LOG:", target.get_agi(),
                                   "INT:", target.get_rea(),
                                   "CHA:", target.get_str())
                attributes.add_row("Essence:", target.get_ess(),
                                   "Edge:", target.get_edg(),
                                   target.get_magres()[0], target.get_magres()[1])
                caller.msg(attributes)

                def cond_count(i, t):
                    if i + 3 <= t:
                        i += 3
                        return "[ ][ ][ ]"
                    elif i + 2 == t:
                        i += 2
                        return "[ ][ ]   "
                    elif i + 1 == t:
                        i += 1
                        return "[ ]      "
                    else:
                        return "         "

                phys_mod = target.get_phys_mod()
                stun_mod = target.get_stun_mod()
                derived = evtable.EvTable(width=120, align="l", border="none")
                derived.add_row("Initiative:", target.get_init(),
                                "Physical Mod:",
                                "Stun Mod:")
                derived.add_row("Astral Initiative:", target.get_astral_init(),
                                cond_count(0, phys_mod),
                                cond_count(0, stun_mod))
                derived.add_row("Matrix Initiative:", target.get_matrix_init(),
                                cond_count(3, phys_mod),
                                cond_count(3, stun_mod))
                derived.add_row("Composure:", target.get_composure(),
                                cond_count(6, phys_mod),
                                cond_count(6, stun_mod))
                derived.add_row("Judge Intentions:", target.get_judge(),
                                cond_count(9, phys_mod),
                                cond_count(9, stun_mod))
                derived.add_row("Memory:", target.get_memory(),
                                cond_count(12, phys_mod))
                derived.add_row("Lift/Carry:", target.get_lift_carry(),
                                cond_count(15, phys_mod))
                derived.add_row("Movement:", target.get_movement())
                caller.msg(derived)

                skills = evtable.EvTable("Skills", width=120, align="l",
                                         border="header")
                # TODO: Add active skill groups.
                active_skills = ""
                skill_list = sorted(target.db.active_skills.items() + target.db.active_skill_groups.items())
                for i in range(0, len(target.db.active_skills)):
                    skill = skill_list[i]
                    skill_string = string.capwords(skill[0])
                    if skill[0] in target.db.active_specializations:
                        skill_string += " (" + string.capwords(target.db.active_specializations[skill[0]]) + " +2)"
                    active_skills += skill_string + " " + str(skill[1])

                    if i < len(target.db.active_skills) - 1:
                        active_skills += ", "

                skills.add_row("Active", active_skills)

                knowledge_skills = ""
                skill_list = sorted(target.db.knowledge_skills.items())

                for i in range(0, len(target.db.knowledge_skills)):
                    skill = skill_list[i]
                    skill_string = string.capwords(skill[0])
                    if skill[0] in target.db.knowledge_specializations:
                        skill_string += " (" + string.capwords(target.db.knowledge_specializations[skill[0]]) + " +2)"
                    knowledge_skills += skill_string + " " + str(skill[1])

                    if i < len(target.db.knowledge_skills) - 1:
                        knowledge_skills += ", "

                skills.add_row("Knowledge", knowledge_skills)

                language_skills = ""
                skill_list = sorted(target.db.language_skills.items())

                for i in range(0, len(target.db.language_skills)):
                    skill = skill_list[i]
                    skill_string = string.capwords(skill[0])
                    if skill[0] in target.db.language_specializations:
                        skill_string += " (" + string.capwords(target.db.language_specializations[skill[0]]) + " +2)"
                    language_skills += skill_string + " " + str(skill[1])

                    if i < len(target.db.language_skills) - 1:
                        language_skills += ", "

                skills.add_row("Language", language_skills)
                caller.msg(skills)
            else:
                # Look for an object that matches self.args and display its sheet if the caller has the authority to see it.
                pass
        elif "blank" in self.switches:
            # Initialize a blank sheet. If the object has a sheet, we might want to prompt for authorization to erase it. If the object's sheet is locked, this command will return an error.
            if not target.sheet_locked == true:
                target.db.sheet_locked = "False"
                target.db.fullname = "Empty"
                target.db.approved = "No"
                target.db.birthdate = "1/1/1970"
                target.db.metatype = "Human"
                target.db.ethnicity = ""
                target.db.height = ""
                target.db.weight = ""
                target.db.street_cred = ""
                target.db.notoriety = ""
                target.db.public_awareness = ""
                target.db.karma = {'current': 0, 'total': 0}
                target.db.attributes = {
                    'body': 1, 'agility': 1, 'reaction': 1, 'strength': 1,
                    'willpower': 1, 'logic': 1, 'intuition': 1, 'charisma': 1,
                    'essence': 6, 'edge': 1, 'magic': 0, 'resonance': 0
                }
                target.db.active_skills = {}
                target.db.active_specializations = {}
                target.db.active_skill_groups = {}
                target.db.knowledge_skills = {}
                target.db.knowledge_specializations = {}
                target.db.language_skills = {}
                target.db.language_specializations = {}
                # Don't store the Karma value of qualities. Store the level
                # and calculate the Karma points based on the lookup table.
                target.db.qualities_positive = {}
                target.db.qualities_negative = {}
            else:
                return caller.msg("That sheet is locked. A member of staff "
                                  "will have to unlock it.")
        elif "prove" in self.switches or "show" in self.switches:
            # Show your sheet to someone else or the room.
            caller.msg("Prove command coming soon.")
        else:
            caller.msg("I don't know what switch that is.")


class CmdKarma(default_cmds.MuxCommand):
    """
    Command for spending karma and viewing logs. If the game allows it, you can
    open a request ticket regarding karma from here, too.

    Usage:
    > karma
    > karma/spend
    > karma/log
    > karma/request <title>=<body>
    """

    key = "karma"
    aliases = ["ka", "xp"]
    help_category = "Shadowrun 5e"

    def func(self):
        caller = self.caller
        if self.args:
            target = self.args
        elif self.args:
            return caller.msg("I can't find a player by that name.")
        else:
            target = caller

        if target.cg:
            target = target.cg
            mode = "chargen"
        else:
            mode = "normal"

        tag = "|Rsr5 > |n"

        if not target.db.karma:
            caller.msg(tag + "That target doesn't seem to have a karma log.")

        if not self.switches:
            caller.msg(target.db.karma)
        elif "log" in self.switches:
            table = evtable.EvTable("Date", "Transaction", "Origin")
            log_list = target.db.karma.log()
            for date, owner, value, currency, reason, origin in log_list:
                # Origin comes in as a dbref and we need it to be a name.
                origin = evennia.search_object(searchdata=origin)[0].name
                table.add_row(
                    date.strftime("%c"),
                    "{} {}: {}".format(value, currency, reason),
                    origin
                )

            caller.msg(table)
        else:
            return False


class CmdNuyen(default_cmds.MuxCommand):
    """
    Command for spending nuyen and viewing logs. If the game allows it, you can
    open a request ticket regarding nuyen from here, too.

    Usage:
    > nuyen
    > nuyen/spend
    > nuyen/log
    > nuyen/request <title>=<body>
    """

    key = "nuyen"
    aliases = ["ny", "nu"]
    help_category = "Shadowrun 5e"

    def func(self):
        caller = self.caller
        if self.args:
            target = self.args
        elif self.args:
            return caller.msg("I can't find a player by that name.")
        else:
            target = caller

        if target.cg:
            target = target.cg
            mode = "chargen"
        else:
            mode = "normal"

        tag = "|Rsr5 > |n"

        if not target.db.karma:
            caller.msg(tag + "That target doesn't seem to have a nuyen log.")

        if not self.switches:
            caller.msg(target.db.nuyen)
        elif "log" in self.switches:
            table = evtable.EvTable("Date", "Transaction", "Origin")
            log_list = target.db.nuyen.log()
            for date, owner, value, currency, reason, origin in log_list:
                # Origin comes in as a dbref and we need it to be a name.
                origin = evennia.search_object(searchdata=origin)[0].name
                table.add_row(
                    date.strftime("%c"),
                    "{} {}: {}".format(value, currency, reason),
                    origin
                )

            caller.msg(table)
        else:
            return False


class CmdEssence(default_cmds.MuxCommand):
    """
    Command for viewing essence and logs.

    Usage:
    > essence
    > essence/log
    > essence/request <title>=<body>
    """

    key = "essence"
    aliases = ["ess", "e"]
    help_category = "Shadowrun 5e"

    def func(self):
        caller = self.caller
        if self.args:
            target = self.args
        elif self.args:
            return caller.msg("I can't find a player by that name.")
        else:
            target = caller

        if target.cg:
            target = target.cg
            mode = "chargen"
        else:
            mode = "normal"

        tag = "|Rsr5 > |n"

        if not target.db.karma:
            caller.msg(tag + "That target doesn't seem to have an essence"
                       "score.")

        if not self.switches:
            caller.msg(target.db.essence)
        elif "log" in self.switches:
            table = evtable.EvTable("Date", "Transaction", "Origin")
            log_list = target.db.essence.log()
            for date, owner, value, currency, reason, origin in log_list:
                # Origin comes in as a dbref and we need it to be a name.
                origin = evennia.search_object(searchdata=origin)[0].name
                table.add_row(
                    date.strftime("%c"),
                    "{} {}: {}".format(value, currency, reason),
                    origin
                )

            caller.msg(table)
        else:
            return False


class CmdBody(default_cmds.MuxCommand):
    """
    Shows any cyberware or metagenic traits in your anatomy.

    Usage:
    > body
    """

    key = "body"
    aliases = ["anatomy"]
    help_category = "Shadowrun 5e"

    cyberware = {"left":
                        {"hand": "",
                         "arm":
                            {"upper": "Armor 1, Agility 3, Strength 3",
                             "lower": ""},
                         "foot": "",
                         "leg":
                            {"upper": "",
                            "lower": ""}
                        },
                 "right":
                        {"hand": "",
                         "arm":
                            {"upper": "",
                             "lower": ""},
                         "foot": "",
                         "leg":
                            {"upper": "",
                             "lower": ""}
                        },
                 "head": "",
                 "torso": "",
                 "abdomen": ""
                }
    cyber_list = []

    # TODO: Rewrite the following code so that it works for things other than cyberware.

    def func(self):
        "Active function."
        caller = self.caller

        tag = "|Rsr5 > |n"

        output = ""

        # TODO: Strip excessive spaces and borders and turn this into an EvTable with the text information displayed to the right of the figure.

        output += ".---------------.\n"
        output += "|      " + self.cyber("/~~~\\", "head") + "    |\n"
        output += "|    " + self.cyber("W", "right", "hand") + self.cyber("( o o )", "head") + "   |\n"
        output += "|     " + self.cyber("\\", "right", "arm", "lower") + self.cyber("\\---/", "head") + "    |\n"
        output += "|      " + self.cyber("\\", "right", "arm", "upper") + self.cyber("I I", "head") + "     |\n"
        output += "|       " + self.cyber("< >", "torso") + self.cyber("\\", "left", "arm", "upper") + "    |\n"
        output += "|       " + self.cyber("< >", "torso") + self.cyber(" \\", "left", "arm", "lower") + "   |\n"
        output += "|       " + self.cyber("/^\\", "abdomen") + self.cyber("  M", "left", "hand") + "  |\n"
        output += "|      " + self.cyber("/", "right", "leg", "upper") + self.cyber("   \\", "left", "leg", "upper") + "    |\n"
        output += "|     " + self.cyber("/", "right", "leg", "lower") + self.cyber("     \\", "left", "leg", "lower") + "   |\n"
        output += "|    " + self.cyber("~ ", "right", "foot") + self.cyber("      ~", "left", "foot") + "  |\n"
        output += "`---------------'\n"

        for item in self.cyber_list:
            output += "|b" + item.title() + "|n\n"

        caller.msg(output)

    def cyber(self, text, *args):
        where_name = ""
        if len(args) >= 1:
            augment = self.cyberware[args[0]]
            where_name += args[0] + " "
        if len(args) >= 2:
            augment = self.cyberware[args[0]][args[1]]
            where_name += args[1]

            # Hands and feet are included by their respective limbs.
            if not augment and args[1] in ["hand", "foot"]:
                if args[1] in "hand":
                    limb = "arm"
                else:
                    limb = "leg"
                if self.cyberware[args[0]][limb]["upper"] or self.cyberware[args[0]][limb]["lower"]:
                    return "|b" + text + "|n"
        if len(args) >= 3:
            augment = self.cyberware[args[0]][args[1]][args[2]]
            where_name.replace(" ", " " + args[2] + " ")

            # Lower arms and legs are included by upper arms and legs.
            if not augment and args[2] in "lower":
                if self.cyberware[args[0]][args[1]]["upper"]:
                    return "|b" + text + "|n"

        if augment:
            self.cyber_list.append(where_name.title() + ": " + augment)
            return "|b" + text + "|n"
        else:
            return text


# TODO: Delete this.
class CmdShowMe(default_cmds.MuxCommand):
    """
    Shows command parsing
    """

    key = "showme"
    help_category = "Shadowrun 5e"

    def func(self):
        self.caller.msg("Switches: " + str(self.switches))
        self.caller.msg("Args: " + str(self.args))
