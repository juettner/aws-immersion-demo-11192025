#!/usr/bin/env python3
"""
CLI tool for generating synthetic concert data.

Usage:
    python generate_synthetic_data.py --artists 1000 --venues 500 --concerts 10000 --sales 50000
    python generate_synthetic_data.py --seed 42 --output-dir ./data --format csv
    python generate_synthetic_data.py --upload-s3 my-bucket --s3-prefix demo-data
"""
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.synthetic_data_generator import SyntheticDataGenerator, GeneratorConfig


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic concert data for demo and testing purposes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate default dataset (1000 artists, 500 venues, 10k concerts, 50k sales)
  python generate_synthetic_data.py
  
  # Generate smaller dataset for testing
  python generate_synthetic_data.py --artists 100 --venues 50 --concerts 500 --sales 2000
  
  # Generate with specific seed for reproducibility
  python generate_synthetic_data.py --seed 42
  
  # Export to JSON instead of CSV
  python generate_synthetic_data.py --format json
  
  # Upload directly to S3
  python generate_synthetic_data.py --upload-s3 my-bucket --s3-prefix synthetic-data
  
  # Generate and export to custom directory
  python generate_synthetic_data.py --output-dir ./my_data
        """
    )
    
    # Generation parameters
    parser.add_argument(
        '--artists',
        type=int,
        default=1000,
        help='Number of artists to generate (default: 1000)'
    )
    parser.add_argument(
        '--venues',
        type=int,
        default=500,
        help='Number of venues to generate (default: 500)'
    )
    parser.add_argument(
        '--concerts',
        type=int,
        default=10000,
        help='Number of concerts to generate (default: 10000)'
    )
    parser.add_argument(
        '--sales',
        type=int,
        default=50000,
        help='Number of ticket sales to generate (default: 50000)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducible generation (default: None)'
    )
    parser.add_argument(
        '--start-years-ago',
        type=int,
        default=5,
        help='How many years in the past to start generating concerts (default: 5)'
    )
    parser.add_argument(
        '--end-years-ahead',
        type=int,
        default=1,
        help='How many years in the future to generate concerts (default: 1)'
    )
    
    # Export parameters
    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'both'],
        default='csv',
        help='Export format (default: csv)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='generated_data',
        help='Output directory for generated files (default: generated_data)'
    )
    parser.add_argument(
        '--no-export',
        action='store_true',
        help='Skip file export (only generate and validate)'
    )
    
    # S3 upload parameters
    parser.add_argument(
        '--upload-s3',
        type=str,
        default=None,
        help='S3 bucket name to upload data to (optional)'
    )
    parser.add_argument(
        '--s3-prefix',
        type=str,
        default='synthetic-data',
        help='S3 key prefix for uploaded files (default: synthetic-data)'
    )
    
    # Validation
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip data quality validation'
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = GeneratorConfig(
        num_artists=args.artists,
        num_venues=args.venues,
        num_concerts=args.concerts,
        num_ticket_sales=args.sales,
        seed=args.seed,
        start_date_years_ago=args.start_years_ago,
        end_date_years_ahead=args.end_years_ahead
    )
    
    # Initialize generator
    print("=" * 70)
    print("Synthetic Concert Data Generator")
    print("=" * 70)
    
    generator = SyntheticDataGenerator(config)
    
    # Generate data
    try:
        data = generator.generate_all()
        print("\n" + "=" * 70)
        print("Generation Complete")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Error during generation: {e}")
        return 1
    
    # Validate data quality
    if not args.skip_validation:
        validation_result = generator.validate_data_quality()
        if not validation_result['valid']:
            print("\n⚠ Data quality validation failed!")
            print("Consider fixing issues before using this data.")
            if input("\nContinue anyway? (y/n): ").lower() != 'y':
                return 1
    
    # Export to files
    if not args.no_export:
        print("\n" + "=" * 70)
        print("Exporting Data")
        print("=" * 70)
        
        try:
            if args.format in ['csv', 'both']:
                generator.export_to_csv(args.output_dir)
            
            if args.format in ['json', 'both']:
                generator.export_to_json(args.output_dir)
        except Exception as e:
            print(f"\n✗ Error during export: {e}")
            return 1
    
    # Upload to S3
    if args.upload_s3:
        print("\n" + "=" * 70)
        print("Uploading to S3")
        print("=" * 70)
        
        try:
            s3_files = generator.upload_to_s3(args.upload_s3, args.s3_prefix)
            print(f"\n✓ Successfully uploaded {len(s3_files)} files to S3")
        except Exception as e:
            print(f"\n✗ Error during S3 upload: {e}")
            print("Make sure you have AWS credentials configured and proper permissions.")
            return 1
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✓ Generated {len(data['artists'])} artists")
    print(f"✓ Generated {len(data['venues'])} venues")
    print(f"✓ Generated {len(data['concerts'])} concerts")
    print(f"✓ Generated {len(data['ticket_sales'])} ticket sales")
    
    if not args.no_export:
        print(f"\n✓ Files exported to: {args.output_dir}/")
    
    if args.upload_s3:
        print(f"✓ Data uploaded to: s3://{args.upload_s3}/{args.s3_prefix}/")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
