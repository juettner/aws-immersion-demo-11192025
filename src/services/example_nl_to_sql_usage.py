"""
Example usage of Natural Language to SQL Query Translator Service.

This demonstrates how to use the NL to SQL service to translate natural language
queries into SQL and execute them against the Redshift data warehouse.
"""
from src.services.nl_to_sql_service import (
    NLToSQLService,
    QueryIntent,
    QueryContext
)
from src.services.redshift_service import RedshiftService


def example_basic_translation():
    """Example: Basic query translation without execution."""
    print("=" * 80)
    print("Example 1: Basic Query Translation")
    print("=" * 80)
    
    # Initialize service without Redshift (translation only)
    nl_service = NLToSQLService()
    
    # Example queries
    queries = [
        "Show me popular rock artists",
        "Find venues in New York with capacity over 10000",
        "What concerts are scheduled in Chicago?",
        "Show me ticket sales for The Beatles",
        "What are the top 5 most popular venues?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        
        # Translate query
        result = nl_service.translate_and_execute(query, execute=False)
        
        if result.success and result.query:
            print(f"Intent: {result.query.intent.value}")
            print(f"Safe: {result.query.is_safe}")
            print(f"Complexity: {result.query.estimated_complexity}")
            print(f"\nGenerated SQL:")
            print(result.query.sql)
        else:
            print(f"Error: {result.error}")
        
        print("-" * 80)


def example_intent_classification():
    """Example: Intent classification."""
    print("\n" + "=" * 80)
    print("Example 2: Intent Classification")
    print("=" * 80)
    
    nl_service = NLToSQLService()
    
    test_queries = [
        "Tell me about The Rolling Stones",
        "Find venues in Los Angeles",
        "Show me upcoming concerts",
        "How many tickets were sold?",
        "What are the most popular artists?",
        "Show me revenue by artist"
    ]
    
    for query in test_queries:
        intent = nl_service.classify_intent(query)
        print(f"Query: {query}")
        print(f"Intent: {intent.value}\n")


def example_entity_extraction():
    """Example: Entity extraction from queries."""
    print("=" * 80)
    print("Example 3: Entity Extraction")
    print("=" * 80)
    
    nl_service = NLToSQLService()
    
    test_queries = [
        'Find concerts by "The Beatles" in New York',
        "Show me top 20 rock artists",
        "Find venues in Chicago with capacity over 5000"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        intent = nl_service.classify_intent(query)
        entities = nl_service.extract_entities(query, intent)
        
        print(f"Intent: {intent.value}")
        print("Entities:")
        for entity in entities:
            print(f"  - {entity.entity_type}: {entity.value} (confidence: {entity.confidence})")


def example_query_context_building():
    """Example: Building query context."""
    print("\n" + "=" * 80)
    print("Example 4: Query Context Building")
    print("=" * 80)
    
    nl_service = NLToSQLService()
    
    query = "Show me top 15 rock artists with high popularity"
    print(f"Query: {query}\n")
    
    context = nl_service.build_query_context(query)
    
    print(f"Intent: {context.intent.value}")
    print(f"Limit: {context.limit}")
    print(f"Sort By: {context.sort_by}")
    print(f"Sort Order: {context.sort_order}")
    print(f"Filters: {context.filters}")
    print(f"\nEntities:")
    for entity in context.entities:
        print(f"  - {entity.entity_type}: {entity.value}")


def example_sql_generation():
    """Example: SQL generation for different intents."""
    print("\n" + "=" * 80)
    print("Example 5: SQL Generation for Different Intents")
    print("=" * 80)
    
    nl_service = NLToSQLService()
    
    # Artist lookup
    print("\n--- Artist Lookup ---")
    context = QueryContext(
        intent=QueryIntent.ARTIST_LOOKUP,
        filters={"genre": "rock"},
        limit=5
    )
    sql_query = nl_service.generate_sql(context)
    print(f"Safe: {sql_query.is_safe}")
    print(f"SQL:\n{sql_query.sql}")
    
    # Venue search
    print("\n--- Venue Search ---")
    context = QueryContext(
        intent=QueryIntent.VENUE_SEARCH,
        filters={"city": "New York", "capacity": "10000"},
        limit=10
    )
    sql_query = nl_service.generate_sql(context)
    print(f"Safe: {sql_query.is_safe}")
    print(f"SQL:\n{sql_query.sql}")
    
    # Concert search
    print("\n--- Concert Search ---")
    context = QueryContext(
        intent=QueryIntent.CONCERT_SEARCH,
        filters={"city": "Chicago"},
        limit=10
    )
    sql_query = nl_service.generate_sql(context)
    print(f"Safe: {sql_query.is_safe}")
    print(f"SQL:\n{sql_query.sql}")


def example_sql_safety_validation():
    """Example: SQL safety validation."""
    print("\n" + "=" * 80)
    print("Example 6: SQL Safety Validation")
    print("=" * 80)
    
    nl_service = NLToSQLService()
    
    # Safe query
    safe_sql = "SELECT * FROM concert_dw.artists LIMIT 10;"
    is_safe, warnings = nl_service._validate_sql_safety(safe_sql)
    print(f"\nSafe Query: {safe_sql}")
    print(f"Is Safe: {is_safe}")
    print(f"Warnings: {warnings}")
    
    # Unsafe queries
    unsafe_queries = [
        "DROP TABLE concert_dw.artists;",
        "SELECT * FROM artists; DELETE FROM venues;",
        "SELECT * FROM artists WHERE name = 'test' OR 1=1--",
        "INSERT INTO artists VALUES ('test', 'Test Artist')"
    ]
    
    for unsafe_sql in unsafe_queries:
        is_safe, warnings = nl_service._validate_sql_safety(unsafe_sql)
        print(f"\nUnsafe Query: {unsafe_sql}")
        print(f"Is Safe: {is_safe}")
        print(f"Warnings: {warnings}")


def example_with_redshift_execution():
    """Example: Full translation and execution with Redshift."""
    print("\n" + "=" * 80)
    print("Example 7: Translation and Execution with Redshift")
    print("=" * 80)
    print("\nNote: This requires a configured Redshift connection and data.")
    
    try:
        # Initialize services
        redshift_service = RedshiftService()
        nl_service = NLToSQLService(redshift_service=redshift_service)
        
        # Example queries
        queries = [
            "Show me top 5 artists by popularity",
            "Find venues in New York",
            "What are the upcoming concerts?"
        ]
        
        for query in queries:
            print(f"\n{'=' * 60}")
            print(f"Query: {query}")
            print('=' * 60)
            
            # Translate and execute
            result = nl_service.translate_and_execute(query, execute=True)
            
            if result.success:
                print(f"\nIntent: {result.query.intent.value}")
                print(f"Rows returned: {result.row_count}")
                print(f"Execution time: {result.execution_time_ms:.2f}ms")
                
                if result.data:
                    print("\nResults:")
                    for i, row in enumerate(result.data[:3], 1):  # Show first 3 rows
                        print(f"  {i}. {row}")
                    
                    if result.row_count > 3:
                        print(f"  ... and {result.row_count - 3} more rows")
            else:
                print(f"\nError: {result.error}")
        
        # Close connection
        redshift_service.close()
        
    except Exception as e:
        print(f"\nCould not connect to Redshift: {e}")
        print("Make sure Redshift is configured and accessible.")


def example_supported_intents():
    """Example: Display supported intents."""
    print("\n" + "=" * 80)
    print("Example 8: Supported Query Intents")
    print("=" * 80)
    
    nl_service = NLToSQLService()
    
    intents = nl_service.get_supported_intents()
    
    for intent_info in intents:
        print(f"\n{intent_info['intent'].upper()}")
        print(f"Description: {intent_info['description']}")
        print("Examples:")
        for example in intent_info['examples']:
            print(f"  - {example}")


def example_complex_queries():
    """Example: Complex multi-filter queries."""
    print("\n" + "=" * 80)
    print("Example 9: Complex Multi-Filter Queries")
    print("=" * 80)
    
    nl_service = NLToSQLService()
    
    complex_queries = [
        'Find rock concerts in "Madison Square Garden" in New York',
        "Show me top 10 venues by revenue in California",
        "What are the ticket sales for concerts in Chicago with over 10000 attendance?"
    ]
    
    for query in complex_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print('=' * 60)
        
        result = nl_service.translate_and_execute(query, execute=False)
        
        if result.success and result.query:
            print(f"\nIntent: {result.query.intent.value}")
            print(f"Complexity: {result.query.estimated_complexity}")
            print(f"\nExtracted Entities:")
            context = nl_service.build_query_context(query)
            for entity in context.entities:
                print(f"  - {entity.entity_type}: {entity.value}")
            
            print(f"\nGenerated SQL:")
            print(result.query.sql)


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("NATURAL LANGUAGE TO SQL QUERY TRANSLATOR - EXAMPLES")
    print("=" * 80)
    
    try:
        example_basic_translation()
        example_intent_classification()
        example_entity_extraction()
        example_query_context_building()
        example_sql_generation()
        example_sql_safety_validation()
        example_supported_intents()
        example_complex_queries()
        
        # Optional: Try with Redshift if available
        print("\n" + "=" * 80)
        print("Attempting Redshift execution examples...")
        print("=" * 80)
        example_with_redshift_execution()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
