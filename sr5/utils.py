"""
Utils

This file contains system-agnostic utility functions.

"""

import math
import string
import re
import pyparsing
from collections import OrderedDict
from dateutil import parser
from decimal import Decimal
from pint import UnitRegistry
from django.db.models import Q
import evennia
from evennia.utils.dbserialize import _SaverDict, _SaverList, _SaverSet
from sr5.models import AccountingLog, AccountingIcetray, Ledger
wiz = evennia.search_player("#1")[0]


ureg = UnitRegistry()

_GA = object.__getattribute__
_SA = object.__setattr__

# TODO: Implement modifiers system here.


def a_n(words):
    if not words:
        return None
    vocab = ["herb"]

    for word in vocab:
        if words[0:len(word)] is word:
            return "an " + words
    if words[0] in "aeiou":
        return "an " + words
    else:
        return "a " + words


# def high_num(l):
#     "Takes an iterable and returns the largest number, defaulting to 0."
#     if not isinstance(l, (dict, _SaverDict, OrderedDict, list, _SaverList,
#                           set, _SaverSet, frozenset, tuple)):
#         raise Exception("This function requires an iterable.")
#     if isinstance(l, (dict, _SaverDict, OrderedDict)):
#         l = l.keys()
#     else:
#         l = list(l)
#
#     try:
#         return sorted(l)[-1]
#     except IndexError:
#         return 0
#
#
# def low_num(l):
#     "Takes an iterable and returns the largest number, defaulting to 0."
#     if not isinstance(l, (dict, _SaverDict, OrderedDict, list, _SaverList,
#                           set, _SaverSet, frozenset, tuple)):
#         raise Exception("This function requires an iterable.")
#     if isinstance(l, (dict, _SaverDict, OrderedDict)):
#         l = l.keys()
#     else:
#         l = list(l)
#
#     try:
#         return sorted(l)[0]
#     except IndexError:
#         return 0


def itemize(words, case="no change"):
    """
    Takes a list and optional case argument, and converts the list into a
    comma-delimited string with the requested case.
    """
    if not words:
        return None
    if isinstance(words, (int, float, Decimal)):
        words = str(words)
    try:
        a = ""
        if len(words) != 1:
            a = "and "
        words = map(str, words)
        if case in "title":
            words = [word.title() for word in words]
        elif case in "upper":
            words = [word.upper() for word in words]
            a = a.upper()
        elif case in "lower":
            words = [word.lower() for word in words]
        words[len(words) - 1] = "{}{}".format(a, words[len(words) - 1])
        if len(words) == 2:
            j = " "
        else:
            j = ", "
        words = j.join(words)
    except TypeError:
        raise TypeError("itemize() expects an iterable, string, or number.")

    return words


def flatten(d):
    "Takes a dict and returns a list of strings in form `key: value`."
    if not d:
        return None
    output = []

    for key, val in d.items():
        output.append("{}: {}".format(key, val))

    return output


def parse_subtype(stat):
    "Takes a stat and returns a tuple `(name, subtype)`."
    name = pyparsing.Word(pyparsing.alphanums + " .-_/,")
    arg = pyparsing.Suppress("(") + name + pyparsing.ZeroOrMore(
            pyparsing.Suppress(",") + name
          ) + pyparsing.Suppress(")")
    hole = pyparsing.Combine("(" +
                             pyparsing.ZeroOrMore(pyparsing.Suppress("[") ^
                                                  pyparsing.Suppress("]"))
                             + ")")
    parser = name + pyparsing.ZeroOrMore(arg) + pyparsing.ZeroOrMore(hole)

    query = parser.parseString(stat)
    query = [q.strip() for q in query]

    subtype = [""]

    if len(query) > 1:
        if str(query[1]) != '()':
            subtype = query[1:len(query)]

    return (query[0], subtype)


def purge_empty_values(d):
    "Iterates through a dictionary and removes all keys that have no values."

    purge = []
    for item in d:
        if not d[item]:
            purge.append(item)
    for item in purge:
        d.pop(item)

    return d


class StatMsg:
    """
    Lightweight error message object. Will evaluate as a bool with ~ or ==
    operators, and will evaluate as a string if asked to.
    """
    def __init__(self, status, msg):
        self.status = status
        self.msg = msg

    def __eq__(self, other):
        if self.status == False:
            return False
        else:
            return True

    def __invert__(self):
        if self.status:
            return True
        else:
            return False

    def __str__(self):
        return self.msg

    def __getitem__(self, n):
        if n == 0:
            r = self.status
        elif n == 1:
            r = self.msg
        else:
            raise KeyError("StatMsg only has two members.")
        return r


