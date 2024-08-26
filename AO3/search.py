from math import ceil

from bs4 import BeautifulSoup

from . import threadable, utils
from .common import get_work_from_banner
from .requester import requester
from .series import Series
from .users import User
from .works import Work

import shelve
import os
import re
import datetime
import pathlib
import hashlib
import dataclasses
import json
from collections.abc import Collection

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from .session import Session
    from .utils import Constraint

DEFAULT = "_score"
BEST_MATCH = "_score"
AUTHOR = "authors_to_sort_on"
TITLE = "title_to_sort_on"
DATE_POSTED = "created_at"
DATE_UPDATED = "revised_at"
WORD_COUNT = "word_count"
RATING = "rating_ids"
HITS = "hits"
BOOKMARKS = "bookmarks_count"
COMMENTS = "comments_count"
KUDOS = "kudos_count"

DESCENDING = "desc"
ASCENDING = "asc"

DIR = pathlib.Path(__file__).parent.resolve()
CACHE_PAGES_DIR = DIR / "search_cache"
CACHE_INDEX = CACHE_PAGES_DIR / "search_cache_index"

CACHE_PAGES_DIR.mkdir(parents=True, exist_ok=True)
if not CACHE_INDEX.is_file():
    with shelve.open(CACHE_INDEX) as f:
        f["dummy"] = "test"

TIME_FMT = "%m/%d/%Y %H:%M:%S"

# cache table
# hash(search query, page), entry = file name, query time/date (if time/date > week then need re search)
# file - soup result stored
# CACHE_INDEX file contains mapping of hash to entry
@dataclasses.dataclass
class SearchQuery:
    any_field: str
    title: str
    author: str
    single_chapter: bool
    word_count: Optional["Constraint"]
    language: str
    fandoms: str
    rating: Optional["Constraint"]
    hits: Optional["Constraint"]
    kudos: Optional["Constraint"]
    crossovers: Optional[bool]
    bookmarks: Optional["Constraint"]
    excluded_tags: str
    comments: Optional["Constraint"]
    completion_status: Optional[bool]
    page: int
    sort_column: str
    sort_direction: str
    revised_at: str
    characters: str
    relationships: str
    tags: str
    guest: bool

    def __init__(
        self,
        any_field="",
        title="",
        author="",
        single_chapter=False,
        word_count=None,
        language="",
        fandoms="",
        rating=None,
        hits=None,
        kudos=None,
        crossovers=None,
        bookmarks=None,
        excluded_tags="",
        comments=None,
        completion_status=None,
        page=1,
        sort_column="",
        sort_direction="",
        revised_at="",
        characters="",
        relationships="",
        tags="",
        guest=True):

        self.any_field = any_field
        self.title = title
        self.author = author
        self.single_chapter = single_chapter
        self.word_count = word_count
        self.language = language
        self.fandoms = fandoms
        self.characters = characters
        self.relationships = relationships
        self.tags = tags
        self.rating = rating
        self.hits = hits
        self.kudos = kudos
        self.crossovers = crossovers
        self.bookmarks = bookmarks
        self.excluded_tags = excluded_tags
        self.comments = comments
        self.completion_status = completion_status
        self.page = page
        self.sort_column = sort_column
        self.sort_direction = sort_direction
        self.revised_at = revised_at
        self.guest = guest

class Search:
    def __init__(
        self, search_query: SearchQuery, session=None):

        self.search_query = search_query
        if session:
            self.search_query.guest = False

        self.session = session

        self.results = None
        self.pages = 0
        self.total_results = 0

    def get_hash(self) -> str:
        print(json_dumps(self.search_query))
        return hashlib.md5(json_dumps(self.search_query).encode('utf-8')).hexdigest()
    
    def load_cache(self) -> Optional[BeautifulSoup]:
        search_hash = self.get_hash()
        filename = os.path.join(CACHE_PAGES_DIR, f"{search_hash}.html")
        cache_hit = False
        with shelve.open(CACHE_INDEX) as f:
            if search_hash in f:
                # check last search time
                cache_hit = True
                print("CACHE HIT")
        soup = None
        if cache_hit:
            with open(filename, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "lxml")
        return soup

        


    @threadable.threadable
    def update(self):
        """Sends a request to the AO3 website with the defined search parameters, and updates all info.
        This function is threadable.
        """
        search_hash = self.get_hash()
        filename = os.path.join(CACHE_PAGES_DIR, f"{search_hash}.html")
        soup = self.load_cache()
        if soup is None:
            print("CACHE MISS")
            soup = search(self.search_query)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(str(soup))
            with shelve.open(CACHE_INDEX) as f:
                f[search_hash] = datetime.datetime.now().strftime(TIME_FMT)

        

        


        results = soup.find("ol", {"class": ("work", "index", "group")})
        if results is None and soup.find("p", text="No results found. You may want to edit your search to make it less specific.") is not None:
            self.results = []
            self.total_results = 0
            self.pages = 0
            return

        works = []
        for work in results.find_all("li", {"role": "article"}):
            if work.h4 is None:
                continue
            
            new = get_work_from_banner(work)
            new._session = self.session
            works.append(new)

        self.results = works
        maindiv = soup.find("div", {"class": "works-search region", "id": "main"})
        self.total_results = int(maindiv.find("h3", {"class": "heading"}).getText().replace(',','').replace('.','').strip().split(" ")[0])
        self.pages = ceil(self.total_results / 20)

