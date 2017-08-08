"""
Characters

Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

import math
import string
import re
import pyparsing
from dateutil import parser
from pint import UnitRegistry
from evennia import DefaultCharacter
from evennia.utils.utils import lazy_property
from sr5.chargen import ChargenScript
from sr5.system import Stats
from sr5.utils import ureg
from sr5.data.skills import Skills


class DefaultShadowrunner(DefaultCharacter, Stats):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(player) -  when Player disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Player has disconnected"
                    to the room.
    at_pre_puppet - Just before Player re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "PlayerName has entered the game" to the room.

    """

    def at_object_creation(self):
        """
        Called only at initial creation. Set default values to fill out character sheet.
        """
        self.permissions = ["unapproved"]
        self.scripts.add("sr5.chargen.ChargenScript")

        self.db.approved = False
        self.db.fullname = "Empty"
        self.db.birthdate = "1/1/1970"
        self.db.metatype = "Human"
        self.db.ethnicity = ""
        self.db.height = ""
        self.db.weight = ""
        self.db.street_cred = ""
        self.db.notoriety = ""
        self.db.public_awareness = ""
        self.db.karma = {'current': 0, 'total': 0}
        self.db.attributes = {
            'body': 1, 'agility': 1, 'reaction': 1, 'strength': 1,
            'willpower': 1, 'logic': 1, 'intuition': 1, 'charisma': 1,
            'essence': 6, 'edge': 1, 'magic': 0, 'resonance': 0
        }
        self.db.active_skills = {
            "archery": 4, "automatics": 2, "blades":1, "clubs": 8,
            "escape artist": 3, "exotic melee weapon (specific)": 4,
            "academic knowledge": 2, "aeronautics mechanic": 2, "arcana": 2,
            "armorer": 2, "automotive mechanic": 2, "biotechnology": 2,
            "chemistry": 2
        }
        self.db.active_specializations = {"archery": "horseback"}
        self.db.active_skill_groups = {}
        self.db.knowledge_skills = {"biotech": 2, "megacorps": 2, "seattle": 2, "slums": 2, "ballistics": 2, "metahumans": 2}
        self.db.knowledge_specializations = {"metahumans": "trolls"}
        self.db.language_skills = {"english": "N", "french": 2}
        self.db.language_specializations = {}
        # Don't store the Karma value of qualities. Store the level and calculate the Karma points based on the lookup table.
        self.db.qualities_positive = {}
        self.db.qualities_negative = {}

    pass
