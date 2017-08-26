class mf:
    @classmethod
    def header(self, text=""):
        if text:
            text = ">|n |h{}|n |R<".format(text)
        return "    |R{:~^71}|n    ".format(text)

    tag = "|Rsr5 > |n"
