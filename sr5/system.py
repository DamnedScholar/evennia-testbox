"""
System

This file contains the code that describes how the game system works.

"""

import math
import string
import re
import pyparsing
from collections import OrderedDict
from dateutil import parser
from evennia import DefaultObject
from fuzzywuzzy import process
from sr5.utils import parse_subtype, purge_empty_values, StatMsg, ureg
from sr5.data.metatypes import Metatypes
from sr5.data.base_stats import Attr, SpecAttr
from sr5.data.skills import Skills
from sr5.data.qualities import NegativeQualities, PositiveQualities

# TODO: Implement default modifiers here.
#   * Each point of Essence loss (rounded up) reduces Magic by 1 (SR5 p. 278)
#   * Limits?


class Stats:
    def set_vital(self, field, value):
        "Attempt to set a vitals field, then return `(bool, string)`."
        field = field.lower()
        if field in ["fullname", "ethnicity"]:
            self.attributes.add(field, value)
        elif field in ["birthdate"]:
            try:
                self.db.birthdate = str(parser.parse(value).date())
            except:
                return StatMsg(False, "That date isn't recognized.")
        elif field in ["height"]:
            value = value.lower()
            units = ["in", "ft", "cm", "'", "\""]
            mag = pyparsing.Word(pyparsing.nums + ".")
            unit = pyparsing.ZeroOrMore(pyparsing.Suppress(" ")) + pyparsing.Word(pyparsing.alphas + "'\"")
            measure = mag + unit + pyparsing.ZeroOrMore(mag + unit)

            height = measure.parseString(value)

            result, ft2cm, in2cm = [], 0, 0

            if len(height) >= 2:
                if height[1] in units:
                    height[0] = float(height[0])
                    if height[1] in "'":
                        height[1] = "ft"
                    ft2cm += height[0] * ureg(height[1])
                    ft2cm = ft2cm.to(ureg.centimeter)
            if len(height) >= 4:
                if height[3] in units:
                    height[2] = float(height[2])
                    if height[3] in '"':
                        height[3] = "in"
                    in2cm += height[2] * ureg(height[3])
                    in2cm = in2cm.to(ureg.centimeter)

            result = ft2cm + in2cm

            self.db.height = "{:~}".format(result)
        elif field in ["weight"]:
            value = value.lower()
            units = ["kg", "kilos", "g", "lb", "lbs", "st", "stone", "#", "oz"]
            mag = pyparsing.Word(pyparsing.nums + ".")
            measure = mag + pyparsing.ZeroOrMore(pyparsing.Suppress(" ")) + pyparsing.Word(pyparsing.alphas)

            weight = measure.parseString(value)

            if weight[1] in units:
                weight[0] = float(weight[0])
                result = weight[0] * ureg(weight[1])
                result = result.to(ureg.kilogram)
                self.db.weight = "{:~}".format(result)

    def set_metatype(self, metatype):
        "Attempt to set a metatype, then return `(bool, string)`."
        metatype = metatype.lower()
        if metatype not in Metatypes.available:
            return StatMsg(False, "Metatype {} is not available at this time".format(
                    metatype.title()))

        self.db.metatype = metatype
        self.db.spec_attr = {'edge': 1, 'magic': 0, 'resonance': 0}
        self.db.meta_attr = Metatypes.meta_attr[metatype]

        return StatMsg(True, "Metatype {} set.".format(metatype.title()))

    def resolve_attr(self, attr):
        """
        Shadowrun attributes will often be written as three-letter short forms.
        This function will expand the short name to the long one to allow for
        easier matching.
        """

        for name in sorted(Attr.names.keys() + SpecAttr.names.keys()):
            if attr in name:
                return name
        return False

    def set_attr(self, attr, rating):
        "Attempt to set an attribute, then return `(bool, string)`."
        if not isinstance(attr, str):
            return StatMsg(False, "The attribute must be a string.")
        if not isinstance(rating, int):
            try:
                rating = int(rating)
            except ValueError:
                return StatMsg(False, "Attribute ratings must be numbers.")
        attr = attr.lower()

        if attr in self.db.attr.keys():
            bounds = list(self.db.meta_attr[attr])
            boost = ""
            # Check for cap bonuses.
            if self.get_quality("exceptional attribute ({})".format(attr)):
                bounds[1] += 1
                boost = " (plus Exceptional Attribute)"

            if rating < bounds[0]:
                return StatMsg(False, "You can't set this attribute below your"
                               " metatype{} minimum of {}".format(
                                    boost, bounds[0]))
            elif rating > bounds[1]:
                return StatMsg(False, "You can't set this attribute above your"
                               " metatype{} maximum of {}".format(
                                    boost, bounds[1]))
            else:
                # Separate the metatype base from the rating and save.
                rating = rating - bounds[0]
                self.db.attr.update({attr: rating})

                return StatMsg(True, "No error.")

        if attr in self.db.spec_attr.keys():
            bounds = list(self.db.meta_attr[attr])
            boost = ""
            # Check for cap bonuses.
            if self.get_quality("exceptional attribute ({})".format(attr)):
                bounds[1] += 1
                boost = " (plus Exceptional Attribute)"
            elif self.get_quality("Lucky") and attr is "edge":
                bounds[1] += 1
                boost = " (plus Lucky)"

            if rating < bounds[0]:
                return StatMsg(False, "You can't set this attribute below your"
                               " metatype{} minimum of {}".format(
                                    boost, bounds[0]))
            elif rating > bounds[1]:
                return StatMsg(False, "You can't set this attribute above your"
                               " metatype{} maximum of {}".format(
                                    boost, bounds[1]))
            else:
                # Separate the metatype base from the rating and save.
                rating = rating - bounds[0]
                self.db.spec_attr.update({attr: rating})

                return StatMsg(True, "No error.")

    def get_attr(self, attr):
        "Return the character's attributes."
        for entry in Attr.names:
            if attr in entry or attr in Attr.names[entry]:
                return self.db.meta_attr[entry][0] + self.db.attr[entry]
        for entry in SpecAttr.names:
            if attr in entry or attr in SpecAttr.names[entry]:
                return self.db.meta_attr[entry][0] + self.db.spec_attr[entry]

        return False

    def get_meta_attr(self, attr):
        "Return the character's metatype's attribute bounds."
        # "agi" matches "magic" by default, so let's change that.
        attr = self.resolve_attr(attr)

        for entry in Attr.names:
            if attr in entry or attr in Attr.names[entry]:
                bounds = [self.db.meta_attr[entry][0],
                          self.db.meta_attr[entry][1]]
        for entry in SpecAttr.names:
            if attr in entry or attr in SpecAttr.names[entry]:
                bounds = [self.db.meta_attr[entry][0],
                          self.db.meta_attr[entry][1]]

        if self.get_quality("exceptional attribute ({})".format(attr)):
            bounds[1] += 1
        elif self.get_quality("lucky") and fullattr is "edge":
            bounds[1] += 1

        return bounds

    def available_skills(self):
        secret = []
        if self.db.metatype in Skills.language['secret'].keys():
            secret = Skills.language['secret'][self.db.metatype]
        return OrderedDict([("groups", Skills.groups.keys()),
                           ("active", Skills.active.keys()),
                           ("knowledge", Skills.knowledge.keys()),
                           ("language", Skills.language['general'] +
                           Skills.language['other'] +
                           Skills.language['sign'] + secret)])

    def set_skill(self, skill, rating):
        "Attempt to set a skill or group, then return a StatMsg."
        if not isinstance(skill, str):
            return StatMsg(False, "The skill must be a string.")
        if not isinstance(rating, int):
            return StatMsg(False, "Skill ratings must be whole numbers.")
        as_entered = skill
        name, subtype = parse_subtype(skill)
        name = name.split("(")[0].strip()
        skill = skill.lower()
        lists = self.available_skills()

        # The max for each skill is 6 in chargen or 12 otherwise.
        if self.typeclass_path == "sr5.chargen.ChargenScript":
            skill_cap = 6
            cap_msg = "The maximum rating for skills is 6 in character " \
                "creation, or 7 if you have Aptitude ({}).".format(
                    skill.title()
                )
        else:
            skill_cap = 12
            cap_msg = "The maximum rating for skills is 12, " \
                "or 13 if you have Aptitude ({}).".format(skill.title())

        if [s.startswith(skill) for s in lists["groups"]].count(True):
            # Check if the skill group is valid (the ratings are the same and
            # no skill in the group has a specialization).
            # Aptitude isn't relevant here.
            if rating > skill_cap:
                return StatMsg(False, cap_msg)

            group = Skills.groups[skill]
            nums = [0, 0, 0]
            for s in range(0, len(group)):
                nums[s] = self.get_skill(group[s])
                spec = self.get_specialization(group[s])
            if spec:
                return StatMsg(False, "You can't use a skill group if one of "
                               "them has a specialization.")
            elif len(set(nums)) > 1:
                return StatMsg(False, "You can't use a skill group if they "
                               "aren't all at the same rating.")
            else:
                for s in range(0, len(group)):
                    new = {group[s]: rating}
                    skills = self.attributes.get("active_skills")

                    skills.update(new)

                return StatMsg(True, "Skill group {} set at {}".format(
                    skill, rating))
        elif [s.startswith(name) for s in lists["active"]].count(True):
            match = lists["active"][
                [s.startswith(name) for s in lists["active"]].index(True)
            ]
            # TODO: Gotta add a special check for the three exotic skills.
            # Need to make it generic, so that it can be used for other
            # systems. This could be a list on Skills of skills with open
            # fields, potentially expansible to skills with limited subtype
            # lists?
            # Check for Aptitude
            if self.get_quality("aptitude ({})".format(skill)):
                skill_cap += 1
            if rating > skill_cap:
                return StatMsg(False, cap_msg)

            skills = self.attributes.get("active_skills")

            skills.update({skill: rating})
        elif [skill.endswith("({})".format(i.lower())) for i in lists["knowledge"]].count(True):
            # Check for Aptitude
            if self.get_quality("aptitude ({})".format(skill)):
                skill_cap += 1
            if rating > skill_cap:
                return StatMsg(False, cap_msg)

            skills = self.attributes.get("knowledge_skills")

            skills.update({as_entered: rating})
        elif [bool(s.lower().count(skill)) for s in lists["language"]].count(True):
            match = lists["language"][
                [s.startswith(skill) for s in lists["language"]].index(True)
            ]
            # Check for Aptitude
            if self.get_quality("aptitude ({})".format(skill)):
                skill_cap += 1
            if rating > skill_cap:
                return StatMsg(False, cap_msg)

            skills = self.attributes.get("languages")

            cur = skills.get(match, False)
            if cur == "N":
                if self.typeclass_path != "sr5.chargen.ChargenScript":
                    return StatMsg(False, "You can't raise a native language.")

            skills.update({match: rating})
        else:
            return StatMsg(False, "Skill {} not found.".format(skill.title()))

    def set_specialization(self, skill, spec):
        "Attempt to set a specialization, then return `(bool, string)`."
        skill, spec = skill.lower(), spec.lower()
        lists = {"active": self.db.active_skills.keys(),
                 "knowledge": self.db.knowledge_skills.keys(),
                 "language": self.db.language_skills.keys()}

        if skill in lists["active"]:
            specs = self.db.active_specializations
        elif skill in lists["knowledge"]:
            specs = self.db.knowledge_specializations
        elif skill in lists["language"]:
            specs = self.db.language_specializations
        else:
            return StatMsg(False,
                           "{} doesn't seem to be a skill you possess.".format(
                                skill.title()))

        if skill in specs.keys():
            return StatMsg(False, "You can only have one specialization per"
                           "skill. If you want to change your specialization,"
                           "you have to remove the old one first.")
        else:
            specs.update({skill: spec})

            return StatMsg(True, "Specialization {} ({}) set.".format(
                    skill.title(), spec.title()))

    def unset_specialization(self, skill):
        "Attempt to unset a specialization, then return `(bool, string)`."
        skill = skill.lower()
        lists = {"active": Skills.active.keys(),
                 "knowledge": Skills.knowledge.keys()}

        if skill in lists["active"]:
            specs = self.db.active_specializations
        elif skill in lists["knowledge"]:
            specs = self.db.knowledge_specializations
        else:
            return StatMsg(False,
                           "{} doesn't seem to be a valid skill.".format(
                                skill.title()))

        if skill in specs.keys():
            spec = specs.pop(skill)

            return StatMsg(True, "Specialization {} ({}) removed.".format(
                    skill.title(), spec.title()))
        else:
            return StatMsg(False, "That skill doesn't appear to have a"
                           "specialization.")

    def get_specialization(self, skill):
        skill = skill.lower()

        for k in self.db.active_specializations.keys():
            if skill in k.lower():
                return self.db.active_specializations[k]
        for k in self.db.knowledge_specializations.keys():
            if skill in k.lower():
                return self.db.knowledge_specializations[k]
        return ""

    def get_skill(self, skill):
        "Check for a particular skill or skill group and return its value."
        if not skill:
            return None
        skill = skill.lower()
        lists = {"active": Skills.active.keys(),
                 "groups": Skills.groups.keys(),
                 "knowledge": Skills.knowledge.keys()}

        for item in lists["active"]:
            # TODO: Figure out exotic skills.
            if skill in item.lower():
                stat = self.attributes.get("active_skills")
                return stat.get(item, None)
        for item in lists["groups"]:
            if skill in item.lower():
                stat = self.get_skills("group")
                return stat.get(item, None)
        for item in lists["knowledge"]:
            if skill in item.lower():
                stat = self.attributes.get("knowledge_skills")
                return stat.get(item, None)

    def get_skills(self, cat):
        """
        Return a dict of skills in the category chosen. Valid choices for `cat`
        include all skill groups, all active skill categories, attributes,
        "active", "group", "knowledge", "language", "academic", "professional",
        "interest", and "street".
        """
        output, raw, stat = {}, [], {}
        if cat in "active":
            raw = Skills.active.keys()
            stat = dict(self.attributes.get("active_skills"))
            for group, skills in Skills.groups.items():
                # If a skill is included in a valid group, remove it from here.
                get = self.get_skills("group")
                if group in get:
                    stat.pop(skills[0])
                    stat.pop(skills[1])
                    stat.pop(skills[2])
        elif cat in "group":
            raw = Skills.groups.keys()
            stat = dict(self.attributes.get("active_skills"))

            for group in raw:
                # Check that all skills in the group have the same rating and
                # no specializations.
                skills = self.get_skills(group)
                specs = self.attributes.get("active_specializations")
                if set(skills.keys()) == set(Skills.groups[group]):
                    if len(set(skills.values())) == 1:
                        if not set(skills.keys()) & set(specs.keys()):
                            output.update({group: skills.values()[0]})
            return output
        elif cat in "knowledge":
            raw = Skills.knowledge.keys()
            stat = dict(self.attributes.get("knowledge_skills"))
        elif cat in "language":
            output = self.attributes.get("languages")
        elif cat in "academic":
            raw = ["academic"]
            stat = dict(self.attributes.get("knowledge_skills"))
        elif cat in "professional":
            raw = ["professional"]
            stat = dict(self.attributes.get("knowledge_skills"))
        elif cat in "interest":
            raw = ["interest"]
            stat = dict(self.attributes.get("knowledge_skills"))
        elif cat in "street":
            raw = ["street"]
            stat = dict(self.attributes.get("knowledge_skills"))
        else:
            for group in Skills.groups.keys():
                if cat in group:
                    raw = Skills.groups[group]
                    stat = dict(self.attributes.get("active_skills"))
                    break
            for category in Skills.categories.keys():
                if cat in category:
                    raw = Skills.categories[category]
                    stat = dict(self.attributes.get("active_skills"))
                    break
            for attr in Attr.names.keys():
                if cat in attr:
                    raw = Skills.categories[attr]
                    stat = dict(self.attributes.get("active_skills"))
                    stat.update(dict(self.attributes.get("knowledge_skills")))
                    break

        if not output:
            if not stat:
                return {}
            # Search in stat for all instances in raw.
            for k in sorted(stat.keys()):
                k = k.lower()
                for r in raw:
                    r = r.lower()
                    if k.startswith(
                     "{}".format(r)) or k.endswith("({})".format(r)):
                        output.update({k: stat[k]})

        return output

    def query_qualities(self, quality):
        name = pyparsing.Word(pyparsing.alphanums + " .-_/,")
        arg = pyparsing.Suppress("(") + name + pyparsing.ZeroOrMore(
                pyparsing.Suppress(",") + name
              ) + pyparsing.Suppress(")")
        hole = pyparsing.Combine("(" +
                                 pyparsing.ZeroOrMore(pyparsing.Suppress("[") ^
                                                      pyparsing.Suppress("]"))
                                 + ")")
        parser = name + pyparsing.ZeroOrMore(arg) + pyparsing.ZeroOrMore(hole)

        query = parse_subtype(quality)
        search = query[0]
        subtype = query[1][0]
        grab = {}

        # TODO: I could abstract this out into a utils function that takes a
        # list of names to search, a dict of categories to look in, and a dict
        # of info to attach to the end of the returned query. This would
        # require a systematic way to figure out which fields to append for
        # subtype entries and which to replace (which could be hardcoded as
        # `description`, but probably shouldn't be.)

        # TODO: Need to make it sufficiently generic to go in a contrib.
        q_names = [n.lower() for n in PositiveQualities.names]
        pos = sorted([
            parse_subtype(n[0])[0] for n in process.extract(search, q_names)
            if n[1] > 80
        ], reverse=True)
        if pos:
            # TODO: When making this a function, we should probably preserve
            # the category order so that more popular categories are searched
            # first.
            cats = [("General", PositiveQualities.general),
                    ("Metagenic", PositiveQualities.metagenic)]
            for cat, items in cats:
                for entry in pos:
                    # Reverse sort will place the primary entries before the
                    # subtype entries.
                    fuzz = sorted([
                        n[0] for n in process.extract(entry, items.keys(),
                                                      limit=2) if n[1] > 80
                    ], reverse=True)
                    for k in fuzz:
                        if k.endswith("([])"):
                            grab.update(items[k])
                            grab.update(
                                {"name": k, "type": "Positive",
                                 "category": cat}
                            )
                        elif k.lower().endswith("({})".format(subtype.lower())):
                            # If there's a previously matched open entry,
                            # we want to replace certain entries and append
                            # to others.
                            if grab:
                                desc = "{}\n\n{}".format(
                                    grab["description"],
                                    items[k]["description"])
                            else:
                                desc = items[k]["description"]
                            grab.update(items[k])
                            grab.update(
                                {"name": k, "type": "Positive",
                                 "category": cat, "description": desc}
                            )
                        else:
                            grab.update(items[k])
                            grab.update(
                                {"name": k, "type": "Positive",
                                 "category": cat}
                            )
                            return grab
        if grab:
            if grab["name"].endswith("([])"):
                name = grab["name"][0:-4].strip()
                grab["name"] = "{} ({})".format(name, subtype)
            return grab

        q_names = [n.lower() for n in NegativeQualities.names]
        neg = sorted([
            parse_subtype(n[0])[0] for n in process.extract(search, q_names)
            if n[1] > 80
        ], reverse=True)
        if neg:
            cats = [("General", NegativeQualities.general),
                    ("Metagenic", NegativeQualities.metagenic)]
            for cat, items in cats:
                for entry in neg:
                    # Reverse sort will place the primary entries before the
                    # subtype entries.
                    fuzz = sorted([
                        n[0] for n in process.extract(entry, items.keys(),
                                                      limit=2) if n[1] > 80
                    ], reverse=True)
                    for k in fuzz:
                        if k.endswith("([])"):
                            grab.update(items[k])
                            grab.update(
                                {"name": k, "type": "Pegative",
                                 "category": cat}
                             )
                        elif k.lower().endswith("({})".format(subtype.lower())):
                            # If there's a previously matched open entry,
                            # we want to replace certain entries and append
                            # to others.
                            if grab:
                                desc = "{}\n\n{}".format(
                                    grab["description"],
                                    items[k]["description"])
                            else:
                                desc = items[k]["description"]
                            grab.update(items[k])
                            grab.update(
                                {"name": k, "type": "Pegative",
                                 "category": cat, "description": desc}
                             )
                        else:
                            grab.update(items[k])
                            grab.update(
                                {"name": k, "type": "Pegative",
                                 "category": cat}
                            )
                            return grab
        if grab:
            if grab["name"].endswith("([])"):
                name = grab["name"][0:-4].strip()
                grab["name"] = "{} ({})".format(name, subtype)
            return grab

    def set_quality(self, quality, rating):
        "Attempt to set a quality and return True or False."
        quality = quality.lower()

        query = self.query_qualities(quality)
        name, subtype = parse_subtype(quality)
        sub = None
        if not query:
            return StatMsg(False, "No such quality in the database.")
        if rating > len(query['rank']):
            return StatMsg(False, "Requested rating too high.")
        if query['subtypes']:
            for s in query['subtypes']:
                if subtype[0] in s or s[0] == "*":
                    sub = s
            if not sub:
                return StatMsg(False, "The subtype you entered doesn't match.")
        stats = self.attributes.get("qualities_" + query["type"])
        stats.update({query["name"]: rating})
        # Purge any empty values.
        purge_empty_values(stats)

        return StatMsg(True, "No error.")

    def get_quality(self, quality):
        """
        Return the rating of the requested quality, or the first quality that
        has the same name if the input quality has an empty subfield.

        Args:
            quality (str, optional): A quality name to look for.
        """
        output = {}
        quality = quality.lower()
        query = self.query_qualities(quality)
        if not query:
            return None
        name, subtype = parse_subtype(quality)
        if not name:
            return False
        stats = self.attributes.get("qualities_" + query["type"])

        for s, v in stats.items():
            s = s.lower()
            if quality in s or name[0:len(name) - 3] in s:
                output.update({s: v})

        return output

    def get_qualities(self, cat):
        """
        Return the list requested. This only includes qualities on the subject.

        Args:
            cat (str, optional): "Positive" or "negative", or the name
                of one of the specialized lists, or a substring thereof.
        """
        cat = cat.lower()
        raw, sel, output = None, [], {}

        if cat in "positive":
            raw = PositiveQualities.__dict__
        elif cat in "negative":
            raw = NegativeQualities.__dict__
        if raw:
            for c in raw['categories']:
                sel += raw[c.lower()].keys()

            for s in sel:
                get = self.get_quality(s)
                if get:
                    output.update(get)

        # TODO: Add category search.
        return output

    def set_magic_type(self, type):
        "Attempt to set a magic type, then return `(bool, string)`."
        pass

    def set_tradition(self, tradition):
        "Attempt to set a tradition, then return `(bool, string)`."
        pass

    def set_magic_skill(self, skill, rating):
        "Attempt to set a skill or group, then return `(bool, string)`."
        # TODO: Work it like normal skills.
        pass

    def set_lifestyle(self, lifestyle):
        "Attempt to set a lifestyle, then return `(bool, string)`."
        # TODO: This will always affect nuyen.
        pass

    def set_resources(self, resources):
        "Attempt to set a resources level, then return `(bool, string)`."
        # TODO: Check to see if the new resources level makes previous
        # purchases unaffordable.
        pass

    def physical_limit(self):
        "(STR x 2 + BOD + REA) / 3"

        strength, body, reaction = self.get_attr("str") * 2, self.get_attr("bod"), self.get_attr("rea")

        output = math.ceil(strength + body + reaction / 3)
        return int(output)

    def mental_limit(self):
        "(LOG x 2 + INT + WIL) / 3"

        logic, intuition, willpower = self.get_attr("log") * 2, self.get_attr("int"), self.get_attr("wil")

        output = math.ceil(logic + intuition + willpower / 3)
        return int(output)

    def social_limit(self):
        "(CHA x 2 + WIL + ESS) / 3"

        charisma, willpower, reaction = self.get_attr("cha") * 2, self.get_attr("wil"), self.get_attr("ess")

        output = math.ceil(charisma + willpower + reaction / 3)
        return int(output)

    def get_init(self):
        """
        Calculate the character's initiative (REA + INT).
        """
        return self.get_attr("rea") + self.get_attr("int")

    def get_astral_init(self):
        """
        Calculate the character's Astral initiative.
        """
        return self.get_attr("int") * 2

    def get_matrix_init(self):
        """
        Calculate the character's Matrix initiative.
        """
        return -1

    def get_phys_mod(self):
        """
        Calculate the character's physical modifier (half BOD, rounded up, plus 8).
        """
        # Need to be able to iterate over the character's augmentations and magical effects to check for bonuses.
        # The denominator has to have a decimal in order to force a float assignment.
        return math.ceil(self.get_attr("bod") / 2.0) + 8

    def get_stun_mod(self):
        """
        Calculate the character's stun modifier (half WIL, rounded up, plus 8).
        """
        # Need to be able to iterate over the character's augmentations and magical effects to check for bonuses.
        # The denominator has to have a decimal in order to force a float assignment.
        return math.ceil(self.get_attr("wil") / 2.0) + 8

    def get_composure(self):
        """
        Calculate the character's Matrix initiative.
        """
        return -1

    def get_judge(self):
        """
        Calculate the character's Matrix initiative.
        """
        return -1

    def get_memory(self):
        """
        Calculate the character's Matrix initiative.
        """
        return -1

    def get_lift_carry(self):
        """
        Calculate the character's Matrix initiative.
        """
        return -1

    def get_movement(self):
        """
        Calculate the character's Matrix initiative.
        """
        return -1
