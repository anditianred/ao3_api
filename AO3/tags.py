from enum import Enum
from bs4 import BeautifulSoup
from typing import Optional
import hashlib

class TagType(Enum):
    RELATIONSHIPS = "relationships"
    CHARACTERS = "characters"
    FREEFORMS = "freeforms"

class Tag:
    # def __init__(self, *args):
    #     def constructor1(name: str, tag_type: TagType) -> None:
    #         self.name = name
    #         self.type = tag_type
        
    #     def constructor2(name: str, soup: BeautifulSoup) -> None:
    #         self.name = name
    #         list_items = soup.find_all("a", class_="tag", string=name) # TODO: what if none, account for that
    #         tag_type = list_items[0].find_parent().get("class")[0]
    #         self.type = TagType(tag_type)

    #     if (len(args) == 2) and (type(args[0]) is str) and (type(args[1]) is TagType):
    #         constructor1(args[0], args[1])
    #     elif (len(args) == 2) and (type(args[0]) is str) and (type(args[1]) is BeautifulSoup):
    #         constructor2(args[0], args[1])
        
    def __init__(self, name: str, tag_type: TagType) -> None:
        self.name = name
        self.type = tag_type
    
    def __eq__(self, other: "Tag"):
        return (self.name == other.name) and (self.type == other.type)

    def __hash__(self) -> int:
        hex_hash = hashlib.md5(f"{self.name}_{self.type.value}".encode('utf-8')).hexdigest()
        return int(hex_hash, 16)

def find_tag_in_soup(tag_name: str, soup: BeautifulSoup) -> Optional[Tag]:
    list_items = soup.find_all("a", class_="tag", string=tag_name) # TODO: what if none, account for that
    if list_items is None:
        return
    tag_type = list_items[0].find_parent().get("class")[0] # TODO: check if found
    return Tag(name=tag_name, tag_type=TagType(tag_type))



# TODO: create relationship tag class?