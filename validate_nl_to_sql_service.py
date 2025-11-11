"""
Validation script for Natural Language to SQL Query Translator Service.

This script validates the implementation of the NL to SQL service including:
- Intent classification
- Entity extraction
- SQL query generation
- Safety validation
- Query execution (if Redshift is available)
"""
import sys
from typing import List, Tuple

from src.services.nl_to_sql_service import (
    NLToSQLService,
    QueryIntent,
    QueryContext,
    ExtractedEntity
)


def validate_intent_classification() -> Tuple[bool, List[str]]:
    """Validate intent classification functionality."""
    print("\n" + "=" * 80)
    print("Validating Intent Classification")
    print("=" * 80)
    
    issues = []
    nl_service = NLToSQLService()
    
    # Test cases: (query, expected_intent)
    test_cases = [
        ("Tell me about The Beatles", QueryIntent.ARTIST_LOOKUP),
        ("Show me rock artists", QueryIntent.ARTIST_LOOKUP),
        ("Find venues in New York", QueryIntent.VENUE_SEARCH),
        ("What venues have capacity over 10000?", QueryIntent.VENUE_SEARCH),
        ("Show me upcoming concerts", QueryIntent.CONCERT_SEARCH),
        ("What concerts are in Chicago?", QueryIntent.CONCERT_SEARCH),
        ("How many tickets were sold?", QueryIntent.TICKET_SALES_QUERY),
        ("Show me ticket sales revenue", QueryIntent.TICKET_SALES_QUERY),
        ("What are the most popular artists?", QueryIntent.POPULARITY_RANKING),
        ("Show me top venues", QueryIntent.POPULARITY_RANKING),
        ("Show me total revenue by artist", QueryIntent.REVENUE_ANALYSIS),
        ("What's the highest earning concert?", QueryIntent.REVENUE_ANALYSIS),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_intent in test_cases:
        detected_intent = nl_service.classify_intent(query)
        
        if detected_intent == expected_intent:
            print(f"✓ '{query}' -> {detected_intent.value}")
            passed += 1
        else:
            print(f"✗ '{query}' -> Expected: {expected_intent.value}, Got: {detected_intent.value}")
            issues.append(f"Intent classification failed for: {query}")
            failed += 1
    
    print(f"\nIntent Classification: {passed} passed, {failed} failed")
    
    return len(issues) == 0, issues


def validate_entity_extraction() -> Tuple[bool, List[str]]:
    """Validate entity extraction functionality."""
    print("\n" + "=" * 80)
    print("Validating Entity Extraction")
    print("=" * 80)
    
    issues = []
    nl_service = NLToSQLService()
    
    # Test cases
    test_cases = [
        {
            "query": "Show me top 20 rock artists",
            "expected_entities": ["limit", "genre"],
            "intent": QueryIntent.ARTIST_LOOKUP
        },
        {
            "query": "Find venues in New York",
            "expected_entities": ["city"],
            "intent": QueryIntent.VENUE_SEARCH
        },
        {
            "query": 'Show concerts by "The Beatles"',
            "expected_entities": ["artist_name"],
            "intent": QueryIntent.CONCERT_SEARCH
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        query = test_case["query"]
        expected_entities = test_case["expected_entities"]
        intent = test_case["intent"]
        
        entities = nl_service.extract_entities(query, intent)
        extracted_types = [e.entity_type for e in entities]
        
        # Check if expected entities are present
        all_found = all(expected in extracted_types for expected in expected_entities)
        
        if all_found:
            print(f"✓ '{query}' -> Extracted: {extracted_types}")
            passed += 1
        else:
            print(f"✗ '{query}' -> Expected: {expected_entities}, Got: {extracted_types}")
            issues.append(f"Entity extraction incomplete for: {query}")
            failed += 1
    
    print(f"\nEntity Extraction: {passed} passed, {failed} failed")
    
    return len(issues) == 0, issues


def validate_sql_generation() -> Tuple[bool, List[str]]:
    """Validate SQL query generation."""
    print("\n" + "=" * 80)
    print("Validating SQL Query Generation")
    print("=" * 80)
    
    issues = []
    nl_service = NLToSQLService()
    
    # Test different intents
    test_contexts = [
        {
            "name": "Artist Lookup",
            "context": QueryContext(
                intent=QueryIntent.ARTIST_LOOKUP,
                filters={"genre": "rock"},
                limit=10
            ),
            "expected_keywords": ["SELECT", "FROM concert_dw.artists", "genre", "LIMIT"]
        },
        {
            "name": "Venue Search",
            "context": QueryContext(
                intent=QueryIntent.VENUE_SEARCH,
                filters={"city": "New York"},
                limit=5
            ),
            "expected_keywords": ["SELECT", "FROM concert_dw.venues", "city", "LIMIT"]
        },
        {
            "name": "Concert Search",
            "context": QueryContext(
                intent=QueryIntent.CONCERT_SEARCH,
                filters={},
                limit=10
            ),
            "expected_keywords": ["SELECT", "FROM concert_dw.concerts", "JOIN", "LIMIT"]
        },
        {
            "name": "Ticket Sales Query",
            "context": QueryContext(
                intent=QueryIntent.TICKET_SALES_QUERY,
                filters={},
                limit=10
            ),
            "expected_keywords": ["SELECT", "ticket_sales", "SUM", "GROUP BY"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_contexts:
        name = test["name"]
        context = test["context"]
        expected_keywords = test["expected_keywords"]
        
        sql_query = nl_service.generate_sql(context)
        sql_upper = sql_query.sql.upper()
        
        # Check for expected keywords
        all_found = all(keyword.upper() in sql_upper for keyword in expected_keywords)
        
        if all_found and sql_query.is_safe:
            print(f"✓ {name}: SQL generated successfully")
            print(f"  Complexity: {sql_query.estimated_complexity}")
            passed += 1
        else:
            print(f"✗ {name}: SQL generation failed")
            if not all_found:
                missing = [k for k in expected_keywords if k.upper() not in sql_upper]
                print(f"  Missing keywords: {missing}")
                issues.append(f"SQL generation missing keywords for {name}")
            if not sql_query.is_safe:
                print(f"  Safety warnings: {sql_query.safety_warnings}")
                issues.append(f"SQL safety validation failed for {name}")
            failed += 1
    
    print(f"\nSQL Generation: {passed} passed, {failed} failed")
    
    return len(issues) == 0, issues


def validate_sql_safety() -> Tuple[bool, List[str]]:
    """Validate SQL safety checks."""
    print("\n" + "=" * 80)
    print("Validating SQL Safety Checks")
    print("=" * 80)
    
    issues = []
    nl_service = NLToSQLService()
    
    # Safe queries
    safe_queries = [
        "SELECT * FROM concert_dw.artists LIMIT 10;",
        "SELECT name, city FROM concert_dw.venues WHERE capacity > 5000;",
        "SELECT a.name, COUNT(*) FROM concert_dw.concerts c JOIN concert_dw.artists a ON c.artist_id = a.artist_id GROUP BY a.name;"
    ]
    
    # Unsafe queries
    unsafe_queries = [
        "DROP TABLE concert_dw.artists;",
        "DELETE FROM concert_dw.venues WHERE city = 'New York';",
        "SELECT * FROM artists; DROP TABLE venues;",
        "SELECT * FROM concert_dw.artists WHERE name = 'test' OR 1=1--",
        "INSERT INTO concert_dw.artists VALUES ('test', 'Test Artist');",
        "UPDATE concert_dw.artists SET popularity_score = 100;"
    ]
    
    passed = 0
    failed = 0
    
    # Test safe queries
    print("\nTesting safe queries:")
    for query in safe_queries:
        is_safe, warnings = nl_service._validate_sql_safety(query)
        if is_safe:
            print(f"✓ Safe query validated correctly")
            passed += 1
        else:
            print(f"✗ Safe query incorrectly flagged as unsafe: {warnings}")
            issues.append(f"False positive safety check")
            failed += 1
    
    # Test unsafe queries
    print("\nTesting unsafe queries:")
    for query in unsafe_queries:
        is_safe, warnings = nl_service._validate_sql_safety(query)
        if not is_safe:
            print(f"✓ Unsafe query detected correctly: {warnings[0] if warnings else 'blocked'}")
            passed += 1
        else:
            print(f"✗ Unsafe query not detected: {query}")
            issues.append(f"SQL injection vulnerability: {query}")
            failed += 1
    
    print(f"\nSQL Safety: {passed} passed, {failed} failed")
    
    return len(issues) == 0, issues


def validate_query_context_building() -> Tuple[bool, List[str]]:
    """Validate query context building."""
    print("\n" + "=" * 80)
    print("Validating Query Context Building")
    print("=" * 80)
    
    issues = []
    nl_service = NLToSQLService()
    
    test_queries = [
        {
            "query": "Show me top 15 rock artists",
            "expected_limit": 15,
            "expected_filters": ["genre"]
        },
        {
            "query": "Find venues in Chicago with capacity over 5000",
            "expected_limit": 10,  # default
            "expected_filters": ["city", "capacity"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_queries:
        query = test["query"]
        expected_limit = test["expected_limit"]
        expected_filters = test["expected_filters"]
        
        context = nl_service.build_query_context(query)
        
        # Check limit
        limit_ok = context.limit == expected_limit
        
        # Check filters
        filters_ok = all(f in context.filters for f in expected_filters)
        
        if limit_ok and filters_ok:
            print(f"✓ '{query}' -> Context built correctly")
            print(f"  Limit: {context.limit}, Filters: {list(context.filters.keys())}")
            passed += 1
        else:
            print(f"✗ '{query}' -> Context building failed")
            if not limit_ok:
                print(f"  Expected limit: {expected_limit}, Got: {context.limit}")
            if not filters_ok:
                print(f"  Expected filters: {expected_filters}, Got: {list(context.filters.keys())}")
            issues.append(f"Query context building failed for: {query}")
            failed += 1
    
    print(f"\nQuery Context Building: {passed} passed, {failed} failed")
    
    return len(issues) == 0, issues


def validate_end_to_end_translation() -> Tuple[bool, List[str]]:
    """Validate end-to-end query translation."""
    print("\n" + "=" * 80)
    print("Validating End-to-End Query Translation")
    print("=" * 80)
    
    issues = []
    nl_service = NLToSQLService()
    
    test_queries = [
        "Show me popular rock artists",
        "Find venues in New York",
        "What concerts are scheduled?",
        "Show me ticket sales data",
        "What are the top 5 most popular venues?"
    ]
    
    passed = 0
    failed = 0
    
    for query in test_queries:
        result = nl_service.translate_and_execute(query, execute=False)
        
        if result.success and result.query and result.query.is_safe:
            print(f"✓ '{query}'")
            print(f"  Intent: {result.query.intent.value}")
            print(f"  Safe: {result.query.is_safe}")
            print(f"  Complexity: {result.query.estimated_complexity}")
            passed += 1
        else:
            print(f"✗ '{query}' -> Translation failed")
            if result.error:
                print(f"  Error: {result.error}")
            if result.query and not result.query.is_safe:
                print(f"  Safety warnings: {result.query.safety_warnings}")
            issues.append(f"End-to-end translation failed for: {query}")
            failed += 1
    
    print(f"\nEnd-to-End Translation: {passed} passed, {failed} failed")
    
    return len(issues) == 0, issues


def validate_supported_intents() -> Tuple[bool, List[str]]:
    """Validate supported intents documentation."""
    print("\n" + "=" * 80)
    print("Validating Supported Intents Documentation")
    print("=" * 80)
    
    issues = []
    nl_service = NLToSQLService()
    
    intents = nl_service.get_supported_intents()
    
    if len(intents) >= 6:
        print(f"✓ Found {len(intents)} supported intents")
        for intent_info in intents:
            print(f"  - {intent_info['intent']}: {intent_info['description']}")
    else:
        print(f"✗ Expected at least 6 intents, found {len(intents)}")
        issues.append("Insufficient supported intents")
    
    return len(issues) == 0, issues


def main():
    """Run all validation tests."""
    print("\n" + "=" * 80)
    print("NATURAL LANGUAGE TO SQL SERVICE VALIDATION")
    print("=" * 80)
    
    all_issues = []
    results = []
    
    # Run validation tests
    tests = [
        ("Intent Classification", validate_intent_classification),
        ("Entity Extraction", validate_entity_extraction),
        ("SQL Generation", validate_sql_generation),
        ("SQL Safety", validate_sql_safety),
        ("Query Context Building", validate_query_context_building),
        ("End-to-End Translation", validate_end_to_end_translation),
        ("Supported Intents", validate_supported_intents)
    ]
    
    for test_name, test_func in tests:
        try:
            success, issues = test_func()
            results.append((test_name, success))
            all_issues.extend(issues)
        except Exception as e:
            print(f"\n✗ {test_name} validation failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            all_issues.append(f"{test_name} validation exception: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if all_issues:
        print("\nIssues found:")
        for issue in all_issues:
            print(f"  - {issue}")
    
    # Overall result
    print("\n" + "=" * 80)
    if failed == 0:
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 80)
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
