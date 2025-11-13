#!/usr/bin/env python3
"""
End-to-End System Validation Script

Performs comprehensive validation of the entire Concert Data Platform:
- Data ingestion through Kinesis to Redshift
- Chatbot responses for various query types
- ML model predictions
- Dashboard visualizations
- Error handling and edge cases

Generates a validation report documenting test results.
"""

import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import traceback

# Import validation modules
try:
    from src.config.settings import Settings
    from src.infrastructure.kinesis_client import KinesisClient
    from src.infrastructure.redshift_client import RedshiftClient
    from src.services.venue_popularity_service import VenuePopularityService
    from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
    from src.services.recommendation_service import RecommendationService
    import requests
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class ValidationResult:
    """Stores validation test results"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.details = {}
        self.duration = 0.0
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "duration_seconds": round(self.duration, 2),
            "timestamp": self.timestamp.isoformat()
        }


class EndToEndValidator:
    """Performs end-to-end system validation"""
    
    def __init__(self):
        self.settings = Settings.from_env()
        self.results: List[ValidationResult] = []
        self.chatbot_url = "http://localhost:8000"
        self.api_gateway_url = None  # Set if testing deployed API Gateway
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def print_result(self, result: ValidationResult):
        """Print test result"""
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"{status} | {result.test_name} ({result.duration:.2f}s)")
        if result.message:
            print(f"       {result.message}")
        if not result.passed and result.details:
            print(f"       Details: {json.dumps(result.details, indent=8)}")
    
    def run_test(self, test_name: str, test_func) -> ValidationResult:
        """Run a single test and capture result"""
        result = ValidationResult(test_name)
        start_time = time.time()
        
        try:
            success, message, details = test_func()
            result.passed = success
            result.message = message
            result.details = details
        except Exception as e:
            result.passed = False
            result.message = f"Exception: {str(e)}"
            result.details = {"traceback": traceback.format_exc()}
        
        result.duration = time.time() - start_time
        self.results.append(result)
        self.print_result(result)
        
        return result
    
    # Test 1: Data Ingestion Flow
    def test_kinesis_to_redshift_flow(self) -> Tuple[bool, str, Dict]:
        """Test complete data flow from Kinesis to Redshift"""
        try:
            # Send test record to Kinesis
            kinesis_client = KinesisClient(self.settings.aws)
            
            test_record = {
                "artist_id": "test_artist_001",
                "name": "Test Artist",
                "genre": ["rock"],
                "popularity_score": 75.5,
                "timestamp": datetime.now().isoformat()
            }
            
            stream_name = "concert-stream-artists"
            kinesis_client.put_record(
                stream_name=stream_name,
                data=test_record,
                partition_key=test_record["artist_id"]
            )
            
            # Wait for processing (Lambda + S3 + Glue)
            time.sleep(5)
            
            # Check if data reached Redshift
            redshift_client = RedshiftClient(self.settings.aws)
            
            query = f"""
                SELECT COUNT(*) as count
                FROM concerts.artists
                WHERE artist_id = '{test_record["artist_id"]}'
                AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 minute'
            """
            
            result = redshift_client.execute_query(query)
            
            if result and len(result) > 0 and result[0].get("count", 0) > 0:
                return True, "Data successfully flowed from Kinesis to Redshift", {
                    "stream": stream_name,
                    "record_id": test_record["artist_id"],
                    "records_found": result[0]["count"]
                }
            else:
                return False, "Data not found in Redshift after Kinesis ingestion", {
                    "stream": stream_name,
                    "record_id": test_record["artist_id"],
                    "note": "May need more time for processing or check Lambda/Glue logs"
                }
        
        except Exception as e:
            return False, f"Error in data flow test: {str(e)}", {}
    
    # Test 2: Chatbot Artist Lookup
    def test_chatbot_artist_lookup(self) -> Tuple[bool, str, Dict]:
        """Test chatbot artist information retrieval"""
        try:
            response = requests.post(
                f"{self.chatbot_url}/chat",
                json={
                    "message": "Tell me about The Rolling Stones",
                    "session_id": "validation_test_001"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "response" in data and len(data["response"]) > 0:
                    return True, "Chatbot successfully responded to artist lookup", {
                        "response_length": len(data["response"]),
                        "has_data": "data" in data
                    }
                else:
                    return False, "Chatbot response missing or empty", data
            else:
                return False, f"Chatbot returned status {response.status_code}", {
                    "status": response.status_code,
                    "body": response.text
                }
        
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to chatbot service", {
                "url": self.chatbot_url,
                "note": "Ensure chatbot service is running: python src/api/chatbot_api.py"
            }
        except Exception as e:
            return False, f"Error testing chatbot: {str(e)}", {}
    
    # Test 3: Chatbot Venue Recommendations
    def test_chatbot_venue_recommendations(self) -> Tuple[bool, str, Dict]:
        """Test chatbot venue recommendation queries"""
        try:
            response = requests.post(
                f"{self.chatbot_url}/chat",
                json={
                    "message": "What are the best venues in New York?",
                    "session_id": "validation_test_002"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "response" in data and "venue" in data["response"].lower():
                    return True, "Chatbot successfully provided venue recommendations", {
                        "response_contains_venues": True
                    }
                else:
                    return False, "Chatbot response doesn't contain venue information", data
            else:
                return False, f"Chatbot returned status {response.status_code}", {}
        
        except Exception as e:
            return False, f"Error testing venue recommendations: {str(e)}", {}
    
    # Test 4: Chatbot Data Analysis
    def test_chatbot_data_analysis(self) -> Tuple[bool, str, Dict]:
        """Test chatbot data analysis capabilities"""
        try:
            response = requests.post(
                f"{self.chatbot_url}/chat",
                json={
                    "message": "Show me concert attendance trends",
                    "session_id": "validation_test_003"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for visualization or data analysis
                has_viz = "visualization" in data
                has_analysis = "response" in data and any(
                    word in data["response"].lower()
                    for word in ["trend", "analysis", "average", "increase", "decrease"]
                )
                
                if has_viz or has_analysis:
                    return True, "Chatbot successfully performed data analysis", {
                        "has_visualization": has_viz,
                        "has_analysis": has_analysis
                    }
                else:
                    return False, "Chatbot didn't provide analysis or visualization", data
            else:
                return False, f"Chatbot returned status {response.status_code}", {}
        
        except Exception as e:
            return False, f"Error testing data analysis: {str(e)}", {}
    
    # Test 5: Chatbot Conversation Memory
    def test_chatbot_conversation_memory(self) -> Tuple[bool, str, Dict]:
        """Test chatbot conversation context retention"""
        try:
            session_id = "validation_test_004"
            
            # First message
            response1 = requests.post(
                f"{self.chatbot_url}/chat",
                json={
                    "message": "I like rock music",
                    "session_id": session_id
                },
                timeout=30
            )
            
            time.sleep(1)
            
            # Follow-up message referencing previous context
            response2 = requests.post(
                f"{self.chatbot_url}/chat",
                json={
                    "message": "What concerts would you recommend based on my preferences?",
                    "session_id": session_id
                },
                timeout=30
            )
            
            if response2.status_code == 200:
                data = response2.json()
                
                # Check if response references rock music
                if "rock" in data.get("response", "").lower():
                    return True, "Chatbot successfully retained conversation context", {
                        "context_retained": True
                    }
                else:
                    return False, "Chatbot didn't retain conversation context", {
                        "response": data.get("response", "")
                    }
            else:
                return False, f"Chatbot returned status {response2.status_code}", {}
        
        except Exception as e:
            return False, f"Error testing conversation memory: {str(e)}", {}
    
    # Test 6: Venue Popularity Predictions
    def test_venue_popularity_predictions(self) -> Tuple[bool, str, Dict]:
        """Test ML venue popularity predictions"""
        try:
            service = VenuePopularityService(self.settings)
            
            # Get top venues
            top_venues = service.get_top_venues(limit=5)
            
            if top_venues and len(top_venues) > 0:
                # Check prediction structure
                first_venue = top_venues[0]
                required_fields = ["venue_id", "popularity_rank", "avg_attendance_rate"]
                
                has_all_fields = all(field in first_venue for field in required_fields)
                
                if has_all_fields:
                    return True, f"Venue popularity predictions working ({len(top_venues)} venues)", {
                        "venues_count": len(top_venues),
                        "top_venue": first_venue.get("venue_id"),
                        "top_rank": first_venue.get("popularity_rank")
                    }
                else:
                    return False, "Venue predictions missing required fields", {
                        "available_fields": list(first_venue.keys())
                    }
            else:
                return False, "No venue popularity predictions returned", {}
        
        except Exception as e:
            return False, f"Error testing venue predictions: {str(e)}", {}
    
    # Test 7: Ticket Sales Predictions
    def test_ticket_sales_predictions(self) -> Tuple[bool, str, Dict]:
        """Test ML ticket sales predictions"""
        try:
            service = TicketSalesPredictionService(self.settings)
            
            # Get a sample artist and venue from Redshift
            redshift_client = RedshiftClient(self.settings.aws)
            
            query = """
                SELECT a.artist_id, v.venue_id
                FROM concerts.artists a
                CROSS JOIN concerts.venues v
                LIMIT 1
            """
            
            result = redshift_client.execute_query(query)
            
            if result and len(result) > 0:
                artist_id = result[0]["artist_id"]
                venue_id = result[0]["venue_id"]
                event_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                
                prediction = service.predict_sales(
                    artist_id=artist_id,
                    venue_id=venue_id,
                    event_date=event_date
                )
                
                if prediction and "predicted_sales" in prediction:
                    return True, "Ticket sales predictions working", {
                        "predicted_sales": prediction["predicted_sales"],
                        "confidence": prediction.get("confidence_score", 0)
                    }
                else:
                    return False, "Ticket sales prediction missing required fields", prediction
            else:
                return False, "No data available for ticket sales prediction", {}
        
        except Exception as e:
            return False, f"Error testing ticket sales predictions: {str(e)}", {}
    
    # Test 8: Recommendation Engine
    def test_recommendation_engine(self) -> Tuple[bool, str, Dict]:
        """Test concert recommendation engine"""
        try:
            service = RecommendationService(self.settings)
            
            user_preferences = {
                "genres": ["rock", "alternative"],
                "location": "New York"
            }
            
            recommendations = service.get_recommendations(
                user_preferences=user_preferences,
                limit=5
            )
            
            if recommendations and len(recommendations) > 0:
                first_rec = recommendations[0]
                
                if "concert_id" in first_rec and "recommendation_score" in first_rec:
                    return True, f"Recommendation engine working ({len(recommendations)} recommendations)", {
                        "recommendations_count": len(recommendations),
                        "top_score": first_rec.get("recommendation_score")
                    }
                else:
                    return False, "Recommendations missing required fields", first_rec
            else:
                return False, "No recommendations returned", {}
        
        except Exception as e:
            return False, f"Error testing recommendation engine: {str(e)}", {}
    
    # Test 9: Dashboard API Endpoints
    def test_dashboard_api_endpoints(self) -> Tuple[bool, str, Dict]:
        """Test dashboard API endpoints"""
        try:
            # Test venue popularity endpoint
            response = requests.get(
                f"{self.chatbot_url}/api/venues/popularity",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    return True, "Dashboard API endpoints working", {
                        "venues_returned": len(data)
                    }
                else:
                    return False, "Dashboard API returned empty data", {}
            else:
                return False, f"Dashboard API returned status {response.status_code}", {}
        
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to dashboard API", {
                "note": "API endpoints may not be implemented or service not running"
            }
        except Exception as e:
            return False, f"Error testing dashboard API: {str(e)}", {}
    
    # Test 10: Error Handling
    def test_error_handling(self) -> Tuple[bool, str, Dict]:
        """Test system error handling"""
        try:
            # Test chatbot with invalid query
            response = requests.post(
                f"{self.chatbot_url}/chat",
                json={
                    "message": "",  # Empty message
                    "session_id": "validation_test_error"
                },
                timeout=10
            )
            
            # Should handle gracefully (either 400 or 200 with error message)
            if response.status_code in [200, 400]:
                return True, "System handles errors gracefully", {
                    "status_code": response.status_code
                }
            else:
                return False, f"Unexpected error response: {response.status_code}", {}
        
        except Exception as e:
            return False, f"Error testing error handling: {str(e)}", {}
    
    # Test 11: Data Quality
    def test_data_quality(self) -> Tuple[bool, str, Dict]:
        """Test data quality in Redshift"""
        try:
            redshift_client = RedshiftClient(self.settings.aws)
            
            # Check for null values in critical fields
            query = """
                SELECT
                    (SELECT COUNT(*) FROM concerts.artists WHERE name IS NULL) as null_artist_names,
                    (SELECT COUNT(*) FROM concerts.venues WHERE capacity IS NULL) as null_venue_capacity,
                    (SELECT COUNT(*) FROM concerts.concerts WHERE event_date IS NULL) as null_concert_dates,
                    (SELECT COUNT(*) FROM concerts.artists) as total_artists,
                    (SELECT COUNT(*) FROM concerts.venues) as total_venues,
                    (SELECT COUNT(*) FROM concerts.concerts) as total_concerts
            """
            
            result = redshift_client.execute_query(query)
            
            if result and len(result) > 0:
                data = result[0]
                
                null_count = (
                    data.get("null_artist_names", 0) +
                    data.get("null_venue_capacity", 0) +
                    data.get("null_concert_dates", 0)
                )
                
                total_records = (
                    data.get("total_artists", 0) +
                    data.get("total_venues", 0) +
                    data.get("total_concerts", 0)
                )
                
                if total_records > 0:
                    quality_rate = ((total_records - null_count) / total_records) * 100
                    
                    if quality_rate >= 95:
                        return True, f"Data quality excellent ({quality_rate:.1f}%)", data
                    else:
                        return False, f"Data quality below threshold ({quality_rate:.1f}%)", data
                else:
                    return False, "No data found in Redshift", data
            else:
                return False, "Cannot query data quality metrics", {}
        
        except Exception as e:
            return False, f"Error testing data quality: {str(e)}", {}
    
    # Test 12: Referential Integrity
    def test_referential_integrity(self) -> Tuple[bool, str, Dict]:
        """Test referential integrity between tables"""
        try:
            redshift_client = RedshiftClient(self.settings.aws)
            
            # Check for orphaned records
            query = """
                SELECT
                    (SELECT COUNT(*) FROM concerts.concerts c
                     WHERE NOT EXISTS (SELECT 1 FROM concerts.artists a WHERE a.artist_id = c.artist_id)) as orphaned_concerts_artist,
                    (SELECT COUNT(*) FROM concerts.concerts c
                     WHERE NOT EXISTS (SELECT 1 FROM concerts.venues v WHERE v.venue_id = c.venue_id)) as orphaned_concerts_venue,
                    (SELECT COUNT(*) FROM concerts.ticket_sales ts
                     WHERE NOT EXISTS (SELECT 1 FROM concerts.concerts c WHERE c.concert_id = ts.concert_id)) as orphaned_sales
            """
            
            result = redshift_client.execute_query(query)
            
            if result and len(result) > 0:
                data = result[0]
                
                orphaned_count = (
                    data.get("orphaned_concerts_artist", 0) +
                    data.get("orphaned_concerts_venue", 0) +
                    data.get("orphaned_sales", 0)
                )
                
                if orphaned_count == 0:
                    return True, "Referential integrity maintained (no orphaned records)", data
                else:
                    return False, f"Found {orphaned_count} orphaned records", data
            else:
                return False, "Cannot query referential integrity", {}
        
        except Exception as e:
            return False, f"Error testing referential integrity: {str(e)}", {}
    
    def run_all_tests(self):
        """Run all validation tests"""
        self.print_header("End-to-End System Validation")
        
        print("Starting comprehensive system validation...")
        print(f"Timestamp: {datetime.now().isoformat()}\n")
        
        # Data Flow Tests
        self.print_header("Data Flow Tests")
        self.run_test("Kinesis to Redshift Data Flow", self.test_kinesis_to_redshift_flow)
        self.run_test("Data Quality Validation", self.test_data_quality)
        self.run_test("Referential Integrity Check", self.test_referential_integrity)
        
        # Chatbot Tests
        self.print_header("Chatbot Tests")
        self.run_test("Chatbot Artist Lookup", self.test_chatbot_artist_lookup)
        self.run_test("Chatbot Venue Recommendations", self.test_chatbot_venue_recommendations)
        self.run_test("Chatbot Data Analysis", self.test_chatbot_data_analysis)
        self.run_test("Chatbot Conversation Memory", self.test_chatbot_conversation_memory)
        
        # ML Model Tests
        self.print_header("ML Model Tests")
        self.run_test("Venue Popularity Predictions", self.test_venue_popularity_predictions)
        self.run_test("Ticket Sales Predictions", self.test_ticket_sales_predictions)
        self.run_test("Recommendation Engine", self.test_recommendation_engine)
        
        # API and Error Handling Tests
        self.print_header("API and Error Handling Tests")
        self.run_test("Dashboard API Endpoints", self.test_dashboard_api_endpoints)
        self.run_test("Error Handling", self.test_error_handling)
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate validation summary"""
        self.print_header("Validation Summary")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Total Duration: {sum(r.duration for r in self.results):.2f}s")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.test_name}: {result.message}")
        
        # Save detailed report
        self.save_report()
    
    def save_report(self):
        """Save validation report to file"""
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
                "pass_rate": (sum(1 for r in self.results if r.passed) / len(self.results) * 100) if self.results else 0,
                "total_duration": sum(r.duration for r in self.results)
            },
            "test_results": [r.to_dict() for r in self.results]
        }
        
        filename = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: {filename}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="End-to-end system validation")
    parser.add_argument(
        "--chatbot-url",
        type=str,
        default="http://localhost:8000",
        help="Chatbot API URL"
    )
    parser.add_argument(
        "--skip-kinesis",
        action="store_true",
        help="Skip Kinesis data flow test (requires write access)"
    )
    
    args = parser.parse_args()
    
    validator = EndToEndValidator()
    validator.chatbot_url = args.chatbot_url
    
    try:
        validator.run_all_tests()
        
        # Exit with appropriate code
        failed_count = sum(1 for r in validator.results if not r.passed)
        sys.exit(0 if failed_count == 0 else 1)
    
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error during validation: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
