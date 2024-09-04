from enum import Enum
from bs4 import BeautifulSoup
from typing import Optional
import hashlib

class TagType(Enum):
    RELATIONSHIPS = "relationships"
    CHARACTERS = "characters"
    FREEFORMS = "freeforms"

class Tag:
    def __init__(self, name: str, tag_type: TagType) -> None:
        self.name = name
        self.type = tag_type
    
    def __eq__(self, other: "Tag"):
        return (self.name == other.name) and (self.type == other.type)

    def __hash__(self) -> int:
        hex_hash = hashlib.md5(f"{self.name}_{self.type.value}".encode('utf-8')).hexdigest()
        return int(hex_hash, 16)

class RelationshipTag(Tag):
    class Type(Enum):
        PLATONIC = "&"
        ROMANTIC = "/"

    def __init__(self, name: str) -> None:
        super(RelationshipTag, self).__init__(name=name, tag_type=TagType.RELATIONSHIPS)
        self.relationship_type = self.Type.PLATONIC if self.Type.PLATONIC.value in name else self.Type.ROMANTIC
        self.people = [Tag(name.strip(), TagType.CHARACTERS) for name in name.split(self.relationship_type.value)]
    
    @staticmethod
    def from_tag(tag: Tag) -> Optional["RelationshipTag"]:
        if tag.type != TagType.RELATIONSHIPS:
            return
        return RelationshipTag(tag.name)

def find_tag_in_soup(tag_name: str, soup: BeautifulSoup) -> Optional[Tag]:
    list_items = soup.find_all("a", class_="tag", string=tag_name) # TODO: what if none, account for that
    if list_items is None:
        return
    tag_type = list_items[0].find_parent().get("class")[0] # TODO: check if found
    return Tag(name=tag_name, tag_type=TagType(tag_type))

# def tag_to_relationship_tag(tag: Tag) -> Optional[Tag]:
#     if tag.type != TagType.RELATIONSHIPS:
#         return
#     return RelationshipTag(tag.name)


# TODO: create relationship tag class?

if __name__ == "__main__":
    t = Tag("nn & ggg ", TagType.RELATIONSHIPS)
    g = RelationshipTag.from_tag(t)
    print([person.name for person in g.people])
    print(RelationshipTag.from_tag(Tag("hhh", TagType.CHARACTERS)))