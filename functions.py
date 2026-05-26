from typing import Optional, Dict, List, Tuple
import os
import pandas as pd


def verify_user(ic_number: str, password: str) -> bool:
    if not isinstance(ic_number, str) or not ic_number.isdigit() or len(ic_number) != 12:
        return False
    if not isinstance(password, str) or len(password) != 4 or not password.isdigit():
        return False
    return password == ic_number[-4:]



TAX_BRACKETS: List[Tuple[Optional[float], float]] = [
    (5000, 0.00),
    (20000, 0.01),
    (35000, 0.03),
    (50000, 0.06),
    (70000, 0.11),
    (100000, 0.19),
    (250000, 0.25),
    (400000, 0.26),
    (600000, 0.28),
    (1000000, 0.30),
    (2000000, 0.32),
    (None, 0.33),
]


def _progressive_tax(chargeable_income: float) -> float:
    if chargeable_income <= 0:
        return 0.0

    tax = 0.0
    lower = 0.0
    for upper, rate in TAX_BRACKETS:
        if upper is None:
            # Final open-ended bracket
            amount = max(0.0, chargeable_income - lower)
            tax += amount * rate
            break
        if chargeable_income <= lower:
            break
        slice_upper = min(chargeable_income, upper)
        amount = max(0.0, slice_upper - lower)
        tax += amount * rate
        lower = upper
    return max(0.0, round(tax, 2))


def calculate_tax(income: float, tax_relief: float) -> float:
    try:
        income = float(income)
        tax_relief = float(tax_relief)
    except (TypeError, ValueError):
        raise ValueError("Income and tax_relief must be numeric.")

    if income < 0:
        raise ValueError("Income cannot be negative.")
    if tax_relief < 0:
        raise ValueError("Tax relief cannot be negative.")

    chargeable = max(0.0, income - tax_relief)
    tax = _progressive_tax(chargeable)
    return round(tax, 2)


def save_to_csv(data, filename="tax_records.csv"):
    import os
    import pandas as pd

    file_exists = os.path.isfile(filename)


    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)


    if not file_exists:
        df.to_csv(filename, index=False, mode='w', header=True)
    else:
        df.to_csv(filename, index=False, mode='a', header=False)


def read_from_csv(filename: "tax_records.csv"):
    import os
    import pandas as pd

    if not os.path.exists(filename):
        return None
    df = pd.read_csv(filename, dtype={'ic_number': str})
    return df

