# src/silencio2/models.py
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import List

CODE_RE = r"^\([1-4]\)\([A-EX]\)(?:\([a-ex]\))?$"

class RedactionItem(BaseModel):
    id: int
    code: str = Field(pattern=CODE_RE)
    desc: str
    surface: str # canonical match text
    aliases: List[str] = Field(default_factory=list)
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
            if item.code == code and item.desc == desc and norm_surface and item.aliases:
                # NOTE:
                # If same (code, desc) and new surface is already an alias,
                # we consider it already exists.
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

    def add_alias(self, item_id: int, alias_surface: str) -> None:
        """
        Add an alias surface to an existing RedactionItem.

        Args:
            item_id (int): The ID of the redaction item.
            alias_surface (str): The alias surface to add.
        """
        item = self.find(item_id)
        if not item:
            raise ValueError(f"RedactionItem with id {item_id} not found")

        alias_surface = alias_surface.strip()
        if not alias_surface:
            raise ValueError("Alias surface cannot be empty or whitespace")

        if alias_surface == item.surface or alias_surface in item.aliases:
            # already exists
            return

        item.aliases.append(alias_surface)
