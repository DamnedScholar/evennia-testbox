"""
Utils

This file contains system-agnostic utility functions.

"""

import math
import string
import re
import pyparsing
from dateutil import parser
from pint import UnitRegistry
from django.db.models import Q
import evennia
from evennia.utils.dbserialize import _SaverDict, _SaverList, _SaverSet
from sr5.models import AccountingLog, AccountingIcetray, Ledger


ureg = UnitRegistry()

# TODO: Implement modifiers system here.


class SlotsHandler:
    """
    Handler for the slots system. This handler is designed to be attached to
    objects with a particular @lazy-property name, so it will be referred to as
    `.slots`, though individual games can set that however they like.

    ```
    @lazy_property
    def slots(self):
        return SlotsHandler(self)
    ```

    The purpose of this handler is to sit on a "holder" typeclassed object and
    manage slots for "held" objects. The first thing that should happen is
    using `self.slots.add()` on the holder object to identify the available
    options. `.slots.delete()` can be used to delete or pop old slots.

    By default, a held object can have slots stored on it (the handler will
    check `.db.slots`, `.ndb.slots`, and `.slots` in that order), and
    `self.slots.attach()` will attempt to attach it on all of those slots (it
    should fail if it can't attach on every slot). `self.slots.drop()` will
    remove the target from any of the slots given it. Both of these methods
    have the option to be given a custom `slots` argument, which will override
    the slots on the held object.

    Using the custom `slots` in `attach()` and `drop()` provides some
    customization facility in that you can store *any* object in a slot, not
    just an object that has been set up for it.
    """

    def __init__(self, obj):
        self.obj = obj
        self._objid = obj.id

    def add(self, name, num=0, *slots):
        """
        Create an array of slots, or add additional slots to an existing array.

        Args:
            name: The name of the array.
            *slots: A set of lists, strings, and/or tuples defining slot names.
            num: Any unnamed slots.
        """

        name = "slots_{}".format(name)
        existing = self.obj.attributes.get(name)
        slot_list = []
        for arg in slots:
            if isinstance(arg, list):
                slot_list += arg
            elif isinstance(arg, str):
                slot_list.append(arg)
            elif isinstance(arg, tuple):
                slot_list.append(list(arg))
            else:
                raise ValueError("Only lists, strings, and tuples accepted.")
        # To find where the numbers should start, iterate through numerical
        # keys and store the highest value.
        highest = 0
        if existing:
            for key in existing.keys():
                if isinstance(key, int) and key > highest:
                    highest = key
        for i in range(highest, highest + num):
            slot_list.append(i+1)
        slots = dict(zip(slot_list, [""] * len(slot_list)))

        if not existing:
            new = self.obj.attributes.add(name, slots)

            return True
        else:
            existing.update(slots)
            return True

    # TODO: Apparently named arguments aren't optional just because they have a
    # default value. I need to figure out how to make them optional.

    def delete(self, name, num=0, *slots):
        """
        This will delete slots from an existing array.
        WARNING: If you have anything attached in slots when they are removed,
        the slots' contents will also be removed. This function will return a
        dict of any removed slots and their contents, so it can act as a pop(),
        but if you don't catch that data, it WILL be lost.
        """

        name = "slots_{}".format(name)
        existing = self.obj.attributes.get(name)
        if not existing: # If the named array isn't there, don't bother.
            return False
        slot_list = []
        if not num and not slots:
            self.obj.attributes.remove(name)
        for arg in slots:
            if isinstance(arg, list):
                slot_list += arg
            elif isinstance(arg, str):
                slot_list.append(arg)
            elif isinstance(arg, tuple):
                slot_list.append(list(arg))
            else:
                raise ValueError
        # To find where the numbers should start, iterate through numerical
        # keys and store the highest value.
        highest = 0
        if existing:
            for key in existing.keys():
                if isinstance(key, int) and key > highest:
                    highest = key
        for i in range(highest, highest - num, -1):
            slot_list.append(i)

        deleted = {}

        for slot in slot_list:
            deleted.update({slot: existing.pop(slot)})

        return deleted

    def attach(self, target, slots=None):
        "Attempt to attach the target in all slots it consumes. Optionally, the target's slots may be overridden."

        if not slots:
            slots = target.db.slots
            if not slots:
                slots = target.ndb.slots
                if not slots:
                    try:
                        slots = target.slots
                    except: AttributeError
                        return (False, "No slots detected.")

        modified = {}

        for name in slots:
            array = self.obj.attributes.get("slots_{}".format(name))

            # For any integers in `slots`, remove them and add to list of
            # numbers to be appended.
            highest = 0
            numbered = []
            place = 0
            for slot in slots[name]:
                if isinstance(slot, int):
                    for i in range(highest, highest + slot):
                        numbered.append(i)
                    highest += slot
                    slots[name].pop(place)
                elif not isinstance(slot, str):
                    slots[name].pop(place)
                    slots[name].append(str(slot))

                place += 1

            new = {}

            for slot in slots[name]:
                if slot not in array.keys():
                    return (False, "Slot name not recognized.")
                if array[slot]:
                    return (False, "Insufficient slots.")
                new.update({slot: target})

            highest = 0
            success = 0
            for i in range(0, len(numbered)):
                for j in range(highest, len(array), 1):
                    if array[j] is '':
                        new.update({j: target})
                        success += 1
                        highest = j
                        break

            if success is not len(numbered):
                return (False, "Insufficient slots.")

            array.update(new)
            modified.update(array)

        return modified

    def drop(self, target, slots=None):
        "Attempt to drop the target from all slots it occupies, or the list of slots provided. This function is messy in that it doesn't care if the slots exist or not, it just tries to drop everything it is given."

        if not slots:
            slots = target.db.slots

            if not slots:
                slots = target.ndb.slots
                if not slots:
                    try:
                        slots = target.slots
                    except: AttributeError
                        return (False, "No slots detected.")

        modified = {}

        for name in slots:
            array = self.obj.attributes.get("slots_{}".format(name))

            # For any integers in `slots`, remove them and add to list of
            # numbers to be appended.
            highest = 0
            numbered = []
            place = 0
            for slot in slots[name]:
                if isinstance(slot, int):
                    for i in range(highest, highest + slot):
                        numbered.append(i)
                    highest += slot
                    slots[name].pop(place)
                elif not isinstance(slot, str):
                    slots[name].pop(place)
                    slots[name].append(str(slot))

                place += 1

            new = {}

            for slot in slots[name]:
                if array[slot] is target:
                    new.update({slot: ''})

            highest = 0
            for i in range(0, len(numbered)):
                for entry in array.keys():
                    if isinstance(entry, int) and entry > highest:
                        highest = entry
                for j in range(highest, 0, -1):
                    if array[j] is target:
                        new.update({j: ''})
                        break

            array.update(new)
            modified.update(array)

        return modified


def validate(target, validate, result_categories):
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
    in: Take a list and check if all member of the stat are in the list.
    not in: Take a list and check if no members are in the list.
    contains: Take a list and check that all members are in the stat.
    """
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

        # Grab a reference to the stat to be checked.
        stat = check.get("stat", None)
        # Find out which comparisons to perform.
        s = {
            "max": check.get("max", None),
            "min": check.get("min", None),
            "equals": check.get("equals", None),
            "in": check.get("in", None),
            "not in": check.get("not in", None),
            "contains": check.get("contains", None),
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

            # Check that the stat is not in the list provided.
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

            # Check that the stat contains a member of the list.
            if isinstance(s['contains'], (list)):
                if not set(s['not in']).intersection(list_check):
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
                    "tip": "\"Contains\" values should be a list."
                }]

    result_header, result_text, to_display = "", "", ""
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

        to_display += output + "\n"

    return (ok, to_display)
