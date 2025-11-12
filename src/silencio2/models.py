# src/silencio2/models.py
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

CODE_RE = r"^\([1-4]\)\([A-EX]\)(?:\([a-ex]\))?$"

class Alias(BaseModel):
    id: int
    surface: str

    @field_validator("surface")
    @classmethod
    def no_empty(cls, v: str) -> str:
        """
        Ensure alias surface is not empty or just whitespace.

        Args:
            v (str): The alias surface string to validate.

        Returns:
            str: The validated alias surface string.
        """
        vs = v.strip()
        if not vs:
            raise ValueError("alias surface cannot be empty or whitespace")
        return vs

class RedactionItem(BaseModel):
    id: int
    code: str = Field(pattern=CODE_RE)
    desc: str
    surface: str # canonical match text
    aliases: List[Alias] = Field(default_factory=list) # alternative match texts
    scope: str = Field(default="global") # "global" | "file-local"

    @field_validator("surface")
    @classmethod
    def no_empty(cls, v: str) -> str:
        """
        Ensure surface is not empty or just whitespace.

        Args:
            v (str): The surface string to validate.

        Returns:
            str: The validated surface string.
        """
        vs = v.strip()
        if not vs:
            raise ValueError("surface cannot be empty or whitespace")
        return vs

class Inventory(BaseModel):
    items: List[RedactionItem] = Field(default_factory=list)

    def next_id(self) -> int:
        """
        Get the next available ID for a new RedactionItem.

        Returns:
            int: The next available ID.
        """
        return max((item.id for item in self.items), default=0) + 1

    def find(self, item_id: int) -> RedactionItem | None:
        """
        Find a RedactionItem by its ID.

        Args:
            item_id (int): The ID of the redaction item to find.

        Returns:
            RedactionItem | None: The found redaction item, or None if not found.
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def add_or_merge(self, code: str, desc: str, surface: str) -> RedactionItem:
        """
        Add a new RedactionItem to the inventory, 
        or merge with an existing one if (code, surface) matches.

        Args:
            code (str): The code of the redaction item.
            desc (str): The description of the redaction item.
            surface (str): The surface text of the redaction item.

        Returns:
            RedactionItem: The added or merged redaction item.
        """
        norm_surface = surface

        # Merge only when exact same (code, surface) alraedy exists.
        for item in self.items:
            if item.code == code and item.surface == surface:
                # already exists, return it
                return item
            if item.code == code and item.desc == desc:
                # already present as alias?
                if any(alias.surface == norm_surface for alias in item.aliases):
                    return item

        # Create new item
        new_item = RedactionItem(
            id=self.next_id(),
            code=code,
            desc=desc,
            surface=norm_surface,
        )
        self.items.append(new_item)
        return new_item

    def add_alias(self, item_id: int, alias_surface: str) -> int:
        """
        Add an alias surface to an existing RedactionItem.
        And return the alias ID.

        Args:
            item_id (int): The ID of the redaction item.
            alias_surface (str): The alias surface to add.

        Returns:
            int: The ID of the added alias.
        """
        item = self.find(item_id)
        if not item:
            raise ValueError(f"RedactionItem with id {item_id} not found")

        alias_surface = alias_surface.strip()
        if not alias_surface:
            raise ValueError("alias surface cannot be empty or whitespace")

        if alias_surface == item.surface or any(alias.surface == alias_surface for alias in item.aliases):
            # already exists
            existing = next((alias for alias in item.aliases if alias.surface == alias_surface), None)
            return existing.id if existing else 0

        next_alias_id = max((alias.id for alias in item.aliases), default=0) + 1 # steadily increase the ID
        item.aliases.append(
            Alias(
                id=next_alias_id,
                surface=alias_surface
            )
        )

        return next_alias_id

    def get_alias_surface(self, item_id: int, alias_id: int) -> Optional[str]:
        """
        Given an item ID and alias ID, return the alias surface if exists.

        Args:
            item_id (int): The ID of the redaction item.
            alias_id (int): The ID of the alias.

        Returns:
            Optional[str]: The alias surface if found, else None.
        """
        item = self.find(item_id)
        if not item:
            return None
        for alias in item.aliases:
            if alias.id == alias_id:
                return alias.surface

        return None
