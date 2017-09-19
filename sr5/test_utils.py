from evennia.utils.test_resources import EvenniaTest
from evennia.objects.objects import (DefaultObject, DefaultCharacter,
                                     DefaultRoom, DefaultExit)
from evennia.players.players import DefaultPlayer
from evennia.scripts.scripts import DefaultScript
from evennia.server.serversession import ServerSession
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import create
from evennia.utils.idmapper.models import flush_cache
from evennia.utils.utils import lazy_property
from sr5.utils import *


class TestArticle(EvenniaTest):
    "Test the function `a_n()`."
    def test_article_aardvark(self):
        expected = "an aardvark"
        real = a_n("aardvark")
        self.assertEqual(expected, real)

    def test_article_yodel(self):
        expected = "a yodel"
        real = a_n("yodel")
        self.assertEqual(expected, real)


class TestItemize(EvenniaTest):
    "Test the function `itemize()`."
    def test_list(self):
        expected = "Wilbur, Timothy, and Ferdinand"
        real = itemize(["Wilbur", "Timothy", "Ferdinand"])
        self.assertEqual(expected, real)

    def test_string(self):
        expected = "r, u, and n"
        real = itemize("run")
        self.assertEqual(expected, real)

    def test_num(self):
        expected = "1, 2, and 3"
        real = itemize(123)
        self.assertEqual(expected, real)


class TestFlatten(EvenniaTest):
    "Test the function `flatten()`."
    def test_flatten(self):
        expected = ["key: value"]
        real = flatten({"key": "value"})
        self.assertEqual(expected, real)


class TestSubtype(EvenniaTest):
    "Test the function `parse_subtype()`."
    def test_subtype_empty(self):
        expected = ("stat", [""])
        real = parse_subtype("stat ()")
        self.assertEqual(expected, real)
        real = parse_subtype("stat ([])")
        self.assertEqual(expected, real)

    def test_subtype_full(self):
        expected = ("stat", ["type"])
        real = parse_subtype("stat (type)")
        self.assertEqual(expected, real)

    def test_subtype_none(self):
        expected = ("stat", [""])
        real = parse_subtype("stat")
        self.assertEqual(expected, real)


class TestPurgeEmptyValues(EvenniaTest):
    "Test the function `purge_empty_values()`."
    def test_purge_empty_values(self):
        expected = {"yes": 1}
        real = purge_empty_values({"yes": 1, "no": 0})
        self.assertEqual(expected, real)


class TestStatMsg(EvenniaTest):
    """
    Test the class `StatMsg`, an error message object designed to bundle a
    boolean status with an informative text string.
    """
    def test_stat_msg(self):
        msg = StatMsg(True, "This is a successful result.")
        self.assertTrue(~msg)
        self.assertEqual(msg, True)
        self.assertEqual(str(msg), "This is a successful result.")
        self.assertEqual(msg[0], True)
        self.assertEqual(msg[1], "This is a successful result.")


class CatDbPlayer(DefaultPlayer, LogsHandler, LedgerHandler):
    """
    This is the test player for CatDbHolder tests and should inherit from all
    handlers associated with it.
    """
    pass


class TestCatDbHolder(EvenniaTest):
    "Test the class `CatDbHolder`."
    def test_cat_db_holder(self):
        player = create.create_player("CatDbPlayer", email="test@test.com", password="testpassword", typeclass=CatDbPlayer)

        expected = "What happen!!!"
        player.attributes.add("record", expected, category="Logs")
        self.assertEqual(expected, player.logs.record)

        expected = "Someone set up us the bomb!!!"
        player.attributes.add("result", expected, category="Ledgers")
        self.assertEqual(expected, player.ldb.result)


class SlottedObject(DefaultObject):
    """
    This is a test object for SlotsHandler tests. All typeclassed objects
    *should* play nicely with SlotsHandler.
    """

    @lazy_property
    def slots(self):
        return SlotsHandler(self)


class SlottableObjectOne(DefaultObject):
    """
    This is a test object for SlotsHandler tests. All typeclassed objects
    *should* play nicely with SlotsHandler.
    """

    def at_object_creation(self):
        self.db.slots = {"addons": ["left"]}


class SlottableObjectTwo(DefaultObject):
    """
    This is a test object for SlotsHandler tests. All typeclassed objects
    *should* play nicely with SlotsHandler.
    """

    def at_object_creation(self):
        self.db.slots = {"addons": [1, "right"]}


class SlottableObjectThree(DefaultObject):
    """
    This is a test object for SlotsHandler tests. All typeclassed objects
    *should* play nicely with SlotsHandler.
    """

    def at_object_creation(self):
        self.db.slots = {"addons": ["left"]}


