"""
AWS Glue ETL jobs for concert data transformation and normalization.
"""
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import re
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process
import boto3
from botocore.exceptions import ClientError

# AWS Glue imports
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.context import SparkContext
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import pyspark.sql.functions as F

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)


class DataQualityMonitor:
    """Monitor and track data quality metrics during ETL processing."""
    
    def __init__(self, cloudwatch_client=None):
        self.cloudwatch = cloudwatch_client or boto3.client('cloudwatch')
        self.quality_metrics = {}
        
    def track_metric(self, metric_name: str, value: float, unit: str = 'Count', dimensions: Dict[str, str] = None):
        """Track a data quality metric."""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace='ConcertDataPlatform/DataQuality',
                MetricData=[metric_data]
            )
            
            self.quality_metrics[metric_name] = value
            
        except Exception as e:
            print(f"Failed to track metric {metric_name}: {str(e)}")
    
    def calculate_completeness_score(self, df: DataFrame, required_columns: List[str]) -> float:
        """Calculate data completeness score for required columns."""
        total_rows = df.count()
        if total_rows == 0:
            return 0.0
        
        completeness_scores = []
        for col in required_columns:
            if col in df.columns:
                non_null_count = df.filter(F.col(col).isNotNull() & (F.col(col) != "")).count()
                completeness_scores.append(non_null_count / total_rows)
            else:
                completeness_scores.append(0.0)
        
        return sum(completeness_scores) / len(completeness_scores) * 100
    
    def calculate_uniqueness_score(self, df: DataFrame, key_column: str) -> float:
        """Calculate uniqueness score for a key column."""
        total_rows = df.count()
        if total_rows == 0:
            return 100.0
        
        unique_rows = df.select(key_column).distinct().count()
        return (unique_rows / total_rows) * 100
    
    def detect_anomalies(self, df: DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect statistical anomalies in numeric columns."""
        anomalies = {}
        
        for col in numeric_columns:
            if col in df.columns:
                stats = df.select(
                    F.mean(col).alias('mean'),
                    F.stddev(col).alias('stddev'),
                    F.min(col).alias('min'),
                    F.max(col).alias('max'),
                    F.count(col).alias('count')
                ).collect()[0]
                
                if stats['stddev'] and stats['count'] > 1:
                    # Calculate z-score threshold (3 standard deviations)
                    threshold = 3
                    lower_bound = stats['mean'] - (threshold * stats['stddev'])
                    upper_bound = stats['mean'] + (threshold * stats['stddev'])
                    
                    outlier_count = df.filter(
                        (F.col(col) < lower_bound) | (F.col(col) > upper_bound)
                    ).count()
                    
                    anomalies[col] = {
                        'outlier_count': outlier_count,
                        'outlier_percentage': (outlier_count / stats['count']) * 100,
                        'mean': stats['mean'],
                        'stddev': stats['stddev'],
                        'min': stats['min'],
                        'max': stats['max']
                    }
        
        return anomalies


class FuzzyMatcher:
    """Fuzzy matching utilities for data deduplication."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def normalize_string(self, text: str) -> str:
        """Normalize string for better matching."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove common prefixes/suffixes
        text = re.sub(r'^(the|a|an)\s+', '', text)
        text = re.sub(r'\s+(inc|llc|ltd|corp|corporation)\.?$', '', text)
        
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings."""
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        norm_str1 = self.normalize_string(str1)
        norm_str2 = self.normalize_string(str2)
        
        # Use multiple similarity metrics and take the maximum
        ratio = fuzz.ratio(norm_str1, norm_str2)
        partial_ratio = fuzz.partial_ratio(norm_str1, norm_str2)
        token_sort_ratio = fuzz.token_sort_ratio(norm_str1, norm_str2)
        token_set_ratio = fuzz.token_set_ratio(norm_str1, norm_str2)
        
        return max(ratio, partial_ratio, token_sort_ratio, token_set_ratio) / 100.0
    
    def find_duplicates(self, df: DataFrame, match_columns: List[str], id_column: str) -> DataFrame:
        """Find potential duplicate records using fuzzy matching."""
        # Convert to Pandas for fuzzy matching (for smaller datasets)
        pandas_df = df.toPandas()
        
        duplicates = []
        processed_ids = set()
        
        for i, row1 in pandas_df.iterrows():
            if row1[id_column] in processed_ids:
                continue
                
            matches = [row1[id_column]]
            
            for j, row2 in pandas_df.iterrows():
                if i >= j or row2[id_column] in processed_ids:
                    continue
                
                # Calculate similarity across all match columns
                similarities = []
                for col in match_columns:
                    if col in pandas_df.columns:
                        sim = self.calculate_similarity(str(row1[col]), str(row2[col]))
                        similarities.append(sim)
                
                if similarities and max(similarities) >= self.similarity_threshold:
                    matches.append(row2[id_column])
            
            if len(matches) > 1:
                # Mark all but the first as duplicates
                for match_id in matches[1:]:
                    duplicates.append({
                        'duplicate_id': match_id,
                        'master_id': matches[0],
                        'similarity_score': max(similarities) if similarities else 0.0,
                        'match_columns': match_columns
                    })
                    processed_ids.add(match_id)
            
            processed_ids.add(row1[id_column])
        
        # Convert back to Spark DataFrame
        if duplicates:
            duplicate_schema = StructType([
                StructField("duplicate_id", StringType(), True),
                StructField("master_id", StringType(), True),
                StructField("similarity_score", DoubleType(), True),
                StructField("match_columns", ArrayType(StringType()), True)
            ])
            
            return spark.createDataFrame(duplicates, duplicate_schema)
        else:
            # Return empty DataFrame with correct schema
            return spark.createDataFrame([], StructType([
                StructField("duplicate_id", StringType(), True),
                StructField("master_id", StringType(), True),
                StructField("similarity_score", DoubleType(), True),
                StructField("match_columns", ArrayType(StringType()), True)
            ]))


class ArtistETL:
    """ETL processor for artist data normalization."""
    
    def __init__(self, quality_monitor: DataQualityMonitor, fuzzy_matcher: FuzzyMatcher):
        self.quality_monitor = quality_monitor
        self.fuzzy_matcher = fuzzy_matcher
    
    def normalize_artist_data(self, df: DataFrame) -> DataFrame:
        """Normalize and clean artist data."""
        print("Starting artist data normalization...")
        
        # Clean and standardize artist names
        df = df.withColumn(
            "name_normalized",
            F.trim(F.regexp_replace(F.col("name"), r"[^\w\s&'-]", ""))
        )
        
        # Standardize genres (convert to lowercase, split by common delimiters)
        df = df.withColumn(
            "genres_normalized",
            F.split(F.lower(F.regexp_replace(F.col("genre"), r"[,;/|]", ",")), ",")
        )
        
        # Clean up genres array (remove empty strings and trim)
        df = df.withColumn(
            "genres_cleaned",
            F.expr("filter(transform(genres_normalized, x -> trim(x)), x -> x != '')")
        )
        
        # Normalize popularity score (ensure 0-100 range)
        df = df.withColumn(
            "popularity_score_normalized",
            F.when(F.col("popularity_score").isNull(), 0.0)
            .when(F.col("popularity_score") < 0, 0.0)
            .when(F.col("popularity_score") > 100, 100.0)
            .otherwise(F.col("popularity_score"))
        )
        
        # Parse and validate formation date
        df = df.withColumn(
            "formation_date_parsed",
            F.when(F.col("formation_date").isNotNull(), 
                   F.to_date(F.col("formation_date"), "yyyy-MM-dd"))
        )
        
        # Clean member names
        df = df.withColumn(
            "members_cleaned",
            F.expr("transform(members, x -> trim(x))")
        )
        
        # Add data quality flags
        df = df.withColumn(
            "data_quality_score",
            F.when(F.col("name").isNull() | (F.col("name") == ""), 0)
            .when(F.col("artist_id").isNull() | (F.col("artist_id") == ""), 0)
            .otherwise(
                (F.when(F.col("name").isNotNull() & (F.col("name") != ""), 25).otherwise(0) +
                 F.when(F.col("genres_cleaned").isNotNull() & (F.size("genres_cleaned") > 0), 25).otherwise(0) +
                 F.when(F.col("popularity_score").isNotNull(), 25).otherwise(0) +
                 F.when(F.col("formation_date_parsed").isNotNull(), 25).otherwise(0))
            )
        )
        
        # Calculate quality metrics
        total_records = df.count()
        high_quality_records = df.filter(F.col("data_quality_score") >= 75).count()
        
        self.quality_monitor.track_metric(
            "ArtistDataQualityScore",
            (high_quality_records / total_records * 100) if total_records > 0 else 0,
            "Percent",
            {"DataType": "Artists"}
        )
        
        print(f"Artist normalization completed. Processed {total_records} records.")
        return df
    
    def deduplicate_artists(self, df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        """Identify and handle duplicate artist records."""
        print("Starting artist deduplication...")
        
        # Find duplicates based on name similarity
        duplicates_df = self.fuzzy_matcher.find_duplicates(
            df, 
            match_columns=["name_normalized"], 
            id_column="artist_id"
        )
        
        duplicate_count = duplicates_df.count()
        total_count = df.count()
        
        self.quality_monitor.track_metric(
            "ArtistDuplicateCount",
            duplicate_count,
            "Count",
            {"DataType": "Artists"}
        )
        
        self.quality_monitor.track_metric(
            "ArtistDuplicatePercentage",
            (duplicate_count / total_count * 100) if total_count > 0 else 0,
            "Percent",
            {"DataType": "Artists"}
        )
        
        # Remove duplicates from main dataset
        if duplicate_count > 0:
            duplicate_ids = duplicates_df.select("duplicate_id").rdd.flatMap(lambda x: x).collect()
            df_deduplicated = df.filter(~F.col("artist_id").isin(duplicate_ids))
        else:
            df_deduplicated = df
        
        print(f"Artist deduplication completed. Found {duplicate_count} duplicates.")
        return df_deduplicated, duplicates_df


class VenueETL:
    """ETL processor for venue data normalization."""
    
    def __init__(self, quality_monitor: DataQualityMonitor, fuzzy_matcher: FuzzyMatcher):
        self.quality_monitor = quality_monitor
        self.fuzzy_matcher = fuzzy_matcher
    
    def normalize_venue_data(self, df: DataFrame) -> DataFrame:
        """Normalize and clean venue data."""
        print("Starting venue data normalization...")
        
        # Clean and standardize venue names
        df = df.withColumn(
            "name_normalized",
            F.trim(F.regexp_replace(F.col("name"), r"[^\w\s&'-]", ""))
        )
        
        # Standardize venue types
        venue_type_mapping = {
            "arena": "arena",
            "stadium": "stadium", 
            "theater": "theater",
            "theatre": "theater",
            "club": "club",
            "outdoor": "outdoor",
            "amphitheater": "amphitheater",
            "amphitheatre": "amphitheater",
            "hall": "hall",
            "center": "center",
            "centre": "center"
        }
        
        venue_type_expr = F.lower(F.trim(F.col("venue_type")))
        for key, value in venue_type_mapping.items():
            venue_type_expr = F.when(venue_type_expr.contains(key), value).otherwise(venue_type_expr)
        
        df = df.withColumn("venue_type_normalized", venue_type_expr)
        
        # Validate and normalize capacity
        df = df.withColumn(
            "capacity_normalized",
            F.when(F.col("capacity").isNull() | (F.col("capacity") <= 0), None)
            .when(F.col("capacity") > 200000, None)  # Unreasonably large
            .otherwise(F.col("capacity"))
        )
        
        # Normalize location data
        df = df.withColumn(
            "city_normalized",
            F.trim(F.regexp_replace(F.col("location.city"), r"[^\w\s'-]", ""))
        )
        
        df = df.withColumn(
            "state_normalized", 
            F.upper(F.trim(F.col("location.state")))
        )
        
        df = df.withColumn(
            "country_normalized",
            F.upper(F.trim(F.col("location.country")))
        )
        
        # Validate coordinates
        df = df.withColumn(
            "latitude_validated",
            F.when((F.col("location.latitude") >= -90) & (F.col("location.latitude") <= 90), 
                   F.col("location.latitude"))
        )
        
        df = df.withColumn(
            "longitude_validated",
            F.when((F.col("location.longitude") >= -180) & (F.col("location.longitude") <= 180),
                   F.col("location.longitude"))
        )
        
        # Clean amenities
        df = df.withColumn(
            "amenities_cleaned",
            F.expr("transform(amenities, x -> lower(trim(x)))")
        )
        
        # Calculate data quality score
        df = df.withColumn(
            "data_quality_score",
            F.when(F.col("name").isNull() | (F.col("name") == ""), 0)
            .when(F.col("venue_id").isNull() | (F.col("venue_id") == ""), 0)
            .otherwise(
                (F.when(F.col("name").isNotNull() & (F.col("name") != ""), 20).otherwise(0) +
                 F.when(F.col("capacity_normalized").isNotNull(), 20).otherwise(0) +
                 F.when(F.col("city_normalized").isNotNull() & (F.col("city_normalized") != ""), 20).otherwise(0) +
                 F.when(F.col("venue_type_normalized").isNotNull(), 20).otherwise(0) +
                 F.when(F.col("latitude_validated").isNotNull() & F.col("longitude_validated").isNotNull(), 20).otherwise(0))
            )
        )
        
        # Calculate quality metrics
        total_records = df.count()
        high_quality_records = df.filter(F.col("data_quality_score") >= 80).count()
        
        self.quality_monitor.track_metric(
            "VenueDataQualityScore",
            (high_quality_records / total_records * 100) if total_records > 0 else 0,
            "Percent",
            {"DataType": "Venues"}
        )
        
        print(f"Venue normalization completed. Processed {total_records} records.")
        return df
    
    def deduplicate_venues(self, df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        """Identify and handle duplicate venue records."""
        print("Starting venue deduplication...")
        
        # Find duplicates based on name and location similarity
        duplicates_df = self.fuzzy_matcher.find_duplicates(
            df,
            match_columns=["name_normalized", "city_normalized"],
            id_column="venue_id"
        )
        
        duplicate_count = duplicates_df.count()
        total_count = df.count()
        
        self.quality_monitor.track_metric(
            "VenueDuplicateCount",
            duplicate_count,
            "Count",
            {"DataType": "Venues"}
        )
        
        # Remove duplicates from main dataset
        if duplicate_count > 0:
            duplicate_ids = duplicates_df.select("duplicate_id").rdd.flatMap(lambda x: x).collect()
            df_deduplicated = df.filter(~F.col("venue_id").isin(duplicate_ids))
        else:
            df_deduplicated = df
        
        print(f"Venue deduplication completed. Found {duplicate_count} duplicates.")
        return df_deduplicated, duplicates_df


class ConcertETL:
    """ETL processor for concert data normalization."""
    
    def __init__(self, quality_monitor: DataQualityMonitor):
        self.quality_monitor = quality_monitor
    
    def normalize_concert_data(self, df: DataFrame) -> DataFrame:
        """Normalize and clean concert data."""
        print("Starting concert data normalization...")
        
        # Parse and validate event dates
        df = df.withColumn(
            "event_date_parsed",
            F.to_timestamp(F.col("event_date"), "yyyy-MM-dd HH:mm:ss")
        )
        
        # Validate event dates (not too far in past or future)
        current_year = datetime.now().year
        df = df.withColumn(
            "event_date_validated",
            F.when(
                (F.year("event_date_parsed") >= current_year - 50) & 
                (F.year("event_date_parsed") <= current_year + 5),
                F.col("event_date_parsed")
            )
        )
        
        # Normalize status values
        status_mapping = {
            "scheduled": "scheduled",
            "confirmed": "scheduled", 
            "completed": "completed",
            "finished": "completed",
            "cancelled": "cancelled",
            "canceled": "cancelled",
            "postponed": "postponed",
            "rescheduled": "postponed"
        }
        
        status_expr = F.lower(F.trim(F.col("status")))
        for key, value in status_mapping.items():
            status_expr = F.when(status_expr == key, value).otherwise(status_expr)
        
        df = df.withColumn("status_normalized", status_expr)
        
        # Validate attendance and revenue
        df = df.withColumn(
            "total_attendance_validated",
            F.when((F.col("total_attendance") >= 0) & (F.col("total_attendance") <= 500000),
                   F.col("total_attendance"))
        )
        
        df = df.withColumn(
            "revenue_validated",
            F.when((F.col("revenue") >= 0) & (F.col("revenue") <= 100000000),
                   F.col("revenue"))
        )
        
        # Process ticket prices (convert to structured format if needed)
        df = df.withColumn(
            "ticket_prices_validated",
            F.when(F.col("ticket_prices").isNotNull(), F.col("ticket_prices"))
        )
        
        # Calculate data quality score
        df = df.withColumn(
            "data_quality_score",
            F.when(F.col("concert_id").isNull() | (F.col("concert_id") == ""), 0)
            .when(F.col("artist_id").isNull() | (F.col("artist_id") == ""), 0)
            .when(F.col("venue_id").isNull() | (F.col("venue_id") == ""), 0)
            .otherwise(
                (F.when(F.col("concert_id").isNotNull() & (F.col("concert_id") != ""), 25).otherwise(0) +
                 F.when(F.col("event_date_validated").isNotNull(), 25).otherwise(0) +
                 F.when(F.col("artist_id").isNotNull() & (F.col("artist_id") != ""), 25).otherwise(0) +
                 F.when(F.col("venue_id").isNotNull() & (F.col("venue_id") != ""), 25).otherwise(0))
            )
        )
        
        # Calculate quality metrics
        total_records = df.count()
        high_quality_records = df.filter(F.col("data_quality_score") >= 75).count()
        
        self.quality_monitor.track_metric(
            "ConcertDataQualityScore",
            (high_quality_records / total_records * 100) if total_records > 0 else 0,
            "Percent",
            {"DataType": "Concerts"}
        )
        
        print(f"Concert normalization completed. Processed {total_records} records.")
        return df


def process_artist_data():
    """Main Glue job for processing artist data."""
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'input_path',
        'output_path',
        'duplicates_output_path'
    ])
    
    job.init(args['JOB_NAME'], args)
    
    try:
        # Initialize components
        quality_monitor = DataQualityMonitor()
        fuzzy_matcher = FuzzyMatcher(similarity_threshold=0.85)
        artist_etl = ArtistETL(quality_monitor, fuzzy_matcher)
        
        # Read input data
        input_df = glueContext.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={"paths": [args['input_path']]},
            format="json"
        ).toDF()
        
        print(f"Processing {input_df.count()} artist records...")
        
        # Normalize data
        normalized_df = artist_etl.normalize_artist_data(input_df)
        
        # Deduplicate
        deduplicated_df, duplicates_df = artist_etl.deduplicate_artists(normalized_df)
        
        # Write output
        output_dynamic_frame = DynamicFrame.fromDF(deduplicated_df, glueContext, "artists_processed")
        glueContext.write_dynamic_frame.from_options(
            frame=output_dynamic_frame,
            connection_type="s3",
            connection_options={"path": args['output_path']},
            format="parquet"
        )
        
        # Write duplicates report
        if duplicates_df.count() > 0:
            duplicates_dynamic_frame = DynamicFrame.fromDF(duplicates_df, glueContext, "artists_duplicates")
            glueContext.write_dynamic_frame.from_options(
                frame=duplicates_dynamic_frame,
                connection_type="s3", 
                connection_options={"path": args['duplicates_output_path']},
                format="json"
            )
        
        print("Artist data processing completed successfully.")
        
    except Exception as e:
        print(f"Artist data processing failed: {str(e)}")
        raise
    
    finally:
        job.commit()


