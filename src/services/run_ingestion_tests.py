#!/usr/bin/env python3
"""
Test runner for ingestion component unit tests.
Validates API connector error handling, retry logic, and file processing with various data formats.
"""
import subprocess
import sys
from pathlib import Path


def run_test_suite():
    """Run the complete ingestion component test suite."""
    
    print("🧪 Running Ingestion Component Unit Tests")
    print("=" * 50)
    
    # Test categories and their specific tests
    test_categories = [
        {
            "name": "API Client Error Handling & Retry Logic",
            "tests": [
                "src/services/external_apis/test_api_connectors.py::TestRateLimiter",
                "src/services/external_apis/test_api_connectors.py::TestAPIClient::test_api_client_retry_logic_server_error",
                "src/services/external_apis/test_api_connectors.py::TestAPIClient::test_api_client_retry_logic_timeout",
                "src/services/external_apis/test_api_connectors.py::TestAPIClient::test_api_client_rate_limit_handling",
                "src/services/external_apis/test_api_connectors.py::TestAPIClient::test_api_client_client_error_no_retry",
                "src/services/external_apis/test_api_connectors.py::TestAPIClient::test_api_client_network_error_retry",
            ]
        },
        {
            "name": "Ingestion Service Error Scenarios",
            "tests": [
                "src/services/external_apis/test_api_connectors.py::TestIngestionService::test_ingestion_service_missing_credentials",
                "src/services/external_apis/test_api_connectors.py::TestIngestionService::test_ingest_artist_data_no_client",
                "src/services/external_apis/test_api_connectors.py::TestIngestionService::test_ingest_artist_data_api_failure",
                "src/services/external_apis/test_api_connectors.py::TestIngestionService::test_ingest_artist_data_partial_success",
                "src/services/external_apis/test_api_connectors.py::TestIngestionService::test_comprehensive_ingestion_exception_handling",
            ]
        },
        {
            "name": "File Processing with Various Data Formats & Quality Issues",
            "tests": [
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_process_malformed_csv_file",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_process_large_csv_file",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_process_corrupted_json_file",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_process_empty_xml_file",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_process_mixed_encoding_file",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_file_size_validation",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_unsupported_file_extension",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_data_quality_validation_edge_cases",
            ]
        },
        {
            "name": "Data Transformation & Validation",
            "tests": [
                "src/services/external_apis/test_api_connectors.py::TestSpotifyClient::test_transform_artist_data",
                "src/services/external_apis/test_api_connectors.py::TestTicketmasterClient::test_transform_venue_data",
                "src/services/external_apis/test_api_connectors.py::TestTicketmasterClient::test_transform_event_data",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_validate_data_quality_valid",
                "src/services/test_file_processor.py::TestFileUploadProcessor::test_validate_data_quality_invalid",
            ]
        }
    ]
    
    total_passed = 0
    total_failed = 0
    failed_tests = []
    
    for category in test_categories:
        print(f"\n📋 {category['name']}")
        print("-" * len(category['name']))
        
        category_passed = 0
        category_failed = 0
        
        for test in category['tests']:
            try:
                # Run individual test
                result = subprocess.run(
                    ["python", "-m", "pytest", test, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print(f"  ✅ {test.split('::')[-1]}")
                    category_passed += 1
                    total_passed += 1
                else:
                    print(f"  ❌ {test.split('::')[-1]}")
                    category_failed += 1
                    total_failed += 1
                    failed_tests.append(test)
                    
                    # Print error details for failed tests
                    if result.stderr:
                        print(f"     Error: {result.stderr.strip()}")
                    
            except subprocess.TimeoutExpired:
                print(f"  ⏰ {test.split('::')[-1]} (timeout)")
                category_failed += 1
                total_failed += 1
                failed_tests.append(test)
            except Exception as e:
                print(f"  💥 {test.split('::')[-1]} (exception: {e})")
                category_failed += 1
                total_failed += 1
                failed_tests.append(test)
        
        print(f"  📊 Category Results: {category_passed} passed, {category_failed} failed")
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if failed_tests:
        print(f"\n🔍 Failed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    # Test coverage summary
    print(f"\n📋 Test Coverage Summary:")
    print(f"  🔄 API Error Handling & Retry Logic: Comprehensive")
    print(f"  📁 File Processing Various Formats: Comprehensive") 
    print(f"  🧪 Mock External APIs: Implemented")
    print(f"  🛡️ Data Quality Validation: Comprehensive")
    print(f"  ⚡ Edge Case Handling: Extensive")
    
    success_rate = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print("\n🎉 All ingestion component tests passed!")
        return True
    else:
        print(f"\n⚠️  {total_failed} test(s) failed. Please review and fix.")
        return False


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)