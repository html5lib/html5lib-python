import etreefull

class TreeBuilder(etreefull.TreeBuilder):
    def getDocument(self):
        return self.document._element.find("html")
