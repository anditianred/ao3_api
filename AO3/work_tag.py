"""Representation of a work through it's tags"""

from .tags import TagType, Tag

from bs4 import BeautifulSoup

from typing import TypedDict

class TagSection(TypedDict):
    tag_type: TagType
    tags: set

class WorkTags:
    def __init__(self, tags: set[Tag], sectioned_tags: TagSection) -> None:
        self.tags = set(tags)
        self.sectioned_tags = sectioned_tags

def parse_worktags_from_soup(soup: BeautifulSoup, debug: bool = False) -> list[WorkTags]:
    results = soup.find("ol", {"class": ("work", "index", "group")})
    if results is None:
        return
    works = []
    for work in results.find_all("li", {"role": "article"}):
        if work.h4 is None:
            continue
        tags_section = work.select_one("ul.tags.commas")
        tags = tags_section.find_all("li", class_=[TagType.CHARACTERS.value, TagType.RELATIONSHIPS.value, TagType.FREEFORMS.value])
        # always ordered Rel -> Char -> Freeform
        sectioned_tags = {tag_type:set() for tag_type in TagType}
        full_tag_set = set()
        for tag in tags:
            t = Tag(name=tag.text, tag_type=TagType(tag["class"][0]))
            sectioned_tags[t.type].update([t])
            full_tag_set.update([t])
        
        # create work representation
        work = WorkTags(full_tag_set, sectioned_tags)
        works.append(work)

        # just for debug printing
        if debug:
            for sec in [work.tags] + list(work.sectioned_tags.values()):
                print("______________section______________")
                for tag in sec:
                    print(f"{tag.type}: {tag.name}")
                
    return works
