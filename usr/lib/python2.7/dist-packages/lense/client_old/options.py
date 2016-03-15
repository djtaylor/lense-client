# Common options
OPTIONS = [
    {
        "short": "d",
        "long": "detailed",
        "help": "Show detailed information when listing objects.",
        "action": "store_true"
    },
    {
        "short": "c",
        "long": "count",
        "help": "Return an object count instead.",
        "action": "store_true"
    },
    {
        "short": "f",
        "long": "filter",
        "help": (
            "\nSQL Filtering:\n\n"
            "MATCHING:\n"
            "> Equality:      --filter='attr=val' OR --filter='attr==val'\n"
            "> Not Equal:     --filter='attr!=val' OR --filter='attr<>val'\n"
            "> Like:          --filter='attr~=%%val%%'\n"
            "> Greater/Equal: --filter='attr>=3245' OR --filter='attr>3245'\n"
            "> Less/Equal:    --filter='attr<=3245' OR --filter='attr<3245'\n"
            "> Not Greater:   --filter='attr!>3245'\n"
            "> Not Less:      --filter='attr!<3245'\n"
            
            "\n"
            "OPERATORS:\n"
            "> AND:           --filter='attr==123&&another!=3456536'\n"
            "> OR:            --filter='attr==123||another!=3456536'\n"
            "\n"
        ),
        "action": "store"
    },
    {
        "short": "s",
        "long": "sum",
        "help": (
            "\nSum Attribute:\n\n"
            "> Example:       powertools vmware list_vms --sum='memory'\n\n"
        ),
        "action": "store"
    },
    {
        "short": "a",
        "long": "attrs",
        "help": (
            "\nAttribute Filtering:\n\n"
            "> Single:        --attrs='attr'\n"
            "> Multiple:      --attrs='attr,another,more'\n"
            "\n"
        ),
        "action": "store"
    }
]