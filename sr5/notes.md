TODO: "Accessory" or "Extra" typeclass, extending the default object, with a set of flags telling the game about it and any attributes or methods I feel like a universal thing prototype should have.

# Flags
* Visible? (Defaut: No)
  * If visible, it needs a description.
* Inherent? (Default: No)
  * If inherent, sheet and roll code might care.
* Permanent? (Default: Yes)
  * If not permanent, it needs a duration.
* Is it part of the user's body? (Default: No)
* What does it cost to obtain? (Default: 0)
  * The object should have its cost and the resource name stored here. If an automated command is used to acquire the object, then the buying command can look up what it needs.
  * XP and money are really just different ways of implementing the same process.
* Does it use up a slot? (Default: No)
  * If yes, slot usage should be identified. You might have a certain number of slots available, or slots for specific parts of the body, or slots provided by a stat. Need a robust name and quantity system here, something that can serve in a wide variety of games.
  * This might be **applicable** to things like spell slots.

# Stats
* Stats are going to vary wildly based on the individual accessory, and depending on the game system, the code isn't necessarily going to be able to predict which ones will be needed. Commands that interact with specific types of accessories should know what they're looking for.
* Some accessories are going to have upgrade options.
  * Possible SR5 syntax: `cyberware/upgrade=right arm/strength`