def process_venue_data():
    """Main Glue job for processing venue data."""
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'input_path', 
        'output_path',
        'duplicates_output_path'
    ])
    
    job.init(args['JOB_NAME'], args)
    
    try:
        # Initialize components
        quality_monitor = DataQualityMonitor()
        fuzzy_matcher = FuzzyMatcher(similarity_threshold=0.80)
        venue_etl = VenueETL(quality_monitor, fuzzy_matcher)
        
        # Read input data
        input_df = glueContext.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={"paths": [args['input_path']]},
            format="json"
        ).toDF()
        
        print(f"Processing {input_df.count()} venue records...")
        
        # Normalize data
        normalized_df = venue_etl.normalize_venue_data(input_df)
        
        # Deduplicate
        deduplicated_df, duplicates_df = venue_etl.deduplicate_venues(normalized_df)
        
        # Write output
        output_dynamic_frame = DynamicFrame.fromDF(deduplicated_df, glueContext, "venues_processed")
        glueContext.write_dynamic_frame.from_options(
            frame=output_dynamic_frame,
            connection_type="s3",
            connection_options={"path": args['output_path']},
            format="parquet"
        )
        
        # Write duplicates report
        if duplicates_df.count() > 0:
            duplicates_dynamic_frame = DynamicFrame.fromDF(duplicates_df, glueContext, "venues_duplicates")
            glueContext.write_dynamic_frame.from_options(
                frame=duplicates_dynamic_frame,
                connection_type="s3",
                connection_options={"path": args['duplicates_output_path']},
                format="json"
            )
        
        print("Venue data processing completed successfully.")
        
    except Exception as e:
        print(f"Venue data processing failed: {str(e)}")
        raise
    
    finally:
        job.commit()


