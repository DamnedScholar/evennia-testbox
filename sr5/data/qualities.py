class PositiveQualities:
    names = ["ambidextrous", "exceptional attribute ([])"]
    categories = ["general", "metagenic"]

    general = {
        "ambidextrous": {
            "subtypes": None,
            "rank": tuple([4]),
            "description": "",
            "source": ""
        },
        "exceptional attribute ([])": {
            "subtypes": ["body", "agility", "reaction", "strength",
                         "willpower", "logic", "intuition", "charisma",
                         "magic", "resonance"],
            "rank": tuple([14]),
            "description": "",
            "source": ""
        }
    }

    metagenic = {"functional tail ([])": {}}


class NegativeQualities:
    names = ["allergy - common ([])"]
    categories = ["general", "metagenic"]

    general = {"allergy - common ([])": {
                    "subtypes": ["*allergen"],
                    "rank": tuple([5, 10, 15, 20]),
                    "description": ""
    }}

    metagenic = {}
