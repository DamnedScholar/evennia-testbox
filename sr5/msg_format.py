from tekmunkey.devUtils.stringExtends import ansiStringClass as ansi

class mf:
    # Define defaults. Some methods might overload them.
    width = 78

    @classmethod
    def header(self, text=""):
        width = 100
        margin = 4
        # VERSION 1
        # if text:
        #     text = ">|n |h{}|n |R<".format(text)
        # return "    |R{:~^71}|n    ".format(text)

        # VERSION 2
        # if text:
        #     text = "$pad(>|n |h{}|n |r<, 70, c,~)".format(text)
        # else:
        #     text = "~" * 70
        #
        # text = "$pad({}, 78, c, )".format(text)

        # VERSION 3
        if text:
            text = ansi(">|n |h{}|n |R<".format(text))
        else:
            text = ansi("")
        pad = width / 2 - text.rawTextLen() / 2
        text = ansi("{mar}|R{pad}{}{pad}|n{mar}".format(
            text.ansiSlice(0, text.ansiTextLen()), mar=" " * margin, pad="~" * pad
        ))
        return text.ansiSlice(0, text.ansiTextLen())

    tag = "|Rsr5 > |n"

# IDEA: mf.prepend() that takes two strings and attaches the first to the
# second, but returns nothing if the second doesn't contain anything. Maybe
# have a switch on that last part in case someone wants to return the first
# string all the time. This would be useful for a lot of circumstances where
# I'm adding conditional extra clauses to sentences in format().