# This is my addition to Evennia's attributes system to allow for the intuitive
# `.db` syntax form to be used for attributes that have categories. This should
# be implemented only for categories that will be used a lot and will remain
# relatively static.
class CatDbHolder(object):
    "Holder for allowing property access of attributes based on categories."
    def __init__(self, obj, name, category="", manager_name='attributes'):
        _SA(self, name, _GA(obj, manager_name))
        _SA(self, 'name', name)
        _SA(self, 'category', category)

    def __getattribute__(self, attrname):
        if attrname == 'all':
            # we allow to overload our default .all
            attr = _GA(self, _GA(
                self, 'name')).get("all", category=_GA(self, 'category'))
            return attr if attr else _GA(self, "all")
        return _GA(self, _GA(
            self, 'name')).get(attrname, category=_GA(self, 'category'))

    def __setattr__(self, attrname, value):
        _GA(self, _GA(
            self, 'name')).add(attrname, value, category=_GA(self, 'category'))

    def __delattr__(self, attrname):
        _GA(self, _GA(
            self, 'name')).remove(attrname, category=_GA(self, 'category'))

    def get_all(self):
        return _GA(self, _GA(self, 'name')).all()
    all = property(get_all)


class LogsHandler:
    """
    Handler for ledgers to compensate for Evennia having really weird behavior
    regarding attributes that have categories.
    """

    def __init__(self, obj):
        self.obj = obj
        self._objid = obj.id

    # @property logs
    def __logs_get(self):
        """
        Attribute handler wrapper. Allows for the syntax
           obj.logs.attrname = value
             and
           value = obj.logs.attrname
             and
           del obj.logs.attrname
             and
           all_attr = obj.logs.all() (unless there is an attribute
                named 'all', in which case that will be returned instead).
        """
        try:
            return self._logs_holder
        except AttributeError:
            self._logs_holder = CatDbHolder(self, 'attributes',
                                           category="Logs")
            return self._logs_holder

    # @db.setter
    def __logs_set(self, value):
        "Stop accidentally replacing the db object"
        string = "Cannot assign directly to db object! "
        string += "Use logs.attr=value instead."
        raise Exception(string)

    # @db.deleter
    def __logs_del(self):
        "Stop accidental deletion."
        raise Exception("Cannot delete the db object!")
    logs = property(__logs_get, __logs_set, __logs_del)


class LedgerHandler:
    """
    Handler for ledgers to compensate for Evennia having really weird behavior
    regarding attributes that have categories.
    """

    def __init__(self, obj):
        self.obj = obj
        self._objid = obj.id

    # @property ldb
    def __ldb_get(self):
        """
        Attribute handler wrapper. Allows for the syntax
           obj.ldb.attrname = value
             and
           value = obj.ldb.attrname
             and
           del obj.ldb.attrname
             and
           all_attr = obj.ldb.all() (unless there is an attribute
                named 'all', in which case that will be returned instead).
        """
        try:
            return self._ldb_holder
        except AttributeError:
            self._ldb_holder = CatDbHolder(self, 'attributes',
                                           category="Ledgers")
            return self._ldb_holder

    # @db.setter
    def __ldb_set(self, value):
        "Stop accidentally replacing the db object"
        string = "Cannot assign directly to db object! "
        string += "Use ldb.attr=value instead."
        raise Exception(string)

    # @db.deleter
    def __ldb_del(self):
        "Stop accidental deletion."
        raise Exception("Cannot delete the db object!")
    ldb = property(__ldb_get, __ldb_set, __ldb_del)


"""
Slots Handler

This class is designed to sit on typeclassed objects and allow for other objects to be attached to configurable slots on the handler-endowed object.

# Built by DamnedScholar (https://github.com/damnedscholar)
"""


