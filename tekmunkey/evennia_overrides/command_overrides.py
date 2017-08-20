from django.conf import settings
from evennia.utils import utils, evtable
from tekmunkey.adaptiveDisplay import adaptiveDisplayFunctions

COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)

def getNameAnsi( object ):
    r = object.name
    if object.db.key_ansi is not None:
        r = object.db.key_ansi
    return r

class CmdInventory(COMMAND_DEFAULT_CLASS):
    """
    view inventory

    Usage:
      inventory
      inv

    Shows your inventory.
    """
    key = "inventory"
    aliases = ["inv", "i"]
    locks = "cmd:all()"
    arg_regex = r"$"

    def func(self):
        """check inventory"""
        items = self.caller.contents
        if not items:
            string = "You are not carrying anything."
        else:
            table = evtable.EvTable(border="header")
            for item in items:
                table.add_row("|C%s|n" % item.get_display_name( self.caller ), item.db.desc or "")
            string = "|wYou are carrying:\n%s" % table
        self.caller.msg(string)

class CmdGet(COMMAND_DEFAULT_CLASS):
    """
    pick up something

    Usage:
      get <obj>

    Picks up an object from your location and puts it in
    your inventory.
    """
    key = "get"
    aliases = "grab"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """implements the command."""

        caller = self.caller

        if not self.args:
            caller.msg("Get what?")
            return
        obj = caller.search(self.args, location=caller.location)
        if not obj:
            return
        if caller == obj:
            caller.msg("You can't get yourself.")
            return
        if not obj.access(caller, 'get'):
            if obj.db.get_err_msg:
                caller.msg(obj.db.get_err_msg)
            else:
                caller.msg("You can't get that.")
            return

        obj.move_to(caller, quiet=True)
        caller.msg("You pick up %s." % obj.get_display_name( caller ) )
        for this_looker in self.caller.location.contents:
            if not (this_looker is caller):
                message = caller.get_display_name( this_looker ) + " picks up " + obj.get_display_name( this_looker )
                this_looker.msg( message )
        # calling hook method
        obj.at_get(caller)

class CmdDrop(COMMAND_DEFAULT_CLASS):
    """
    drop something

    Usage:
      drop <obj>

    Lets you drop an object from your inventory into the
    location you are currently in.
    """

    key = "drop"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """Implement command"""

        caller = self.caller
        if not self.args:
            caller.msg("Drop what?")
            return

        # Because the DROP command by definition looks for items
        # in inventory, call the search function using location = caller
        obj = caller.search(self.args, location=caller,
                            nofound_string="You aren't carrying %s." % self.args,
                            multimatch_string="You carry more than one %s:" % self.args)
        if not obj:
            return

        obj.move_to(caller.location, quiet=True)
        caller.msg("You drop %s." % (obj.get_display_name( caller ),))
        for this_looker in self.caller.location.contents:
            if not (this_looker is caller):
                message = caller.get_display_name( this_looker ) + " drops " + obj.get_display_name( this_looker )
                this_looker.msg( message )
        # Call the object script's at_drop() method.
        obj.at_drop(caller)

class CmdGive(COMMAND_DEFAULT_CLASS):
    """
    give away something to someone

    Usage:
      give <inventory obj> = <target>

    Gives an items from your inventory to another character,
    placing it in their inventory.
    """
    key = "give"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """Implement give"""

        caller = self.caller
        if not self.args or not self.rhs:
            caller.msg("Usage: give <inventory object> = <target>")
            return
        to_give = caller.search(self.lhs, location=caller,
                                nofound_string="You aren't carrying %s." % self.lhs,
                                multimatch_string="You carry more than one %s:" % self.lhs)
        target = caller.search(self.rhs)
        if not (to_give and target):
            return
        if target == caller:
            caller.msg("You keep %s to yourself." % to_give.get_display_name( caller ))
            return
        if not to_give.location == caller:
            caller.msg("You are not holding %s." % to_give.get_display_name( caller ))
            return
        # give object
        caller.msg("You give %s to %s." % (to_give.get_display_name( caller ), target.get_display_name( caller )))
        to_give.move_to(target, quiet=True)
        target.msg("%s gives you %s." % (caller.get_display_name( target ), to_give.get_display_name( target )))
        # Call the object script's at_give() method.
        to_give.at_give(caller, target)

class CmdSay(COMMAND_DEFAULT_CLASS):
    """
    speak as your character

    Usage:
      say <message>

    Talk to those in your current location.
    """

    key = "say"
    aliases = ['"', "'"]
    locks = "cmd:all()"

    def func(self):
        """Run the say command"""

        caller = self.caller

        if not self.args:
            caller.msg("Say what?")
            return

        speech = self.args

        # calling the speech hook on the location
        speech = caller.location.at_say(caller, speech)

        # Feedback for the object doing the talking.
        caller.msg('You say, "%s|n"' % speech)

        # Build the string to emit to neighbors.
        emit_string = '%s says, "%s|n"' % ( getNameAnsi( caller ), speech )
        caller.location.msg_contents(text=(emit_string, {"type": "say"}),
                                     exclude=caller, from_obj=caller)


