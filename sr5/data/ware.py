"""
Cyberware and bioware prototype dictionary and rules reference.
"""


class Grades():
    @classmethod
    def options(self):
        return [k for k in self.__dict__
                if (not k.startswith("__") or not k.endswith("__"))
                and not k == "options"]

    standard = {"costs": {"essence": 1.0}, "availability": 0, "cost": 1.0}
    alphaware = {"costs": {"essence": 0.8}, "availability": 2, "cost": 1.2}
    betaware = {"costs": {"essence": 0.7}, "availability": 4, "cost": 1.5}
    deltaware = {"costs": {"essence": 0.5}, "availability": 8, "cost": 2.5}
    used = {"costs": {"essence": 1.25}, "availability": -4, "cost": 0.75}


class Obvious():
    full_arm = {"capacity": 15, "cost": 15000}
    full_leg = {"capacity": 20, "cost": 15000}
    hand_foot = {"capacity": 4, "cost": 5000}
    lower_arm = {"capacity": 10, "cost": 10000}
    lower_leg = {"capacity": 12, "cost": 10000}
    torso = {"capacity": 10, "cost": 20000}
    skull = {"capacity": 4, "cost": 10000}


class Synthetic():
    full_arm = {"capacity": 8, "cost": 20000}
    full_leg = {"capacity": 10, "cost": 20000}
    hand_foot = {"capacity": 2, "cost": 6000}
    lower_arm = {"capacity": 5, "cost": 12000}
    lower_leg = {"capacity": 6, "cost": 12000}
    torso = {"capacity": 5, "cost": 25000}
    skull = {"capacity": 2, "cost": 15000}


class BuyableWare():
    cyberlimbs = ["LEFT_ARM", "LEFT_FOOT", "LEFT_HAND", "LEFT_LEG",
                  "LEFT_LOWER_ARM", "LEFT_LOWER_LEG", "RIGHT_ARM",
                  "RIGHT_FOOT", "RIGHT_HAND", "RIGHT_LEG", "RIGHT_LOWER_ARM",
                  "RIGHT_LOWER_LEG", "SKULL", "TORSO"]


# Cyberlimbs
CYBERLIMB = {"key": "Cyberlimb Prototype",
             "typeclass": "sr5.objects.Cyberlimb",
             "strength": 3,
             "agility": 3,
             "armor": 0,
             "phys_cond": 1,
             "exec": [
                "costs, obj.db.capacity = "
                    "obj.cyberlimb_costs_and_capacity("
                    "obj.db.slots, obj.db.synthetic, obj.db.grade,"
                    "c_str=obj.db.custom_str, c_agi=obj.db.custom_agi"
                ")",
                "obj.db.strength += obj.db.custom_str",
                "obj.db.agility += obj.db.custom_agi"
             ]}
TORSO = {"key": "Torso",
         "prototype": "CYBERLIMB",
         "modifiers": [
            # Tuple (<stat>, <type>, <value>, <condition or False>)
            ("attributes.strength", "flat",
             "this:strength", "this:condition"),
            ("attributes.agility", "flat",
             "this:agility", "this:condition"),
            ("condition.physical", "bonus", "this:phys_cond", False)
         ],
         "costs": {"essence": 1.5},
         "condition": "When using the torso.",
         "slots": {"body": ["torso"]}}
SKULL = {"key": "Skull",
         "prototype": "CYBERLIMB",
         "modifiers": [
            # Tuple (<stat>, <type>, <value>, <condition or False>)
            ("attributes.strength", "flat",
             "this:strength", "this:condition"),
            ("attributes.agility", "flat",
             "this:agility", "this:condition"),
            ("weapons", "innate", "cyberhead", False),
            ("condition.physical", "bonus", "this:phys_cond", False)
         ],
         "costs": {"essence": 0.75},
         "condition": "When using the head.",
         "slots": {"body": ["skull"]}}