class SlotsHandler:
    """
    Handler for the slots system. This handler is designed to be attached to
    objects with a particular @lazy-property name, so it will be referred to as
    `.slots`, though individual games can set that however they like.

    Place on character or other typeclassed object:
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

    def __defrag_nums(self, cats):
        "Worker function to consolidate filled numbered slots."
        if not isinstance(cats, list):
            cats = [cats]

        arrays = self.all(obj=True)
        arrays = [a for a in arrays if a.key in cats]

        for a in arrays:
            slots = a.value
            out = {k: v for k, v in slots.items() if isinstance(k, str)}
            numbered = [(k, v) for k, v in slots.items() if isinstance(k, int)]
            keys = [n[0] for n in numbered]
            values = [n[1] for n in numbered]
            d = len(values) - 1
            empty = [values.pop(0) for i in range(0, d) if values[0] == ""]
            numbered = zip(keys, values + empty)
            out.update(numbered)
            self.obj.attributes.add(a.key, out, category="slots")

    # Public methods
    def all(self, obj=False):
        """
        Args:
            obj (bool): Whether or not to return the attribute objects.
                (Default: False)

        Returns:
            slots (dict): A dict of all slots.
        """
        d = self.obj.attributes.get(category="slots", return_obj=True)

        if not d:
            return {}
        elif not isinstance(d, list):
            d = [d]

        if obj:
            # Return attribute objects if requested.
            return d
        else:
            # Return a dict detached from the database.
            r = {s.key: s.value for s in d}
            return r

    def add(self, slots):
        """
        Create arrays of slots, or add additional slots to existing arrays.

        Args:
            slots (dict): A dict of slots to add. Since you can't add empty
                categories, it would be pointless to pass a list to this
                function, and so it doesn't accept lists for input.

        Returns:
            slots (dict): A dict of slots that have been successfully added.
        """

        if not isinstance(slots, (dict, _SaverDict)):
            raise Exception("You have to declare slots in the form "
                            "`{key: [values]}`.")

        wiz.msg("Gonna add some slots! Yeah!")

        arrays = {a.key: a for a in self.obj.slots.all(obj=True)}
        modified = {}
        for name in slots:
            existing = arrays.get(name, False)
            self.obj.location.msg("-> Inspecting {}: {}".format(name, existing))
            # Add all string values to the slot list.
            to_add = [k for k in slots[name] if isinstance(k, str)]
            # Iterate through numerical values in the input and store the sum.
            requirement = [n for n in slots[name] if isinstance(n, int)] + [0]
            requirement = sum(requirement)
            highest = 0
            if existing:
                array = existing.value
                numbered = [k for k in array if isinstance(k, int)] + [0]
                highest = sorted(numbered)[-1]
            for i in range(highest, highest + requirement):
                to_add.append(i+1)
            to_add = {slot: "" for slot in to_add}

            if not existing:
                self.obj.attributes.add(name, to_add, category="slots")
                new = self.obj.attributes.get(name, category="slots")
                modified.update({name: new})
            else:
                array.update(to_add)
                modified.update({name: array})

        return modified

    def delete(self, slots):
        """
        This will delete slots from an existing array.
        WARNING: If you have anything attached in slots when they are removed,
        the slots' contents will also be removed. This function will return a
        dict of any removed slots and their contents, so it can act as a pop(),
        but if you don't catch that data, it WILL be lost.

        Args:
            slots (list or dict): Slot categories or individual slots to
                delete.

        Returns:
            slots (dict): A dict of slots that have been successfully deleted
                and their contents.
        """

        if not isinstance(slots, (dict, _SaverDict, list, _SaverList)):
            raise Exception("You have to declare slots in the form "
                            "`{key: [values]}`, or categories in the form "
                            "`[values]`.")

        arrays = {a.key: a for a in self.obj.slots.all(obj=True)}
        deleted = {}
        for name in slots:
            existing = arrays.get(name, False)
            del_temp = {}
            if not existing:
                # If the named array isn't there, skip to the next one.
                break
            array = existing.value

            if isinstance(slots, (list, _SaverList)):
                # If the input is a list, it is interpreted as a list of
                # category names and all slots are deleted.
                deleted.update({name: array})
                self.obj.attributes.remove(name, category="slots")
            elif isinstance(slots, (dict, _SaverDict)):
                # If the input is a dict, only the specific slots indicated
                # will be deleted.
                self.__defrag_nums(existing.key)  # Just in case.
                named = {k: v for k, v in array.items()
                         if isinstance(k, str)}
                numbered = {k: v for k, v in array.items()
                            if isinstance(k, int)}
                to_del = [s for s in slots[name] if isinstance(s, str)]
                highest = sorted(numbered.keys() + [0])[-1]
                del_num = sum([n for n in slots[name] if isinstance(n, int)])
                to_del = to_del + [i for i
                                   in range(highest, highest - del_num, -1)]

                del_temp = {d: array.pop(d) for d in to_del}
                deleted.update({name: del_temp})

        return deleted

    def attach(self, target, slots=None):
        """
        Attempt to attach the target in all slots it consumes. Optionally, the
        target's slots may be overridden.

        Args:
            target (object): The object to be attached.
            slots (list or dict, optional): If slot instructions are given,
                this will completely override any slots on the object.

        Returns:
            slots (dict): A dict of slots that `target` has attached to.
        """

        if not slots:
            slots = target.db.slots
            if not slots:
                slots = target.ndb.slots
                if not slots:
                    try:
                        slots = target.slots
                    except AttributeError:
                        raise Exception("No slots detected.")

        modified = {}

        if not isinstance(slots, (dict, _SaverDict, list, _SaverList)):
            raise Exception("You have to declare slots in the form "
                            "`{key: [values]}`, or categories in the form "
                            "`[values]`.")

        arrays = {a.key: a for a in self.obj.slots.all(obj=True)}
        for name in slots:
            array = arrays.get(name, False)
            if not array:
                raise Exception("You need to add slots before you can "
                                "attach things to them.")
            else:
                array = array.value

            new = {}

            if isinstance(slots, (dict, _SaverDict)):
                # Get the number of open slots, then count to see if there are
                # enough for the attachment.
                numbered = [n for n in array.keys()
                            if isinstance(n, int) and not array[n]]
                requirement = [n for n in slots[name] if isinstance(n, int)]
                requirement = sum(requirement + [0])
                if len(numbered) < requirement:
                    raise Exception("You're running out of numbered "
                                    "slots. You need to add or free up slots "
                                    "before you can attach this.")

                if numbered:
                    new.update({numbered[i]: target
                                for i in range(0, requirement)})

                # Get the list of open named slots and check to see if all of
                # the requested slots are members of them.
                named = [n for n in array.keys()
                         if isinstance(n, str) and not array[n]]
                requirement = [n for n in slots[name] if isinstance(n, str)]
                if requirement and not set(requirement).issubset(named):
                    raise Exception("You're running out of named slots. "
                                    "You need to add or free up slots before "
                                    "you can attach this.")

                if named:
                    new.update({req: target
                                for req in requirement})

            elif isinstance(slots, (list, _SaverList)):
                for slot, contents in array.items():
                    if contents == "":
                        new.update({slot: target})

            array.update(new)
            modified.update({name: new})

        return modified

    def drop(self, target, slots=None):
        """
        Attempt to drop the target from all slots it occupies, or the slots
        provided. This function is messy in that it doesn't care if the
        slots exist or not, it just tries to drop everything it is given. This
        function will return a dict of any emptied slots, so it can act as a
        pop(), but if you don't catch that data, it WILL be lost.

        Args:
            target (object or `None`): The object being dropped.
            slots (dict or list, optional): Slot categories or individual slots
                to drop from.

        Returns:
            slots (dict): A dict of slots that have been emptied.
        """

        arrays = self.obj.slots.all()
        if not slots:
            slots = arrays.keys()

        if not isinstance(slots, (dict, _SaverDict, list, _SaverList)):
            raise Exception("You have to declare slots in the form "
                            "`{key: [values]}`, or categories in the form "
                            "`[values]`.")

        modified = {}

        # If no slots are declared, the object should be dropped from all slots
        # without regard for which slots the object thinks that it should be
        # occupying.
        if not arrays:
            raise Exception("You don't seem to have any slots to use.")
        if not slots:
            slots = [cat for cat in arrays.keys()]

        for name in slots:
            new = {}
            mod = {}
            array = arrays[name]

            if isinstance(slots, (list, _SaverList)):
                # If the input is a list, it is interpreted as a list of
                # category names and all slots are emptied of the target.
                for slot, contents in array.items():
                    if (target and contents is target) or not target:
                        new.update({slot: ''})
                        mod.update({slot: contents})
            elif isinstance(slots, (dict, _SaverDict)):
                # If the input is a dict, only named slots will be emptied.
                # Numbered slots should be specified as a single number.
                i = 0
                numbered = [k for k in slots[name] if isinstance(k, int)]
                numbered = [i + 1 for k in numbered for i in range(i, k)]
                named = [k for k in slots[name] if isinstance(k, str)]
                for slot in named:
                    if (target and array[slot] is target) or not target:
                        new.update({slot: ''})
                        mod.update({slot: array[slot]})
                for i in range(0, len(numbered)):
                    for check in array:
                        if isinstance(check, int) and array[check] is target:
                            new.update({check: ''})
                            mod.update({check: array[check]})

            else:
                raise Exception("The slots requested are not in an "
                                "appropriate type (a list of attribute names, "
                                "or a dict of category and slot names).")

            arrays[name].update(new)
            modified.update({name: mod})

        self.__defrag_nums(modified.keys())
        return {k: v for k, v in modified.items() if v}

    def replace(self, target, slots=None):
        """
        Works exactly like `.slots.attach`, but first invokes `.slots.drop` on
        all requested slots.

        Args:
            target (object): The object to be attached.
            slots (list or dict, optional): If slot instructions are given,
                this will completely override any slots on the object.

        Returns:
            results (tuple): The results of both commands are returned as a
                tuple in the form `(drop, attach)`.
        """

        if not slots:
            slots = target.db.slots
            if not slots:
                slots = target.ndb.slots
                if not slots:
                    try:
                        slots = target.slots
                    except AttributeError:
                        raise Exception("You have to either have slots on "
                                        "the target or declare them in the "
                                        "method call.")

        drop = self.obj.slots.drop(None, slots)
        attach = self.obj.slots.attach(target, slots)

        return (drop, attach)

    def where(self, target):
        """
        Returns:
            slots (dict): Slots where `target` is attached.
        """

        arrays = self.obj.slots.all()
        # Filter out all empty entries.
        r = {name: [s for s, c in slots.items() if c is target]
             for name, slots in arrays.items()}
        r = {name: contents for name, contents in r.items() if contents}

        return r


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
