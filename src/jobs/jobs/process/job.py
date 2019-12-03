# """Acquisition jobs"""
# import math
import pandas as pd
from pyspark.mllib.stat import Statistics
from pyspark.ml.feature import StringIndexer
from pyspark.sql.functions import (
    approx_count_distinct, isnan, when, count, col)
from jobs.config.file import THIS_DIR, FromJson
from jobs.jobs.common import SparkSQL


class GetTrainingData(SparkSQL):
    """Get training data"""
    metrics = {}

    def _execute(self) -> str:
        """Run this job"""
        df = self.df_from_temp_table(self.kwargs["previous_job_temp_table"])
        conf = FromJson(THIS_DIR)
        columns_to_drop = conf["conf.modelling.drop_columns"]
        df = df.drop(*columns_to_drop)
        df = df.filter(
            (df["loan_status"] == "Fully Paid") |
            (df["loan_status"] == "Charged Off")
        )
        self.metrics["num_records"] = df.count()
        self.metrics["num_columns"] = len(df.columns)
        df.createOrReplaceTempView(self.temp_table)
        return self.temp_table


class DropNullAndDuplicateRow(SparkSQL):
    """Drop null rows and duplicates

    Remove null and duplicate rows"""

    metrics = {}

    def _execute(self) -> str:
        """Run this job"""
        df = self.df_from_temp_table(self.kwargs["previous_job_temp_table"])
        cols_ = df.columns

        threshold = float(self.kwargs.get("na_threshold", "0.7"))

        na_thresh = int(threshold * len(cols_))
        df = df.dropna(thresh=na_thresh).dropDuplicates()

        self.metrics["num_records"] = df.count()
        self.metrics["num_columns"] = len(df.columns)

        df.createOrReplaceTempView(self.temp_table)
        return self.temp_table


class DropNullColumns(SparkSQL):
    """Prepare training data

    Remove columns with a certain threshold of null values"""

    metrics = {}

    @staticmethod
    def null_columns(
            df_,
            num_rows_: int,
            threshold: float = 0.8) -> list:
        """Get columns that have many null values than threshold

        :param df_: pyspark dataframe
        :param num_rows_: size of the dataframe
        :param threshold: The ratio of NaNs to num_rows
        :return:
        """
        df = df_.select(
            [count(when(isnan(c) | col(c).isNull(), c)).alias(c) for c in
             df_.columns])
        cols_data = df.toPandas().to_dict()
        cols_data = {col_: val[0] for col_, val in cols_data.items()}

        cols = []
        for col_, frequency in cols_data.items():
            if (float(frequency) / num_rows_) > threshold:
                cols.append(col_)

        return cols

    def _execute(self) -> str:
        """Run this job"""
        df = self.df_from_temp_table(self.kwargs["previous_job_temp_table"])
        num_rows = df.count()
        threshold = float(self.kwargs.get("na_threshold", "0.7"))
        columns_to_drop = self.null_columns(df, num_rows, threshold)

        if columns_to_drop:
            df = df.drop(*columns_to_drop)

        self.metrics["num_records"] = df.count()
        self.metrics["num_columns"] = len(df.columns)
        self.metrics["columns_dropped"] = len(columns_to_drop)

        df.createOrReplaceTempView(self.temp_table)
        return self.temp_table


class SetTrainingData(SparkSQL):
    """Get training data

    Use category columns with few dimensions"""

    metrics = {}
    target = "loan_status"

    @staticmethod
    def index_columns(sdf_, cols: list):
        """Index string columns

        :param sdf_: pyspark dataframe
        :param cols: Columns to be indexed
        :return: Pyspark Dataframe with newly added columns
        """
        col_names = sdf_.columns
        df_corr = sdf_.select(*col_names)

        for col_ in cols:
            indexer_ = StringIndexer(
                inputCol=col_, outputCol="indexed{}".format(col_))
            indexer_.setHandleInvalid("skip")
            model_ = indexer_.fit(df_corr)
            sdf_ = model_.transform(sdf_)

        return sdf_

    @staticmethod
    def corr(sdf_) -> pd.DataFrame:
        """Calculate correlation of data

        :param sdf_: pyspark dataframe
        :return: Correlation matrix in a pamdas dataframe
        """
        col_names = sdf_.columns

        features = sdf_.rdd.map(lambda row: row[0:])
        corr_mat = Statistics.corr(features, method="pearson")
        corr_df = pd.DataFrame(corr_mat)
        corr_df.index, corr_df.columns = col_names, col_names
        return corr_df

    def group_distinct(self, df_, columns: list) -> dict:
        """

        :param df_: pysaprk df
        :param columns: columns of type str in the dataframe
        :return: dict of columns and distinct values
        """
        data = []
        for c in columns:
            cnt = df_.agg(approx_count_distinct(col(c)).alias(c)).collect()
            data.append(cnt[0][0])
        df_pd = pd.DataFrame(
            index=columns,
            columns=["num_distinct"],
            data=data
        )
        return df_pd.sort_values(
            "num_distinct", axis=0, ascending=True).to_dict()["num_distinct"]

    def _execute(self) -> str:
        """Run this job"""
        df = self.df_from_temp_table(self.kwargs["previous_job_temp_table"])
        str_col_ = [col[0] for col in df.dtypes if col[1] == "string"]
        non_str_col = [col[0] for col in df.dtypes if col[1] != "string"]
        unq_grp = self.group_distinct(df, str_col_)

        to_double_col = [k for k, v in unq_grp.items() if (int(v) > 1000)]

        # Only use category columns with fewer dimensions
        category_cols = [k for k, v in unq_grp.items() if (int(v) <= 10)]

        df_train = df.selectExpr(
            *non_str_col,
            *category_cols,
            *[
                "cast({col} as float) {col}".format(
                    col=col) for col in to_double_col
            ])

        category_cols = [
            col[0] for col in df_train.dtypes if col[1] == "string"]
        df_train = self.index_columns(df_train, category_cols)

        # corr_df: pd.DataFrame = self.corr(df_train)
        #
        # d: dict = corr_df["loan_status"].to_dict()
        # print(d)
        # cols_to_drop = [k for k, v in d.items() if math.isnan(v)]
        #
        # df_train = df_train.drop(*cols_to_drop)

        self.metrics["num_records"] = df_train.count()
        self.metrics["num_columns"] = len(df_train.columns)

        df_train.createOrReplaceTempView(self.temp_table)
        return self.temp_table
