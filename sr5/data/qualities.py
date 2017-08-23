class PositiveQualities:
    names = ["Ambidextrous", "Exceptional Attribute ([])", "Functional Tail (Thagomizer)"]
    categories = ["General", "Metagenic"]

    general = {
        "Ambidextrous": {
            "subtypes": None,
            "rank": tuple([4]),
            "description": "",
            "source": ""
        },
        "Exceptional Attribute ([])": {
            "subtypes": ["body", "agility", "reaction", "strength",
                         "willpower", "logic", "intuition", "charisma",
                         "magic", "resonance"],
            "rank": tuple([14]),
            "description": "",
            "source": ""
        }
    }

    metagenic = {
        "Functional Tail ([])": {
            "subtypes": ["Thagomizer", "Balance", "Paddle", "Prehensile"],
            "rank": None,
            "description": "A tail grows from the base of the character's spine; this may be scaly (like a lizard), hairy (like a monkey), or hairless (like an opossum's tail), and it is fully developed and functional, unlike the Vestigial Tail (p. 123).\n\nThe character's clothing must accommodate the tail to gain any of the above effects. Sitting in certain positions for long periods of time will be uncomfortable and cause a -1 dice pool modifier to all actions while the character is sitting on his tail. The Functional Tail quality is incompatible with any other tail modification or quality. Characters with the Functional Tail quality suffer social stigma and modifiers (see Freaks sidebar, p. 123).",
            "source": ""
        },
        "Functional Tail (Balance)": {
            "subtypes": None,
            "rank": tuple([6]),
            "description": "",
            "source": ""
        },
        "Functional Tail (Paddle)": {
            "subtypes": None,
            "rank": tuple([4]),
            "description": "",
            "source": ""
        },
        "Functional Tail (Prehensile)": {
            "subtypes": None,
            "rank": tuple([7]),
            "description": "",
            "source": ""
        },
        "Functional Tail (Thagomizer)": {
            "subtypes": None,
            "rank": tuple([5]),
            "description": "This powerfully muscled prehensile tail ends in an array of dermal spikes and can be used for a melee attack using the Exotic Melee Weapon (Thagomizer) skill, with the following stats: DV (STR + 3)P, Reach 1, AP -1.",
            "source": ""
        }
    }


class NegativeQualities:
    names = ["Allergy - Common ([])"]
    categories = ["General", "Metagenic"]

    general = {"Allergy - Common ([])": {
                    "subtypes": ["*allergen"],
                    "rank": tuple([5, 10, 15, 20]),
                    "description": ""
    }}

    metagenic = {}
