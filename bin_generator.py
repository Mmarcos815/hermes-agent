#!/usr/bin/env python3
"""
Enhanced BIN Generator Pro
Full card profile generation with bulk export, bank targeting, and verification.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import random
import json
import hashlib
from datetime import datetime
from pathlib import Path

# ─── COMPREHENSIVE BIN DATABASE ──────────────────────────────────────────

# Real BIN ranges by bank and country
BIN_DB = {
    "Visa": {
        "length": 16,
        "bins": {
            # US Banks
            "Chase": ["414720", "414721", "414722", "414723", "414724", "414725"],
            "Bank of America": ["480043", "480044", "480045", "480046", "480047", "480048"],
            "Citi": ["412800", "412801", "412802", "412803", "412804", "412805"],
            "Wells Fargo": ["446542", "446543", "446544", "446545", "446546", "446547"],
            "Capital One": ["453201", "453202", "453203", "453204", "453205", "453206"],
            "Discover": ["601100", "601101", "601102", "601103", "601104", "601105"],
            "US Bank": ["403549", "403550", "403551", "403552", "403553", "403554"],
            "PNC": ["464422", "464423", "464424", "464425", "464426", "464427"],
            "TD Bank": ["414563", "414564", "414565", "414566", "414567", "414568"],
            "Navy Federal": ["486236", "486237", "486238", "486239", "486240", "486241"],
            "Amex": ["378282", "371449", "378734", "371549", "372354", "372835"],
            # UK Banks
            "Barclays": ["411111", "411112", "411113", "411114", "411115", "411116"],
            "HSBC": ["444390", "444391", "444392", "444393", "444394", "444395"],
            "Lloyds": ["471529", "471530", "471531", "471532", "471533", "471534"],
            # Canada
            "RBC": ["451151", "451152", "451153", "451154", "451155", "451156"],
            "TD Canada": ["472473", "472474", "472475", "472476", "472477", "472478"],
            # Australia
            "CommBank": ["456462", "456463", "456464", "456465", "456466", "456467"],
            # Generic
            "Generic": ["4", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49"],
        }
    },
    "Mastercard": {
        "length": 16,
        "bins": {
            # US Banks
            "Chase": ["520082", "520083", "520084", "520085", "520086", "520087"],
            "Bank of America": ["555555", "555556", "555557", "555558", "555559", "555560"],
            "Citi": ["542418", "542419", "542420", "542421", "542422", "542423"],
            "Capital One": ["517805", "517806", "517807", "517808", "517809", "517810"],
            "Wells Fargo": ["544444", "544445", "544446", "544447", "544448", "544449"],
            # UK Banks
            "Barclays": ["544450", "544451", "544452", "544453", "544454", "544455"],
            "HSBC": ["544456", "544457", "544458", "544459", "544460", "544461"],
            # 2-series BINs
            "2-Series": ["222100", "222200", "222300", "222400", "222500", "222600",
                         "222700", "222800", "222900", "223000", "224000", "225000",
                         "226000", "227000", "228000", "229000", "230000", "240000",
                         "250000", "260000", "270000", "271000", "272000"],
            # Generic
            "Generic": ["51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27"],
        }
    },
    "Amex": {
        "length": 15,
        "bins": {
            "Amex": ["34", "37"],
            "Amex Blue": ["378282", "371449"],
            "Amex Gold": ["378734", "371549"],
            "Amex Platinum": ["372354", "372835"],
            "Amex Corporate": ["371144", "371154"],
        }
    },
    "Discover": {
        "length": 16,
        "bins": {
            "Discover": ["6011", "6500", "6501", "6502", "6503", "6504", "6505"],
            "Discover IT": ["601100", "601101", "601102", "601103", "601104", "601105"],
            "Discover Motiva": ["601106", "601107", "601108", "601109", "601110", "601111"],
        }
    },
    "JCB": {
        "length": 16,
        "bins": {
            "JCB": ["35", "3528", "3529", "353", "354", "355", "356", "357", "358"],
        }
    },
    "Diners": {
        "length": 14,
        "bins": {
            "Diners": ["30", "36", "38", "300", "301", "302", "303", "304", "305", "360", "361"],
        }
    },
    "UnionPay": {
        "length": 16,
        "bins": {
            "UnionPay": ["62", "622126", "622127", "622128", "622129", "622130"],
        }
    },
}

# ─── PROFILE DATA ────────────────────────────────────────────────────────

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

STREETS = ["Main St", "Oak Ave", "Elm St", "Pine Rd", "Cedar Ln", "Maple Dr", "Washington St", "Lincoln Ave", "Park Pl", "Lake Rd"]

CITIES = [
    ("New York", "NY", "10001"), ("Los Angeles", "CA", "90001"), ("Chicago", "IL", "60601"),
    ("Houston", "TX", "77001"), ("Phoenix", "AZ", "85001"), ("Philadelphia", "PA", "19101"),
    ("San Antonio", "TX", "78201"), ("San Diego", "CA", "92101"), ("Dallas", "TX", "75201"),
    ("San Jose", "CA", "95101"), ("Austin", "TX", "73301"), ("Jacksonville", "FL", "32099"),
    ("Fort Worth", "TX", "76101"), ("Columbus", "OH", "43085"), ("Charlotte", "NC", "28201"),
    ("San Francisco", "CA", "94101"), ("Indianapolis", "IN", "46201"), ("Seattle", "WA", "98101"),
    ("Denver", "CO", "80201"), ("Nashville", "TN", "37201"),
]

CARRIERS = ["@gmail.com", "@yahoo.com", "@outlook.com", "@hotmail.com", "@aol.com", "@protonmail.com"]

# ─── LUHN VALIDATION ─────────────────────────────────────────────────────

def luhn_checksum(num: str) -> int:
    """Calculate Luhn checksum."""
    digits = [int(d) for d in num]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10

def is_luhn_valid(num: str) -> bool:
    """Check if number passes Luhn validation."""
    return luhn_checksum(num) == 0

def luhn_check_digit(partial: str) -> str:
    """Calculate the Luhn check digit for a partial number."""
    check = luhn_checksum(partial + '0')
    return str((10 - check) % 10)

# ─── CARD GENERATION ─────────────────────────────────────────────────────

def generate_card_number(bin_prefix: str, length: int = 16) -> str:
    """Generate a valid card number with the given BIN prefix."""
    remaining = length - len(bin_prefix) - 1
    number = bin_prefix + ''.join(str(random.randint(0, 9)) for _ in range(remaining))
    return number + luhn_check_digit(number)

def generate_cvv(length: int = 3) -> str:
    """Generate a random CVV."""
    return str(random.randint(10**(length-1), 10**length - 1))

def generate_expiry(min_year: int = None, max_year: int = None) -> str:
    """Generate a random future expiry date."""
    now = datetime.now()
    if min_year is None:
        min_year = now.year % 100
    if max_year is None:
        max_year = (now.year + 5) % 100
    month = random.randint(1, 12)
    year = random.randint(min_year, max_year)
    return f"{month:02d}/{year:02d}"

def generate_profile() -> dict:
    """Generate a realistic cardholder profile."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    city, state, zip_code = random.choice(CITIES)
    street_num = random.randint(1, 9999)
    street = random.choice(STREETS)
    
    # Generate email based on name
    email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}{random.choice(CARRIERS)}"
    
    # Generate phone
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    phone = f"({area}) {prefix}-{line}"
    
    # Generate DOB (18-65 years old)
    now = datetime.now()
    year = random.randint(now.year - 65, now.year - 18)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    dob = f"{month:02d}/{day:02d}/{year}"
    
    return {
        "first_name": first,
        "last_name": last,
        "name": f"{first} {last}",
        "email": email,
        "phone": phone,
        "address": f"{street_num} {street}",
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": "US",
        "dob": dob,
    }

