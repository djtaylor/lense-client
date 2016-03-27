class ClientHandler_Base(object):
    """
    Base class for command handlers.
    """
    def __init__(self, handler):
        LENSE.CLIENT.ARGS.construct(
            desc = self.desc,
            opts = self.options,
            cmds = self.commands,
            objs = getattr(self, 'objects', None),
            base = False
        )
        
        # Handler / command
        self.handler = handler
        self.command = LENSE.CLIENT.ARGS.get('command')
    
    def run(self):
        """
        Public method for running the command handler.
        """
    
        # If commands are supported
        if self.commands:
            if not self.command in self.commands:
                LENSE.CLIENT.ARGS.help()
                LENSE.die("\nUnsupported command: {0}\n".format(self.command))
    
            # Run the method if it exists
            if hasattr(self, self.command) and callable(getattr(self, self.command)):
                return getattr(self, self.command)()
    
        # Run a default method if found
        if hasattr(self, 'default') and callable(getattr(self, 'default')):
            return self.default()
            
        # No appropriate method found
        LENSE.die('No method found for command "{0}" and no default method found'.format(self.command))
    
    def help(self):
        """
        Return the help prompt for the VMware command handler.
        """
        LENSE.CLIENT.ARGS.help()