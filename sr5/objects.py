"""
Object

These objects are used by the system package. This file should be used mostly
for prototypes and parents.

"""
from evennia import DefaultObject
from sr5.data.ware import Grades, Obvious, Synthetic

# TODO: Remove the Object class. I'm just keeping it around for reference
# as I figure out what Extra needs.
class Object(DefaultObject):
    """
    * Base properties defined/available on all Objects

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved to
                           database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
                                  back to this class
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     player (Player) - controlling player (if any, only set together with
                       sessid below)
     sessid (int, read-only) - session id (if any, only set together with
                       player above). Use `sessions` handler to get the
                       Sessions directly.
     location (Object) - current location. Is None if this is a room
     home (Object) - safety start-location
     sessions (list of Sessions, read-only) - returns all sessions connected
                       to this object
     has_player (bool, read-only)- will only return *connected* players
     contents (list of Objects, read-only) - returns all objects inside this
                       object (including exits)
     exits (list of Objects, read-only) - returns all exits from this
                       object, if any
     destination (Object) - only set if this object is an exit.
     is_superuser (bool, read-only) - True/False if this user is a superuser

    * Handlers available

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                             self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create
                             a database entry when storing data
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().
     sessions - sessions-handler. Get Sessions connected to this
                object with sessions.get()

    * Helper methods (see src.objects.objects.py for full headers)

     search(ostring, global_search=False, attribute_name=None,
             use_nicks=False, location=None, ignore_errors=False, player=False)
     execute_cmd(raw_string)
     msg(text=None, **kwargs)
     msg_contents(message, exclude=None, from_obj=None, **kwargs)
     move_to(destination, quiet=False, emit_to_obj=None, use_destination=True)
     copy(new_key=None)
     delete()
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False)
     check_permstring(permstring)

    * Hooks (these are class methods, so args should start with self):

     basetype_setup()     - only called once, used for behind-the-scenes
                            setup. Normally not modified.
     basetype_posthook_setup() - customization in basetype, after the object
                            has been created; Normally not modified.

     at_object_creation() - only called once, when object is first created.
                            Object customizations go here.
     at_object_delete() - called just before deleting an object. If returning
                            False, deletion is aborted. Note that all objects
                            inside a deleted object are automatically moved
                            to their <home>, they don't need to be removed here.

     at_init()            - called whenever typeclass is cached from memory,
                            at least once every server restart/reload
     at_cmdset_get(**kwargs) - this is called just before the command handler
                            requests a cmdset from this object. The kwargs are
                            not normally used unless the cmdset is created
                            dynamically (see e.g. Exits).
     at_pre_puppet(player)- (player-controlled objects only) called just
                            before puppeting
     at_post_puppet()     - (player-controlled objects only) called just
                            after completing connection player<->object
     at_pre_unpuppet()    - (player-controlled objects only) called just
                            before un-puppeting
     at_post_unpuppet(player) - (player-controlled objects only) called just
                            after disconnecting player<->object link
     at_server_reload()   - called before server is reloaded
     at_server_shutdown() - called just before server is fully shut down

     at_access(result, accessing_obj, access_type) - called with the result
                            of a lock access check on this object. Return value
                            does not affect check result.

     at_before_move(destination)             - called just before moving object
                        to the destination. If returns False, move is cancelled.
     announce_move_from(destination)         - called in old location, just
                        before move, if obj.move_to() has quiet=False
     announce_move_to(source_location)       - called in new location, just
                        after move, if obj.move_to() has quiet=False
     at_after_move(source_location)          - always called after a move has
                        been successfully performed.
     at_object_leave(obj, target_location)   - called when an object leaves
                        this object in any fashion
     at_object_receive(obj, source_location) - called when this object receives
                        another object

     at_traverse(traversing_object, source_loc) - (exit-objects only)
                              handles all moving across the exit, including
                              calling the other exit hooks. Use super() to retain
                              the default functionality.
     at_after_traverse(traversing_object, source_location) - (exit-objects only)
                              called just after a traversal has happened.
     at_failed_traverse(traversing_object)      - (exit-objects only) called if
                       traversal fails and property err_traverse is not defined.

     at_msg_receive(self, msg, from_obj=None, **kwargs) - called when a message
                             (via self.msg()) is sent to this obj.
                             If returns false, aborts send.
     at_msg_send(self, msg, to_obj=None, **kwargs) - called when this objects
                             sends a message to someone via self.msg().

     return_appearance(looker) - describes this object. Used by "look"
                                 command by default
     at_desc(looker=None)      - called by 'look' whenever the
                                 appearance is requested.
     at_get(getter)            - called after object has been picked up.
                                 Does not stop pickup.
     at_drop(dropper)          - called when this object has been dropped.
     at_say(speaker, message)  - by default, called if an object inside this
                                 object speaks

     """
    pass


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
        self.db.slot = (False)
        self.db.slot_list = []
        # self.db.slot = (True, ["right_upper_arm", "right_lower_arm", "right_hand"])

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
        self.db.slot = (True)
        self.db.slot_list = []

    # Initial setup functions called by the prototype.
    def apply_costs_and_capacity(self, slot_list, synthetic):
        results = Aug_Methods.apply_costs_and_capacity(
            Aug_Methods(), slot_list, synthetic
        )

        self.db.cost = results[0]
        self.db.capacity = results[1]

    def apply_customizations(self):
        self.db.strength += self.db.custom_str
        self.db.agility += self.db.custom_agi

        customizations = self.db.custom_agi + self.db.custom_str
        self.db.cost += customizations * 5000

    def apply_grade(self):
        grade = getattr(Grades, self.db.grade)

        self.db.cost = self.db.cost * grade["cost"]
        self.db.essence = self.db.essence * grade["essence"]

class Aug_Methods():
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