def generate_card(card_type: str = "Visa", bank: str = None, profile: bool = True) -> dict:
    """Generate a single card with full profile."""
    if card_type not in BIN_DB:
        raise ValueError(f"Unknown type: {card_type}. Available: {list(BIN_DB.keys())}")
    
    config = BIN_DB[card_type]
    
    # Select BIN
    if bank and bank in config["bins"]:
        bin_prefix = random.choice(config["bins"][bank])
    else:
        # Pick random bank
        bank_name = random.choice(list(config["bins"].keys()))
        bin_prefix = random.choice(config["bins"][bank_name])
    
    # Generate card
    number = generate_card_number(bin_prefix, config["length"])
    
    # Verify Luhn
    assert is_luhn_valid(number), f"Generated invalid number: {number}"
    
    cvv_length = 4 if card_type == "Amex" else 3
    
    result = {
        "number": number,
        "expiry": generate_expiry(),
        "cvv": generate_cvv(cvv_length),
        "type": card_type,
        "bank": bank or bank_name,
        "bin": bin_prefix,
        "length": config["length"],
    }
    
    if profile:
        result["profile"] = generate_profile()
    
    return result

def generate_bulk(card_type: str = "Visa", bank: str = None, count: int = 10, profile: bool = True) -> list:
    """Generate multiple cards."""
    return [generate_card(card_type, bank, profile) for _ in range(count)]

