def print_system(message) -> str:
    print(f"\033[0;0m{message}")
    return message


def print_assistant(message="", end: str = "\n", flush: bool = False) -> str:
    print(f"\033[92m{message}", end=end, flush=flush)
    return message


def user_input(message="") -> str:
    return input(f"\033[1;34m{message}")
