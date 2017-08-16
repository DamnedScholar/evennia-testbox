from evennia.utils.test_resources import EvenniaTest
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
