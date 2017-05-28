"""
Characters

Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

import math
from evennia import DefaultCharacter
from chargen import ChargenScript
from sr5.data.skills import Skills

class DefaultShadowrunner(DefaultCharacter):
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
        self.scripts.add("ChargenScript")

        self.db.sheet_locked = "False"
        self.db.approved = "No"
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
        self.db.qualities_negative={}

    def get_bod(self):
        """
        Return the character's Body.
        """
        return self.db.attributes["body"]
    def set_bod(self, new):
        """
        Set the character's Body.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['body'] = new

            return True
        else:
            return False
    def get_agi(self):
        """
        Return the character's Agility.
        """
        return self.db.attributes['agility']
    def set_agi(self, new):
        """
        Set the character's Agility.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['agility'] = new

            return True
        else:
            return False
    def get_rea(self):
        """
        Return the character's Reaction.
        """
        return self.db.attributes['reaction']
    def set_rea(self, new):
        """
        Set the character's Reaction.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['reaction'] = new

            return True
        else:
            return False
    def get_str(self):
        """
        Return the character's Strength.
        """
        return self.db.attributes['strength']
    def set_str(self, new):
        """
        Set the character's Strength.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['strength'] = new

            return True
        else:
            return False
    def get_wil(self):
        """
        Return the character's Willpower.
        """
        return self.db.attributes['willpower']
    def set_wil(self, new):
        """
        Set the character's Willpower.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['willpower'] = new

            return True
        else:
            return False
    def get_log(self):
        """
        Return the character's Logic.
        """
        return self.db.attributes['logic']
    def set_log(self, new):
        """
        Set the character's Logic.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['logic'] = new

            return True
        else:
            return False
    def get_int(self):
        """
        Return the character's Intuition.
        """
        return self.db.attributes['intuition']
    def set_int(self, new):
        """
        Set the character's Intuition.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['intuition'] = new

            return True
        else:
            return False
    def get_cha(self):
        """
        Return the character's Charisma.
        """
        return self.db.attributes['charisma']
    def set_cha(self, new):
        """
        Set the character's Charisma.
        """
        if isinstance( new, ( int, long ) ):
            self.db.attributes['charisma'] = new

            return True
        else:
            return False

    def get_ess(self):
        """
        Return the character's Essence.
        """
        return self.db.attributes['essence']
    def get_edg(self):
        """
        Return the character's Edge.
        """
        return self.db.attributes['edge']
    def get_mag(self):
        """
        Return the character's Magic.
        """
        return self.db.attributes['magic']
    def get_res(self):
        """
        Return the character's Resonance.
        """
        return self.db.attributes['resonance']

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

    pass
