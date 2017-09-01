"""
Object

These objects are used by the system package. This file should be used mostly
for prototypes and parents.

"""
import pyparsing as pp
import evennia
from evennia import DefaultObject
from evennia.utils import spawner
# TODO: In a production situation, it might have negative performance
# implications if every call to a function in this module has to import the
# entire game system. It won't matter with a small userbase, but a lot of
# functions could potentially live in this file, and it should only import
# what it needs when it needs it.
from sr5.data.ware import *
from sr5.msg_format import mf
from sr5.utils import (a_n, itemize, flatten, LedgerHandler, SlotsHandler,
                       validate, ureg)
wiz = evennia.search_player("#1")[0]


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
        # self.location.msg("lookup: " + str(lookup))
        # self.location.msg("entry: " + str(entry))

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

    @classmethod
    def buy(self, caller, item, options,
            dest=None, costs={}, seller="", buyer=""):
        """
        Buy this object! This method orchestrates pre- and post-purchase hooks
        and spawns the object. It should not be overridden.

        Arguments:
            caller (Evennia object or dbref) - The source of the purchase.
            item (str) - The item being obtained.
            dest (Evennia object or dbref) - Where the object will appear. This
                is the same as `caller` by default.
            costs (dict) - A dict of cost values that will override the ones
                generated by the object's methods.
            seller (str) - The name of the NPC, shop, or menu if desired.
            buyer (Evennia object or dbref) - The object that will pay the
                costs for the item. This is the same as `caller` by default.
            options (iterable) - Any extra options for the specific item being
                bought. `at_pre_purchase()` will know what to do with this.
        """
        if not dest:
            dest = caller
        if not buyer:
            buyer = caller
        can_afford = True

        # The at_pre_purchase() hook on an Extra child is run before purchase
        # and has the ability to cancel the whole exchange. It should parse
        # the list of options into something usable and return a dict.
        c = self.at_pre_purchase(caller, item, options, dest=dest, costs={},
                                 seller=seller, buyer=buyer)
        if not c:
            return False
        c.update({
            "prototype": item,
            "location": dest
        })
        # Allow cost totals to be overridden in some cases.
        if costs:
            c.update({"costs": costs})

        ledgers = buyer.attributes.get(category="ledgers", return_obj=True)
        ledgers = [(l.key.lower(), l.value) for l in ledgers]

        aff = dict([(l.currency.lower(), l.value) for k, l in ledgers])

        wiz.msg(repr(ledgers))
        wiz.msg(repr(ledgers[0][1].currency))
        wiz.msg(repr(aff))

        can_afford = [(currency, False)
                      for currency, value in aff.items()
                      for ccurrency, cvalue in costs.items()
                      if ccurrency.lower() == currency.lower()
                      and cvalue > value]

        if can_afford and can_afford != True:
            for a in can_afford:
                caller.msg(mf.tag + "You have {} {} left and {} will cost "
                           "{}".format(
                            ledgers[a[0]].value, ledgers[a[0]].currency,
                            a_n(item), c['costs'][a[0]]))
            return False

        wiz.msg(repr(c))

        item = spawner.spawn(c)[0]

        if seller:
            seller = " from {}".format(seller)
        reason = "Purchased {}{}.".format(item.key, seller)

        results = [(c_name, ledger.record(0 - cost, reason, buyer.dbref))
                   for c_name, cost in costs.items()
                   for l_name, ledger in ledgers
                   if c_name.lower() == l_name.lower()]

        for n, r in results:
            item.attributes.set("logs_" + n, r, category="logs")

        return item

        #     if attach[0] is False:
        #         purchased.delete()
        #         caller.msg(mf.tag + attach[1])
        #         return False
        #
        #     if synthetic:
        #         target[0] = "synthetic {}".format(target[0])
        #     target[0] += " ({})".format(grade)
        #
        #     # Record expenditures and store the AccountingIcetray entries
        #     # on the purchased object for easy reference later on.
        #     purchased.db.nuyen_logs = cg.db.nuyen.record(0 - cost, "Purchased " + target[0])
        #     purchased.db.essence_logs = cg.db.essence.record(
        #         0 - purchased.db.essence, target[0].capitalize()
        #     )
        #
        # caller.msg(mf.tag + "You have placed an order for a {} with strength "
        #            "+{} and agility +{} at a cost of {} nuyen and "
        #            "{} essence. {}".format(target[0], strength, agility,
        #                                    cost, purchased.db.essence,
        #                                    result))

    @classmethod
    def at_pre_purchase(options):
        "This is called before an Extra is bought. It should perform any necessary checks and return False if the purchase isn't valid."
        return True

    @classmethod
    def at_post_purchase(options):
        "This is called after an Extra is bought."
        pass

    def destroy(self, mode="normal", refund={}):
        """
        Destroy this object.

        Arguments:
            mode (str, optional):
                "normal" (default) - Destroy this object and preserve logs.
                "anull" - Destroy this object as if it had never existed.
            refund (dict, optional): A dict with each key representing a Ledger
                currency and each value representing the amount of currency to
                refund. In "normal" mode, no currency is refunded unless this
                is set. In "anull" mode, all currency is refunded unless this
                is set.
        """


