from getpass import getpass
import accounts

def prompt_auth():
    while True:
        choice = input("(l)ogin or (c)reate account? ").lower()
        if choice in ("l", "c"):
            return choice

def main():
    print("=== Secure Chat ===")
    choice = prompt_auth()

    user = input("Username: ").strip()
    pw = getpass("Password: ")

    if choice == "c":
        pw_hash = accounts.hash_password(pw)
        if not accounts.create_account(user, pw_hash):
            print("Account already exists.")
            return
        print("Account created.")

    else:
        if not accounts.authenticate_account(user, pw):
            print("Invalid login.")
            return

    print("\nLogged in as", user)
    print("Local chat mode (server not implemented yet)")
    print("Type /quit to exit\n")

    history = []

    while True:
        msg = input("> ")
        if msg == "/quit":
            break
        line = f'{user}: "{msg}"'
        history.append(line)
        print(line)

if __name__ == "__main__":
    main()
