#!/usr/bin/env python3
"""
data_preprocessing.py

Preprocess MIND behaviors + news → one Parquet of (user_id, news_id, impression_id,
 impressions, clicks, ctr, avg_hour, category_idx, title_len, abstract_len).

Handles mixed one- and two-digit hours, avoids OOM via shuffle tuning & repartitioning.
"""

import argparse
import logging

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, explode, split, avg, sum as _sum, length,
    lit, to_timestamp, coalesce, when
)
from pyspark.ml.feature import StringIndexer


def parse_args():
    p = argparse.ArgumentParser(
        description="Preprocess MIND-small dataset for FeedRanker"
    )
    p.add_argument("--behaviors", required=True,
                   help="train/behaviors.tsv")
    p.add_argument("--news", required=True,
                   help="train/news.tsv")
    p.add_argument("--output", required=True,
                   help="where to write features.parquet")
    p.add_argument("--date-format",
                   default="M/d/yyyy h:mm:ss a",
                   help="Use M/d/yyyy h:mm:ss a to accept 1- or 2-digit hours")
    return p.parse_args()


def main():
    args = parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger()

    # build session and immediately tune memory
    spark = (SparkSession.builder
             .appName("FeedRankerPreprocessing-MIND")
             .config("spark.memory.fraction", "0.6")       # MUST be a string
             .getOrCreate())

    # tune shuffle partitions based on cores
    cores = spark.sparkContext.defaultParallelism
    shuffle_parts = max(cores * 4, 50)
    log.info(f"Setting spark.sql.shuffle.partitions = {shuffle_parts}")
    spark.conf.set("spark.sql.shuffle.partitions", str(shuffle_parts))  # MUST be a string

    # ----------------------------------------------------------------
    # 1) Load + parse behaviors
    # ----------------------------------------------------------------
    log.info("Loading behaviors")
    beh = (spark.read
            .option("sep", "\t")
            .csv(args.behaviors)
            .toDF("user_id", "imp_id", "imp_time", "history", "impressions"))

    log.info("Parsing timestamps")
    beh2 = (beh
        .withColumn(
            "ts0",
            coalesce(
                to_timestamp(col("imp_time"), args.date_format),
                lit(None).cast("timestamp")
            )
        )
        .withColumn("ts", col("ts0").cast("long"))
        .withColumn(
            "hour_of_day",
            when(col("ts").isNotNull(), (col("ts") % 86400) / 3600)
            .otherwise(lit(None))
        )
        .drop("imp_time", "ts0")
    )

    # ----------------------------------------------------------------
    # 2) Explode impressions → one row per (news, click)
    # ----------------------------------------------------------------
    log.info("Exploding impressions")
    exp = (beh2
        .withColumn("pair", explode(split(col("impressions"), " ")))
        .withColumn("news_id", split(col("pair"), "-").getItem(0))
        .withColumn("click", split(col("pair"), "-").getItem(1).cast("int"))
        .withColumn("imp", lit(1))
        .select("user_id", "imp_id", "news_id", "hour_of_day", "imp", "click")
        .drop("pair", "impressions")
    )

    # bound per-partition data for the big groupBy
    exp = exp.repartition(shuffle_parts, "imp_id")

    # ----------------------------------------------------------------
    # 3) Aggregate per impression
    # ----------------------------------------------------------------
    log.info("Aggregating features per (user,news,imp_id)")
    feat = (exp.groupBy("user_id", "news_id", "imp_id")
               .agg(
                   _sum("imp").alias("impressions"),
                   _sum("click").alias("clicks"),
                   avg("hour_of_day").alias("avg_hour")
               )
               .withColumn(
                   "ctr",
                   when(col("impressions") > 0,
                        col("clicks") / col("impressions"))
                   .otherwise(lit(0.0))
               )
    )

    # ----------------------------------------------------------------
    # 4) Load + featurize news metadata
    # ----------------------------------------------------------------
    log.info("Loading news metadata")
    news = (spark.read
               .option("sep", "\t")
               .csv(args.news)
               .toDF("news_id", "category", "subcategory", "title",
                     "abstract", "url", "title_ent", "abs_ent"))

    news_feats = news.select(
        "news_id",
        "category",
        length(col("title")).alias("title_len"),
        length(col("abstract")).alias("abstract_len")
    )

    log.info("Indexing categories")
    idxer = StringIndexer(
        inputCol="category",
        outputCol="category_idx",
        handleInvalid="keep"
    ).fit(news_feats)

    news_idx = (idxer.transform(news_feats)
                    .select("news_id", "category_idx", "title_len", "abstract_len"))

    # ----------------------------------------------------------------
    # 5) Join & write
    # ----------------------------------------------------------------
    log.info("Joining behavior & content features")
    final = (feat.join(news_idx, on="news_id", how="left")
                 .fillna({
                     "category_idx": -1.0,
                     "title_len": 0,
                     "abstract_len": 0,
                     "avg_hour": 0.0
                 }))

    log.info("Repartitioning to 200 files and writing to Parquet")
    (final.repartition(200)
          .write.mode("overwrite")
          .parquet(args.output))

    log.info("Done.")
    spark.stop()


if __name__ == "__main__":
    main()
