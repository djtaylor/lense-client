class ClientHandler_Base(object):
    """
    Base class for command handlers.
    """
    def __init__(self, handler):
        LENSE.CLIENT.ARGS.construct(
            desc = self.desc,
            opts = self.options,
            cmds = self.commands,
            base = False
        )
        
        # Handler / command
        self.handler = handler
        self.command = LENSE.CLIENT.ARGS.get('command')
    
    def run(self):
        """
        Public method for running the command handler.
        """
    
        # Unsupported command
        if not self.command in self.commands:
            LENSE.CLIENT.ARGS.help()
            LENSE.die("\nUnsupported command: {0}\n".format(self.command))
    
        # Run the command
        getattr(self, self.command)()
    
    def help(self):
        """
        Return the help prompt for the VMware command handler.
        """
        LENSE.CLIENT.ARGS.help()