RIGHT_ARM = {"key": "Right Arm",
             "prototype": "CYBERLIMB",
             "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "this:condition"),
                ("attributes.agility", "flat",
                 "this:agility", "this:condition"),
                ("weapons", "innate", "cyberhand", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
             ],
             "costs": {"essence": 1},
             "condition": "When using the right arm.",
             "slots": {"body": ["right_upper_arm", "right_lower_arm", "right_hand"]}}
RIGHT_LOWER_ARM = {"key": "Right Lower Arm",
                   "prototype": "RIGHT_ARM",
                   "phys_cond": 0.5,
                   "costs": {"essence": 0.45},
                   "condition": "When using the right lower arm.",
                   "slots": {"body": ["right_lower_arm", "right_hand"]}}
RIGHT_HAND = {"key": "Right Hand",
              "prototype": "RIGHT_ARM",
              "phys_cond": 0,
              "costs": {"essence": 0.25},
              "condition": "When using the right hand.",
              "slots": {"body": ["right_hand"]}}
LEFT_ARM = {"key": "Left Arm",
            "prototype": "CYBERLIMB",
            "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "this:condition"),
                ("attributes.agility", "flat",
                 "this:agility", "this:condition"),
                ("weapons", "innate", "cyberhand", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
            ],
            "capacity": 15,
            "costs": {"essence": 1},
            "condition": "When using the left arm.",
            "slots": {"body": ["left_upper_arm", "left_lower_arm", "left_hand"]}}
LEFT_LOWER_ARM = {"key": "Left Lower Arm",
                  "prototype": "LEFT_ARM",
                  "phys_cond": 0.5,
                  "costs": {"essence": 0.45},
                  "condition": "When using the left lower arm.",
                  "slots": {"body": ["left_lower_arm", "left_hand"]}}
LEFT_HAND = {"key": "Left Hand",
             "prototype": "LEFT_ARM",
             "phys_cond": 0,
             "costs": {"essence": 0.25},
             "condition": "When using the left hand.",
             "slots": {"body": ["left_hand"]}}
RIGHT_LEG = {"key": "Right Leg",
             "prototype": "CYBERLIMB",
             "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "this:condition"),
                ("attributes.agility", "flat",
                 "this:agility", "this:condition"),
                ("weapons", "innate", "cyberfoot", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
             ],
             "costs": {"essence": 1},
             "condition": "When using the right leg.",
             "slots": {"body": ["right_upper_leg", "right_lower_leg", "right_foot"]}}
RIGHT_LOWER_LEG = {"key": "Right Lower Leg",
                   "prototype": "RIGHT_LEG",
                   "phys_cond": 0.5,
                   "costs": {"essence": 0.45},
                   "condition": "When using the right lower leg.",
                   "slots": {"body": ["right_lower_leg", "right_foot"]}}
RIGHT_FOOT = {"key": "Right Foot",
              "prototype": "RIGHT_LEG",
              "phys_cond": 0,
              "costs": {"essence": 0.25},
              "condition": "When using the right foot.",
              "slots": {"body": ["right_foot"]}}
LEFT_LEG = {"key": "Left Leg",
            "prototype": "CYBERLIMB",
            "modifiers": [
                # Tuple (<stat>, <type>, <value>, <condition or False>)
                ("attributes.strength", "flat",
                 "this:strength", "this:condition"),
                ("attributes.agility", "flat",
                 "this:agility", "this:condition"),
                ("weapons", "innate", "cyberfoot", False),
                ("condition.physical", "bonus", "this:phys_cond", False)
            ],
            "costs": {"essence": 1},
            "condition": "When using the left leg.",
            "slots": {"body": ["left_upper_leg", "left_lower_leg", "left_foot"]}}
LEFT_LOWER_LEG = {"key": "Left Lower Leg",
                  "prototype": "LEFT_LEG",
                  "phys_cond": 0.5,
                  "costs": {"essence": 0.45},
                  "condition": "When using the left lower leg.",
                  "slots": {"body": ["left_lower_leg", "left_foot"]}}
LEFT_FOOT = {"key": "Left Foot",
             "prototype": "LEFT_LEG",
             "phys_cond": 0,
             "costs": {"essence": 0.25},
             "condition": "When using the left foot.",
             "slots": {"body": ["left_foot"]}}
