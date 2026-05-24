import json
from pathlib import Path

from app.models import Hall, Layout, Table


DEFAULT_LAYOUT = Layout(
    hall=Hall(width=1024, height=1536),
    tables=[
        Table(id="table_1", name="Стол 1", x=226, y=1110, shape="round", seats=8),
        Table(id="table_2", name="Стол 2", x=200, y=914, shape="round", seats=8),
        Table(id="table_3", name="Стол 3", x=216, y=720, shape="round", seats=8),
        Table(id="table_4", name="Стол 4", x=346, y=540, shape="round", seats=8),
        Table(id="table_5", name="Стол 5", x=520, y=506, shape="round", seats=8),
        Table(id="table_6", name="Стол 6", x=708, y=540, shape="round", seats=8),
        Table(id="table_7", name="Стол 7", x=824, y=720, shape="round", seats=8),
        Table(id="table_8", name="Стол 8", x=826, y=914, shape="round", seats=8),
        Table(id="table_9", name="Стол 9", x=810, y=1118, shape="round", seats=8),
    ],
)


class LayoutStore:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load(self) -> Layout:
        if not self.file_path.exists():
            self.save(DEFAULT_LAYOUT)
            return DEFAULT_LAYOUT

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return Layout.model_validate(data)
        except (json.JSONDecodeError, OSError, ValueError):
            return DEFAULT_LAYOUT

    def save(self, layout: Layout) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(layout.model_dump(), file, ensure_ascii=False, indent=2)

    def get_table(self, table_id: str) -> Table | None:
        layout = self.load()
        return next((table for table in layout.tables if table.id == table_id), None)

    def upsert_table(self, table: Table, original_id: str | None = None) -> None:
        layout = self.load()
        target_id = original_id or table.id
        updated = False

        for index, existing in enumerate(layout.tables):
            if existing.id == target_id:
                layout.tables[index] = table
                updated = True
                break

        if not updated:
            layout.tables.append(table)

        self.save(layout)

    def delete_table(self, table_id: str) -> bool:
        layout = self.load()
        original_count = len(layout.tables)
        layout.tables = [table for table in layout.tables if table.id != table_id]
        self.save(layout)
        return len(layout.tables) < original_count
