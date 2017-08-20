from evennia import CmdSet
import command_overrides

class CharacterCmdSet(CmdSet):
    """
    The CharacterCmdSet contains general in-game commands like look,
    get etc available on in-game Character objects. It is merged with
    the PlayerCmdSet when a Player puppets a Character.
    """
    key = "tekmunkeyEvenniaOverridesCharacterCmdSet"
    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        self.add( command_overrides.CmdInventory() )
        self.add( command_overrides.CmdGet( ) )
        self.add( command_overrides.CmdDrop( ) )
        self.add( command_overrides.CmdGive( ) )
        self.add( command_overrides.CmdSay( ) )
        self.add( command_overrides.CmdWhisper( ) )
        self.add( command_overrides.CmdPose( ) )
        self.add( command_overrides.CmdEmit( ) )