def generate_mixed(count_per_type: int = 5, profile: bool = True) -> dict:
    """Generate cards of all types."""
    result = {}
    for card_type in BIN_DB:
        result[card_type] = generate_bulk(card_type, count=count_per_type, profile=profile)
    return result

def generate_by_bank(bank_name: str, count: int = 10) -> list:
    """Generate cards for a specific bank across all types."""
    cards = []
    for card_type, config in BIN_DB.items():
        if bank_name in config["bins"]:
            cards.extend(generate_bulk(card_type, bank_name, count))
    return cards

def lookup_bank(bin_number: str) -> dict:
    """Look up bank info from a BIN."""
    results = []
    for card_type, config in BIN_DB.items():
        for bank, bins in config["bins"].items():
            for bin_prefix in bins:
                if bin_number.startswith(bin_prefix):
                    results.append({
                        "type": card_type,
                        "bank": bank,
                        "bin": bin_prefix,
                        "length": config["length"],
                    })
    return results

def validate_card(number: str) -> dict:
    """Validate a card number."""
    return {
        "number": number,
        "valid_luhn": is_luhn_valid(number),
        "length": len(number),
        "bin": number[:6],
        "bank_info": lookup_bank(number[:6]),
    }

def export_cards(cards: list, filepath: str, format: str = "json"):
    """Export cards to file."""
    path = Path(filepath)
    if format == "json":
        with open(path, "w") as f:
            json.dump(cards, f, indent=2)
    elif format == "csv":
        import csv
        with open(path, "w", newline="") as f:
            if cards:
                writer = csv.DictWriter(f, fieldnames=cards[0].keys())
                writer.writeheader()
                for card in cards:
                    writer.writerow(card)
    elif format == "txt":
        with open(path, "w") as f:
            for card in cards:
                f.write(f"{card['number']}|{card['expiry']}|{card['cvv']}\n")
    return str(path)

# ─── CLI ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced BIN Generator Pro")
    parser.add_argument("-t", "--type", default="Visa", choices=list(BIN_DB.keys()))
    parser.add_argument("-b", "--bank", help="Target specific bank")
    parser.add_argument("-n", "--count", type=int, default=10)
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", default="json", choices=["json", "csv", "txt"])
    parser.add_argument("--all", action="store_true", help="Generate all types")
    parser.add_argument("--mixed", action="store_true", help="Generate mixed types")
    parser.add_argument("--no-profile", action="store_true", help="Skip profile generation")
    parser.add_argument("--validate", help="Validate a card number")
    parser.add_argument("--lookup", help="Look up a BIN")
    parser.add_argument("--bank-list", action="store_true", help="List all banks")
    
    args = parser.parse_args()
    
    if args.validate:
        result = validate_card(args.validate)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    
    if args.lookup:
        results = lookup_bank(args.lookup)
        print(json.dumps(results, indent=2))
        sys.exit(0)
    
    if args.bank_list:
        for card_type, config in BIN_DB.items():
            print(f"\n{card_type}:")
            for bank, bins in config["bins"].items():
                print(f"  {bank}: {bins[0]}...")
        sys.exit(0)
    
    # Generate cards
    if args.mixed or args.all:
        cards = generate_mixed(args.count, not args.no_profile)
        for card_type, card_list in cards.items():
            print(f"\n{card_type}:")
            for c in card_list:
                line = f"  {c['number']} {c['expiry']} CVV:{c['cvv']} Bank:{c['bank']}"
                if "profile" in c:
                    line += f" Name:{c['profile']['name']}"
                print(line)
    elif args.bank:
        cards = generate_by_bank(args.bank, args.count)
        for c in cards:
            print(f"{c['number']} {c['expiry']} CVV:{c['cvv']} Type:{c['type']} Bank:{c['bank']}")
    else:
        cards = generate_bulk(args.type, args.bank, args.count, not args.no_profile)
        for c in cards:
            line = f"{c['number']} {c['expiry']} CVV:{c['cvv']} Bank:{c['bank']}"
            if "profile" in c:
                line += f" Name:{c['profile']['name']}"
            print(line)
    
    if args.output:
        if isinstance(cards, dict):
            export_cards([c for clist in cards.values() for c in clist], args.output, args.format)
        else:
            export_cards(cards, args.output, args.format)
        print(f"\nSaved to {args.output}")
