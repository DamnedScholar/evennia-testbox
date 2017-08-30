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
from sr5.utils import (a_n, itemize, flatten, LedgerHandler, SlotsHandler,
                       validate, ureg)
from sr5.data.skills import Skills


class DefaultShadowrunner(DefaultCharacter, Stats, LedgerHandler):
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

    @lazy_property
    def slots(self):
        return SlotsHandler(self)

    def at_object_creation(self):
        """
        Called only at initial creation. Set default values to fill out character sheet.
        """
        self.permissions = ["unapproved"]
        self.scripts.add("sr5.chargen.ChargenScript")
