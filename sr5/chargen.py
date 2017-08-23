"""
Chargen

The script and functions that make chargen work.

"""

import math
import string
import re
import pyparsing
from evennia import CmdSet
from evennia import default_cmds
from evennia import DefaultRoom
from evennia import DefaultScript
from evennia.utils import evtable, spawner
from evennia.utils.utils import lazy_property
from sr5.msg_format import mf
from sr5.data.metatypes import Metatypes
from sr5.data.base_stats import Attr, SpecAttr
from sr5.data.skills import Skills
from sr5.data.ware import BuyableWare, Grades, Obvious, Synthetic
from sr5.objects import Augment
from sr5.system import Stats
from sr5.utils import a_n, itemize, flatten, SlotsHandler, validate, ureg


class ChargenScript(DefaultScript, Stats):
    """
    This script is placed on a character object when it is created. It holds variables relevant to the chargen process that need to be cleaned up after and it inherits the data that is important for the chargen process.
    """
    # TODO: These variables are here for testing purposes and should be broken out into a separate module for storage once the chargen is completed.
    cg_steps = ["priority", "vitals", "metatype", "attributes", "attr",
                "magic", "resonance", "qualities", "skills", "resources",
                "background", "karma"]
    categories = ["metatype", "attributes", "magic", "resonance", "skills",
                  "resources"]
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
    resources = {"a": {"street": 75000, "experienced": 450000, "prime": 500000},
                 "b": {"street": 50000, "experienced": 275000, "prime": 325000},
                 "c": {"street": 25000, "experienced": 140000, "prime": 210000},
                 "d": {"street": 15000, "experienced": 50000, "prime": 150000},
                 "e": {"street": 6000, "experienced": 6000, "prime": 100000}}

    @lazy_property
    def slots(self):
        return SlotsHandler(self)

    def priority(self, category):
        return self.db.priorities.keys()[
            self.db.priorities.values().index(category)]

    def at_script_creation(self):
        # Evennia stuff
        self.key = "chargen"
        self.desc = "Handles Character Creation"
        self.persistent = True

        self.db.essence = Ledger()
        self.db.essence.configure(self.obj, "essence", 6)
        # Don't touch the karma Ledger until the very end. Chargen will have
        # its own karma count that it uses for qualities and metatype. When the
        # player submits their sheet and locks it, then any metatype and
        # qualities will be written to the Ledger and they will be able to
        # spend karma on other stats.
        self.db.karma = Ledger()
        self.db.karma.configure(self.obj, "karma", 25)
        self.db.nuyen = Ledger()
        self.db.nuyen.configure(self.obj, "nuyen", 0)

        # Establish body slots
        self.slots.add("body", ["head", "torso", "right_upper_arm", "right_lower_arm", "right_hand", "left_upper_arm", "left_lower_arm", "left_hand", "right_upper_leg", "right_lower_leg", "right_foot", "left_upper_leg", "left_lower_leg", "left_foot"])

        self.reset_all()

    def reset_all(self):
        "Resets chargen."
        # Preliminary chargen stuff. Does this need to be here?
        self.db.tier = "experienced"
        self.db.priorities = {"a": "", "b": "", "c": "",
                              "d": "", "e": ""}

        # TODO: Can't I automate this by polling __dict__ for functions that
        # start with `reset_`?
        self.reset_metatype()
        self.reset_attr()
        self.reset_magres()
        self.reset_skills()
        self.reset_resources()
        self.reset_qualities()
        self.reset_vitals()
        self.reset_background()
    # TODO: Is it intuitive to have defaults labeled as `reset_`?

    def reset_metatype(self):
        "Resets metatype and related stats."
        self.db.metatype, self.db.metakarma = "", 0
        self.db.spec_attr = {'edge': 0, 'magic': 0, 'resonance': 0}
        self.db.meta_attr = {'body': (1, 6), 'agility': (1, 6),
                             'reaction': (1, 6), 'strength': (1, 6),
                             'willpower': (1, 6), 'logic': (1, 6),
                             'intuition': (1, 6), 'charisma': (1, 6),
                             'edge': (1, 6),
                             'magic': (0, 6), 'resonance': (0, 6)}

    def reset_attr(self):
        "Resets normal attributes."
        self.db.attr = {'body': 0, 'agility': 0, 'reaction': 0, 'strength': 0,
                        'willpower': 0, 'logic': 0, 'intuition': 0,
                        'charisma': 0}

    def reset_magres(self):
        "Resets magic type, tradition, freebie skills, and powers."
        self.db.magic_type, self.db.tradition = "", ""
        self.db.magic_skills = {}
        self.db.spells, self.db.powers, self.db.forms = [], {}, []
        # TODO: Reset specifically qualities, skills, and gear that rely on
        # this category, and inform the player about that fact.

    def reset_qualities(self):
        "Resets qualities."
        self.db.qualities_positive = {}
        self.db.qualities_negative = {}

    def reset_skills(self):
        "Resets skills and specializations."
        self.db.active_skills = {}
        self.db.active_specializations = {}
        self.db.knowledge_skills = {}
        self.db.knowledge_specializations = {}
        self.db.languages = {}
        self.db.language_specializations = {}

    def reset_resources(self):
        "Resets lifestyle and purchases."
        self.db.lifestyle = ""
        self.obj.db.nuyen.configure(self.obj, "nuyen", 0)
        self.obj.db.essence.configure(self.obj, "essence", 6)
        self.db.augments, self.db.gear = {}, {}
        # TODO: The above line is highly suspect.

    def reset_vitals(self):
        "Resets name, birthdate, etc."
        self.db.fullname, self.db.birthdate = "", ""
        self.db.ethnicity, self.db.height, self.db.weight = "", "", ""

    def reset_background(self):
        "Resets background."
        self.db.background = {}

    def at_start(self):
        """
        This initializes the back-reference and chargen cmdset on a character
        """
        self.obj.cg = self.obj.scripts.get("chargen")[0]
        self.obj.cmdset.add("sr5.chargen.ChargenCmdSet")

    # TODO: I should probably move the entirety of cgview to separate functions
    def cgview(self, step, priority):
        "Calculate the view for the user that shows a particular CG step."
        def meta(attr):
            "Local formatting function."
            return "{} ({} to {})".format(self.get_attr(attr),
                                          self.get_meta_attr(attr)[0],
                                          self.get_meta_attr(attr)[1])

        def magres(which, text):
            "Local formatting function."
            if self.get_attr(which):
                out = "{}".format(text)
            else:
                out = "|x|h{}|n".format(text)
            return out

        def spec(skills):
            "Local formatting function."
            for sk in skills:
                spec = self.get_specialization(sk)
                if spec:
                    pop = skills.pop(sk)
                    skills.update({"{} ({})".format(sk, spec): pop})

            return skills

        if step in "priorities":
            title = "Priorities"
            output = "You've set the following priorities:\n\n" \
                     "A: {a}\nB: {b}\nC: {c}\nD: {d}\nE: {e}".format(
                        a=self.db.priorities["a"].title(),
                        b=self.db.priorities["b"].title(),
                        c=self.db.priorities["c"].title(),
                        d=self.db.priorities["d"].title(),
                        e=self.db.priorities["e"].title()
                      )
        elif step in "metatypes":
            # Metatype View
            title = "Metatype"
            options, names = Metatypes.priorities[priority], []
            for option in options:
                names += [option[0]]
            # If no valid metatype is set, give options to set it.
            if self.db.metatype not in names:
                output = "At priority {0}, you have the following " \
                         "choices:\n\n".format(priority.title())
                output += "\t|h{left:<20}{right:>30}|n" \
                          "\n".format(left="Command to Set",
                                      right="Metatype (Attributes, Karma)")
                for i in range(0, len(options)):
                    option = options[i]
                    left = "\t> meta {command}".format(command=option[0])
                    right = "{name} ({sa} SA, {karma} Karma)" \
                            "\n".format(name=option[0].title(),
                                        sa=option[1], karma=option[2])
                    output += "{left:<20}{right:>30}".format(left=left,
                                                             right=right)

                output += "\nYou can look at a metatype's stats " \
                          "with \"stat <metatype>\"."
            # If there's a valid metatype, give options to set
            # special attributes.
            else:
                title = "Metatype -> Special Attributes"
                i = names.index(self.db.metatype)
                current = self.db.spec_attr
                total = sum(current.values())

                output = "As {mt}, you have {sa} points for " \
                         "special attributes ({sp} spent) and will be " \
                         "charged {ka} karma.".format(
                            mt=a_n(self.db.metatype),
                            sa=options[i][1], sp=total,
                            ka=options[i][2])
                output += "\n\n"
                table = evtable.EvTable(border=None, width=70)
                table.add_column(
                    "Edge:", magres("magic", "Magic:"),
                    magres("resonance", "Resonance:"),
                    align="r"
                )
                table.add_column(
                    meta("edg"), magres("magic", meta("mag")),
                    magres("resonance", meta("res")),
                    align="l"
                )
                output += str(table)
        elif step in "attr":
            # Attributes View
            title = "Attributes"
            current = self.db.attr
            points, total = Attr.priorities[priority], sum(current.values())

            output = "You have {} points available for attributes at " \
                     "priority {} ({} spent).".format(
                        points, priority.title(), total)
            if total > points:
                output += " You have spent more points than you have " \
                             "available. Please reduce some of your " \
                             "attributes to bring yourself in line."
            output += "\n\n"
            table = evtable.EvTable(border=None, width=70)
            table.add_column(
                "|hPhysical|n",
                "Body:", "Agility:", "Reaction:", "Strength:",
                align="r"
            )
            table.add_column(
                "",
                meta("bod"), meta("agi"),
                meta("rea"), meta("str"),
                align="l"
            )
            table.add_column(
                "|hMental|n",
                "Willpower:", "Logic:", "Intuition:", "Charisma:",
                align="r"
            )
            table.add_column(
                "",
                meta("wil"), meta("log"),
                meta("int"), meta("cha"),
                align="l"
            )
            table.add_column(
                "|hLimits|n",
                "Physical:", "Mental:", "Social:",
                align="r"
            )
            table.add_column(
                "",
                self.physical_limit(), self.mental_limit(),
                self.social_limit(),
                align="l"
            )

            output += str(table)
        elif step in "magres":
            # Magres View
            title = "Magic/Resonance"
            output = "You have arrived at the CG step for Magic/Resonance. " \
                     "Well, let me tell you, that shit is a pain in the " \
                     "ass. The Magic/Resonance step will be implemented " \
                     "after literally everything else. In the mean time, " \
                     "set the priority to E, because you can't use this " \
                     "step right now."
        elif step in "qualities":
            # Qualities View
            title = "Qualities"
            positive = self.get_qualities("positive")
            negative = self.get_qualities("negative")
            pos, neg = 0, 0
            for qual, rank in positive.items():
                pos += self.query_qualities(qual)['rank'][rank - 1]
            for qual, rank in negative.items():
                neg += self.query_qualities(qual)['rank'][rank - 1]
            current = self.db.karma.value - pos + neg

            output = "In character creation, you begin with {} karma " \
                     "and can take up to 25 karma worth of positive " \
                     "qualities and up to 25 karma worth of negative " \
                     "qualities.".format(self.db.karma.initial)
            if current < 0:
                output += " |rYou have spent more karma than you have " \
                          "available. Please take on negative qualities " \
                          "or remove some positive ones.|n"
            if pos > 25:
                output += " |rYou have spent more karma on positive " \
                          "qualities than permitted. You will not be " \
                          "permitted to submit your character sheet " \
                          "until you remove some.|n"
            if neg > 25:
                output += " |rYou have gained more karma from negative " \
                          "qualities than permitted. You will not be " \
                          "permitted to submit your character sheet " \
                          "until you remove some.|n"
            output += "\n\n"
            table = evtable.EvTable("Positive: " + str(pos),
                                    border="header", width=70)
            table.add_row(itemize(flatten(positive), case="title"))
            output += unicode(table) + "\n\n"
            table = evtable.EvTable("Negative: " + str(neg),
                                    border="header", width=70)
            table.add_row(itemize(flatten(negative), case="title"))
            output += unicode(table)
        elif step in "skills":
            # Skills View
            title = "Skills"
            active = self.get_skills("active")
            active_specs = self.db.active_specializations
            group = self.get_skills("group")
            knowledge = self.get_skills("knowledge")
            knowledge_specs = self.db.knowledge_specializations
            language = self.get_skills("language")
            language_specs = self.db.language_specializations
            points, group_points = Skills.priorities[priority]
            know_points = (self.get_attr("int") + self.get_attr("log")) * 2
            # Knowledge and language points come from the same pool, but we're
            # keeping the totals separate.
            act_total =  sum(active.values()) + len(active_specs)
            group_total = sum(group.values())
            know_total = sum(knowledge.values()) + len(knowledge_specs)
            lang_total = sum(language.values()) + len(language_specs)

            output = "At priority {}, you begin with {} points to spend on " \
                     "active skills and {} to spend on active skill groups. " \
                     "A specialization costs 1 skill point, and you can't " \
                     "have a skill group including any skill in which you " \
                     "possess a specialization.\n\n" \
                     "With Intuition {} and Logic {}, you have {} points to " \
                     "spend on knowledge and language skills.".format(
                        priority.title(), points, group_points,
                        self.get_attr("int"), self.get_attr("log"),
                        know_points)
            if points - act_total < 0:
                output += " |rYou have spent more skill points than you " \
                          "have available. Please take on negative " \
                          "qualities or remove some positive ones.|n"
            output += "\n\n"
            table = evtable.EvTable("Active: " + str(act_total),
                                    border="header", width=70)
            table.add_row(itemize(flatten(spec(active)), case="title"))
            output += unicode(table) + "\n\n"
            table = evtable.EvTable("Groups: " + str(group_total),
                                    border="header", width=70)
            table.add_row(itemize(flatten(group), case="title"))
            output += unicode(table) + "\n\n"
            table = evtable.EvTable("Knowledge: " + str(know_total),
                                    border="header", width=70)
            table.add_row(itemize(flatten(spec(knowledge))))
            output += unicode(table) + "\n\n"
            table = evtable.EvTable("Language: " + str(lang_total),
                                    border="header", width=70)
            table.add_row(itemize(flatten(language)))
            output += unicode(table)
        elif step in "lifestyle resources":
            # Lifestyle and Resources View
            title = "Lifestyle and Resources"
            pass
        else:
            title = "OMG what"
            output = "We're not finding that step."

        return "{}\n\n{}\n{}".format(mf.header(title), output, mf.header())

    # Stats are validated through a series of if and for statements passed in
    # a dict. They can be passed two statements deep (this could be expanded
    # to allow deeper nesting, but that is probably not necessary).
    validate = [
        "stat: attr.foreach, max: meta_attr.foreach.1,"
        "min: meta_attr.foreach.0, not in: alabama reflexes, cat: attr,"
        "tip: 'Please tweak your attributes.'",
        "stat: tradition, in: shaman hermetic, not in: zoroastrian, cat: magres"
    ]
    result_categories = [
        {"attr": "Attributes"},
        {"magres": "Magic/Resonance"},
        {"skills": "Skills"},
        {"qual": "Qualities"},
        {"life": "Resources/Lifestyle"},
        {"other": "Other"}
    ]

    def cg_complete(self):
        # TODO: This function will run the validation, run the write function,
        # and then destroy this script if everything executes successfully.
        valid = validate(self, self.validate, self.result_categories)
        # success = write_stats()

        if valid[0]:    # You're approved!
            self.obj.msg(valid[1])
        else:           # Your sheet needs work.
            self.obj.msg(valid[1])

    def write_stats(self):
        # TODO: This function will administer the process of writing data on
        # the chargen script onto the character. This function will convert
        # any chargen-only values to the permanent ones to go on the character.
        pass


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


