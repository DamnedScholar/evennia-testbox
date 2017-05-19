"""
Commands

Commands describe the input the player can do to the game.

"""

from evennia import Command as BaseCommand
from evennia import default_cmds
from evennia.utils import evtable
import math
import string

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

        if not self.switches:
            # Display the character sheet. If the object doesn't have a character sheet, display an error message.
            if not self.args:
                # Display the caller's sheet.
                vitals = evtable.EvTable(width=120, align="l")
                vitals.add_row("Full Name:",target.db.fullname,
                               "Birthdate:",target.db.birthdate)
                vitals.add_row("Metatype:",target.db.metatype,
                               "Ethnicity:",target.db.ethnicity)
                vitals.add_row("Height:",target.db.height,
                               "Weight:",target.db.weight)
                rep = evtable.EvTable(width=120, align="l")
                rep.add_row("Street Cred:",target.db.street_cred,
                            "Notoriety:",target.db.notoriety,
                            "Public Awareness:",target.db.public_awareness)
                karma = evtable.EvTable(width=120, align="l")
                karma.add_row("Karma:",target.db.karma["current"],
                               "Total:",target.db.karma["total"])
                caller.msg(vitals)
                caller.msg(rep)
                caller.msg(karma)

                attributes = evtable.EvTable(width=120, align="l")
                attributes.add_row("BOD:",target.get_bod(),
                                   "AGI:",target.get_agi(),
                                   "REA:",target.get_rea(),
                                   "STR:",target.get_str())
                attributes.add_row("WIL:",target.get_bod(),
                                   "LOG:",target.get_agi(),
                                   "INT:",target.get_rea(),
                                   "CHA:",target.get_str())
                attributes.add_row("Essence:",target.get_ess(),
                                   "Edge:",target.get_edg(),
                                   "Magic:",target.get_mag(),
                                   "Resonance:",target.get_res())
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
                derived = evtable.EvTable(width=120, align="l", border = "none")
                derived.add_row("Initiative:",target.get_init(),
                                "Physical Mod:",
                                "Stun Mod:")
                derived.add_row("Astral Initiative:",target.get_astral_init(),
                                cond_count(0, phys_mod),
                                cond_count(0, stun_mod))
                derived.add_row("Matrix Initiative:",target.get_matrix_init(),
                                cond_count(3, phys_mod),
                                cond_count(3, stun_mod))
                derived.add_row("Composure:",target.get_composure(),
                                cond_count(6, phys_mod),
                                cond_count(6, stun_mod))
                derived.add_row("Judge Intentions:",target.get_judge(),
                                cond_count(9, phys_mod),
                                cond_count(9, stun_mod))
                derived.add_row("Memory:",target.get_memory(),
                                cond_count(12, phys_mod))
                derived.add_row("Lift/Carry:",target.get_lift_carry(),
                                cond_count(15, phys_mod))
                derived.add_row("Movement:",target.get_movement())
                caller.msg(derived)

                skills = evtable.EvTable("Skills", width=120, align="l",
                                         border = "header")
                # TODO: Add active skill groups.
                active_skills = ""
                skill_list = target.db.active_skills.items() + target.db.active_skill_groups.items()
                def getkey(tuple):
                    return tuple[0]

                skill_list.sort(key=getkey)
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
                skill_list = target.db.knowledge_skills.items()
                skill_list.sort(key=getkey)

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
                skill_list = target.db.language_skills.items()
                skill_list.sort(key=getkey)

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
