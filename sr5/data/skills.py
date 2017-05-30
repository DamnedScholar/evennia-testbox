class Skills():
	"""
	This class has been automatically generated based on a Google sheet.
	"""
	active = {
		"archery": {
			"attribute": "agility", "default": "yes",
			"group": "none", "category": "combat",
			"description": "Archery is used to fire string-loaded projectile weapons. An archer is familiar with many different styles of bow and the multitude of arrows that can be used to maximum effect.",
			"specs": "Bow, Crossbow, Non-Standard Ammunition, Slingshot",
			"source": "SR p. 130"
		},
		"automatics": {
			"attribute": "agility", "default": "yes",
			"group": "firearms", "category": "combat",
			"description": "The Automatics skill covers a specific subset of firearms larger than handheld pistols but smaller than rifles. This category includes submachine guns and other fully automatic carbines.",
			"specs": "Assault Rifles, Cyber-Implant, Machine Pistols, Submachine Guns",
			"source": "SR p. 130"
		},
		"blades": {
			"attribute": "", "default": "yes",
			"group": "close combat", "category": "combat",
			"description": "",
			"specs": "",
			"source": ""
		},
	}

	knowledge = {
		"street": {
			"attribute": "intuition", "default": "no",
			"description": "Street Knowledge is linked to Intuition. This type of Knowledge skill is about knowing the movers and shakers in an urban area, along with how things get done on the street. You know about the people who live in different neighborhoods, who to ask to get what, and where things are. The information that these skills cover tends to change rapidly, but your instincts help you keep up.",
			"specs": "",
			"source": "SR p. 148"
		},
		"academic": {
			"attribute": "logic", "default": "no",
			"description": "Academic knowledge is linked to Logic. This type of knowledge includes university subjects such as history, science, design, technology, magical theory, and the people and organizations with fingers in those pies. The humanities (cultures, art, philosophy, and so on) are also included in this category.",
			"specs": "",
			"source": "SR p. 148"
		},
		"professional": {
			"attribute": "logic", "default": "no",
			"description": "Professional Knowledge skills deal with subjects related to normal trades, professions, and occupations, things like journalism, engineering, business, and so on. You might find them helpful when doing legwork for a run, especially those in the corporate world. All Professional Knowledge skills are linked to Logic.",
			"specs": "",
			"source": "SR p. 148"
		},
		"interest": {
			"attribute": "intuition", "default": "no",
			"description": "Strange as it might sound, you might have some hobbies outside of slinging mana and bullets. Interests are the kind of Knowledge skill that describes what you know because of what you do for fun. There are no guidelines (and no limit) to the sort of interest skills you can have. Interest Knowledge skills are linked to Intuition.",
			"specs": "",
			"source": "SR p. 148"
		},
		"language": {
			"attribute": "intuition", "default": "yes",
			"description": "Language is the ability to converse in a specific language through written and verbal means. Characters who speak multiple languages must purchase a separate language skill for each language.",
			"specs": "Read/Write, Speak, by dialect, by lingo",
			"source": "SR p. 150"
		},
	}
	groups = {u'close combat': [u'blades'], u'firearms': [u'automatics']}
	categories = {u'combat': [u'archery', u'automatics', u'blades']}
	attr = {u'agility': [u'archery', u'automatics'], u'intuition': [u'street', u'interest', u'language'], u'logic': [u'academic', u'professional']}