class CmdCGStart(default_cmds.MuxCommand):
    # TODO: Probably delete this.

    key = "cgstart"
    aliases = ["cg"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def func(self):

        self.caller.msg(mf.tag + "You have entered character creation.")
        self.caller.scripts.delete(key="chargen")
        self.caller.scripts.add("sr5.chargen.ChargenScript")


class CmdSetPriority(default_cmds.MuxCommand):
    """
    Sets your priorities in chargen. You must set each of priorities A through E to one of 'Metatype', 'Attributes', 'Magic', 'Resonance', 'Skills', and 'Resources'. The command will match partials, and both "Magic" and "Resonance" are valid names for the third column.

    Usage:
        priority a = metatype
        priority b=mag
        priority b reson
        pri e resources
        pri a = unset
    """

    key = "priority"
    aliases = ["pri"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def parse(self):
        # Take a command with two arguments and optional spaces and equals signs and render it down into two arguments.
        self.args = self.args.strip()
        self.args = self.args.replace('=', ' ')
        self.dump = self.args.split(' ')
        self.args = [self.dump[0], self.dump[len(self.dump) - 1]]

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        # Break apart self.args and return errors if things aren't what they're supposed to be.
        self.priority = self.args[0].lower()
        self.category = self.args[1].lower()
        if self.priority == self.category:
            self.category = ""
        match, occupied, success = '', '', False
        if self.priority not in "abcde" or not self.priority:
            caller.msg(mf.tag + "Please enter 'a', 'b', 'c', 'd', or 'e'.")
            return False

        if self.category and self.category in "unset":
            caller.msg(mf.tag + "Priority {} unset.".format(self.priority.title()))
            cg.db.priorities[self.priority] = ""
            return False

        for i in range(0,len(cg.categories)):
          if self.category not in "" and self.category in cg.categories[i]:
            match = True
            self.category = cg.categories[i]
        if not match:
            caller.msg(mf.tag + 'Please enter a valid category. Valid choices ' \
                       'are "Metatype", "Attributes", "Magic", "Resonance", ' \
                       '"Skills", and "Resources".')
            return False
        # Check to see if something's already in that priority slot.
        former = cg.db.priorities[self.priority]
        if former and former is not self.category:
            occupied = ' and category "' + former.title() + '" removed'

        # Check to see if the category's on the list. "Magic" and "Resonance" are synonymous for this step, so they remove each other.
        self.existing = cg.db.priorities.items()
        for i in range(0,len(self.existing)):
            if self.category in self.existing[i][1] or self.category in "magic" and "resonance" in self.existing[i][1] or self.category in "resonance" and "magic" in self.existing[i][1]:
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
            caller.msg(mf.tag + 'Category "' + self.category.title() + '" set as priority ' + self.priority.title() + occupied + '.')
        elif self.operation == "replace":
            caller.msg(mf.tag + 'Category "' + self.category.title() + '" changed to priority ' + self.priority.title() + occupied + '.')


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

        step, match, priority = '', False, ''

        # Check if the args match a CG step.
        for i in range(0, len(cg.cg_steps)):
            if self.args in cg.cg_steps[i]:
                match = True
                step = cg.cg_steps[i]

        if not match:
            caller.msg(mf.tag + "Please select a valid step of CG.")
            return False

        # Check if a priority has been set for that CG step.
        for pri, cat in cg.db.priorities.items():
            if step in cat:
                priority = pri
        if not priority and step in "priority priorities":
            priority = "a"
            step = "priorities"
        elif not priority and step in "quality qualities":
            priority = "a"
            step = "qualities"
        elif not priority:
            caller.msg(mf.tag + "You have to set a priority for it first.")
            return False

        if step in "attributes attrs":
            step = "attr"
        elif step in "magic resonance":
            step = "magres"
        elif step in "quality":
            step = "qualities"

        caller.msg(cg.cgview(step, priority))


class CmdCGReset(default_cmds.MuxCommand):
    """
    Resets character creation.

    Usage:
    > reset
    > reset metatype
    """

    key = "reset"
    lock = "cmd:perm(unapproved) and attr(cg.db.metatype)"
    help_category = "Chargen"

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        # TODO: This could probably be abstracted like with the validator.

        if self.args and self.args in "metatype":
            cg.reset_metatype()
            caller.msg(mf.tag + "Metatype and special attributes are reset.")
        elif self.args and self.args in "attributes":
            cg.reset_attr()
            caller.msg(mf.tag + "Attributes are reset.")
        elif self.args and self.args in "magic" or self.args and self.args in "resonance":
            cg.reset_magres()
            caller.msg(mf.tag + "Magic and Resonance choices are reset.")
        elif self.args and self.args in "skills":
            cg.reset_attr()
            caller.msg(mf.tag + "Skills are reset.")
        elif self.args and self.args in "resources":
            cg.reset_attr()
            caller.msg(mf.tag + "Resources, gear, and lifestyle choices are reset.")
        elif self.args and self.args in "qualities":
            cg.reset_attr()
            caller.msg(mf.tag + "Qualities are reset.")
        elif self.args and self.args in "background":
            cg.reset_attr()
            caller.msg(mf.tag + "Background cleared.")
        elif self.args and self.args in "vitals":
            cg.reset_attr()
            caller.msg(mf.tag + "Vitals cleared.")
        elif self.args and self.args:
            caller.msg(mf.tag + 'Please input a stage of chargen. Valid choices are "Metatype", "Attributes", "Magic", "Resonance", "Skills", "Resources", "Qualities", "Background", and "Vitals". If you want to restart chargen, type "reset" by itself.')
        else:
            # TODO: Ask for confirmation? Can I use EvMenu for a one-off prompt?
            cg.reset_all()
            caller.msg(mf.tag + "The chargen process has been reset.")


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

        # Find out which priority this category is.
        priority = cg.priority("metatype")

        for metatype in Metatypes.priorities[priority]:
            if self.args in metatype[0]:
                cg.set_metatype(metatype[0])

                caller.msg(mf.tag + "Your metatype has been set to {mt}, at " \
                           "a cost of {ka} karma. You now have {sa} points " \
                           "to distribute among special attributes.".format(
                           mt=metatype[0], sa=metatype[1], ka=metatype[2]))


class CmdSetSpecAttr(default_cmds.MuxCommand):
    """
    Sets your special attributes. The attribute field will match partials.

    Usage:
    > sa magic 2
    > specattr mag = 2
    """

    key = "specattr"
    aliases = ["sa"]
    lock = "cmd:perm(unapproved) and attr(cg.db.metatype)"
    help_category = "Chargen"

    def parse(self):
        # Take a command with two arguments and optional spaces and equals
        # signs and render it down into two arguments.
        self.args = self.args.strip()
        self.args = self.args.replace('=', ' ')
        self.dump = self.args.split(' ')
        self.args = [self.dump[0], self.dump[len(self.dump) - 1]]

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        priority = ""

        # Find out which priority this category is.
        for pri, cat in cg.db.priorities.items():
            if "metatype" in cat:
                priority = pri

        if not priority:
            caller.msg(mf.tag + "You must set a priority first.")
            return False

        try:
            rating = int(self.args[1])
        except ValueError:
            caller.msg(mf.tag + "You must enter a number.")
            return False

        for stat in SpecAttr.names:
            if self.args[0] in stat or self.args[0] in SpecAttr.names[stat]:
                diff = rating - cg.get_attr(stat)
                total = sum(cg.db.spec_attr.values()) + diff
                # remainder = Metatypes.priorities[priority][0] - total
                remainder = 6

                if remainder >= 0:
                    attempt = cg.set_attr(stat, rating)
                else:
                    caller.msg(mf.tag + "You have insufficient points left.")
                    return False

                if attempt[0] == False:
                    caller.msg(mf.tag + str(attempt))
                else:
                    caller.msg(mf.tag + "{} has been set to {}. You have {} "
                               "points left.".format(stat.title(),
                                                     self.args[1], remainder))


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

    def parse(self):
        # Take a command with two arguments and optional spaces and equals
        # signs and render it down into two arguments.
        self.args = self.args.strip()
        self.args = self.args.replace('=', ' ')
        self.dump = self.args.split(' ')
        self.args = [self.dump[0], self.dump[len(self.dump) - 1]]

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        priority = ""

        # Find out which priority this category is.
        for pri, cat in cg.db.priorities.items():
            if "attr" in cat:
                priority = pri

        if not priority:
            caller.msg(mf.tag + "You must set a priority first.")
            return False

        try:
            rating = int(self.args[1])
        except ValueError:
            caller.msg(mf.tag + "You must enter a number.")
            return False

        for stat in Attr.names:
            if self.args[0] in stat or self.args[0] in Attr.names[stat]:
                diff = rating - cg.get_attr(stat)
                total = sum(cg.db.attr.values()) + diff
                remainder = Attr.priorities[priority] - total

                if remainder >= 0:
                    attempt = cg.set_attr(stat, rating)
                else:
                    caller.msg(mf.tag + "You have insufficient points left.")
                    return False

                if attempt[0] == False:
                    caller.msg(mf.tag + str(attempt))
                else:
                    caller.msg(mf.tag + "{} has been set to {}. You have {} "
                               "points left.".format(stat.title(),
                                                     self.args[1], remainder))


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

    def parse(self):
        # Take a command with two arguments and optional spaces and equals
        # signs and render it down into two arguments.
        self.args = self.args.strip()
        self.args = self.args.replace('=', ' ')
        self.dump = self.args.split(' ')
        self.args = [self.dump[0], self.dump[len(self.dump) - 1]]

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        priority = ""

        # Find out which priority this category is.
        for pri, cat in cg.db.priorities.items():
            if "skill" in cat:
                priority = pri

        if not priority:
            caller.msg(mf.tag + "You must set a priority first.")
            return False

        try:
            rating = int(self.args[1])
        except ValueError:
            caller.msg(mf.tag + "You must enter a number.")
            return False

        lists = cg.available_skills()

        for cat, l in lists.items():
            for s in l:
                if self.args[0] in s:
                    name = s
                    if cat == "active":
                        points = Skills.priorities[priority][0]
                        specs = len(cg.db.active_specializations)
                        spent = sum(cg.get_skills("active").values()) + specs
                    elif cat == "groups":
                        name = "group " + s
                        points = Skills.priorities[priority][1]
                        spent = sum(cg.get_skills("group").values())
                    elif cat in ["knowledge", "language"]:
                        know = cg.get_skills("knowledge").values()
                        lang = cg.get_skills("language").values()
                        lang = lang.remove(lang.index("N"))
                        specs = len(cg.db.knowledge_specializations) + len(cg.db.language_specializations)
                        points = cg.get_attr("int") + cg.get_attr("log")
                        spent = sum(know + lang) + specs
                    if spent > points:
                        caller.msg(mf.tag + "You have spent {} out of {} "
                                   "points on {} skills.".format(
                                        spent, points, cat))
                        return False
                    attempt = cg.set_skill(s, rating)

                    caller.msg(mf.tag + "Skill {} set to {}.".format(
                        name, rating))

                    return True


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

    def parse(self):
        # Take a command with two arguments and optional spaces and equals
        # signs and render it down into two arguments.
        self.args = self.args.strip()
        self.args = self.args.replace('=', ' ')
        self.args = self.args.replace('.', ' ')
        self.dump = self.args.split(' ')
        self.args = [self.dump[0], self.dump[len(self.dump) - 1]]

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        priority = ""

        # Find out which priority this category is.
        for pri, cat in cg.db.priorities.items():
            if "skill" in cat:
                priority = pri

        if not priority:
            caller.msg(mf.tag + "You must set a priority first.")
            return False

        if not self.args[1] or self.args[1] == "unset":
            mode = "unset"
        else:
            mode = "set"

        lists = cg.available_skills()

        for cat, l in lists.items():
            for s in l:
                if self.args[0] in s:
                    name = s
                    if cat == "active":
                        points = Skills.priorities[priority][0]
                        specs = len(cg.db.active_specializations)
                        spent = sum(cg.get_skills("active").values()) + specs
                    elif cat == "groups":
                        name = "group " + s
                        caller.msg(mf.tag + "You can't set a specialization "
                                   "for a group.")
                        return False
                    elif cat in ["knowledge", "language"]:
                        know = cg.get_skills("knowledge").values()
                        lang = cg.get_skills("language").values()
                        lang = lang.remove(lang.index("N"))
                        specs = len(cg.db.knowledge_specializations) + len(cg.db.language_specializations)
                        points = cg.get_attr("int") + cg.get_attr("log")
                        spent = sum(know + lang) + specs
                    if mode == "set":
                        if spent > points:
                            caller.msg(mf.tag + "You have spent {} out of {} "
                                       "points on {} skills.".format(
                                            spent, points, cat))
                            return False
                        attempt = cg.set_specialization(s, self.args[1])

                        caller.msg(mf.tag + "Spec {} added to {}.".format(
                            self.args[1], name))

                        return True
                    elif mode =="unset":
                        attempt = cg.unset_specialization(s)

                        caller.msg(mf.tag + "Spec {} removed from {}.".format(
                            self.args[1], name))

                        return True


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

        caller.msg("This command isn't in place yet.")


class CmdCGInventory(default_cmds.MuxCommand):
    """
    Chargen inventory

    Usage:
      inventory
      inv

    Shows your inventory.
    """
    key = "inventory"
    aliases = ["inv", "i"]
    locks = "cmd:all()"
    arg_regex = r"$"

    def func(self):
        """check inventory"""
        items = self.caller.contents
        if not items:
            string = "You are not carrying anything."
        else:
            table = evtable.EvTable(border="header")
            for item in items:
                table.add_row("|C%s|n" % item.name, item.db.desc or "")
            string = "|wYou are carrying:\n%s" % table
        self.caller.msg(string)


class CmdBuyAugment(default_cmds.MuxCommand):
    """
    Buy augments in character creation. This system needs to be figured out.

    Usage:
    > augment cyberlimb=left foot/synthetic/strength 2
    > aug cyberlimb=skull
    """

    key = "augment"
    aliases = ["aug"]
    lock = "cmd:perm(unapproved)"
    help_category = "Chargen"

    def parse(self):
        # Take a command with two arguments and optional spaces and equals
        # signs and render it down into two arguments.
        self.args = self.args.strip()
        if self.args.find('=') == -1:
            self.args = 'blank =' + self.args
        self.args = self.args.split('=', 1)
        for i in range(0, len(self.args)):
            self.args[i] = self.args[i].strip()

        # TODO: Figure out a unified parse().

    def func(self):
        "Active function."
        caller = self.caller
        cg = caller.cg

        # Break up the second argument into keywords.
        if len(self.args) == 2:
            options = self.args[1].split('/')
        else:
            options = ["show"]

        # Make human- and code-readable versions of `target`
        target = [options[0].lower(),
                  options[0].upper().replace(' ', '_')]

        # Grab the list of available things to be purchased.
        buyable = BuyableWare.__dict__

        # Here we determine which category of things the target is in, if the
        # category hasn't been provided.
        umbrella = self.args[0]
        if umbrella == "blank":
            # Search through the buyable lists until `target` matches
            # something, then set `umbrella` accordingly.
            for category in buyable:
                if target[1] in buyable[category]:
                    umbrella = category
                    break
            if umbrella == "blank":
                # TODO: Present a list of valid categories and items in them.
                caller.msg("You have to choose a valid category or an item that exists in one of the valid categories. List to come soon.")

                return False

        grades = Grades.__dict__.keys()
        if "show" in options and target[1] not in buyable:
            caller.msg("List of grades: " + str(grades))
            caller.msg("List of available 'ware': " + str(buyable[umbrella]))

            return True

        # Special category-based rules. For items that don't have special
        # properties, refer to the `else` at the end of this chain.
        # TODO: All of this could be moved to the Augment() class.
        if umbrella in ["cyberlimbs", "cyberlimb", "cyberarm", "cyberleg",
                        "cyberhead", "cyberskull", "cybertorso", "cyberhand",
                        "cyberfoot"]:
            # Define options.
            strength = 0
            agility = 0
            synthetic = False
            grade = "standard"

            for i in range(0, len(options)):
                if options[i] == "synthetic":
                    synthetic = True
                elif options[i] == "obvious":
                    synthetic = False
                elif options[i] in grades:
                    grade = options[i]
                else:
                    if "strength" in options[i]:
                        strength = int(float(options[i].split(' ')[1]))
                    if "agility" in options[i]:
                        agility = int(float(options[i].split(' ')[1]))

            s = cg.db.qualities_positive.get("exceptional attribute (strength)", 0)
            if strength + 3 > cg.db.meta_attr["strength"][1] + s:
                caller.msg(mf.tag + "You can't have a cyberlimb built with higher"
                           " strength than your natural maximum.")
                return False
            a = cg.db.qualities_positive.get("exceptional attribute (agility)", 0)
            if agility + 3 > cg.db.meta_attr["agility"][1] + a:
                caller.msg(mf.tag + "You can't have a cyberlimb built with higher"
                           " agility than your natural maximum.")
                return False

            # TODO: Check to see if the cyberlimb being purchased takes up a slot
            # already occupied. If the slot is occupied by another cyberlimb,
            # replace it with this one.

            # Calculate costs.
            cost = Augment.apply_costs_and_capacity(
                [target[1].lower()], synthetic)[0]
            cost = cost + (strength + agility) * 5000

            if cost > cg.db.nuyen.value:
                result = "You cannot afford that."

                if synthetic:
                    target[0] = "synthetic {}".format(target[0])
            else:
                result = "Enjoy your shiny new " + target[0] + "."
                purchased = spawner.spawn({
                    "prototype": target[1],
                    "location": caller,
                    "custom_str": strength,
                    "custom_agi": agility,
                    "synthetic": synthetic,
                    "grade": grade
                })[0]

                # Try to attach the new cyberlimb in its slots.
                attach = cg.slots.attach(purchased)

                if attach[0] is False:
                    purchased.delete()
                    caller.msg(mf.tag + attach[1])
                    return False

                if synthetic:
                    target[0] = "synthetic {}".format(target[0])
                target[0] += " ({})".format(grade)

                # Record expenditures and store the AccountingIcetray entries
                # on the purchased object for easy reference later on.
                purchased.db.nuyen_logs = cg.db.nuyen.record(0 - cost, "Purchased " + target[0])
                purchased.db.essence_logs = cg.db.essence.record(
                    0 - purchased.db.essence, target[0].capitalize()
                )

            caller.msg(mf.tag + "You have placed an order for a {} with strength "
                       "+{} and agility +{} at a cost of {} nuyen and "
                       "{} essence. {}".format(target[0], strength, agility,
                                               cost, purchased.db.essence,
                                               result))
        elif umbrella == "headware":
            pass
        elif umbrella == "sell":
            subject = caller.search(target[0])
            if isinstance(subject, list):
                caller.msg(mf.tag + "You seem to have multiple items that fit the description given. You should use more specific language.")

                return False
            elif not isinstance(subject, Augment):
                caller.msg(mf.tag + "That doesn't appear to be an augment.")

                return False
            else:
                nuyen = 0 - subject.db.nuyen_logs[0].value
                essence = 0 - subject.db.essence_logs[0].value
                subject.db.nuyen_logs[0].delete()
                subject.db.nuyen_logs[1].delete()
                subject.db.essence_logs[0].delete()
                subject.db.essence_logs[1].delete()
                subject.delete()

                cg.db.nuyen.value += nuyen
                cg.db.essence.value += essence

                caller.msg(mf.tag + "The {} was returned to the store and {} nuyen and {} essence were refunded.".format(subject, nuyen, essence))
        else:
            # This is for items that don't have special creation rules.
            pass


class CmdSetQualities(default_cmds.MuxCommand):
    """
    Sets your qualities. The quality field will match partials. If you enter
    a number above the maximum level for the quality, the highest level of the
    quality will be entered. Qualities with multiple forms are most likely
    split into individual entries, so make sure to check them first.

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

        caller.msg("This command isn't in place yet.")


class ChargenCmdSet(CmdSet):
    """
    This is the cmdset available to the Player at all times. It is
    combined with the `CharacterCmdSet` when the Player puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """
    key = "Chargen"
    priority = 10

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdSetPriority())           # key: priority, pri
        self.add(CmdCGRoom())                # key: chargen, cg
        self.add(CmdCGReset())               # key: chargen, cg
        # Metatype Room
        self.add(CmdSetMetatype())           # key: metatype, meta
        self.add(CmdSetSpecAttr())           # key: specattr, sa
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
        self.add(CmdCGInventory())           # key: inventory, inv, i
        self.add(CmdBuyAugment())            # key: augment, aug
        # Qualities Room
        self.add(CmdSetQualities())          # key: quality, qual
