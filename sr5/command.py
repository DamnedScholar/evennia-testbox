"""
Commands

Commands describe the input the player can do to the game.

"""

import math
import string
import evennia
from evennia import Command as BaseCommand
from evennia import default_cmds
from evennia.utils import evtable

class Command(BaseCommand):
    """
    Inherit from this if you want to create your own command styles
    from scratch.  Note that Evennia's default commands inherits from
    MuxCommand instead.

    Note that the class's `__doc__` string (this text) is
    used by Evennia to create the automatic help entry for
    the command, so make sure to document consistently here.

    Each Command implements the following methods, called
    in this order (only func() is actually required):
        - at_pre_cmd(): If this returns True, execution is aborted.
        - parse(): Should perform any extra parsing needed on self.args
            and store the result on self.
        - func(): Performs the actual work.
        - at_post_cmd(): Extra actions, often things done after
            every command, like prompts.

    """
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

    # TODO: Make the sheet silently ask the chargen script for information instead of the player object if the player is unapproved.

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
                # Don't store the Karma value of qualities. Store the level and calculate the Karma points based on the lookup table.
                target.db.qualities_positive = {}
                target.db.qualities_negative={}
            else:
                return caller.msg("That sheet is locked. A member of staff will have to unlock it.")
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
