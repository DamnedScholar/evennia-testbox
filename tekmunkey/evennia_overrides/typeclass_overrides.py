from evennia import DefaultObject as baseDefaultObject, DefaultCharacter as baseDefaultCharacter, DefaultRoom as baseDefaultRoom, DefaultExit as baseDefaultExit, DefaultChannel as baseDefaultChannel
from tekmunkey.devUtils import stringExtends

#
# Do your myGameDir/typeclasses/somefile.py imports like this:
#
# ie: for objects.py:
# #from evennia import DefaultObject
# from tekmunkey.evennia_overrides.typeclass_overrides import tekDefaultObject as DefaultObject
#
# * yes, just comment out the default import (that's why there's a second comment marker above) and then import the
#   tekmunkey.evennia_overrides object as the new DefaultObject.  Why?  Because that's the only change you have to make
#   and then if you want to switch back all you have to do is uncomment the original import and comment or delete the
#   tekmunkey import.  EZ-PZ
#
# or for characters.py:
# #from evennia import DefaultCharacter
# from tekmunkey.evennia_overrides.typeclass_overrides import tekDefaultCharacter as DefaultCharacter
#
# * and so on for rooms and exits
#

def doObjectName_atCreate( targetobject ):
    ansistring_object_key = stringExtends.ansiStringClass( targetobject.key )
    # use the user's Text, not the ansiTextFormat() which is for output measurement
    if ansistring_object_key.isTextDecorated():
        # reset key if and only if it is decorated with ANSI tags to begin with
        # otherwise key is already set
        # use the stripped/formatted text
        targetobject.key = ansistring_object_key.rawTextFormat( )
    # we do need to update the key_ansi value regardless tho
    targetobject.db.key_ansi = ansistring_object_key.Text
    targetobject.save()

def doObjectName_atRename( targetobject, oldname, newname ):
    if not hasattr( targetobject, "keyNameChangeRepeating" ):
        ansistring_object_newname = stringExtends.ansiStringClass( newname )
        if ansistring_object_newname.isTextDecorated( ) :
            # reset key if and only if it is decorated with ANSI tags to begin with
            # otherwise key is already set
            # use the stripped/formatted text
            targetobject.keyNameChangeRepeating = 0
            targetobject.key = ansistring_object_newname.rawTextFormat( )
        # this is not part of the preceding if, it is not an elif, it is done regardless
        targetobject.db.key_ansi = newname
        # write the object back to the db
        targetobject.save( )
    else:
        del targetobject.keyNameChangeRepeating

"""
Object

The Object is the "naked" base class for things in the game world.

Note that the default Character, Room and Exit does not inherit from
this Object, but from their respective default implementations in the
evennia library. If you want to use this class as a parent to change
the other types, you can do so by adding this as a multiple
inheritance.

"""
class tekDefaultObject(baseDefaultObject):
    """
    This is the root typeclass object, implementing an in-game Evennia
    game object, such as having a location, being able to be
    manipulated or looked at, etc. If you create a new typeclass, it
    must always inherit from this object (or any of the other objects
    in this file, since they all actually inherit from BaseObject, as
    seen in src.object.objects).

    The BaseObject class implements several hooks tying into the game
    engine. By re-implementing these hooks you can control the
    system. You should never need to re-implement special Python
    methods, such as __init__ and especially never __getattribute__ and
    __setattr__ since these are used heavily by the typeclass system
    of Evennia and messing with them might well break things for you.


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

    def getInventoryNames( self, allowdbref ):
        """
        Gets the names of the object's contents as an array of strings.

        :param allowdbref: {bool} If true, returns the value of get_display_name instead of key_ansi.  Whether
                                  this actually includes the object's dbref or not depends upon the viewer's privilege
                                  level relative to the object in question.
        :return: {array of str} An array of strings representing the names of the object's contents.
        """
        r = []
        for item in self.contents:
            item_name = item.db.key_ansi
            if allowdbref:
                item_name = item.get_display_name(self)
            r.append( item_name )
        return r

    #
    # We can't do ansi-stripping at_object_creation because Evennia apparently calls the hook before actually setting
    # the key/name itself, so it clobbers our ANSI fixing.  posthook_setup does the trick since it's called at the end
    # of DefaultObject.at_first_save instead of at the beginning
    #
    def basetype_posthook_setup(self):
        """
        Called once, after basetype_setup and at_object_creation. This
        should generally not be overloaded unless you are redefining
        how a room/exit/object works. It allows for basetype-like
        setup after the object is created. An example of this is
        EXITs, who need to know keys, aliases, locks etc to set up
        their exit-cmdsets.

        """
        super( tekDefaultObject, self ).basetype_posthook_setup()
        doObjectName_atCreate( self )


    def at_rename( self, oldname, newname ):
        super( tekDefaultObject, self ).at_rename( oldname, newname )
        doObjectName_atRename( self, oldname, newname )

    def get_display_name(self, looker, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            looker (TypedObject): The object or player that is looking
                at/getting inforamtion for this object.

        Returns:
            name (str): A string containing the name of the object,
                including the DBREF if this user is privileged to control
                said object.

        Notes:
            This function could be extended to change how object names
            appear to users in character, but be wary. This function
            does not change an object's keys or aliases when
            searching, and is expected to produce something useful for
            builders.

        """
        return_value = self.key
        if self.db.key_ansi is not None:
            return_value = self.db.key_ansi
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return_value = "{}(#{})".format(return_value, self.id)
        return return_value

    def at_msg_receive( self, text = None, **kwargs ):
        r = super( tekDefaultObject, self ).at_msg_receive( text, ** kwargs )
        r = True # just make sure this is True regardless of implementation
        return r