class CmdWhisper(COMMAND_DEFAULT_CLASS):
    """
    Speak privately as your character to another

    Usage:
      whisper <player> = <message>

    Talk privately to those in your current location, without
    others being informed.
    """

    key = "whisper"
    locks = "cmd:all()"

    def func(self):
        """Run the whisper command"""

        caller = self.caller

        if not self.lhs or not self.rhs:
            caller.msg("Usage: whisper <player> = <message>")
            return

        receiver = caller.search(self.lhs)

        if not receiver:
            return

        if caller == receiver:
            caller.msg("You can't whisper to yourself.")
            return

        speech = self.rhs

        # Feedback for the object doing the talking.
        caller.msg( 'You whisper to %s, "%s|n"' % ( getNameAnsi( receiver ), speech ) )

        # Build the string to emit to receiver.
        emit_string = '%s whispers, "%s|n"' % ( getNameAnsi( caller ), speech )
        receiver.msg(text=(emit_string, {"type": "whisper"}), from_obj=caller)


class CmdPose(COMMAND_DEFAULT_CLASS):
    """
    strike a pose

    Usage:
      pose <pose text>
      pose's <pose text>

    Example:
      pose is standing by the wall, smiling.
       -> others will see:
      Tom is standing by the wall, smiling.

    Describe an action being taken. The pose text will
    automatically begin with your name.
    """
    key = "pose"
    aliases = [":", "emote"]
    locks = "cmd:all()"

    def parse(self):
        """
        Custom parse the cases where the emote
        starts with some special letter, such
        as 's, at which we don't want to separate
        the caller's name and the emote with a
        space.
        """
        args = self.args
        if args and not args[0] in ["'", ",", ":"]:
            args = " %s" % args.strip()
        self.args = args

    def func(self):
        """Hook function"""
        if not self.args:
            msg = "What do you want to do?"
            self.caller.msg(msg)
        else:
            msg = "%s%s" % ( getNameAnsi( self.caller ), self.args )
            self.caller.location.msg_contents(text=(msg, {"type": "pose"}),
                                              from_obj=self.caller)

class CmdEmit(COMMAND_DEFAULT_CLASS):
    """
    admin command for emitting message to multiple objects

    Usage:
      @emit[/switches] [<obj>, <obj>, ... =] <message>
      @remit           [<obj>, <obj>, ... =] <message>
      @pemit           [<obj>, <obj>, ... =] <message>

    Switches:
      room : limit emits to rooms only (default)
      players : limit emits to players only
      contents : send to the contents of matched objects too

    Emits a message to the selected objects or to
    your immediate surroundings. If the object is a room,
    send to its contents. @remit and @pemit are just
    limited forms of @emit, for sending to rooms and
    to players respectively.
    """
    key = "@emit"
    aliases = ["@pemit", "@remit"]
    locks = "cmd:all()" # "cmd:perm(emit) or perm(Builders)"
    help_category = "Admin"

    def func(self):
        """Implement the command"""

        caller = self.caller
        args = self.args

        if not args:
            string = "Usage: "
            string += "\n@emit[/switches] [<obj>, <obj>, ... =] <message>"
            string += "\n@remit           [<obj>, <obj>, ... =] <message>"
            string += "\n@pemit           [<obj>, <obj>, ... =] <message>"
            caller.msg(string)
            return

        rooms_only = 'rooms' in self.switches
        players_only = 'players' in self.switches
        send_to_contents = 'contents' in self.switches

        # we check which command was used to force the switches
        if self.cmdstring == '@remit':
            rooms_only = True
            send_to_contents = True
        elif self.cmdstring == '@pemit':
            players_only = True

        if not self.rhs:
            message = self.args
            objnames = [caller.location.key]
        else:
            message = self.rhs
            objnames = self.lhslist

        # send to all objects
        for objname in objnames:
            obj = caller.search(objname, global_search=True)
            if not obj:
                return
            if rooms_only and obj.location is not None:
                caller.msg("%s is not a room. Ignored." % objname)
                continue
            if players_only and not obj.has_player:
                caller.msg("%s has no active player. Ignored." % objname)
                continue
            if obj.access(caller, 'tell'):
                obj.msg(message)
                if send_to_contents and hasattr(obj, "msg_contents"):
                    obj.msg_contents(message)
                    caller.msg("Emitted to %s and contents:\n%s" % (objname, message))
                else:
                    caller.msg("Emitted to %s:\n%s" % (objname, message))
            else:
                caller.msg("You are not allowed to emit to %s." % objname)