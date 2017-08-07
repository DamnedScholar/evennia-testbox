"""
System

This file contains the code that describes how the game system works.

"""

import math
import string
import re
import pyparsing
from dateutil import parser
from evennia import DefaultObject
from sr5.utils import ureg

# TODO: Implement default modifiers here.
#   * Each point of Essence loss (rounded up) reduces Magic by 1 (SR5 p. 278)
#   * Limits?


class SlotArray:
    """
    Instantiate an array of slots on an object for controlling the available
    choices for Extras.

    self.db.body = SlotArray("body", "Augments, mutations, and physical qualities.", ["head", "torso", "right_upper_arm", "right_lower_arm", "right_hand", "left_upper_arm", "left_lower_arm", "left_hand", "right_upper_leg", "right_lower_leg", "right_foot", "left_upper_leg", "left_lower_leg", "left_foot"])

    Arguments:
        kind (str): What does this SlotArray represent? Extras will look for this.
        desc (str): Human-readable description.
        options (sequence): All of the available slots (more can be added).

    Methods:
        add(to_add): Adds to the options list.
        remove(to_remove): Removes from the options list.
    """

    def __init__(self, kind, desc, options):
        self.kind = kind
        self.desc = desc
        self.options = list(options)

    def add(self, to_add):
        self.options.append(list(to_add))

    def remove(self, to_remove):
        new = []

        for option in self.options:
            if option not in to_remove:
                new.append(option)

        self.options = new

    # TODO: This class isn't unpickling with its current state intact. Need to
    # figure out why.

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        # Restore instance attributes (i.e., filename and lineno).
        self.__dict__.update(state)


