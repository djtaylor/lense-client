# Common options
OPTIONS = [
    {
        "short": "H",
        "long": "host",
        "help": "Specify an alternative API server to connect to.",
        "action": "store"
    },
    {
        "short": "u",
        "long": "user",
        "help": "Specify an API username if not set as an environment variable.",
        "action": "store"
    },
    {
        "short": "g",
        "long": "group",
        "help": "Specify an API group if not set as an environment variable.",
        "action": "store"
    },
    {
        "short": "k",
        "long": "key",
        "help": "Specify an API key if not set as an environment variable.",
        "action": "store"
    }
]