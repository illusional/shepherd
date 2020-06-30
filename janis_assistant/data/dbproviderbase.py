from typing import (
    Type,
    List,
    Tuple,
    Dict,
    Union,
    ContextManager,
    Optional,
    TypeVar,
    Generic,
)
from abc import abstractmethod
from sqlite3 import Connection, Cursor, OperationalError
from contextlib import contextmanager

from janis_core import Logger

from janis_assistant.data.models.base import DatabaseObject

T = TypeVar("T")


class DbProviderBase(Generic[T]):
    def __init__(
        self,
        base_type: Type[DatabaseObject],
        db: Connection,
        tablename: str,
        scopes: Dict[str, str],
    ):

        self.db: Connection = db
        self.tablename = tablename
        self.scopes = scopes
        self.base = base_type

        schema = self.table_schema()
        with self.with_cursor() as cursor:
            cursor.execute(schema)

    @contextmanager
    def with_cursor(self) -> ContextManager[Cursor]:
        cursor = None
        try:
            cursor = self.db.cursor()
            yield cursor
        finally:
            # Change back up
            if cursor:
                cursor.close()

    def get(
        self, keys: Union[str, List[str]] = "*", where: Tuple[str, List[any]] = None
    ) -> Optional[List[T]]:
        jkeys = ", ".join(keys) if isinstance(keys, list) else keys
        if jkeys == "*":
            keys = [k for _, k in self.base.table_schema()]

        values = []
        whereclauses = []
        if self.scopes:
            scopes = self.scopes.items()
            whereclauses.extend(f"{k} = ?" for k, _ in scopes)
            values.extend(v for _, v in scopes)

        if where:
            whereclauses.append(where[0])
            values.extend(where[1])

        query = f"SELECT {jkeys} FROM {self.tablename}"

        if whereclauses:
            query += f" WHERE {' AND '.join(whereclauses)}"

        with self.with_cursor() as cursor:
            try:
                rows = cursor.execute(query, values).fetchall()
            except OperationalError as e:
                if "readonly database" in str(e):
                    # mfranklin: idk, this sometimes happens. We're doing a select query, idk sqlite3 driver...
                    Logger.debug(
                        "Got readonly error when running query: '{query}', skipping for now"
                    )
                    return None
                elif "locked" in str(e):
                    Logger.debug(
                        "We hit the database at the same time the janis process wrote to it, meh"
                    )
                    return None

        parsedrows = [self.base.deserialize(keys, r) for r in rows]
        return parsedrows

    def commit(self):
        return self.db.commit()

    def table_schema(self):
        return f"""\
        CREATE TABLE IF NOT EXISTS {self.tablename} (
        {self.base.table_schema()}
        )
        """

    def insert_or_update_many(self, els: List[T]):
        queries: Dict[str, List[List[any]]] = {}
        update_separator = ",\n"
        tab = "\t"
        for el in els:
            keys, values = el.prepare_insert()
            prepared_statement = f"""
INSERT INTO {self.tablename}
    ({', '.join(keys)})
VALUES
    ({', '.join(f':{k}' for k in keys)})
ON DUPLICATE KEY UPDATE 
{update_separator.join(f'{tab}{k} = :{k}' for k in keys)};
"""
            if prepared_statement in queries:
                queries[prepared_statement].append(values)
            else:
                queries[prepared_statement] = [values]

        with self.with_cursor() as cursor:
            for query, vvalues in queries.items():
                cursor.executemany(query, vvalues)

        return True
