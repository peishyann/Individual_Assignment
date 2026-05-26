
import os
import sys
from typing import Optional
import pandas as pd

from functions import verify_user, calculate_tax, save_to_csv, read_from_csv

USERS_FILE = "users.csv"
DATA_FILE = "tax_records.csv"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter to continue...")


def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame(columns=["user_id", "ic_number"])
        df.to_csv(USERS_FILE, index=False)


def load_users() -> pd.DataFrame:
    ensure_users_file()
    try:
        return pd.read_csv(USERS_FILE, dtype=str).fillna("")
    except Exception:
        df = pd.DataFrame(columns=["user_id", "ic_number"])
        df.to_csv(USERS_FILE, index=False)
        return df


def save_users(df: pd.DataFrame):
    df.to_csv(USERS_FILE, index=False)


def is_registered(user_id: str) -> bool:
    users = load_users()
    return any(users["user_id"] == user_id)


def register_flow() -> Optional[tuple]:
    clear_screen()
    print("=== Registration ===")
    user_id = input("Choose a user ID: ").strip()

    if not user_id:
        print("User ID cannot be empty.")
        pause()
        return None

    users = load_users()
    if any(users["user_id"] == user_id):
        print("This user ID is already registered. Please log in instead.")
        pause()
        return None

    ic = input("Enter your IC number (12 digits, no dashes/spaces): ").strip()
    if not ic.isdigit() or len(ic) != 12:
        print("Invalid IC. It must be exactly 12 digits.")
        pause()
        return None

    users = pd.concat([users, pd.DataFrame([{"user_id": user_id, "ic_number": ic}])], ignore_index=True)
    save_users(users)
    print("\nRegistration successful.")

    print("\nPlease log in to continue.")
    pwd = input("Enter password (last 4 digits of your IC): ").strip()
    if verify_user(ic, pwd):
        print("Login successful.")
        pause()
        return user_id, ic
    else:
        print("Login failed. Password does not match last 4 digits of IC.")
        pause()
        return None


def login_flow() -> Optional[tuple]:

    clear_screen()
    print("=== Login ===")
    user_id = input("User ID: ").strip()
    users = load_users()

    row = users[users["user_id"] == user_id]
    if row.empty:
        print("No such user ID. Please register first.")
        pause()
        return None

    ic = row.iloc[0]["ic_number"]
    pwd = input("Password (last 4 digits of your IC): ").strip()

    if verify_user(ic, pwd):
        print("Login successful.")
        pause()
        return user_id, ic
    else:
        print("Login failed. Incorrect password.")
        pause()
        return None


def prompt_float(name: str, minimum: float = 0.0) -> float:
    while True:
        raw = input(f"Enter {name}: ").strip().replace(",", "")
        try:
            val = float(raw)
            if val < minimum:
                print(f"{name} cannot be less than {minimum}.")
                continue
            return val
        except ValueError:
            print(f"Invalid number for {name}. Try again.")


def handle_new_calculation(ic_number: str):
    clear_screen()
    print("=== New Tax Calculation ===")
    income = prompt_float("Annual income (RM)", 0.0)
    relief = calculate_detailed_relief()

    tax_payable = calculate_tax(income, relief)

    clear_screen()
    print("=== Final Tax Result ===")
    print(f"Income (RM):       {income:,.2f}")
    print(f"Tax relief (RM):   {relief:,.2f}")
    print(f"Tax payable (RM):  {tax_payable:,.2f}")

    record = {
        "ic_number": ic_number,
        "income": income,
        "tax_relief": relief,
        "tax_payable": tax_payable,
    }
    try:
        save_to_csv(record, DATA_FILE)
        print("\nRecord saved.")
    except Exception as e:
        print(f"\nFailed to save record: {e}")

    pause()


def calculate_detailed_relief() -> float:
    clear_screen()
    print("=== Tax Relief Questionnaire ===")

    total_relief = 0.0

    # 1. Individual Relief (Fixed)
    print("1. Individual Relief: RM 9,000.00 (Applied automatically)")
    total_relief += 9000.0

    # 2. Spouse Relief (Conditional)
    while True:
        spouse = input("2. Do you have a qualifying spouse (no income or income <= RM4,000)? (y/n): ").strip().lower()
        if spouse in ['y', 'n']:
            if spouse == 'y':
                total_relief += 4000.0
            break
        print("Please enter 'y' for yes or 'n' for no.")

    # 3. Child Relief (Multiplied)
    while True:
        try:
            children = int(input("3. Number of qualifying children (max 12): ").strip())
            if 0 <= children <= 12:
                total_relief += (children * 8000.0)
                break
            else:
                print("Please enter a number between 0 and 12.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

    # 4-7. Capped Reliefs
    print("\n--- Variable Expenses ---")
    print("Enter your actual expenses. The system will automatically apply the maximum cap.")

    medical = prompt_float("Medical expenses (Cap RM8,000)", 0.0)
    total_relief += min(medical, 8000.0)

    lifestyle = prompt_float("Lifestyle purchases (Cap RM2,500)", 0.0)
    total_relief += min(lifestyle, 2500.0)

    education = prompt_float("Education fees (Cap RM7,000)", 0.0)
    total_relief += min(education, 7000.0)

    parental = prompt_float("Parental care (Cap RM5,000)", 0.0)
    total_relief += min(parental, 5000.0)

    print(f"\nTotal Calculated Tax Relief: RM {total_relief:,.2f}")
    pause()

    return total_relief


def handle_view_records(ic_number: str):
    clear_screen()
    print("=== View Tax Records ===")
    df = read_from_csv(DATA_FILE)

    if df is None or df.empty:
        print("No records found.")
        pause()
        return

    # 1. CREATE the tax_records variable by filtering for the logged-in IC
    tax_records = df[df['ic_number'].astype(str) == str(ic_number)]

    # 2. CORRECT SYNTAX to check if the filtered dataframe is empty
    if tax_records.empty:
        print("You have no saved tax records yet.")
        pause()
        return

    # Display the filtered table
    try:
        # 3. MATCH the variable name here
        display_df = tax_records.copy()

        # Format numbers
        for col in ["income", "tax_relief", "tax_payable"]:
            if col in display_df.columns:
                display_df[col] = pd.to_numeric(display_df[col], errors="coerce")
        print(display_df.to_string(index=False))
    except Exception as e:
        print(f"Error displaying records: {e}")

    pause()


def main_menu(ic_number: str):
    while True:
        clear_screen()
        print("=== Malaysian Tax Input Program ===")
        print("1) New tax calculation")
        print("2) View saved tax records")
        print("3) Exit")
        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            handle_new_calculation(ic_number)
        elif choice == "2":
            handle_view_records(ic_number)
        elif choice == "3":
            clear_screen()
            print("Goodbye.")
            sys.exit(0)
        else:
            print("Invalid option.")
            pause()


def entry():
    clear_screen()
    print("Welcome to the Malaysian Tax Input Program")
    print("-----------------------------------------")
    print("1) Register")
    print("2) Login")
    print("3) Exit")
    choice = input("Choose an option (1-3): ").strip()

    session = None
    if choice == "1":
        session = register_flow()
    elif choice == "2":
        session = login_flow()
    elif choice == "3":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid selection.")
        pause()
        return

    if session is None:
        return
    _, ic = session
    main_menu(ic)


if __name__ == "__main__":
    while True:
        entry()
