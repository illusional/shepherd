import datetime

from janis_runner.utils.dateutil import DateUtil


class WorkflowOutputModel:

    ARRAY_SEPARATOR = "::"

    def __init__(
        self, tag, original_path, new_path, timestamp, prefix, tags, secondaries
    ):
        self.tag = tag
        self.originalpath = original_path
        self.newpath = new_path
        self.prefix = prefix

        self.tags = None
        if tags:
            if isinstance(tags, str):
                self.tags = tags.split(WorkflowOutputModel.ARRAY_SEPARATOR)
            else:
                self.tags = tags

        self.secondaries = None
        if secondaries:
            if isinstance(secondaries, str):
                self.secondaries = secondaries.split(
                    WorkflowOutputModel.ARRAY_SEPARATOR
                )
            else:
                self.secondaries = secondaries

        if not isinstance(timestamp, datetime.datetime):
            timestamp = DateUtil.parse_iso(timestamp)
        self.timestamp = timestamp

    @staticmethod
    def from_row(row):
        return WorkflowOutputModel(
            row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        )