"""
Characters

Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
class tekDefaultCharacter(baseDefaultCharacter):
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


    #
    # We can't do ansi-stripping at_object_creation because Evennia apparently calls the hook before actually setting
    # the key/name itself, so it clobbers our ANSI fixing.  posthook_setup does the trick since it's called at the end
    # of DefaultObject.at_first_save instead of at the beginning
    #
    def basetype_posthook_setup( self ) :
        """
        Called once, after basetype_setup and at_object_creation. This
        should generally not be overloaded unless you are redefining
        how a room/exit/object works. It allows for basetype-like
        setup after the object is created. An example of this is
        EXITs, who need to know keys, aliases, locks etc to set up
        their exit-cmdsets.

        """
        super( tekDefaultCharacter, self ).basetype_posthook_setup( )
        doObjectName_atCreate( self )

    def at_rename( self, oldname, newname ):
        super( tekDefaultCharacter, self ).at_rename( oldname, newname )
        doObjectName_atRename( self, oldname, newname )

    def get_display_name(self, looker, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            looker (TypedObject): The object or player that is looking
                at/getting inforamtion for this object.

        Returns:
            name (str): A string containing the name of the object,
                including the DBREF if this user is privileged to control
                said object.

        Notes:
            This function could be extended to change how object names
            appear to users in character, but be wary. This function
            does not change an object's keys or aliases when
            searching, and is expected to produce something useful for
            builders.

        """
        return_value = self.key
        if self.db.key_ansi is not None:
            return_value = self.db.key_ansi
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return_value = "{}(#{})".format(return_value, self.id)
        return return_value

    def at_msg_receive( self, text = None, **kwargs ):
        r = super( tekDefaultCharacter, self ).at_msg_receive( text, ** kwargs )
        r = True # just make sure this is True regardless of implementation
        return r

"""
Room

Rooms are simple containers that has no location of their own.

"""
class tekDefaultRoom(baseDefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """


    #
    # We can't do ansi-stripping at_object_creation because Evennia apparently calls the hook before actually setting
    # the key/name itself, so it clobbers our ANSI fixing.  posthook_setup does the trick since it's called at the end
    # of DefaultObject.at_first_save instead of at the beginning
    #
    def basetype_posthook_setup( self ) :
        """
        Called once, after basetype_setup and at_object_creation. This
        should generally not be overloaded unless you are redefining
        how a room/exit/object works. It allows for basetype-like
        setup after the object is created. An example of this is
        EXITs, who need to know keys, aliases, locks etc to set up
        their exit-cmdsets.

        """
        super( tekDefaultRoom, self ).basetype_posthook_setup( )
        doObjectName_atCreate( self )

    def at_rename( self, oldname, newname ):
        super( tekDefaultRoom, self ).at_rename( oldname, newname )
        doObjectName_atRename( self, oldname, newname )

    def get_display_name(self, looker, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            looker (TypedObject): The object or player that is looking
                at/getting inforamtion for this object.

        Returns:
            name (str): A string containing the name of the object,
                including the DBREF if this user is privileged to control
                said object.

        Notes:
            This function could be extended to change how object names
            appear to users in character, but be wary. This function
            does not change an object's keys or aliases when
            searching, and is expected to produce something useful for
            builders.

        """
        return_value = self.key
        if self.db.key_ansi is not None:
            return_value = self.db.key_ansi
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return_value = "{}(#{})".format(return_value, self.id)
        return return_value

    def at_msg_receive( self, text = None, **kwargs ):
        r = super( tekDefaultRoom, self ).at_msg_receive( text, ** kwargs )
        r = True # just make sure this is True regardless of implementation
        return r

"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
class tekDefaultExit(baseDefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_after_traverse(traveller, source_loc) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """


    #
    # We can't do ansi-stripping at_object_creation because Evennia apparently calls the hook before actually setting
    # the key/name itself, so it clobbers our ANSI fixing.  posthook_setup does the trick since it's called at the end
    # of DefaultObject.at_first_save instead of at the beginning
    #
    def basetype_posthook_setup( self ) :
        """
        Called once, after basetype_setup and at_object_creation. This
        should generally not be overloaded unless you are redefining
        how a room/exit/object works. It allows for basetype-like
        setup after the object is created. An example of this is
        EXITs, who need to know keys, aliases, locks etc to set up
        their exit-cmdsets.

        """
        super( tekDefaultExit, self ).basetype_posthook_setup( )
        doObjectName_atCreate( self )

    def at_rename( self, oldname, newname ):
        super( tekDefaultExit, self ).at_rename( oldname, newname )
        doObjectName_atRename( self, oldname, newname )

    def get_display_name(self, looker, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            looker (TypedObject): The object or player that is looking
                at/getting inforamtion for this object.

        Returns:
            name (str): A string containing the name of the object,
                including the DBREF if this user is privileged to control
                said object.

        Notes:
            This function could be extended to change how object names
            appear to users in character, but be wary. This function
            does not change an object's keys or aliases when
            searching, and is expected to produce something useful for
            builders.

        """
        return_value = self.key
        if self.db.key_ansi is not None:
            return_value = self.db.key_ansi
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return_value = "{}(#{})".format(return_value, self.id)
        return return_value

    def at_msg_receive( self, text = None, **kwargs ):
        r = super( tekDefaultExit, self ).at_msg_receive( text, ** kwargs )
        r = True # just make sure this is True regardless of implementation
        return r