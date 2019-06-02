import abc

from shepherd.data.dbproviderbase import DbProviderBase
from shepherd.management import Archivable
from shepherd.utils import Logger


class KeyValueDbProviderBase(DbProviderBase, abc.ABC):
    def __init__(self, db, cursor, tablename: str):
        super(KeyValueDbProviderBase, self).__init__(db, cursor)
        self.tablename = tablename

        self.create_schema_if_required()

    def create_schema_if_required(self):
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {self.tablename}(
                    identifier varchar(10) NOT NULL,
                    key varchar(15) NOT NULL,
                    value text, 
                    PRIMARY KEY(identifier, key)
                )""")

    @abc.abstractmethod
    def get_type_from_args(self, args) -> Archivable:
        pass

    def get(self, identifier) -> Archivable:
        args = self.cursor.execute(f"SELECT key, value FROM {self.tablename} where identifier = ?", (identifier, )).fetchall()
        arged = {k: v for k, v in args}

        T = self.get_type_from_args(arged["fstype"])

        return T.db_from_kwargs(**arged)

    def persist(self, t: Archivable, throw_if_exists=True, should_commit=True):
        # check if already exists

        if self.cursor.execute(f"SELECT COUNT(*) from {self.tablename} where identifier = ?", (t.id(),)).fetchone()[0] > 0:
            message = f"An environment with identifier '{t.id()}' already exists"
            Logger.log(message)
            if throw_if_exists:
                raise Exception(message)
            return

        kvargs = t.db_to_kwargs()
        for (k, v) in kvargs.items():
            self.cursor.execute(f"""INSERT INTO {self.tablename} (identifier, key, value) VALUES (?, ?, ?)""",
                                (t.id(), k, v))

        if should_commit:
            self.commit()
