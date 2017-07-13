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
  * This might be applicable to things like spell slots.

# Stats
* Stats are going to vary wildly based on the individual accessory, and depending on the game system, the code isn't necessarily going to be able to predict which ones will be needed. Commands that interact with specific types of accessories should know what they're looking for.
* Some accessories are going to have upgrade options.
  * Possible SR5 syntax: `cyberware/upgrade=right arm/strength`

TODO: Learn about model fields.
* 7/4/2017 at 07:51:45 in #evennia
  Tehom_ | damned_scholar: One thing you can do to simplify the process is grouping up how you use attributes under handlers. For example, say you have a bunch of attributes that represent languages. But you hide how they're saved/stored/used in a languagehander you right, like character.languages. If you convert to using models for them in the future, you just change the handler
02:57	<Griatch>	damned_scholar: I would recommend not worrying too much about it. Attributes are very powerful too. Models are useful too but more specialized (which is why we cannot offer a general solution of them)
02:58	<Griatch>	Basically, if you come to a point where you realize you need models you will usually also be at a point in your understanding that implementing them is no big deal.
02:58	<Griatch>	Tehom_: Evennia being a framework is the problem here, yes. :)
03:00	<Griatch>	Even so, it will not be a single-command thing. My latest attempt is to leverage git tags so one can do it in stages.
03:03	<Tehom_>	Yeah, I agree with Griatch, damned_scholar. Attributes are enormously flexible, so you can use them for almost everything and not worry about it. Even not being able to query Attributes isn't as bad as someone might think due to all the caching that Evennia does - iterating through a list of characters and checking their attributes isn't really a big deal
03:03	<Griatch>	My previous attempt used raw SQL, which worked fine except it made it hard to continue with other migrations in the future - the migration state operations didn't quite work as well as I'd hoped.
03:03	<Griatch>	This attempt uses the migration mechanics more cleanly but instead leverages GIT. I hope that will be more future-proof.
03:05	<Griatch>	Querying Attributes is only slightly less efficient than querying any other non-serialized piece of data actually. It's highly optimized. And if you really wanted fast lookup and needed to query string-data, Attributes has a str_value you can use too - which can be queried at full speed.
03:06	<Griatch>	For most uses, especially in a MU*-game, none of those speedups will be noticeable.

* https://docs.djangoproject.com/en/1.11/topics/db/models/#fields

TODO: Set up tag system for gear and whatever else.
* https://github.com/evennia/evennia/wiki/Tags

IDEA: Cyberlimb augmentations can be stored as items inside individual cyberlimbs. This causes some object proliferation, but makes it easy to tell the difference between augs that use Capacity and ones that use Essence.

XXX: Modifiers can be aggregated by scanning objects in the character's inventory, as well as any attribute tagged as a modifier. Modifiers without a condition can be applied automatically, and modifiers with a condition can be made available to be tagged and quickly added to a roll. Still need to figure out how to prioritize overlapping ones.

Cyberlimbs will contain their Strength, Agility, Armor, and Physical Condition stats and the modifier list will reference them. A given modifier can reference an attribute on its own object or another object with `path.to.object:attribute`, such as `this:strength` to refer to its own strength or `this.obj:attributes.strength` to refer to the owner's strength. I can do dumb things with eval() if I need to in order to shoe-horn these strings into useful object paths.
