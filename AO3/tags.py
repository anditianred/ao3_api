from enum import Enum
from bs4 import BeautifulSoup

class TagType(Enum):
    RELATIONSHIPS = "relationships"
    CHARACTERS = "characters"
    FREEFORMS = "freeforms"

class Tag:
    def __init__(self, *args):
        def constructor1(name: str, tag_type: TagType) -> None:
            self.name = name
            self.type = tag_type
        
        def constructor2(name: str, soup: BeautifulSoup) -> None:
            self.name = name
            list_items = soup.find_all("a", class_="tag", string=name) # TODO: what if none, account for that
            tag_type = list_items[0].find_parent().get("class")[0]
            self.type = TagType(tag_type)

        if (len(args) == 2) and (type(args[0]) is str) and (type(args[1]) is TagType):
            constructor1(args[0], args[1])
        elif (len(args) == 2) and (type(args[0]) is str) and (type(args[1]) is BeautifulSoup):
            constructor2(args[0], args[1])
        