class Stats:
    def set_vital(self, field, value):
        "Attempt to set a vitals field, then return `(bool, string)`."
        field = field.lower()
        self.obj.msg("{}: {}".format(field, value))
        if field in ["fullname", "ethnicity"]:
            self.attributes.add(field, value)
        elif field in ["birthdate"]:
            try:
                self.db.birthdate = str(parser.parse(value).date())
            except:
                return (False, "That date isn't recognized.")
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
            return (False, "Metatype {} is not available at this time".format(
                    metatype.title()))

        self.db.metatype = metatype
        self.db.spec_attr = {'edge': 1, 'magic': 0, 'resonance': 0}
        self.db.meta_attr = Metatypes.meta_attr[metatype]

        return (True, "Metatype {} set.".format(metatype.title()))

    def set_attr(self, attr, rating):
        "Attempt to set an attribute, then return `(bool, string)`."
        if not isinstance(attr, str):
            return (False, "The attribute must be a string.")
        if not isinstance(rating, int):
            return (False, "Attribute ratings must be whole numbers.")
        attr = attr.lower()
        attrs = self.db.attr

        if attr in attrs.keys():
            bounds = list(self.db.met_attr[attr])
            boost = ""
            # Check for Aptitude
            if self.get_quality("exceptional attribute ({})".format(attr)):
                bounds[1] += 1
                boost = " (plus Exceptional Attribute)"
            elif self.get_quality("Lucky") and attr == "edge":
                bounds[1] += 1
                boost = " (plus Lucky)"
            if rating < bounds[0]:
                return (False, "You can't set this attribute below your "
                        "metatype{} minimum of {}".format(boost, bounds[0]))
            elif rating > bounds[1]:
                return (False, "You can't set this attribute above your "
                        "metatype{} maximum of {}".format(boost, bounds[1]))
            else:
                attrs.update({attr: rating})

    def set_skill(self, skill, rating):
        "Attempt to set a skill or group, then return `(bool, string)`."
        if not isinstance(skill, str):
            return (False, "The skill must be a string.")
        if not isinstance(rating, int):
            return (False, "Skill ratings must be whole numbers.")
        skill = skill.lower()
        lists = {"active": Skills.active.keys(),
                 "groups": Skills.groups.keys(),
                 "knowledge": Skills.knowledge.keys()}

        # The max for each skill is 6 in chargen or 12 otherwise.
        if self == "chargen":
            skill_cap = 6
            cap_msg = "The maximum rating for skills is 6 in character" \
                "creation, or 7 if you have Aptitude ({}).".format(
                    skill.title()
                )
        else:
            skill_cap = 12
            cap_msg = "The maximum rating for skills is 12," \
                "or 13 if you have Aptitude ({}).".format(skill.title())

        if skill in lists["groups"]:
            # Check if the skill group is valid (the ratings are the same and
            # no skill in the group has a specialization).
            # Aptitude isn't relevant here.
            if rating > skill_cap:
                return (False, cap_msg)

            group = Skills.groups[skill]
            nums = []
            for s in range(0, len(group)):
                nums[s] = self.get_skill(group[s])
                spec = self.get_specialization(group[s])
            if spec:
                return (False, "You can't use a skill group if one of them"
                        " has a specialization.")
            elif len(set(nums)) > 1:
                return (False, "You can't use a skill group if they aren't all"
                        " at the same rating.")
            else:
                for s in range(0, len(group)):
                    new = {group[s]: rating}
                    skills = self.attributes.get("active_skills")

                    skills.update(new)

                return (True, "Skill group {} set at {}".format(skill, rating))
        elif skill in lists["active"]:
            # Check for Aptitude
            if self.get_quality("aptitude ({})".format(skill)):
                skill_cap += 1
            if rating > skill_cap:
                return (False, cap_msg)

            skills = self.attributes.get("active_skills")

            skills.update({skill: rating})
        elif skill in lists["knowledge"]:
            # Check for Aptitude
            if self.get_quality("aptitude ({})".format(skill)):
                skill_cap += 1
            if rating > skill_cap:
                return (False, cap_msg)

            skills = self.attributes.get("active_skills")

            skills.update({skill: rating})
        else:
            return (False, "Skill {} not found.".format(skill.title()))

    def set_specialization(self, skill, spec):
        "Attempt to set a specialization, then return `(bool, string)`."
        skill, spec = skill.lower(), spec.lower()
        lists = {"active": Skills.active.keys(),
                 "knowledge": Skills.knowledge.keys()}

        if skill in lists["active"]:
            specs = self.db.active_specializations
        elif skill in lists["knowledge"]:
            specs = self.db.knowledge_specializations
        else:
            return (False, "{} doesn't seem to be a valid skill.".format(
                    skill.title()))

        if skill in specs.keys():
            return (False, "You can only have one specialization per skill. "
                    "If you want to change your specialization, you have to "
                    "remove the old one first.")
        else:
            specs.update({skill: spec})

            return (True, "Specialization {} ({}) set.".format(
                    skill.title(), spec.title()))

    def unset_specialization(self, skill, spec):
        "Attempt to unset a specialization, then return `(bool, string)`."
        skill, spec = skill.lower(), spec.lower()
        lists = {"active": Skills.active.keys(),
                 "knowledge": Skills.knowledge.keys()}

        if skill in lists["active"]:
            specs = self.db.active_specializations
        elif skill in lists["knowledge"]:
            specs = self.db.knowledge_specializations
        else:
            return (False, "{} doesn't seem to be a valid skill.".format(
                    skill.title()))

        if skill in specs.keys():
            specs.pop(skill)

            return (True, "Specialization {} ({}) removed.".format(
                    skill.title(), spec.title()))
        else:
            return (False, "That skill doesn't appear to have a"
                    "specialization.")

    def set_quality(self, quality, rating):
        "Attempt to set a quality, then return `(bool, string)`."
        pass

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


    def get_bod(self):
        """
        Return the character's Body.
        """
        return self.db.attr["body"]

    def set_bod(self, new):
        """
        Set the character's Body.
        """
        if isinstance(new, (int, long)):
            self.db.attr['body'] = new

            return True
        else:
            return False

    def get_agi(self):
        """
        Return the character's Agility.
        """
        return self.db.attr['agility']

    def set_agi(self, new):
        """
        Set the character's Agility.
        """
        if isinstance(new, (int, long)):
            self.db.attr['agility'] = new

            return True
        else:
            return False

    def get_rea(self):
        """
        Return the character's Reaction.
        """
        return self.db.attr['reaction']

    def set_rea(self, new):
        """
        Set the character's Reaction.
        """
        if isinstance(new, (int, long)):
            self.db.attr['reaction'] = new

            return True
        else:
            return False

    def get_str(self):
        """
        Return the character's Strength.
        """
        return self.db.attr['strength']

    def set_str(self, new):
        """
        Set the character's Strength.
        """
        if isinstance(new, (int, long)):
            self.db.attr['strength'] = new

            return True
        else:
            return False

    def get_wil(self):
        """
        Return the character's Willpower.
        """
        return self.db.attr['willpower']

    def set_wil(self, new):
        """
        Set the character's Willpower.
        """
        if isinstance(new, (int, long)):
            self.db.attr['willpower'] = new

            return True
        else:
            return False

    def get_log(self):
        """
        Return the character's Logic.
        """
        return self.db.attr['logic']

    def set_log(self, new):
        """
        Set the character's Logic.
        """
        if isinstance(new, (int, long)):
            self.db.attr['logic'] = new

            return True
        else:
            return False

    def get_int(self):
        """
        Return the character's Intuition.
        """
        return self.db.attr['intuition']

    def set_int(self, new):
        """
        Set the character's Intuition.
        """
        if isinstance(new, (int, long)):
            self.db.attr['intuition'] = new

            return True
        else:
            return False

    def get_cha(self):
        """
        Return the character's Charisma.
        """
        return self.db.attr['charisma']

    def set_cha(self, new):
        """
        Set the character's Charisma.
        """
        if isinstance(new, (int, long)):
            self.db.attr['charisma'] = new

            return True
        else:
            return False

    def get_ess(self):
        """
        Return the character's Essence.
        """
        if self.attributes.get("spent"):
            essence = 6 - self.db.spent.get("essence")
        else:
            essence = 6

        return essence

    def get_edg(self):
        """
        Return the character's Edge.
        """
        return self.db.spec_attr['edge']

    def get_magres(self):
        """
        Return the character's Magic or Resonance.
        """
        if self.db.spec_attr.get("magic"):
            return ("Magic", self.db.spec_attr['magic'])

        elif self.db.spec_attr.get("resonance"):
            return ("Resonance", self.db.spec_attr['resonance'])

        else:
            return ("", "")

    def get_init(self):
        """
        Calculate the character's initiative (REA + INT).
        """
        return self.get_rea() + self.get_int()

    def get_astral_init(self):
        """
        Calculate the character's Astral initiative.
        """
        return self.get_int() * 2

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
        return math.ceil(self.get_bod() / 2.0)+8

    def get_stun_mod(self):
        """
        Calculate the character's stun modifier (half WIL, rounded up, plus 8).
        """
        # Need to be able to iterate over the character's augmentations and magical effects to check for bonuses.
        # The denominator has to have a decimal in order to force a float assignment.
        return math.ceil(self.get_wil() / 2.0) + 8

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