class Augment(Extra):
    """
    This is a class for defining the default values and implementing any unique
    functions for cyberware and bioware.
    """

    def at_object_creation(self):
        self.db.grade = "standard"
        self.db.costs = {"nuyen": 0, "essence": 0}

        # Override default flags where necessary.
        self.db.visible = True
        self.db.inherent = False
        self.db.permanent = True

        # This will hold the list of slots that the Extra consumes.
        self.db.slots = {"body": []}

    @classmethod
    def at_pre_purchase(caller, item, options):
        "This is called before an Extra is bought. It should perform any necessary checks and return False if the purchase isn't valid."

    @classmethod
    def at_post_purchase(options):
        "This is called after an Extra is bought."
        pass


class Cyberlimb(Augment):
    """
    This is a class for defining the default values and implementing any unique
    functions for cyberware and bioware.
    """

    def at_object_creation(self):
        self.db.custom_str = 0
        self.db.custom_agi = 0
        self.db.costs = {"nuyen": 0, "essence": 0}

    @classmethod
    def at_pre_purchase(self, caller, item, options,
                        dest=None, costs={}, seller="", buyer=""):
        "This is called before an Extra is bought. It should perform any necessary checks and return False if the purchase isn't valid."

        costs = {"nuyen": 0, "essence": 0}
        grades = Grades.__dict__.keys()
        value = pp.Suppress(pp.Word(pp.alphas + " -_':=")) + pp.Word(pp.nums)

        # Define options.
        strength = 0
        agility = 0
        synthetic = False
        grade = "standard"

        # Find the prototype.
        exec("proto = " + item)
        slots = proto['slots']

        synthetic = bool([o for o in options if o in "synthetic"])
        grade = [g for o in options for g in grades if o in g]
        raw_str = [o for o in options if o.startswith("str")]
        raw_agi = [o for o in options if o.startswith("agi")]
        if raw_str:
            strength = int(value.parseString(raw_str[0])[0])
        if raw_agi:
            agility = int(value.parseString(raw_agi[0])[0])
        if grade:
            grade = grade[0]

        s = caller.get_quality("exceptional attribute (strength)")
        if s:
            s = s.values()[0]
        if strength + 3 > caller.db.meta_attr["strength"][1] + s:
            caller.msg(mf.tag + "You can't have a cyberlimb built with higher"
                       " strength than your natural maximum.")
            return False
        a = caller.get_quality("exceptional attribute (agility)")
        if a:
            a = a.values()[0]
        if agility + 3 > caller.db.meta_attr["agility"][1] + a:
            caller.msg(mf.tag + "You can't have a cyberlimb built with higher"
                       " agility than your natural maximum.")
            return False

        # Capacity probably isn't needed in this function, but we can unpack
        # it anyway.
        costs, capacity = self.cyberlimb_costs_and_capacity(
            slots, synthetic, grade, c_agi=0, c_str=0)
        costs["nuyen"] = costs["nuyen"] + (strength + agility) * 5000
        # Merge in essence costs.
        costs.update(proto['costs'])

        return {
            "costs": costs,
            "prototype": item,
            "custom_str": strength,
            "custom_agi": agility,
            "synthetic": synthetic,
            "grade": grade
        }

    @classmethod
    def at_post_purchase(self, options):
        "This is called after an Extra is bought."
        pass

    # Functions that can be called by external modules.
    @classmethod
    def cyberlimb_costs_and_capacity(self, slots, synthetic,
                                     grade, c_agi=0, c_str=0):
        # TODO: Costs and capacity are no longer as tightly associated as
        # they once were. Maybe I should reconsider this.
        slots = [s.lower() for s in slots["body"]]
        costs = {"nuyen": 0}
        # This function doesn't actually care about left or right.
        if "right_arm" in slots or "left_arm" in slots:
            slots += ["right_upper_arm"]
        elif "right_leg" in slots or "left_leg" in slots:
            slots += "right_upper_leg"

        if synthetic:
            source = Synthetic
        else:
            source = Obvious

        if [s for s in slots if "upper_arm" in s]:
            costs["nuyen"] = source.full_arm["cost"]
            capacity = source.full_arm["capacity"]
        elif [s for s in slots if "lower_arm" in s]:
            costs["nuyen"] = source.lower_arm["cost"]
            capacity = source.lower_arm["capacity"]
        elif [s for s in slots if "hand" in s or "foot" in s]:
            costs["nuyen"] = source.hand_foot["cost"]
            capacity = source.hand_foot["capacity"]
        elif [s for s in slots if "upper_leg" in s]:
            costs["nuyen"] = source.full_leg["cost"]
            capacity = source.full_leg["capacity"]
        elif [s for s in slots if "lower_leg" in s]:
            costs["nuyen"] = source.lower_leg["cost"]
            capacity = source.lower_leg["capacity"]
        elif [s for s in slots if "torso" in s]:
            costs["nuyen"] = source.torso["cost"]
            capacity = source.torso["capacity"]
        elif [s for s in slots if "skull" in s]:
            costs["nuyen"] = source.skull["cost"]
            capacity = source.skull["capacity"]

        # Add costs for customized attributes.
        costs["nuyen"] += (c_agi + c_str) * 5000

        return [costs, capacity]
