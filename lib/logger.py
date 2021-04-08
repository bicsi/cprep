from colorama import Fore 


def warning(message: str, requires_input=False):
    # print()
    print(f"{Fore.YELLOW}[WARNING] {message}{Fore.RESET}")
    if requires_input:
        input("Press [ENTER] to continue: ")
    print()