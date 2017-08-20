"""
Object

These objects are used by the system package. This file should be used mostly
for prototypes and parents.

"""
from evennia import DefaultObject
from sr5.data.ware import Grades, Obvious, Synthetic


class Extra(DefaultObject):
    """
    This is a prototype for objects to represent things in the game system that
    are too complex and individual to just be listed on a sheet. They will have
    their own stats and information about what the mechanic represents and how
    the user interacts with it.
    """

    # TODO: Make sure to use tags when defining children of this class.
    # https://github.com/evennia/evennia/wiki/Tags
    # Tehom thinks that I should make a typeclass for every little variation.
    # I feel like that would be less intuitive for everybody. This should be
    # friendly for novice developers. You can also have multiple tags for a
    # particular item.

    # NOTE: The easiest way to define item-specific attributes:
    # https://github.com/evennia/evennia/wiki/Spawner

    # TODO: Define default stats.

    def at_object_creation(self):
        # Default flags. These will frequently be overridden.
        self.db.visible = False
        self.db.inherent = False
        self.db.permanent = True

    # TODO: Define methods used to get and set stats. It doesn't have to be
    # complicated, but it should be easy to at least make sure that only
    # integers and floats are accepted when a numerical value is assigned to
    # the default.

    def set_stat(self, stat, *args, **kwargs):
        """
        stat - A period-delimited list of attr name and keys.
        args - User input.
        kwargs - Switches if necessary.
        """
        lookup = stat.split('.')                # A list of attr name and keys.
        depth = len(lookup)                     # How deep we should look.
        entry = getattr(self.db, lookup[0], 0)  # The attr itself.

        # TODO: Make this create a list if there are multiple args, or a
        # number, bool, or string if there's only one.
        if len(args) > 1:
            return "The command only accepts a single input argument at the "\
                "moment. This restriction will be removed once we're sure "\
                "that everything else works."
        arg = args[0]

        # TODO: Remove these. They're only for testing.
        self.location.msg("lookup: " + str(lookup))
        self.location.msg("entry: " + str(entry))

        # Store the current value.
        err_no_nest = "You seem to be trying to add a nested value to"\
            "something that already exists and is a flat value. In order to"\
            "restructure the data, please set it by hand (if you can't, you"\
            "shouldn't)."
        if depth == 1:
            cur = entry
        elif depth == 2:
            try:
                # Attempt to follow the dict path entered.
                cur = entry.get(lookup[1], 0)
            except AttributeError:
                # Error sensibly if something above isn't a dict.
                return err_no_nest
        elif depth == 3:
            try:    # Attempt to follow the dict path entered.
                cur = entry.get(lookup[1], 0)
                cur = cur.get(lookup[2], 0)
            except AttributeError:
                # Error sensibly if something above isn't a dict.
                return err_no_nest
        elif depth == 4:
            try:    # Attempt to follow the dict path entered.
                cur = entry.get(lookup[1], 0)
                cur = cur.get(lookup[2], 0)
                cur = cur.get(lookup[3], 0)
            except AttributeError:
                # Error sensibly if something above isn't a dict.
                return err_no_nest
        else:
            # You shouldn't need to store things this deep. If you have more
            # than four levels, your schema for storing information needs work.
            # Evennia has categories and stuff. Also, this is an arbitrary
            # limit I'm setting because I can't think of a programmatic way to
            # do the above.
            return "You shouldn't nest information that deeply. Consider"\
                "reoganizing your data to make use of attribute categories."

        if not cur:
            if depth == 1:
                self.attributes.add(lookup[0], arg)
            elif depth == 2:
                entry.setdefault(lookup[1], arg)
            elif depth == 3:
                dig = entry.get(lookup[1])
                dig.setdefault(lookup[2], arg)
            elif depth == 4:
                dig = entry.get(lookup[1])
                dig = entry.get(lookup[2])
                dig.setdefault(lookup[3], arg)

            return "Attribute " + lookup[0] + " added with value "\
                + str(arg) + "."

        # If there is a current value, check to see what type it is.
        # Then check to see what type the input argument is.
        if isinstance(cur, (int, long)):
            if isinstance(arg, (int, long)):
                # Set the stat, probably with self.set().
                result = arg
            else:
                return "The input should match the current value, which is a"\
                    "whole number."
        elif isinstance(cur, (float)):
            if isinstance(arg, (int, long, float)):
                # Set the stat and add 0.0 to it to make sure there's a decimal
                result = arg + 0.0
            else:
                return "The input should match the current value, which is a"\
                    "number."
        elif isinstance(cur, str):
            result = str(arg)
        elif isinstance(cur, list):
            result = arg
        else:
            return "The attribute is not a valid type."
            # return False

        self.location.msg("result: " + str(result))
        cur = result

        if depth == 1:
            entry = result
        elif depth == 2:
            entry[lookup[1]] = result
        elif depth == 3:
            entry[lookup[1]][lookup[2]] = result
        elif depth == 4:
            entry[lookup[1]][lookup[2]][lookup[3]] = result

        return "Attribute " + stat + " set to " + str(result) + "."

        # XXX: It is frustrating and infuriating that I can't use setattr()
        # to set things inside dicts. There has to be a way that I'm missing.


