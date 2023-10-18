from collections import namedtuple

Ev = namedtuple("Ev", ["category", "name", "sname", "db", "replace", "log"])


class Event:
    GENS_EDITOR_CREATE = Ev("gens", "GENS_EDITOR_CREATE", "create", False, False, True)
    GENS_EDITOR_EDIT = Ev("gens", "GENS_EDITOR_EDIT", "edit", False, False, True)
    GENS_EDITOR_DELETE = Ev("gens", "GENS_EDITOR_DELETE", "delete", False, False, True)
    GENS_EDITOR_TEST = Ev("gens", "GENS_EDITOR_TEST", "test", False, False, False)

    GENS_EDITOR_BACKUP = Ev("gens", "GENS_EDITOR_BACKUP", "", False, False, True)

    GENS_RESULT = Ev("gens", "GENS_RESULT", "result", False, False, False)
    GENS_RESULT_RATELIMIT = Ev(
        "gens", "GENS_RESULT_RATELIMIT", "ratelimit", True, True, True
    )

    GENS_SEARCH = Ev("gens", "GENS_SEARCH", "search", False, False, True)

    LISTS_EDITOR_CREATE = Ev(
        "lists", "LISTS_EDITOR_CREATE", "create", False, False, True
    )
    LISTS_EDITOR_EDIT = Ev("lists", "LISTS_EDITOR_EDIT", "edit", False, False, True)
    LISTS_EDITOR_DELETE = Ev(
        "lists", "LISTS_EDITOR_DELETE", "delete", False, False, True
    )

    GENERAL_RESULT = Ev("general", "GENERAL_RESULT", "result", False, False, False)
    GENERAL_RESULT_RATELIMIT = Ev(
        "general", "GENERAL_RESULT_RATELIMIT", "result", True, True, True
    )
    GENERAL_SUGGEST = Ev("general", "GENERAL_SUGGEST", "suggest", False, False, True)

    PROFILES_INFO_EDIT = Ev(
        "profiles", "PROFILES_INFO_EDIT", "info_edit", True, True, True
    )

    USERS_CHANGE_USERNAME = Ev(
        "users", "USERS_CHANGE_USERNAME", "change_username", True, True, True
    )
