class Metatypes():
    # Priorities entries: `(metatype, special attributes, karma cost)`
    priorities = {"a": [("human", 9, 0), ("elf", 8, 0), ("dwarf", 7, 0),
                        ("ork", 7, 0), ("troll", 5, 0)],
                  "b": [("human", 7, 0), ("elf", 6, 0), ("dwarf", 4, 0),
                        ("ork", 4, 0), ("troll", 0, 0)],
                  "c": [("human", 5, 0), ("elf", 3, 0), ("dwarf", 1, 0),
                        ("ork", 0, 0)],
                  "d": [("human", 3, 0), ("elf", 0, 0)],
                  "e": [("human", 1, 0)]}

    meta_attr = {
        "human": {"body": (1, 6), "agility": (1, 6), "reaction": (1, 6),
                  "strength": (1, 6), "willpower": (1, 6), "logic": (1, 6),
                  "intuition": (1, 6), "charisma": (1, 6),
                  "edge": (2, 7), "magic": (0, 6), "resonance": (0, 6)},
        "elf": {"body": (1, 6), "agility": (2, 7), "reaction": (1, 6),
                "strength": (1, 6), "willpower": (1, 6), "logic": (1, 6),
                "intuition": (1, 6), "charisma": (3, 8),
                "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        "dwarf": {"body": (3, 8), "agility": (1, 6), "reaction": (1, 5),
                  "strength": (3, 8), "willpower": (2, 7), "logic": (1, 6),
                  "intuition": (1, 6), "charisma": (1, 6),
                  "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        "ork": {"body": (4, 9), "agility": (1, 6), "reaction": (1, 6),
                "strength": (3, 8), "willpower": (1, 6), "logic": (1, 5),
                "intuition": (1, 6), "charisma": (1, 5),
                "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        "troll": {"body": (5, 10), "agility": (1, 5), "reaction": (1, 6),
                  "strength": (5, 10), "willpower": (1, 6), "logic": (1, 5),
                  "intuition": (1, 5), "charisma": (1, 4),
                  "edge": (1, 6), "magic": (0, 6), "resonance": (0, 6)},
        }

    available = ["human", "elf", "dwarf", "ork", "troll"]
