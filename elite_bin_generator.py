#!/usr/bin/env python3
"""
Elite BIN Generator — High-Tier Card Ranges
Premium, Infinite, Corporate, and World-class card BINs.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import random
import json
from datetime import datetime
from pathlib import Path

# ─── ELITE BIN DATABASE ────────────────────────────────────────────────--

ELITE_BINS = {
    # ═══════════════════════════════════════════════════════════════════════
    # VISA PREMIUM / SIGNATURE / INFINITE
    # ═══════════════════════════════════════════════════════════════════════
    "Visa_Signature": {
        "length": 16,
        "bins": {
            # Chase Sapphire Preferred/Reserve
            "Chase_Sapphire": ["414720", "414721", "414722", "414723", "414724", "414725", "438857", "438858", "438859"],
            # Chase Ink Business
            "Chase_Ink": ["420767", "420768", "420769", "428261", "428262", "428263", "478284", "478285"],
            # Amex Gold/Platinum (Visa co-brand)
            "Amex_CoBrand": ["378282", "371449", "378734", "371549", "372354", "372835"],
            # Capital One Venture
            "Capital_One_Venture": ["410608", "410609", "410610", "453201", "453202", "453203", "453204", "453205"],
            # Capital One Quicksilver
            "Capital_One_Quicksilver": ["414755", "414756", "414757", "453215", "453216", "453217"],
            # Citi AAdvantage
            "Citi_AAdvantage": ["412800", "412801", "412802", "412803", "412804", "412805"],
            # Citi Premier
            "Citi_Premier": ["453205", "453206", "453207", "453208", "453209"],
            # Citi Double Cash
            "Citi_Double_Cash": ["412900", "412901", "412902", "412903", "412904", "412905"],
            # Chase Freedom Unlimited/Diamond
            "Chase_Freedom": ["438854", "438855", "438856", "475054", "475055", "475056"],
            # Wells Fargo Active Cash/Platinum
            "Wells_Fargo_Active": ["446542", "446543", "446544", "446545", "446546", "446547"],
            # US Bank Cash+ / Altitude
            "US_Bank_CashPlus": ["403549", "403550", "403551", "403552", "403553", "403554"],
            # PNC Points/Cash Rewards
            "PNC_Points": ["464422", "464423", "464424", "464425", "464426", "464427"],
            # TD Bank Cash Credit
            "TD_Bank_Cash": ["414563", "414564", "414565", "414566", "414567", "414568"],
            # Navy Federal More Rewards
            "Navy_Federal_More": ["486236", "486237", "486238", "486239", "486240", "486241"],
            # PenFed Pathfinder/Platinum
            "PenFed_Pathfinder": ["411770", "411771", "411772", "411773", "411774", "411775"],
            # Bank of America Premium Rewards
            "BofA_Premium": ["480043", "480044", "480045", "480046", "480047", "480048"],
            # HSBC Premier
            "HSBC_Premier": ["444390", "444391", "444392", "444393", "444394", "444395"],
            # Barclays Arrival Plus
            "Barclays_Arrival": ["411111", "411112", "411113", "411114", "411115", "411116"],
            # Lloyds Bank Avios
            "Lloyds_Avios": ["471529", "471530", "471531", "471532", "471533", "471534"],
            # RBC Avion/Rewards
            "RBC_Avion": ["451151", "451152", "451153", "451154", "451155", "451156"],
            # CommBank Awards
            "CommBank_Awards": ["456462", "456463", "456464", "456465", "456466", "456467"],
            # Visa Infinite (generic premium)
            "Visa_Infinite": ["4", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49"],
        }
    },
    # ═══════════════════════════════════════════════════════════════════════
    # MASTERCARD WORLD / WORLD ELITE / PREMIER
    # ═══════════════════════════════════════════════════════════════════════
    "Mastercard_World": {
        "length": 16,
        "bins": {
            # Chase Sapphire (MC)
            "Chase_Sapphire_MC": ["520082", "520083", "520084", "520085", "520086", "520087"],
            # Chase Freedom (MC)
            "Chase_Freedom_MC": ["520088", "520089", "520090", "520091", "520092", "520093"],
            # Capital One Venture (MC)
            "Capital_One_Venture_MC": ["517805", "517806", "517807", "517808", "517809", "517810"],
            # Capital One Savor/Quicksilver
            "Capital_One_Savor": ["518905", "518906", "518907", "518908", "518909", "518910"],
            # Citi Premier / Double Cash (MC)
            "Citi_Premier_MC": ["542418", "542419", "542420", "542421", "542422", "542423"],
            # Citi AAdvantage (MC)
            "Citi_AAdvantage_MC": ["542424", "542425", "542426", "542427", "542428", "542429"],
            # Wells Fargo Platinum/Active Cash
            "Wells_Fargo_MC": ["544444", "544445", "544446", "544447", "544448", "544449"],
            # Bank of America Premium (MC)
            "BofA_Premium_MC": ["555555", "555556", "555557", "555558", "555559", "555560"],
            # Barclays Arrival+ (MC)
            "Barclays_Plus": ["544450", "544451", "544452", "544453", "544454", "544455"],
            # HSBC Cash Rewards
            "HSBC_CashRewards": ["544456", "544457", "544458", "544459", "544460", "544461"],
            # 2-Series World Elite
            "2Series_WorldElite": ["222100", "222200", "222300", "222400", "222500", "222600",
                                  "222700", "222800", "222900", "223000", "224000", "225000",
                                  "226000", "227000", "228000", "229000", "230000", "240000",
                                  "250000", "260000", "270000", "271000", "272000"],
            # Mastercard Premier
            "MC_Premier": ["51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27"],
        }
    },
    # ═══════════════════════════════════════════════════════════════════════
    # AMEX PREMIUM / GOLD / PLATINUM
    # ═══════════════════════════════════════════════════════════════════════
    "Amex_Premium": {
        "length": 15,
        "bins": {
            # Amex Gold
            "Amex_Gold": ["378282", "371449", "378734", "371549"],
            # Amex Platinum
            "Amex_Platinum": ["372354", "372835", "371144", "371154"],
            # Amex Centurion (Black Card)
            "Amex_Centurion": ["378282", "371449", "378734", "371549", "372354", "372835"],
            # Amex EveryDay
            "Amex_EveryDay": ["371144", "371154", "378282", "371449"],
            # Amex Blue Cash
            "Amex_BlueCash": ["378734", "371549", "372354", "372835"],
            # Amex Hilton/H Marriott co-brand
            "Amex_CoBrand": ["371144", "371154", "378282", "371449"],
        }
    },
    # ═══════════════════════════════════════════════════════════════════════
    # CORPORATE / BUSINESS PREMIUM
    # ═══════════════════════════════════════════════════════════════════════
    "Corporate": {
        "length": 16,
        "bins": {
            # Chase Ink Business Preferred
            "Chase_Ink_Preferred": ["420767", "420768", "420769", "428261", "428262", "428263"],
            # Chase Ink Business Cash
            "Chase_Ink_Cash": ["478284", "478285", "478286", "478287", "478288", "478289"],
            # Chase Ink Business Unlimited
            "Chase_Ink_Unlimited": ["428264", "428265", "428266", "428267", "428268", "428269"],
            # Amex Business Gold/Platinum
            "Amex_Business": ["371144", "371154", "378282", "371449"],
            # Capital One Spark Business
            "Capital_One_Spark": ["414755", "414756", "414757", "453215", "453216", "453217"],
            # Wells Fargo Business Platinum
            "Wells_Fargo_Business": ["446542", "446543", "446544", "446545", "446546", "446547"],
            # Bank of America Business Advantage
            "BofA_Business": ["480043", "480044", "480045", "480046", "480047", "480048"],
            # Citi Business / AAdvantage Business
            "Citi_Business": ["412800", "412801", "412802", "412803", "412804", "412805"],
            # Stripe Corporate
            "Stripe_Corporate": ["424242", "424242", "424242", "424242", "424242", "424242"],
        }
    },
    # ═══════════════════════════════════════════════════════════════════════
    # DISCOVER IT / PREMIUM
    # ═══════════════════════════════════════════════════════════════════════
    "Discover_Premium": {
        "length": 16,
        "bins": {
            # Discover IT
            "Discover_IT": ["601100", "601101", "601102", "601103", "601104", "601105"],
            # Discover Motiva
            "Discover_Motiva": ["601106", "601107", "601108", "601109", "601110", "601111"],
            # Discover Secured
            "Discover_Secured": ["601112", "601113", "601114", "601115", "601116", "601117"],
            # Discover Student
            "Discover_Student": ["601118", "601119", "601120", "601121", "601122", "601123"],
            # Discover Miles
            "Discover_Miles": ["601124", "601125", "601126", "601127", "601128", "601129"],
        }
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE LABEL / STORE PREMIUM
    # ═══════════════════════════════════════════════════════════════════════
    "Private_Label": {
        "length": 16,
        "bins": {
            # Nordstrom Visa Signature
            "Nordstrom": ["414720", "414721", "414722", "414723", "414724", "414725"],
            # Amazon Prime Rewards
            "Amazon_Prime": ["414720", "414721", "414722", "414723", "414724", "414725"],
            # Apple Card (Goldman Sachs)
            "Apple_Card": ["414720", "414721", "414722", "414723", "414724", "414725"],
            # Costco Anywhere Visa
            "Costco": ["414720", "414721", "414722", "414723", "414724", "414725"],
            # Walmart Rewards
            "Walmart": ["414720", "414721", "414722", "414723", "414724", "414725"],
        }
    },
}

# ─── ELITE PROFILES ─────────────────────────────────────────────────────

ELITE_PROFILES = {
    "high_net_worth": {
        "names": ["Alexander", "Victoria", "Maximilian", "Alexandra", "Sebastian", "Anastasia", "Dominic", "Olivia", "Harrison", "Penelope"],
        "domains": ["@privatebank.com", "@wealthmgmt.com", "@familyoffice.com", "@trust.com"],
        "cities": [("Greenwich", "CT", "06830"), ("Palo Alto", "CA", "94301"), ("Atherton", "CA", "94027"),
                   ("Manhattan", "NY", "10021"), ("Beverly Hills", "CA", "90210"), ("Naples", "FL", "34102")],
        "income_range": [250000, 5000000],
    },
    "corporate_exec": {
        "names": ["Michael", "Jennifer", "Robert", "Elizabeth", "William", "Sarah", "James", "Emily", "David", "Amanda"],
        "domains": ["@company.com", "@corp.com", "@enterprise.com", "@inc.com"],
        "cities": [("New York", "NY", "10001"), ("Chicago", "IL", "60601"), ("Houston", "TX", "77001"),
                   ("San Francisco", "CA", "94101"), ("Boston", "MA", "02101"), ("Seattle", "WA", "98101")],
        "income_range": [150000, 500000],
    },
    "tech_professional": {
        "names": ["John", "Jane", "Alex", "Sam", "Chris", "Jordan", "Morgan", "Taylor", "Casey", "Riley"],
        "domains": ["@gmail.com", "@protonmail.com", "@outlook.com"],
        "cities": [("San Francisco", "CA", "94105"), ("Seattle", "WA", "98101"), ("Austin", "TX", "73301"),
                   ("Denver", "CO", "80201"), ("Portland", "OR", "97201"), ("Miami", "FL", "33101")],
        "income_range": [120000, 350000],
    },
}

STREETS_ELITE = ["Park Ave", "Fifth Ave", "Madison Ave", "Wall St", "Broadway", "Lexington Ave", "Rodeo Drive", "Beverly Drive", "Nob Hill", "Pacific Heights"]

CARRIERS_ELITE = ["@gmail.com", "@protonmail.com", "@outlook.com", "@privatebank.com", "@wealthmgmt.com"]

# ─── LUHN VALIDATION ─────────────────────────────────────────────────────

def luhn_checksum(num: str) -> int:
    digits = [int(d) for d in num]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10

def is_luhn_valid(num: str) -> bool:
    return luhn_checksum(num) == 0

def luhn_check_digit(partial: str) -> str:
    check = luhn_checksum(partial + '0')
    return str((10 - check) % 10)

# ─── CARD GENERATION ─────────────────────────────────────────────────────

def generate_card_number(bin_prefix: str, length: int = 16) -> str:
    remaining = length - len(bin_prefix) - 1
    number = bin_prefix + ''.join(str(random.randint(0, 9)) for _ in range(remaining))
    return number + luhn_check_digit(number)

def generate_cvv(length: int = 3) -> str:
    return str(random.randint(10**(length-1), 10**length - 1))

def generate_expiry(min_year: int = None, max_year: int = None) -> str:
    now = datetime.now()
    if min_year is None:
        min_year = now.year % 100
    if max_year is None:
        max_year = (now.year + 5) % 100
    month = random.randint(1, 12)
    year = random.randint(min_year, max_year)
    return f"{month:02d}/{year:02d}"

def generate_elite_profile(profile_type: str = "high_net_worth") -> dict:
    """Generate an elite cardholder profile."""
    profile = ELITE_PROFILES.get(profile_type, ELITE_PROFILES["high_net_worth"])
    
    first = random.choice(profile["names"])
    last = "".join([random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"])])
    
    city, state, zip_code = random.choice(profile["cities"])
    street_num = random.randint(1, 9999)
    street = random.choice(STREETS_ELITE)
    
    email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}{random.choice(profile['domains'])}"
    
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    phone = f"({area}) {prefix}-{line}"
    
    now = datetime.now()
    year = random.randint(now.year - 65, now.year - 25)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    dob = f"{month:02d}/{day:02d}/{year}"
    
    income = random.randint(profile["income_range"][0], profile["income_range"][1])
    
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
        "income": income,
        "profile_type": profile_type,
    }

def generate_elite_card(tier: str = "Visa_Signature", bank: str = None, profile_type: str = None) -> dict:
    """Generate a single elite card."""
    if tier not in ELITE_BINS:
        raise ValueError(f"Unknown tier: {tier}. Available: {list(ELITE_BINS.keys())}")
    
    config = ELITE_BINS[tier]
    
    if bank and bank in config["bins"]:
        bin_prefix = random.choice(config["bins"][bank])
    else:
        bank_name = random.choice(list(config["bins"].keys()))
        bin_prefix = random.choice(config["bins"][bank_name])
    
    number = generate_card_number(bin_prefix, config["length"])
    assert is_luhn_valid(number), f"Generated invalid number: {number}"
    
    cvv_length = 4 if tier == "Amex_Premium" else 3
    
    result = {
        "number": number,
        "expiry": generate_expiry(),
        "cvv": generate_cvv(cvv_length),
        "type": tier,
        "bank": bank or bank_name,
        "bin": bin_prefix,
        "length": config["length"],
    }
    
    if profile_type:
        result["profile"] = generate_elite_profile(profile_type)
    else:
        result["profile"] = generate_elite_profile("high_net_worth")
    
    return result

def generate_elite_bulk(tier: str = "Visa_Signature", bank: str = None, count: int = 10) -> list:
    """Generate multiple elite cards."""
    return [generate_elite_card(tier, bank) for _ in range(count)]

def generate_mixed_elite(count_per_tier: int = 5) -> dict:
    """Generate elite cards across all tiers."""
    result = {}
    for tier in ELITE_BINS:
        result[tier] = generate_elite_bulk(tier, count=count_per_tier)
    return result

def generate_by_tier(tier: str, count: int = 10) -> list:
    """Generate cards for a specific tier."""
    return generate_elite_bulk(tier, count=count)

# ─── CLI ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Elite BIN Generator — High-Tier Cards")
    parser.add_argument("-t", "--tier", default="Visa_Signature", choices=list(ELITE_BINS.keys()))
    parser.add_argument("-b", "--bank", help="Target specific bank")
    parser.add_argument("-n", "--count", type=int, default=10)
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", default="json", choices=["json", "csv", "txt"])
    parser.add_argument("--mixed", action="store_true", help="Generate mixed elite tiers")
    parser.add_argument("--all", action="store_true", help="Generate all tiers")
    parser.add_argument("--list", action="store_true", help="List all tiers and banks")
    parser.add_argument("--profile", default="high_net_worth", choices=["high_net_worth", "corporate_exec", "tech_professional"])
    
    args = parser.parse_args()
    
    if args.list:
        for tier, config in ELITE_BINS.items():
            print(f"\n{tier}:")
            for bank, bins in config["bins"].items():
                print(f"  {bank}: {bins[0]}...")
        sys.exit(0)
    
    if args.mixed or args.all:
        cards = generate_mixed_elite(args.count)
        for tier, card_list in cards.items():
            print(f"\n{tier}:")
            for c in card_list:
                line = f"  {c['number']} {c['expiry']} CVV:{c['cvv']} Bank:{c['bank']}"
                if "profile" in c:
                    line += f" Name:{c['profile']['name']} Income:${c['profile']['income']:,}"
                print(line)
    else:
        cards = generate_elite_bulk(args.tier, args.bank, args.count)
        for c in cards:
            line = f"{c['number']} {c['expiry']} CVV:{c['cvv']} Bank:{c['bank']}"
            if "profile" in c:
                line += f" Name:{c['profile']['name']} Income:${c['profile']['income']:,}"
            print(line)
    
    if args.output:
        if isinstance(cards, dict):
            with open(args.output, "w") as f:
                json.dump(cards, f, indent=2)
        else:
            with open(args.output, "w") as f:
                json.dump(cards, f, indent=2)
        print(f"\nSaved to {args.output}")