def search(search_query: SearchQuery, session=None):
    """Returns the results page for the search as a Soup object

    Args:
        any_field (str, optional): Generic search. Defaults to "".
        title (str, optional): Title of the work. Defaults to "".
        author (str, optional): Authors of the work. Defaults to "".
        single_chapter (bool, optional): Only include one-shots. Defaults to False.
        word_count (AO3.utils.Constraint, optional): Word count. Defaults to None.
        language (str, optional): Work language. Defaults to "".
        fandoms (str, optional): Fandoms included in the work. Defaults to "".
        characters (str, optional): Characters included in the work. Defaults to "".
        relationships (str, optional): Relationships included in the work. Defaults to "".
        tags (str, optional): Additional tags applied to the work. Defaults to "".
        rating (int, optional): Rating for the work. 9 for Not Rated, 10 for General Audiences, 11 for Teen And Up Audiences, 12 for Mature, 13 for Explicit. Defaults to None.
        hits (AO3.utils.Constraint, optional): Number of hits. Defaults to None.
        kudos (AO3.utils.Constraint, optional): Number of kudos. Defaults to None.
        crossovers (bool, optional): If specified, if false, exclude crossovers, if true, include only crossovers
        bookmarks (AO3.utils.Constraint, optional): Number of bookmarks. Defaults to None.
        excluded_tags (str, optional): Tags to exclude. Defaults to "".
        comments (AO3.utils.Constraint, optional): Number of comments. Defaults to None.
        page (int, optional): Page number. Defaults to 1.
        sort_column (str, optional): Which column to sort on. Defaults to "".
        sort_direction (str, optional): Which direction to sort. Defaults to "".
        revised_at (str, optional): Show works older / more recent than this date. Defaults to "".
        session (AO3.Session, optional): Session object. Defaults to None.

    Returns:
        bs4.BeautifulSoup: Search result's soup
    """

    query = utils.Query()
    query.add_field(f"work_search[query]={search_query.any_field if search_query.any_field != '' else ' '}")
    if search_query.page != 1:
        query.add_field(f"page={search_query.page}")
    if search_query.title != "":
        query.add_field(f"work_search[title]={search_query.title}")
    if search_query.author != "":
        query.add_field(f"work_search[creators]={search_query.author}")
    if search_query.single_chapter:
        query.add_field(f"work_search[single_chapter]=1")
    if search_query.word_count is not None:
        query.add_field(f"work_search[word_count]={search_query.word_count}")
    if search_query.language != "":
        query.add_field(f"work_search[language_id]={search_query.language}")
    if search_query.fandoms != "":
        query.add_field(f"work_search[fandom_names]={search_query.fandoms}")
    if search_query.characters != "":
        query.add_field(f"work_search[character_names]={search_query.characters}")
    if search_query.relationships != "":
        query.add_field(f"work_search[relationship_names]={search_query.relationships}")
    if search_query.tags != "":
        query.add_field(f"work_search[freeform_names]={search_query.tags}")
    if search_query.rating is not None:
        query.add_field(f"work_search[rating_ids]={search_query.rating}")
    if search_query.hits is not None:
        query.add_field(f"work_search[hits]={search_query.hits}")
    if search_query.kudos is not None:
        query.add_field(f"work_search[kudos_count]={search_query.kudos}")
    if search_query.crossovers is not None:
        query.add_field(f"work_search[crossover]={'T' if search_query.crossovers else 'F'}")
    if search_query.bookmarks is not None:
        query.add_field(f"work_search[bookmarks_count]={search_query.bookmarks}")
    if search_query.excluded_tags != "":
        query.add_field(f"work_search[excluded_tag_names]={search_query.excluded_tags}")
    if search_query.comments is not None:
        query.add_field(f"work_search[comments_count]={search_query.comments}")
    if search_query.completion_status is not None:
        query.add_field(f"work_search[complete]={'T' if search_query.completion_status else 'F'}")
    if search_query.sort_column != "":
        query.add_field(f"work_search[sort_column]={search_query.sort_column}")
    if search_query.sort_direction != "":
        query.add_field(f"work_search[sort_direction]={search_query.sort_direction}")
    if search_query.revised_at != "":
        query.add_field(f"work_search[revised_at]={search_query.revised_at}")

    url = f"https://archiveofourown.org/works/search?{query.string}"

    if session is None:
        req = requester.request("get", url)
    else:
        req = session.get(url)
    if req.status_code == 429:
        raise utils.HTTPError("We are being rate-limited. Try again in a while or reduce the number of requests")
    soup = BeautifulSoup(req.content, features="lxml")
    return soup

def dict_drop_empty(pairs):
    return dict(
        (k, v)
        for k, v in pairs
        if not (
            v is None
            or not v and isinstance(v, Collection)
        )
    )

def json_default(thing):
    try:
        return dataclasses.asdict(thing, dict_factory=dict_drop_empty)
    except TypeError:
        pass
    if isinstance(thing, datetime.datetime):
        return thing.isoformat(timespec='microseconds')
    raise TypeError(f"object of type {type(thing).__name__} not serializable")

def json_dumps(thing: SearchQuery):
    return json.dumps(
        thing,
        default=json_default,
        ensure_ascii=False,
        sort_keys=True,
        indent=None,
        separators=(',', ':'),
    )


