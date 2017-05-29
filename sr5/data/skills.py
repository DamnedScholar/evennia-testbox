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
	groups = {u'close combat': [u'blades'], u'firearms': [u'automatics']}
	categories = {u'combat': [u'archery', u'automatics', u'blades']}
	attr = {u'': [u'blades'], u'agility': [u'archery', u'automatics']}
