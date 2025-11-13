#!/usr/bin/env python3
"""
Demo Test Queries Script

Provides pre-configured test queries for demonstrating platform capabilities.
Run specific scenarios or all scenarios for comprehensive testing.
"""

import json
import sys
from typing import Dict, List, Any
import requests
from datetime import datetime, timedelta

# Configuration
CHATBOT_API_URL = "http://localhost:8000"
API_GATEWAY_URL = "https://your-api-gateway-url.amazonaws.com/prod"  # Update with actual URL


class DemoQueryRunner:
    """Executes demo queries and displays results"""
    
    def __init__(self, use_local: bool = True):
        self.base_url = CHATBOT_API_URL if use_local else API_GATEWAY_URL
        self.session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def print_section(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def print_result(self, query: str, response: Dict[str, Any]):
        """Print formatted query result"""
        print(f"Query: {query}")
        print(f"\nResponse:")
        print("-" * 80)
        
        if "response" in response:
            print(response["response"])
        
        if "data" in response and response["data"]:
            print(f"\nData:")
            print(json.dumps(response["data"], indent=2))
        
        if "visualization" in response:
            print(f"\nVisualization: {response['visualization']['type']}")
        
        print("-" * 80 + "\n")
    
    def send_chat_message(self, message: str) -> Dict[str, Any]:
        """Send message to chatbot API"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "message": message,
                    "session_id": self.session_id
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "response": f"Error: {str(e)}"}
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            response = requests.get(
                f"{self.base_url}/history",
                params={"session_id": self.session_id},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return [{"error": str(e)}]
    
    # Scenario 1: Artist Lookup
    def scenario_artist_lookup(self):
        """Demonstrate artist information retrieval"""
        self.print_section("Scenario 1: Artist Lookup and Information")
        
        queries = [
            "Tell me about The Rolling Stones",
            "What venues have they performed at?",
            "How popular are they compared to other rock artists?"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # Scenario 2: Venue Search
    def scenario_venue_search(self):
        """Demonstrate venue recommendations"""
        self.print_section("Scenario 2: Venue Search and Recommendations")
        
        queries = [
            "What are the best venues in New York for rock concerts?",
            "Which venue would be best for a mid-sized indie band?",
            "Show me upcoming concerts at Madison Square Garden"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # Scenario 3: Concert Recommendations
    def scenario_concert_recommendations(self):
        """Demonstrate personalized recommendations"""
        self.print_section("Scenario 3: Concert Recommendations")
        
        queries = [
            "I like rock and alternative music. What concerts should I attend?",
            "What about something in the next month?",
            "Which of these concerts are likely to sell out?"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # Scenario 4: Data Analysis
    def scenario_data_analysis(self):
        """Demonstrate data analysis and visualization"""
        self.print_section("Scenario 4: Data Analysis and Visualization")
        
        queries = [
            "Show me the trend of concert attendance over the past year",
            "Which genres are most popular?",
            "Compare ticket sales between venues in California"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # Scenario 5: External Data
    def scenario_external_data(self):
        """Demonstrate external data enrichment"""
        self.print_section("Scenario 5: External Data Enrichment")
        
        queries = [
            "Get me the latest information about Coldplay from Spotify",
            "Are there any upcoming Coldplay concerts on Ticketmaster?",
            "How does their current popularity compare to our historical data?"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # Scenario 6: Conversation Memory
    def scenario_conversation_memory(self):
        """Demonstrate conversation memory"""
        self.print_section("Scenario 6: Conversation Memory")
        
        queries = [
            "What was the first artist I asked about?",
            "What were my music preferences?",
            "Summarize our conversation so far"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # ML Predictions
    def scenario_ml_predictions(self):
        """Demonstrate ML model predictions"""
        self.print_section("ML Model Predictions")
        
        queries = [
            "Predict ticket sales for Arctic Monkeys at Brooklyn Steel next month",
            "What's the popularity ranking of venues in Los Angeles?",
            "Recommend similar artists to The Strokes"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # Quick Demo
    def quick_demo(self):
        """Run abbreviated demo with key highlights"""
        self.print_section("Quick Demo - Key Features")
        
        queries = [
            "Tell me about The Rolling Stones",
            "What are the best venues in New York?",
            "I like rock music. What concerts should I attend?",
            "Show me concert attendance trends",
            "Predict ticket sales for upcoming concerts"
        ]
        
        for query in queries:
            response = self.send_chat_message(query)
            self.print_result(query, response)
            input("Press Enter to continue...")
    
    # Full Demo
    def full_demo(self):
        """Run complete demo with all scenarios"""
        self.print_section("Full Demo - All Scenarios")
        
        print("Running all demo scenarios...")
        print("Press Ctrl+C at any time to stop\n")
        
        try:
            self.scenario_artist_lookup()
            self.scenario_venue_search()
            self.scenario_concert_recommendations()
            self.scenario_data_analysis()
            self.scenario_external_data()
            self.scenario_conversation_memory()
            self.scenario_ml_predictions()
            
            self.print_section("Demo Complete!")
            print("All scenarios executed successfully.")
            
            # Show conversation history
            print("\nConversation History:")
            history = self.get_conversation_history()
            print(json.dumps(history, indent=2))
            
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
            sys.exit(0)


def print_menu():
    """Print demo menu"""
    print("\n" + "=" * 80)
    print("  Concert Data Platform - Demo Test Queries")
    print("=" * 80)
    print("\nAvailable Scenarios:")
    print("  1. Artist Lookup and Information")
    print("  2. Venue Search and Recommendations")
    print("  3. Concert Recommendations")
    print("  4. Data Analysis and Visualization")
    print("  5. External Data Enrichment")
    print("  6. Conversation Memory")
    print("  7. ML Model Predictions")
    print("  8. Quick Demo (5 key queries)")
    print("  9. Full Demo (all scenarios)")
    print("  0. Exit")
    print("=" * 80)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run demo test queries")
    parser.add_argument(
        "--scenario",
        type=int,
        choices=range(0, 10),
        help="Run specific scenario (1-9) or 0 to exit"
    )
    parser.add_argument(
        "--api-gateway",
        action="store_true",
        help="Use API Gateway URL instead of local chatbot"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Custom API URL"
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = DemoQueryRunner(use_local=not args.api_gateway)
    
    if args.url:
        runner.base_url = args.url
    
    # Check if chatbot is accessible
    try:
        response = requests.get(f"{runner.base_url}/health", timeout=5)
        response.raise_for_status()
        print(f"✓ Connected to chatbot at {runner.base_url}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to chatbot at {runner.base_url}")
        print(f"  Error: {e}")
        print("\nPlease ensure the chatbot service is running:")
        print("  python src/api/chatbot_api.py")
        sys.exit(1)
    
    # Run specific scenario if provided
    if args.scenario is not None:
        scenario_map = {
            1: runner.scenario_artist_lookup,
            2: runner.scenario_venue_search,
            3: runner.scenario_concert_recommendations,
            4: runner.scenario_data_analysis,
            5: runner.scenario_external_data,
            6: runner.scenario_conversation_memory,
            7: runner.scenario_ml_predictions,
            8: runner.quick_demo,
            9: runner.full_demo,
            0: lambda: sys.exit(0)
        }
        
        scenario_map[args.scenario]()
        return
    
    # Interactive menu
    while True:
        print_menu()
        
        try:
            choice = input("\nSelect scenario (0-9): ").strip()
            
            if not choice.isdigit():
                print("Invalid input. Please enter a number 0-9.")
                continue
            
            choice = int(choice)
            
            if choice == 0:
                print("Exiting demo.")
                break
            elif choice == 1:
                runner.scenario_artist_lookup()
            elif choice == 2:
                runner.scenario_venue_search()
            elif choice == 3:
                runner.scenario_concert_recommendations()
            elif choice == 4:
                runner.scenario_data_analysis()
            elif choice == 5:
                runner.scenario_external_data()
            elif choice == 6:
                runner.scenario_conversation_memory()
            elif choice == 7:
                runner.scenario_ml_predictions()
            elif choice == 8:
                runner.quick_demo()
            elif choice == 9:
                runner.full_demo()
            else:
                print("Invalid choice. Please select 0-9.")
        
        except KeyboardInterrupt:
            print("\n\nExiting demo.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Continuing to menu...")


if __name__ == "__main__":
    main()
