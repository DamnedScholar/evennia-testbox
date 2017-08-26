class mf:
    @classmethod
    def header(self, text=""):
        # if text:
        #     text = ">|n |h{}|n |R<".format(text)
        # return "    |R{:~^71}|n    ".format(text)
        if text:
            text = "$pad(>|n |h{}|n |r<, 70, c,~)".format(text)
        else:
            text = "~" * 70

        text = "$pad({}, 78, c, )".format(text)
        return text

    tag = "|Rsr5 > |n"
