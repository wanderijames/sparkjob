"""Create a benchmark Model"""
from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.feature import IndexToString, StringIndexer, VectorIndexer, VectorAssembler
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from jobs.jobs.common import SparkSQL


__all__ = ["BenchmarkModel"]


class BenchmarkModel(SparkSQL):
    """Create a benchmark model"""

    target_label = "loan_status"
    metrics = {}

    @staticmethod
    def index_str_columns(df_, cols_to_index: list):
        """Index str columns

        :param df_: pyspark DF
        :param cols_to_index: Columns to index
        :return: pyspark df with indexed columns
        """
        for col_ in cols_to_index:
            indexer_ = StringIndexer(
                inputCol=col_, outputCol="indexed{}".format(col_))
            indexer_.setHandleInvalid("skip")
            model_ = indexer_.fit(df_)
            df_ = model_.transform(df_)
        return df_

    @staticmethod
    def create_feature_vector(df_, cols):
        """Create feature vector

        :param df_: pyspark DF
        :param cols: Columns to use in creating feature vector
        :return: pyspark df with a feature vector column
        """
        assembler = VectorAssembler(
            inputCols=cols,
            outputCol="features",
            handleInvalid="skip")
        return assembler.transform(df_)

    def _execute(self):
        df = self.df_from_temp_table(self.kwargs["previous_job_temp_table"])
        if self.target_label in df.columns:
            df = df.drop(self.target_label)
        cols_to_index = [k for k, v in df.dtypes if
                         (v == "string" and k != self.target_label)]
        cols_not_to_index = [k for k, v in df.dtypes if v != "string"]

        feature_cols = cols_not_to_index + [
            "indexed{}".format(col_) for col_ in cols_to_index]

        df = self.create_feature_vector(df, feature_cols)

        # Index labels, adding metadata to the label column.
        # Fit on whole dataset to include all labels in index.
        label_indexer = StringIndexer(
            inputCol=self.target_label,
            outputCol="{}loan_status".format("indexed"))
        label_indexer.setHandleInvalid("skip")
        label_indexer = label_indexer.fit(df)

        # Automatically identify categorical features, and index them.
        # Set maxCategories so features with > 12 distinct values are
        # treated as continuous.
        feature_indexer = VectorIndexer(
            inputCol="features",
            outputCol="indexedFeatures",
            maxCategories=12)
        feature_indexer.setHandleInvalid("skip")

        # Split the data into training and test sets (30% held out for testing)
        (trainingData, testData) = df.randomSplit([0.7, 0.3])

        # Train a RandomForest model.
        rf = RandomForestClassifier(
            labelCol="{}loan_status".format("indexed"),
            featuresCol="indexedFeatures",
            predictionCol="prediction",
            numTrees=10)

        # # Convert indexed labels back to original labels.
        label_converter = IndexToString(
            inputCol="prediction",
            outputCol="predictedLabel",
            labels=label_indexer.labels)

        # Chain indexers and forest in a Pipeline
        pipeline = Pipeline(
            stages=[label_indexer, feature_indexer, rf, label_converter])

        # Train model.  This also runs the indexers.
        model = pipeline.fit(trainingData)

        # # Make predictions.
        predictions = model.transform(testData)

        # Select (prediction, true label) and compute test error
        evaluator = MulticlassClassificationEvaluator(
            labelCol="{}loan_status".format("indexed"),
            predictionCol="prediction",
            metricName="accuracy")

        accuracy = evaluator.evaluate(predictions)

        self.metrics["accuracy"] = accuracy

        return str(accuracy)
