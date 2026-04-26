from typing import Literal

from pydantic import BaseModel, Field


TableShape = Literal["round", "rectangle"]


class Guest(BaseModel):
    first_name: str
    last_name: str
    table_id: str | None = None
    seat_number: int | None = None


class Hall(BaseModel):
    width: int = 1000
    height: int = 700


class Table(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    shape: TableShape = "round"
    seats: int = Field(..., ge=1, le=40)


class Layout(BaseModel):
    hall: Hall = Hall()
    tables: list[Table] = []


class GuestSearchResult(BaseModel):
    guest: Guest
    table: Table
