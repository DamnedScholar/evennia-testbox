"""
Room

Rooms are simple containers that have no location of their own.

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
from evennia.utils.dbserialize import _SaverDict, _SaverList, _SaverSet
from sr5.data.skills import Skills
from sr5.data.ware import BuyableWare, Grades, Obvious, Synthetic
from sr5.objects import Augment, Aug_Methods


class ChargenScript(DefaultScript):
    """
    This script is placed on a character object when it is created. It holds variables relevant to the chargen process that need to be cleaned up after and it inherits the data that is important for the chargen process.
    """
    # TODO: These variables are here for testing purposes and should be broken out into a separate module for storage once the chargen is completed.
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
    meta_attr = {
        "human": {"body": (1, 6), "agility": (1, 6), "reaction": (1, 6),
                  "strength": (1, 6), "willpower": (1, 6), "logic": (1, 6),
                  "intuition": (1, 6), "charisma": (1, 6),
                  "edge": (2, 7), "magic": (0, 6), "resonance": (0, 6)},
        "elf": {"body": (1, 6), "agility": (2, 7), "reaction": (1, 6),
                  "strength": (1, 6), "willpower": (1, 6), "logic": (1, 6),
                  "intuition": (1, 6), "charisma": (3, 8),
                  "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        "dwarf": {"body": (3, 8), "agility": (1, 6), "reaction": (1, 5),
                  "strength": (3, 8), "willpower": (2, 7), "logic": (1, 6),
                  "intuition": (1, 6), "charisma": (1, 6),
                  "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        "ork": {"body": (4, 9), "agility": (1, 6), "reaction": (1, 6),
                  "strength": (3, 8), "willpower": (1, 6), "logic": (1, 5),
                  "intuition": (1, 6), "charisma": (1, 5),
                  "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        "troll": {"body": (5, 10), "agility": (1, 5), "reaction": (1, 6),
                  "strength": (5, 10), "willpower": (1, 6), "logic": (1, 5),
                  "intuition": (1, 5), "charisma": (1, 4),
                  "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        }
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

        self.reset_all()

    def reset_all(self):
        "Resets chargen."
        # Preliminary chargen stuff. Does this need to be here?
        self.db.tier = "experienced"
        self.db.priorities = {"a": "", "b": "", "c": "",
                              "d": "", "e": ""}
        self.db.karma = 25

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

    def reset_skills(self):
        "Resets skills and specializations."
        self.db.skills = {}
        self.db.skill_groups = {}
        self.db.specs = {}

    def reset_resources(self):
        "Resets lifestyle and purchases."
        self.db.lifestyle = ""
        self.db.nuyen = -1
        self.db.augments, self.db.gear = {}, {}

    def reset_qualities(self):
        "Resets qualities."
        self.db.qualities_positive = {}
        self.db.qualities_negative = {}

    def reset_vitals(self):
        "Resets name, birthdate, etc."
        self.db.fullname, self.db.birthdate = "", ""
        self.db.ethnicity, self.db.height, self.db.weight = "", "", ""

    def reset_background(self):
        "Resets background."
        self.db.background = {}

    def set_vital(self, field, value):
        pass

    def set_metatype(self, metatype):
        self.db.metatype = metatype
        self.db.spec_attr = {'edge': 0, 'magic': 0, 'resonance': 0}
        self.db.meta_attr = cg.meta_attr[metatype]

    def set_attr(self, attr, rating):
        pass

    def set_skill(self, skill, category, rating):
        # TODO: Double check whether `category` is needed.
        pass

    def set_quality(self, quality, rating):
        pass

    def set_magic_type(self, type):
        pass

    def set_tradition(self, tradition):
        pass

    def set_magic_skill(self, skill, rating):
        # TODO: Work it like normal skills.
        pass

    def set_lifestyle(self, lifestyle):
        # TODO: This will always affect nuyen.
        pass

    def set_resources(self, resources):
        # TODO: Check to see if the new resources level makes previous
        # purchases unaffordable.
        pass

    # IDEA: I should have all functions to set or retrieve stats in an
    # external class that I can mix in to both this class and the default
    # character.

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

        # TODO: Clean up this nomenclature so that it's clearer to third parties which variables refer to the stats store, which ones refer to choices the player has made, and which ones are views.

        # Metatype View
        options, names = self.metatypes[priority], []
        for option in options:
            names += [option[0]]
        # If no valid metatype is set, give options to set it.
        if self.db.metatype not in names:
            self.metatype = "At priority {0}, you have the following " \
                            "choices:\n\n".format(priority.title())
            self.metatype += "\t|h{left:<20}{right:>30}|n" \
                             "\n".format(left="Command to Set",
                             right="Metatype (Attributes, Karma)")
            for i in range(0, len(options)):
                option = options[i]
                left = "\t> meta {command}".format(command=option[0])
                right = "{name} ({sa} SA, {karma} Karma)" \
                        "\n".format(name=option[0].title(),
                        sa=option[1], karma=option[2])
                self.metatype += "{left:<20}{right:>30}".format(left=left,
                                 right=right)

            self.metatype += "\nYou can look at a metatype's stats " \
                             "with \"stat <metatype>\"."
        # If there's a valid metatype, give options to set special attributes.
        else:
            i = names.index(self.db.metatype)

            self.metatype = "As a {mt}, you have {sa} points for " \
                            "special attributes and will be charged " \
                            "{ka} karma.".format(mt=self.db.metatype,
                            sa=options[i][1],
                            ka=options[i][2])
            self.metatype += "\n\n"
            # The maximum Edge rating is one higher if the character possesses the Lucky quality.
            self.metatype += "\tEdge: {cur}/{max}\n".format(
                             cur=self.db.meta_attr["edge"][0] + self.db.spec_attr["edge"],
                             max=self.db.meta_attr["edge"][1] + self.db.qualities_positive.get("lucky", 0))
            # No character can have both Magic and Resonance. If a character has an innate Magic rating, such as the metasapients, they cannot possess Resonance.
            if self.db.meta_attr["magic"][0] or self.db.spec_attr["magic"]:
                # The maximum Magic rating is one higher if the character possesses the Exceptional Attribute (Magic) quality.
                self.metatype += "\tMagic: {cur}/{max}\n".format(
                                 cur=self.db.spec_attr["magic"],
                                 max=self.db.meta_attr["magic"][1] + self.db.qualities_positive.get("exceptional attribute (magic)", 0))
            elif self.db.meta_attr["resonance"][0] or self.db.spec_attr["resonance"]:
                # The maximum Resonance rating is one higher if the character possesses the Exceptional Attribute (Resonance) quality.
                self.metatype += "\tResonance: {cur}/{max}\n".format(
                                 cur=self.db.spec_attr["resonance"],
                                 max=self.db.meta_attr["resonance"][1] + self.db.qualities_positive.get("exceptional attribute (resonance)", 0))
            else:
                self.metatype += "\tMagic: 0/6\n" \
                                 "\tResonance: 0/6\n"

        return getattr(self, step, "We're not finding that step.")

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
        valid = cg_validate(self, self.validate, self.result_categories)
        success = write_stats()

    # TODO: Since this function will take `validate` and `result_categories`
    # on the fly, individual chargen rooms could use it to check a specific
    # category or set of stats.

    def cg_validate(self, target, validate, result_categories):
        """
        This is a dynamic chargen validation function that takes a set of
        logical rules with a simple grammar and outputs a boolean for whether
        the test passes or fails, as well as a list of individual results for
        each category.

        Possible rules for `validate`:
        stat: Identify the attribute and key that hold the value being checked.
        max: Flat number or attribute reference.
        min: Flat number or attribute reference.
        equals: Flat number or attribute reference.
        in: Take a list and check if a member of the stat is in the list.
        not in: Take a list and check if no members are in the list.
        """
        # TODO: This function will check to make sure that everything on the
        # character sheet is valid.

        # TODO: Probably have to check every single Extra and Object on the
        # Character for validate attributes as well.
        # Find out the environment

        # This dict will hold a running tally of results.
        results_list = []

        # Define parsing elements.
        # An entity is any rule or value text.
        entity = pyparsing.Word(pyparsing.alphanums + "_-.' ")
        # An arg is in the form of `rule: value`.
        arg = pyparsing.Combine(entity + ": " + entity)
        # Args are separated by commas.
        parse = arg + pyparsing.ZeroOrMore(pyparsing.Suppress(',') + arg)
        # The rule comes before the colon.
        rule = pyparsing.Combine(entity + pyparsing.Suppress(":")) + entity
        # An address is made up of substrs separated by periods.
        substr = pyparsing.Word(pyparsing.alphanums + "_-'")
        address = substr + pyparsing.OneOrMore(
            pyparsing.Suppress('.') + substr)
        # Matching for values made up of quoted strings or plain numbers.
        value_words = pyparsing.QuotedString("'", escChar="\\")
        value_num = pyparsing.Word(pyparsing.nums) ^ pyparsing.Combine(
            pyparsing.Word(pyparsing.nums) + '.' +
            pyparsing.Word(pyparsing.nums))

        for condition in validate:
            # Reset variables
            check = {}

            params = parse.parseString(condition)

            self.obj.msg("\nParams: " + str(params))

            for param in params:
                final = pyparsing.Dict(
                    pyparsing.Group(rule)).parseString(param)
                final_dict = final.asDict()
                key = final_dict.keys()[0]
                value = final_dict[key]

                selection = value_words ^ value_num.setParseAction(
                    lambda toks: int(toks[0])) ^ address.setParseAction(
                    lambda toks: tuple(list(toks))) ^ substr

                if key in ["in", "not in"]:
                    parser = pyparsing.OneOrMore(selection)
                    final_dict[key] = parser.parseString(value).asList()
                else:
                    final_dict[key] = selection.parseString(value).pop(0)

                check.update(final_dict)

            self.obj.msg("To check: " + str(check))

            # Grab a reference to the stat to be checked.
            stat = check.get("stat", None)
            # Find out which comparisons to perform.
            s = {
                "max": check.get("max", None),
                "min": check.get("min", None),
                "equals": check.get("equals", None),
                "in": check.get("in", None),
                "not in": check.get("not in", None),
                "tip": check.get("tip", ""),
                "cat": check.get("cat", "other")
            }

            def add_to_each(l, new):
                # Add the string `new` to each entry in list `l`.
                o = []
                for i in range(0, len(l)):
                    o.append(l[i] + new)

                return o

            def dig(key, lookup, dest, target, prefix="", level=0):
                """
                key: On first run, this is the attribute that contains the info
                    being checked. On recursions, this is the instance of
                    `foreach` being explored.
                lookup: This is the address leading to the `foreach` instance.
                    It will be passed in as a single-item list.
                dest: This is the remaining length of the address.

                This function will return a list to be appended to the `lookup`
                    list of the function that called it.
                """

                i = 0

                while i < len(dest):
                    try:      # Convert `dest[i]` to a number if possible.
                        loc = int(float(dest[i]))
                    except ValueError:
                        loc = dest[i]

                    i += 1
                    if loc == "foreach":
                        # Scan through all entries at the current location and
                        # add an entry to the lookup table for each of them.

                        exec "temp = {}".format(prefix + lookup[0]) in globals(), locals()
                        lookup_fork = []

                        dest = dest[i:len(dest)]

                        if isinstance(temp, (dict, _SaverDict)):
                            # If `temp` is a dict, add the key to the address
                            # string.
                            j = 0
                            for fork in temp:
                                lookup_fork.append(dig(fork,
                                    [lookup[0] + "[\'{}\']".format(fork)],
                                    dest, target, prefix, level=level + 1)
                                )
                                j += 1
                        elif isinstance(temp, (list, tuple)):
                            # If `temp` is a list or tuple, add the index to
                            # the address string.
                            for fork in range(0, len(temp)):
                                lookup_fork.append(dig(fork,
                                    [lookup[0] + "[{}]".format(fork)],
                                    dest, target, prefix, level=level + 1))
                        else:
                            # If neither of the above is true, then the
                            # `foreach` is erroneous.
                            break

                        # We're reassembling the table from scratch.
                        lookup = []
                        for i in range(0, len(lookup_fork)):
                            lookup += lookup_fork[i]

                    elif isinstance(loc, str):
                        # Add a key to every entry in the lookup table.
                        lookup = add_to_each(lookup, "[\'{}\']".format(loc))
                    elif isinstance(loc, int):
                        # Add an index to every entry in the lookup table.
                        lookup = add_to_each(lookup, "[{}]".format(loc))

                # self.obj.msg("lookup looks like {}".format(lookup))

                return lookup

            # Empty list that will be iterable.
            stat_list = []
            # Grab a reference to the stat on the target.
            target_stat = target.attributes.get(key=stat[0])
            if not target_stat:
                target_stat = target.attributes.get(key=stat)
            if "foreach" in stat:
                stat_list = target_stat.keys()
            elif isinstance(stat, (list, tuple)):
                stat_list = [stat[len(stat) - 1]]
            else:
                stat_list = [stat]

            self.obj.msg("Stat: " + str(stat))
            self.obj.msg("Target Stat: " + str(target_stat))

            validating = {}
            comparison = {}

            if isinstance(stat, tuple):
                # Default to looking at the target if no object is named.
                if stat[0].find('.') != -1:
                    prefix = ""
                else:
                    prefix = "target.db."
                lookup = dig(stat[0], [stat[0]],
                             list(stat[1:len(stat)]), target, prefix)

                for looky in lookup:
                    exec "data = " + prefix + looky in locals()

                    key_end = looky.rfind("'")
                    key_begin = looky.rfind("'", 0, key_end) + 1

                    if isinstance(data, (dict, _SaverDict)):
                        validating.update(data)
                    else:
                        validating.update(
                            {looky[key_begin:key_end].lower(): data}
                        )
            else:
                for instance in stat_list:
                    validating.update({instance: target_stat})

            for cond, addy in s.iteritems():
                if isinstance(addy, tuple):
                    # Default to looking at the target if no object is named.
                    if addy[0].find('.') != -1:
                        prefix = ""
                    else:
                        prefix = "target.db."
                    lookup = dig(addy[0], [addy[0]],
                                 list(addy[1:len(addy)]), target, prefix)

                    for looky in lookup:
                        exec "data = " + prefix + looky in locals()

                        key_end = looky.rfind("'")
                        key_begin = looky.rfind("'", 0, key_end) + 1

                        conds = comparison.get(looky[key_begin:key_end], {})
                        conds.update({cond: data})

                        comparison.update(
                            {looky[key_begin:key_end].lower(): conds}
                        )
                else:
                    for instance in stat_list:
                        conds = comparison.get(instance, {})
                        conds.update({cond: addy})
                        comparison.update({instance: conds})

            self.obj.msg("Validating {}\nComparison {}".format(validating, comparison))

            for instance in stat_list:
                to_check = validating[instance]
                s = comparison[instance]

                if not to_check:
                    results_list += [{
                        "stat": stat[0],
                        "cat": s["cat"],
                        "key": instance,
                        "what": "does not exist",
                        "tip": "Please set it."
                    }]

                    continue

                self.obj.msg("to_check: {}".format(to_check))

                # Some comparisons we want to perform require a number. Others
                # will act on a list of items.
                if isinstance(to_check, (int, float)):
                    number_check = to_check
                    list_check = [to_check]
                if isinstance(to_check, (str)):
                    number_check = 1
                    list_check = [to_check]
                elif isinstance(to_check, (dict, _SaverDict)):
                    # Sum all numerical values and make a list of the keys.
                    # Sometimes the user might want to match against the
                    # values in a dict, but in that case, they can use
                    # `foreach` to return a list.
                    number_check = 0
                    for val in to_check.values():
                        if isinstance(val, (int, float)):
                            number_check += val
                    list_check = to_check.keys()
                elif isinstance(to_check, (list, _SaverList)):
                    # Get the number of values and save list.
                    number_check = len(to_check)
                    list_check = to_check
                elif isinstance(to_check, (set, _SaverSet)):
                    # Get the number of values and convert to list.
                    number_check = len(to_check)
                    list_check = list(to_check)
                elif isinstance(to_check, tuple):
                    # Get the number of values and convert to list.
                    number_check = len(to_check)
                    list_check = list(to_check)

                # Check max.
                if isinstance(s['max'], (float, int)):
                    if number_check > s['max']:
                        results_list += [{
                            "stat": stat[0],
                            "cat": s["cat"],
                            "key": instance + " (" + str(number_check) + ")",
                            "what": "has a maximum of " + str(s['max']),
                            "tip": "" + s['tip']
                        }]
                elif s['max']:
                    results_list += [{
                        "stat": stat[0],
                        "cat": s["cat"],
                        "key": instance + " (" + str(number_check) + ")",
                        "what": "has nothing that it can be compared to",
                        "tip": "Max values should be numeric or addresses."
                    }]

                # Check min.
                if isinstance(s['min'], (float, int)):
                    if number_check < s['min']:
                        results_list += [{
                            "stat": stat[0],
                            "cat": s["cat"],
                            "key": instance + " (" + str(number_check) + ")",
                            "what": "has a minimum of " + str(s['min']),
                            "tip": "" + s['tip']
                        }]
                elif s['min']:
                    results_list += [{
                        "stat": stat[0],
                        "cat": s["cat"],
                        "key": instance + " (" + str(number_check) + ")",
                        "what": "has nothing that it can be compared to",
                        "tip": "Min values should be numeric or addresses."
                    }]

                # Check equals.
                if isinstance(s['equals'], (float, int)):
                    if number_check == s['equals']:
                        results_list += [{
                            "stat": stat[0],
                            "cat": s["cat"],
                            "key": instance + " (" + str(number_check) + ")",
                            "what": "must equal " + str(s['equals']),
                            "tip": "" + s['tip']
                        }]
                elif s['equals']:
                    results_list += [{
                        "stat": stat[0],
                        "cat": s["cat"],
                        "key": instance + " (" + str(number_check) + ")",
                        "what": "has nothing that it can be compared to",
                        "tip": "Equals values should be numeric or addresses."
                    }]

                # Check whether all members of the stat are in the list.
                if isinstance(s['in'], (list)):
                    if not set(list_check).issubset(s['in']):
                        results_list += [{
                            "stat": stat[0],
                            "cat": s["cat"],
                            "key": instance + " (" + str(list_check) + ")",
                            "what": "isn't a valid option",
                            "tip": "" + s['tip']
                        }]
                elif s['in']:
                    results_list += [{
                        "stat": stat[0],
                        "cat": s["cat"],
                        "key": instance + " (" + str(list_check) + ")",
                        "what": "has nothing that it can be compared to",
                        "tip": "\"In\" values should be a list."
                    }]

                # Check whether the stat is in the list provided.
                if isinstance(s['not in'], (list)):
                    if set(list_check).intersection(s['not in']):
                        results_list += [{
                            "stat": stat[0],
                            "cat": s["cat"],
                            "key": instance + " (" + str(list_check) + ")",
                            "what": "isn't a valid option",
                            "tip": "" + s['tip']
                        }]
                elif s['not in']:
                    results_list += [{
                        "stat": stat[0],
                        "cat": s["cat"],
                        "key": instance + " (" + str(list_check) + ")",
                        "what": "has nothing that it can be compared to",
                        "tip": "\"Not in\" values should be a list."
                    }]

        result_categories = self.result_categories
        result_header, result_text = "", ""
        ok = True
        for cats in result_categories:
            problem = False
            output = ""

            for result in results_list:
                if result["cat"] == cats.keys()[0]:
                    problem = True
                    ok = False

            if problem:
                status = "NO|n"
                color = "|r"
            else:
                status = "YES|n"
                color = "|g"

            text = "{:<20}|n{:>30}".format(
                color + cats.values()[0], color + status
            )

            output += text

            for result in results_list:
                if result["cat"] == cats.keys()[0]:
                    text = "|h" + result["key"].title() + "|n " + \
                            result["what"] + ". " + result["tip"]
                    output += "\n{:>50}".format(text)

            self.obj.msg(output + "\n")


        if ok:
            self.obj.msg("This character can be approved.")

    def write_stats(self):
        # TODO: This function will administer the process of writing data on
        # the chargen script onto the character.
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
        tag = "|Rsr5 > |n"

        self.caller.msg(tag + "You have entered character creation.")
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

        tag = "|Rsr5 > |n"

        # Break apart self.args and return errors if things aren't what they're supposed to be.
        self.priority = self.args[0].lower()
        self.category = self.args[1].lower()
        if self.priority == self.category:
            self.category = ""
        match, occupied, success = '', '', False
        if self.priority not in "abcde" or not self.priority:
            caller.msg(tag + "Please enter 'a', 'b', 'c', 'd', or 'e'.")
            return False

        if self.category and self.category in "unset":
            caller.msg(tag + "Priority {} unset.".format(self.priority.title()))
            cg.db.priorities[self.priority] = ""
            return False

        for i in range(0,len(cg.categories)):
          if self.category not in "" and self.category in cg.categories[i]:
            match = True
            self.category = cg.categories[i]
        if not match:
            caller.msg(tag + 'Please enter a valid category. Valid choices ' \
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

    # TODO: Reconsider whether the space after the command is valuable.
    key = "chargen "
    aliases = ["cg "]
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

        tag = "|Rsr5 > |n"

        if self.args and self.args in "metatype":
            cg.reset_metatype()
            caller.msg(tag + "Metatype and special attributes are reset.")
        elif self.args and self.args in "attributes":
            cg.reset_attr()
            caller.msg(tag + "Attributes are reset.")
        elif self.args and self.args in "magic" or self.args and self.args in "resonance":
            cg.reset_magres()
            caller.msg(tag + "Magic and Resonance choices are reset.")
        elif self.args and self.args in "skills":
            cg.reset_attr()
            caller.msg(tag + "Skills are reset.")
        elif self.args and self.args in "resources":
            cg.reset_attr()
            caller.msg(tag + "Resources, gear, and lifestyle choices are reset.")
        elif self.args and self.args in "qualities":
            cg.reset_attr()
            caller.msg(tag + "Qualities are reset.")
        elif self.args and self.args in "background":
            cg.reset_attr()
            caller.msg(tag + "Background cleared.")
        elif self.args and self.args in "vitals":
            cg.reset_attr()
            caller.msg(tag + "Vitals cleared.")
        elif self.args and self.args:
            caller.msg(tag + 'Please input a stage of chargen. Valid choices are "Metatype", "Attributes", "Magic", "Resonance", "Skills", "Resources", "Qualities", "Background", and "Vitals". If you want to restart chargen, type "reset" by itself.')
        else:
            # TODO: Ask for confirmation? Can I use EvMenu for a one-off prompt?
            cg.reset_all()
            caller.msg(tag + "The chargen process has been reset.")


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

        # Find out which priority this category is.
        priority = cg.db.priorities.keys()[cg.db.priorities.values().index("metatype")]

        for metatype in cg.metatypes[priority]:
            if self.args in metatype[0]:
                cg.set_metatype(metatype[0])

                caller.msg(tag + "Your metatype has been set to {mt}, at " \
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

        tag = "|Rsr5 > |n"

        # Break up the second argument into keywords.
        if len(self.args) == 2:
            options = self.args[1].split('/')
        else:
            options = ["show"]

        # Make human- and code-readable versions of `target`
        target = [options[0].lower().replace('_', ' '),
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
        if options[1] == "show" and target[1] not in buyable:
            caller.msg("List of grades: " + str(grades))
            caller.msg("List of available 'ware': " + str(buyable[umbrella]))

            return True

        # Special category-based rules. For items that don't have special
        # properties, refer to the `else` at the end of this chain.
        # TODO: All of this could be moved to the Aug_Methods() class.
        if umbrella == "cyberlimbs":
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
                caller.msg(tag + "You can't have a cyberlimb built with higher"
                           " strength than your natural maximum.")
                return False
            a = cg.db.qualities_positive.get("exceptional attribute (agility)", 0)
            if agility + 3 > cg.db.meta_attr["agility"][1] + a:
                caller.msg(tag + "You can't have a cyberlimb built with higher"
                           " agility than your natural maximum.")
                return False

            # TODO: Check to see if the cyberlimb being purchased takes up a slot
            # already occupied. If the slot is occupied by another cyberlimb,
            # replace it with this one.

            # Calculate costs.
            cost = Aug_Methods.apply_costs_and_capacity(
                Aug_Methods(), [target[1].lower()], synthetic
            )[0]
            cost = cost + (strength + agility) * 5000

            if cost > cg.db.nuyen:
                result = "You cannot afford that."
            else:
                result = "Enjoy your shiny new " + target[0] + "."
                purchased = spawner.spawn({
                    "prototype": target[1],
                    "location": caller,
                    "custom_str": strength,
                    "custom_agi": agility,
                    "synthetic": synthetic,
                    "grade": grade
                })

            # Format and print the results.
            if synthetic:
                target[0] = "synthetic " + target[0]

            caller.msg(tag + "You have placed an order for a {} with strength "
                       "+{} and agility +{} at a cost of {} nuyen. "
                       "{}".format(target[0], strength, agility, cost, result))
        elif umbrella == "headware":
            pass
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
        self.add(CmdBuyAugment())            # key: augment, aug
        # Qualities Room
        self.add(CmdSetQualities())          # key: quality, qual
