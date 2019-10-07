from typing import List

from janis_runner.data.dbproviderbase import DbProviderBase
from janis_runner.data.models.outputs import WorkflowOutputModel
from janis_runner.utils.dateutil import DateUtil


class OutputDbProvider(DbProviderBase):
    CURRENT_SCHEMA_VERSION = 1

    def table_schema(self):
        return """\
        CREATE TABLE IF NOT EXISTS outputs (
            tag STRING PRIMARY KEY,
            original_path STRING,
            new_path STRING,
            timestamp NULLABLE STRING,
            prefix STRING,
            tags STRING,
            secondaries STRING
        )
        """

    def __init__(self, db, cursor):
        super().__init__(db, cursor)

    def get(self, tag: str) -> WorkflowOutputModel:
        self.cursor.execute("SELECT * FROM outputs WHERE tag = ?", (tag,))
        row = self.cursor.fetchone()
        if not row:
            raise KeyError("Couldn't find output with tag: " + tag)
        return WorkflowOutputModel.from_row(row)

    def get_all(self) -> List[WorkflowOutputModel]:
        self.cursor.execute("SELECT * FROM outputs")
        rows = self.cursor.fetchall()
        return [WorkflowOutputModel.from_row(row) for row in rows]

    _insert_statement = """\
        INSERT INTO outputs
            (tag, original_path, new_path, timestamp, prefix, tags, secondaries)
        VALUES
            (?, ?, ?, ?, ?, ?, ?)
    """

    def insert_many(self, outputs: List[WorkflowOutputModel]):
        self.cursor.executemany(
            self._insert_statement, [self._insert_model_obj(o) for o in outputs]
        )
        self.commit()

    @staticmethod
    def _insert_model_obj(model: WorkflowOutputModel):
        tags = (
            WorkflowOutputModel.ARRAY_SEPARATOR.join(model.tags) if model.tags else None
        )
        secs = (
            WorkflowOutputModel.ARRAY_SEPARATOR.join(model.secondaries)
            if model.secondaries
            else None
        )
        return (
            model.tag,
            model.originalpath,
            model.newpath,
            model.timestamp,
            model.prefix,
            tags,
            secs,
        )

    def insert(self, model: WorkflowOutputModel):
        self.cursor.execute(self._insert_statement, self._insert_model_obj(model))
        self.commit()

    def update_paths(self, tag: str, original_path: str, new_path: str):
        self.cursor.execute(
            """\
            UPDATE outputs SET
                original_path=?,
                new_path=?,
                timestamp=?
            WHERE tag = ?
            """,
            (original_path, new_path, DateUtil.now(), tag),
        )
        self.commit()

    def upgrade_schema(self, from_version: int):
        # if from_version < 2:
        #     self.migrate_to_2()
        return