class TestSlotsHandler(EvenniaTest):
    "Test the class SlotsHandler."

    def setUp(self):
        super(TestSlotsHandler, self).setUp()
        self.obj = create.create_object(SlottedObject, key="slotted",
                                        location=self.room1, home=self.room1)
        self.slo1 = create.create_object(SlottableObjectOne, key="item 1",
                                         location=self.obj, home=self.obj)
        self.slo2 = create.create_object(SlottableObjectTwo, key="item 2",
                                         location=self.obj, home=self.obj)
        self.slo3 = create.create_object(SlottableObjectThree, key="item 3",
                                         location=self.obj, home=self.obj)

    def test_add(self):
        add = self.obj.slots.add({"addons": ["left", "right"]})
        self.assertTrue(add)

        self.obj.slots.add({"addons": [3, "y"]})
        self.assertEqual(self.obj.attributes.get("addons", category="slots"),
                         {1: "", 2: "", 3: "",
                         "left": "", "right": "", "y": ""})

    def test_delete(self):
        self.test_add()

        delete = self.obj.slots.delete({"addons": [1, "right"]})
        self.assertIsInstance(delete, dict)
        self.assertEqual(self.obj.attributes.get("addons", category="slots"),
                         {1: "", 2: "", "left": "", "y": ""})

    def test_attach(self):
        # When no slots have been added first.
        with self.assertRaises(Exception):
            attach = self.obj.slots.attach(self.slo1)

        # Add the slots.
        self.test_add()

        # Successful attachment.
        attach = self.obj.slots.attach(self.slo1)
        self.assertEqual(attach, {"addons": {"left": self.slo1}})

        # What does the attribute look like?
        real = self.obj.attributes.get("addons", category="slots")
        expected = {1: "", 2: "", 3: "",
                    "left": self.slo1, "right": "", "y": ""}
        self.assertEqual(expected, real)

        # Successful attachment in multiple slots.
        attach = self.obj.slots.attach(self.slo2)
        expected = {"addons": {1: self.slo2, "right": self.slo2}}
        self.assertEqual(attach, expected)

        # Failed attachment because the slot is occupied.
        with self.assertRaises(Exception):
            attach = self.obj.slots.attach(self.slo3)

        # Successful attachment while overriding slots.
        attach = self.obj.slots.attach(self.slo3, {"addons": [2, "y"]})
        expected = {"addons": {2: self.slo3, 3: self.slo3, "y": self.slo3}}
        self.assertEqual(attach, expected)

    def test_attach_extended(self):
        self.test_attach()

        # Attach to all open slots in category
        drop = self.obj.slots.drop(self.slo2, {"addons": ["right"]})
        attach = self.obj.slots.attach(self.slo1, ["addons"])
        self.assertEqual(attach, {"addons": {"right": self.slo1}})

        # Check the end result.
        real = self.obj.attributes.get("addons", category="slots")
        expected = {1: self.slo2, 2: self.slo3, 3: self.slo3,
                    "left": self.slo1, "right": self.slo1, "y": self.slo3}
        self.assertEqual(real, expected)

    def test_drop(self):
        self.test_attach()

        # Drop a specific object from all slots.
        drop = self.obj.slots.drop(self.slo3)
        expected = {"addons": {2: self.slo3, 3: self.slo3,
                    "y": self.slo3}}
        self.assertEqual(drop, expected)

        # Drop a specific object from specific slots.
        drop = self.obj.slots.drop(self.slo2, {"addons": ["right"]})
        self.assertEqual(drop, {"addons": {"right": self.slo2}})
        self.assertEqual(self.obj.slots.where(self.slo2),
                         {"addons": [1]})

        # Try to drop an object with improper input.
        with self.assertRaises(Exception):
            drop = self.obj.slots.drop(self.slo3, "not here")

        # Drop any objects from specific slots.
        drop = self.obj.slots.drop(None, {"addons": ["left"]})
        self.assertEqual(drop, {"addons": {"left": self.slo1}})

    def test_replace(self):
        self.test_attach()

        # Try to replace the contents of a specific slot.
        drop, attach = self.obj.slots.replace(self.slo1, {"addons": ["y"]})
        self.assertEqual(drop, {"addons": {"y": self.slo3}})
        self.assertEqual(attach, {"addons": {"y": self.slo1}})

        # Try to replace the contents of all slots.
        self.obj.slots.replace(self.slo2, ["addons"])
        where = self.obj.slots.where(self.slo2)
        where = {"addons": {n: self.slo2 for n in where['addons']}}
        self.assertEqual(where, self.obj.slots.all())

    def test_defrag(self):
        self.test_add()

        # Set up a situation where there are non-contiguous numbered slots.
        attach_1 = self.obj.slots.attach(self.slo1, {"addons": [1]})
        attach_2 = self.obj.slots.attach(self.slo2, {"addons": [1]})
        drop = self.obj.slots.drop(self.slo1)

        self.assertEqual(self.obj.slots.where(self.slo2),
                         {"addons": [1]})

    def test_where(self):
        self.test_attach()

        self.assertEqual(self.obj.slots.where(self.slo2),
                         {"addons": [1, "right"]})

        self.obj.slots.drop(self.slo2)
        self.assertEqual(self.obj.slots.where(self.slo2),
                         {})

    def tearDown(self):
        flush_cache()
        self.obj.delete()
        self.slo1.delete()
        self.slo2.delete()
        self.slo3.delete()
        super(TestSlotsHandler, self).tearDown()


class TestValidate(EvenniaTest):
    pass
    # validate = [
    #     "stat: attr.foreach, max: meta_attr.foreach.1,"
    #     "min: meta_attr.foreach.0, not in: alabama reflexes, cat: attr,"
    #     "tip: 'Please tweak your attributes.'",
    #     "stat: tradition, in: shaman hermetic, not in: zoroastrian, cat: magres"
    # ]
    # result_categories = [
    #     {"cat1": "Category the First"},
    #     {"cat2": "Category the Second"}
    # ]
