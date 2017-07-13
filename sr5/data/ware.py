"""
Cyberware and bioware prototype dictionary and rules reference.
"""


class Grades():
    standard = {"essence": 1.0, "availability": 0, "cost": 1.0}
    alphaware = {"essence": 0.8, "availability": 2, "cost": 1.2}
    betaware = {"essence": 0.7, "availability": 4, "cost": 1.5}
    deltaware = {"essence": 0.5, "availability": 8, "cost": 2.5}
    used = {"essence": 1.25, "availability": -4, "cost": 0.75}


CYBERLIMB = {"key": "Cyberlimb Prototype",
             "typeclass": "sr5.objects.Augment",
             "strength": 3,
             "agility": 3,
             "armor": 0,
             "phys_cond": 1}
RIGHT_ARM = {"key": "Right Arm",
             "prototype": "CYBERLIMB",
             "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "When using the right arm."),
                ("attributes.agility", "flat",
                 "this:agility", "When using the right arm."),
                ("weapons", "innate", "cyberhand", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
             ],
             "capacity": 15,
             "essence": 1}
RIGHT_LOWER_ARM = {"key": "Right Lower Arm",
                   "prototype": "RIGHT_ARM",
                   "phys_cond": 0.5,
                   "capacity": 10,
                   "essence": 0.45}
RIGHT_HAND = {"key": "Right Hand",
              "prototype": "RIGHT_ARM",
              "phys_cond": 0,
              "capacity": 4,
              "essence": 0.25}
LEFT_ARM = {"key": "Left Arm",
            "prototype": "CYBERLIMB",
            "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "When using the left arm."),
                ("attributes.agility", "flat",
                 "this:agility", "When using the left arm."),
                ("weapons", "innate", "cyberhand", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
            ],
            "capacity": 15,
            "essence": 1}
LEFT_LOWER_ARM = {"key": "Left Lower Arm",
                  "prototype": "LEFT_ARM",
                  "phys_cond": 0.5,
                  "capacity": 10,
                  "essence": 0.45}
LEFT_HAND = {"key": "Left Hand",
             "prototype": "LEFT_ARM",
             "phys_cond": 0,
             "capacity": 4,
             "essence": 0.25}
RIGHT_LEG = {"key": "Right Leg",
             "prototype": "CYBERLIMB",
             "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "When using the right leg."),
                ("attributes.agility", "flat",
                 "this:agility", "When using the right leg."),
                ("weapons", "innate", "cyberfoot", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
             ],
             "capacity": 20,
             "essence": 1}
RIGHT_LOWER_LEG = {"key": "Right Lower Leg",
                   "prototype": "RIGHT_LEG",
                   "phys_cond": 0.5,
                   "capacity": 12,
                   "essence": 0.45}
RIGHT_FOOT = {"key": "Right Foot",
              "prototype": "RIGHT_LEG",
              "phys_cond": 0,
              "capacity": 4,
              "essence": 0.25}
LEFT_LEG = {"key": "Left Leg",
            "prototype": "CYBERLIMB",
            "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "When using the left leg."),
                ("attributes.agility", "flat",
                 "this:agility", "When using the left leg."),
                ("weapons", "innate", "cyberfoot", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
            ],
            "capacity": 15,
            "essence": 1}
LEFT_LOWER_LEG = {"key": "Left Lower Leg",
                  "prototype": "LEFT_LEG",
                  "phys_cond": 0.5,
                  "capacity": 10,
                  "essence": 0.45}
LEFT_FOOT = {"key": "Left Foot",
             "prototype": "LEFT_LEG",
             "phys_cond": 0,
             "capacity": 4,
             "essence": 0.25}
