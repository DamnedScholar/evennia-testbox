class mf:
    @classmethod
    def header(self, text=""):
        if text:
            text = "> {} <".format(text)
        return "    {:~^71}    ".format(text)

    tag = "|Rsr5 > |n"
