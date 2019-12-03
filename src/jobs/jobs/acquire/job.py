"""Acquisition jobs"""
from jobs.jobs.acquire.common import CSVRecord

__all__ = ["LoadCSV"]


class LoadCSV(CSVRecord):
    """Get training data"""
    metrics = {}

    def _execute(self) -> str:
        """Run this job"""
        df = self.load_file()
        self.metrics["num_records"] = df.count()
        self.metrics["num_columns"] = df.columns
        df.createOrReplaceTempView(self.temp_table)
        return self.temp_table
