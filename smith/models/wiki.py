from enum import Enum


class WikiType(Enum):
    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    
    
wiki_type_to_path = {
    WikiType.CHARACTER: "characters",
    WikiType.LOCATION: "locations",
    WikiType.ITEM: "items",
}