#!/usr/bin/env python3
"""
BIN Generator & Validator
Generates valid BINs (Bank Identification Numbers) and validates using Luhn algorithm.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import random
import json

# Major BIN ranges
BINS = {
    "Visa": {
        "bins": ["4", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49"],
        "length": 16,
    },
    "Mastercard": {
        "bins": ["51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27"],
        "length": 16,
    },
    "Amex": {
        "bins": ["34", "37"],
        "length": 15,
    },
    "Discover": {
        "bins": ["60", "65"],
        "length": 16,
    },
}

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

def generate_card_number(bin_prefix: str, length: int = 16) -> str:
    """Generate a valid card number with the given BIN prefix."""
    # Fill remaining digits (minus 1 for check digit)
    remaining = length - len(bin_prefix) - 1
    number = bin_prefix + ''.join(str(random.randint(0, 9)) for _ in range(remaining))
    
    # Calculate check digit
    check = (10 - luhn_checksum(number + '0')) % 10
    return number + str(check)

def generate_cvv() -> str:
    """Generate a random CVV."""
    return str(random.randint(100, 999))

def generate_expiry() -> str:
    """Generate a random future expiry date."""
    month = random.randint(1, 12)
    year = random.randint(25, 30)
    return f"{month:02d}/{year:02d}"

def generate_zip() -> str:
    """Generate a random US ZIP code."""
    return str(random.randint(10000, 99999))

def generate_cards(card_type: str = "Visa", count: int = 10) -> list:
    """Generate multiple valid card numbers."""
    if card_type not in BINS:
        raise ValueError(f"Unknown type: {card_type}")
    
    config = BINS[card_type]
    cards = []
    for _ in range(count):
        bin_prefix = random.choice(config["bins"])
        number = generate_card_number(bin_prefix, config["length"])
        
        # Verify Luhn
        assert is_luhn_valid(number), f"Generated invalid number: {number}"
        
        cards.append({
            "number": number,
            "expiry": generate_expiry(),
            "cvv": generate_cvv(),
            "zip": generate_zip(),
            "type": card_type,
            "bin": bin_prefix,
        })
    return cards

def generate_all_types(count_per_type: int = 5) -> dict:
    """Generate cards of all types."""
    result = {}
    for card_type in BINS:
        result[card_type] = generate_cards(card_type, count_per_type)
    return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BIN Generator")
    parser.add_argument("-t", "--type", default="Visa", choices=list(BINS.keys()))
    parser.add_argument("-n", "--count", type=int, default=10)
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--all", action="store_true", help="Generate all types")
    
    args = parser.parse_args()
    
    if args.all:
        cards = generate_all_types(args.count)
        for card_type, card_list in cards.items():
            print(f"\n{card_type}:")
            for c in card_list:
                print(f"  {c['number']} {c['expiry']} CVV:{c['cvv']} BIN:{c['bin']}")
    else:
        cards = generate_cards(args.type, args.count)
        for c in cards:
            print(f"{c['number']} {c['expiry']} CVV:{c['cvv']} BIN:{c['bin']}")
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(cards, f, indent=2)
        print(f"\nSaved to {args.output}")