class Augment(Extra):
    """
    This is a class for defining the default values and implementing any unique
    functions for cyberware and bioware.
    """

    def at_object_creation(self):
        self.db.grade = "standard"
        self.db.custom_str = 0
        self.db.custom_agi = 0
        self.db.synthetic = False
        self.db.cost = 0

        # Override default flags where necessary.
        self.db.visible = True
        self.db.inherent = False
        self.db.permanent = True

        # This will hold the list of slots that the Extra consumes.
        self.db.slots = {"body": []}

    # Initial setup functions called by the prototype.
    def apply_costs_and_capacity(self, slot_list, synthetic):
        results = self.apply_costs_and_capacity(slot_list, synthetic)

        self.db.cost = results[0]
        self.db.capacity = results[1]

        self.db.slots["body"] = slot_list

    def apply_customizations(self):
        self.db.strength += self.db.custom_str
        self.db.agility += self.db.custom_agi

        customizations = self.db.custom_agi + self.db.custom_str
        self.db.cost += customizations * 5000

    def apply_grade(self):
        grade = getattr(Grades, self.db.grade)

        self.db.cost = self.db.cost * grade["cost"]
        self.db.essence = self.db.essence * grade["essence"]

    @classmethod
    def apply_costs_and_capacity(self, slot_list, synthetic):
        # HACK: This is a kludge so that I can use this function from the buy
        # command. It should be made more sensible and efficient at some point.
        if "right_arm" in slot_list or "left_arm" in slot_list:
            slot_list += ["right_upper_arm"]
        elif "right_leg" in slot_list or "left_leg" in slot_list:
            slot_list += "right_upper_leg"

        if "right_upper_arm" in slot_list or "left_upper_arm" in slot_list:
            if synthetic:
                cost = Synthetic.full_arm["cost"]
                capacity = Synthetic.full_arm["capacity"]
            else:
                cost = Obvious.full_arm["cost"]
                capacity = Obvious.full_arm["capacity"]
        elif "right_lower_arm" in slot_list or "left_lower_arm" in slot_list:
            if synthetic:
                cost = Synthetic.lower_arm["cost"]
                capacity = Synthetic.lower_arm["capacity"]
            else:
                cost = Obvious.lower_arm["cost"]
                capacity = Obvious.lower_arm["capacity"]
        elif "right_hand" in slot_list or "left_hand" in slot_list or "right_foot" in slot_list or "left_foot" in slot_list:
            if synthetic:
                cost = Synthetic.hand_foot["cost"]
                capacity = Synthetic.hand_foot["capacity"]
            else:
                cost = Obvious.hand_foot["cost"]
                capacity = Obvious.hand_foot["capacity"]
        elif "right_upper_leg" in slot_list or "left_upper_leg" in slot_list:
            if synthetic:
                cost = Synthetic.full_leg["cost"]
                capacity = Synthetic.full_leg["capacity"]
            else:
                cost = Obvious.full_leg["cost"]
                capacity = Obvious.full_leg["capacity"]
        elif "right_lower_leg" in slot_list or "left_lower_leg" in slot_list:
            if synthetic:
                cost = Synthetic.lower_leg["cost"]
                capacity = Synthetic.lower_leg["capacity"]
            else:
                cost = Obvious.lower_leg["cost"]
                capacity = Obvious.lower_leg["capacity"]
        elif "torso" in slot_list:
            if synthetic:
                cost = Synthetic.torso["cost"]
                capacity = Synthetic.torso["capacity"]
            else:
                cost = Obvious.torso["cost"]
                capacity = Obvious.torso["capacity"]
        elif "skull" in slot_list:
            if synthetic:
                cost = Synthetic.skull["cost"]
                capacity = Synthetic.skull["capacity"]
            else:
                cost = Obvious.skull["cost"]
                capacity = Obvious.skull["capacity"]

        return [cost, capacity]