def process_concert_data():
    """Main Glue job for processing concert data."""
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'input_path',
        'output_path'
    ])
    
    job.init(args['JOB_NAME'], args)
    
    try:
        # Initialize components
        quality_monitor = DataQualityMonitor()
        concert_etl = ConcertETL(quality_monitor)
        
        # Read input data
        input_df = glueContext.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={"paths": [args['input_path']]},
            format="json"
        ).toDF()
        
        print(f"Processing {input_df.count()} concert records...")
        
        # Normalize data
        normalized_df = concert_etl.normalize_concert_data(input_df)
        
        # Write output
        output_dynamic_frame = DynamicFrame.fromDF(normalized_df, glueContext, "concerts_processed")
        glueContext.write_dynamic_frame.from_options(
            frame=output_dynamic_frame,
            connection_type="s3",
            connection_options={"path": args['output_path']},
            format="parquet"
        )
        
        print("Concert data processing completed successfully.")
        
    except Exception as e:
        print(f"Concert data processing failed: {str(e)}")
        raise
    
    finally:
        job.commit()


if __name__ == "__main__":
    # Determine which job to run based on job name
    job_name = getResolvedOptions(sys.argv, ['JOB_NAME'])['JOB_NAME']
    
    if 'artist' in job_name.lower():
        process_artist_data()
    elif 'venue' in job_name.lower():
        process_venue_data()
    elif 'concert' in job_name.lower():
        process_concert_data()
    else:
        raise ValueError(f"Unknown job type: {job_name}")