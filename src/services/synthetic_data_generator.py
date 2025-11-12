"""
Synthetic concert data generator for demo and testing purposes.

Generates realistic concert data including artists, venues, concerts, and ticket sales
with configurable parameters and reproducible randomization.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.models.artist import Artist
from src.models.venue import Venue
from src.models.concert import Concert
from src.models.ticket_sale import TicketSale


@dataclass
class GeneratorConfig:
    """Configuration for synthetic data generation."""
    num_artists: int = 1000
    num_venues: int = 500
    num_concerts: int = 10000
    num_ticket_sales: int = 50000
    seed: Optional[int] = None
    start_date_years_ago: int = 5
    end_date_years_ahead: int = 1


class SyntheticDataGenerator:
    """Generate realistic synthetic concert data for demo purposes."""
    
    # Genre pools for realistic artist generation
    GENRES = [
        'rock', 'pop', 'hip hop', 'electronic', 'jazz', 'blues', 'country',
        'metal', 'punk', 'indie', 'alternative', 'folk', 'r&b', 'soul',
        'reggae', 'classical', 'latin', 'funk', 'disco', 'grunge'
    ]
    
    # Venue types with typical capacity ranges
    VENUE_TYPES = {
        'club': (100, 500),
        'theater': (500, 2000),
        'hall': (1000, 5000),
        'arena': (5000, 20000),
        'amphitheater': (3000, 15000),
        'stadium': (20000, 80000)
    }
    
    # US cities with states for venue generation
    CITIES = [
        ('New York', 'NY'), ('Los Angeles', 'CA'), ('Chicago', 'IL'),
        ('Houston', 'TX'), ('Phoenix', 'AZ'), ('Philadelphia', 'PA'),
        ('San Antonio', 'TX'), ('San Diego', 'CA'), ('Dallas', 'TX'),
        ('San Jose', 'CA'), ('Austin', 'TX'), ('Jacksonville', 'FL'),
        ('Fort Worth', 'TX'), ('Columbus', 'OH'), ('Charlotte', 'NC'),
        ('San Francisco', 'CA'), ('Indianapolis', 'IN'), ('Seattle', 'WA'),
        ('Denver', 'CO'), ('Washington', 'DC'), ('Boston', 'MA'),
        ('Nashville', 'TN'), ('Detroit', 'MI'), ('Portland', 'OR'),
        ('Las Vegas', 'NV'), ('Memphis', 'TN'), ('Louisville', 'KY'),
        ('Baltimore', 'MD'), ('Milwaukee', 'WI'), ('Albuquerque', 'NM'),
        ('Tucson', 'AZ'), ('Fresno', 'CA'), ('Sacramento', 'CA'),
        ('Kansas City', 'MO'), ('Mesa', 'AZ'), ('Atlanta', 'GA'),
        ('Omaha', 'NE'), ('Colorado Springs', 'CO'), ('Raleigh', 'NC'),
        ('Miami', 'FL'), ('Cleveland', 'OH'), ('Tulsa', 'OK'),
        ('Oakland', 'CA'), ('Minneapolis', 'MN'), ('Wichita', 'KS'),
        ('New Orleans', 'LA'), ('Tampa', 'FL'), ('Honolulu', 'HI'),
        ('Anaheim', 'CA'), ('St. Louis', 'MO')
    ]
    
    # Ticket tiers with typical price multipliers
    TICKET_TIERS = {
        'general': 1.0,
        'premium': 1.5,
        'vip': 2.5,
        'early_bird': 0.8,
        'standing': 0.9,
        'seated': 1.2
    }
    
    # Payment methods
    PAYMENT_METHODS = [
        'credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay'
    ]
    
    # Artist name components for generation
    ARTIST_PREFIXES = [
        'The', 'Electric', 'Cosmic', 'Midnight', 'Golden', 'Silver',
        'Crystal', 'Neon', 'Velvet', 'Iron', 'Steel', 'Diamond'
    ]
    
    ARTIST_NOUNS = [
        'Wolves', 'Eagles', 'Tigers', 'Dragons', 'Phoenix', 'Ravens',
        'Shadows', 'Echoes', 'Dreams', 'Flames', 'Thunder', 'Lightning',
        'Stars', 'Moons', 'Suns', 'Waves', 'Storms', 'Winds', 'Rivers',
        'Mountains', 'Valleys', 'Oceans', 'Skies', 'Horizons', 'Legends'
    ]
    
    VENUE_PREFIXES = [
        'The', 'Grand', 'Royal', 'Imperial', 'Majestic', 'Historic',
        'Classic', 'Modern', 'Downtown', 'Uptown', 'Central', 'Metro'
    ]
    
    VENUE_SUFFIXES = [
        'Arena', 'Theater', 'Hall', 'Auditorium', 'Center', 'Pavilion',
        'Stadium', 'Amphitheater', 'Club', 'Venue', 'House', 'Palace'
    ]
    
    def __init__(self, config: Optional[GeneratorConfig] = None):
        """Initialize generator with configuration."""
        self.config = config or GeneratorConfig()
        if self.config.seed is not None:
            random.seed(self.config.seed)
        
        self.artists: List[Artist] = []
        self.venues: List[Venue] = []
        self.concerts: List[Concert] = []
        self.ticket_sales: List[TicketSale] = []
    
    def generate_all(self) -> Dict[str, List]:
        """Generate all synthetic data."""
        print(f"Generating synthetic concert data with seed={self.config.seed}")
        print(f"  Artists: {self.config.num_artists}")
        print(f"  Venues: {self.config.num_venues}")
        print(f"  Concerts: {self.config.num_concerts}")
        print(f"  Ticket Sales: {self.config.num_ticket_sales}")
        
        self.artists = self._generate_artists()
        print(f"✓ Generated {len(self.artists)} artists")
        
        self.venues = self._generate_venues()
        print(f"✓ Generated {len(self.venues)} venues")
        
        self.concerts = self._generate_concerts()
        print(f"✓ Generated {len(self.concerts)} concerts")
        
        self.ticket_sales = self._generate_ticket_sales()
        print(f"✓ Generated {len(self.ticket_sales)} ticket sales")
        
        return {
            'artists': self.artists,
            'venues': self.venues,
            'concerts': self.concerts,
            'ticket_sales': self.ticket_sales
        }
    
    def _generate_artists(self) -> List[Artist]:
        """Generate realistic artist data."""
        artists = []
        now = datetime.utcnow()
        
        for i in range(self.config.num_artists):
            # Generate artist name
            if random.random() < 0.6:  # 60% chance of band name with prefix
                name = f"{random.choice(self.ARTIST_PREFIXES)} {random.choice(self.ARTIST_NOUNS)}"
            else:  # 40% chance of simple name
                name = random.choice(self.ARTIST_NOUNS)
            
            # Add uniqueness to avoid duplicates
            name = f"{name} {chr(65 + (i % 26))}" if i >= len(self.ARTIST_NOUNS) * 2 else name
            
            # Select 1-3 genres
            num_genres = random.randint(1, 3)
            genres = random.sample(self.GENRES, num_genres)
            
            # Generate popularity score (skewed towards mid-range)
            popularity = random.betavariate(2, 2) * 100
            
            # Generate formation date (between 1960 and 2020)
            years_ago = random.randint(5, 65)
            formation_date = (now - timedelta(days=years_ago * 365)).date()
            
            # Generate band members (1-6 members)
            num_members = random.randint(1, 6)
            members = [f"Member {j+1}" for j in range(num_members)]
            
            artist = Artist(
                artist_id=f"art_{i+1:06d}",
                name=name,
                genre=genres,
                popularity_score=round(popularity, 2),
                formation_date=formation_date,
                members=members,
                spotify_id=f"spotify_{i+1:06d}" if random.random() < 0.7 else None
            )
            artists.append(artist)
        
        return artists

    def _generate_venues(self) -> List[Venue]:
        """Generate realistic venue data."""
        venues = []
        
        for i in range(self.config.num_venues):
            # Select venue type and capacity range
            venue_type = random.choice(list(self.VENUE_TYPES.keys()))
            min_cap, max_cap = self.VENUE_TYPES[venue_type]
            capacity = random.randint(min_cap, max_cap)
            
            # Select city and state
            city, state = random.choice(self.CITIES)
            
            # Generate venue name
            if random.random() < 0.7:  # 70% chance of structured name
                prefix = random.choice(self.VENUE_PREFIXES)
                suffix = random.choice(self.VENUE_SUFFIXES)
                name = f"{prefix} {city} {suffix}"
            else:  # 30% chance of simple name
                name = f"{city} {random.choice(self.VENUE_SUFFIXES)}"
            
            # Add uniqueness
            if i >= len(self.CITIES) * 3:
                name = f"{name} {i % 10}"
            
            # Generate address
            street_num = random.randint(1, 9999)
            street_names = ['Main St', 'Broadway', 'Park Ave', 'Center St', 'Market St']
            address = f"{street_num} {random.choice(street_names)}"
            
            # Generate postal code
            postal_code = f"{random.randint(10000, 99999)}"
            
            venue = Venue(
                venue_id=f"ven_{i+1:06d}",
                name=name,
                city=city,
                state=state,
                country="USA",
                capacity=capacity,
                venue_type=venue_type,
                address=address,
                postal_code=postal_code
            )
            venues.append(venue)
        
        return venues
    
    def _generate_concerts(self) -> List[Concert]:
        """Generate realistic concert event data."""
        if not self.artists or not self.venues:
            raise ValueError("Must generate artists and venues before concerts")
        
        concerts = []
        now = datetime.utcnow()
        
        # Calculate date range
        start_date = now - timedelta(days=self.config.start_date_years_ago * 365)
        end_date = now + timedelta(days=self.config.end_date_years_ahead * 365)
        date_range_days = (end_date - start_date).days
        
        for i in range(self.config.num_concerts):
            # Select random artist and venue
            artist = random.choice(self.artists)
            venue = random.choice(self.venues)
            
            # Generate event date (weighted towards recent/upcoming)
            # Use beta distribution to favor dates closer to present
            date_offset = int(random.betavariate(2, 2) * date_range_days)
            event_date = start_date + timedelta(days=date_offset)
            
            # Add random time (evening concerts typically 7-9 PM)
            hour = random.randint(18, 21)
            minute = random.choice([0, 15, 30, 45])
            event_date = event_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Generate ticket prices based on artist popularity and venue size
            base_price = 30 + (artist.popularity_score * 0.5) + (venue.capacity / 1000)
            base_price = max(20, min(base_price, 300))  # Clamp between $20-$300
            
            ticket_prices = {}
            for tier, multiplier in self.TICKET_TIERS.items():
                if random.random() < 0.7:  # 70% chance of having this tier
                    price = round(base_price * multiplier, 2)
                    ticket_prices[tier] = price
            
            # Ensure at least one tier exists
            if not ticket_prices:
                ticket_prices['general'] = round(base_price, 2)
            
            # Determine status based on date
            if event_date < now:
                status = 'completed' if random.random() < 0.95 else 'cancelled'
            else:
                status = 'scheduled' if random.random() < 0.98 else 'cancelled'
            
            # Generate attendance and revenue for completed concerts
            total_attendance = None
            revenue = None
            if status == 'completed':
                # Attendance based on artist popularity and venue capacity
                attendance_rate = 0.5 + (artist.popularity_score / 200)
                attendance_rate = min(attendance_rate, 0.98)  # Max 98% capacity
                total_attendance = int(venue.capacity * attendance_rate)
                
                # Estimate revenue (simplified)
                avg_ticket_price = sum(ticket_prices.values()) / len(ticket_prices)
                revenue = round(total_attendance * avg_ticket_price, 2)
            
            concert = Concert(
                concert_id=f"con_{i+1:06d}",
                artist_id=artist.artist_id,
                venue_id=venue.venue_id,
                event_date=event_date,
                ticket_prices=ticket_prices,
                total_attendance=total_attendance,
                revenue=revenue,
                status=status
            )
            concerts.append(concert)
        
        return concerts
    
    def _generate_ticket_sales(self) -> List[TicketSale]:
        """Generate realistic ticket sale transactions."""
        if not self.concerts:
            raise ValueError("Must generate concerts before ticket sales")
        
        ticket_sales = []
        
        # Only generate sales for scheduled or completed concerts
        eligible_concerts = [c for c in self.concerts if c.status in ['scheduled', 'completed']]
        
        if not eligible_concerts:
            print("Warning: No eligible concerts for ticket sales")
            return ticket_sales
        
        sales_per_concert = self.config.num_ticket_sales // len(eligible_concerts)
        extra_sales = self.config.num_ticket_sales % len(eligible_concerts)
        
        sale_counter = 0
        
        for concert_idx, concert in enumerate(eligible_concerts):
            # Determine number of sales for this concert
            num_sales = sales_per_concert
            if concert_idx < extra_sales:
                num_sales += 1
            
            # Get available ticket tiers for this concert
            available_tiers = list(concert.ticket_prices.keys())
            if not available_tiers:
                continue
            
            for _ in range(num_sales):
                # Select ticket tier (weighted by price - cheaper tickets sell more)
                tier_weights = [1.0 / concert.ticket_prices[tier] for tier in available_tiers]
                tier = random.choices(available_tiers, weights=tier_weights)[0]
                
                unit_price = concert.ticket_prices[tier]
                
                # Generate quantity (most people buy 1-4 tickets)
                quantity_weights = [0.4, 0.3, 0.2, 0.1]  # 1, 2, 3, 4 tickets
                quantity = random.choices([1, 2, 3, 4], weights=quantity_weights)[0]
                
                total_price = round(quantity * unit_price, 2)
                
                # Generate purchase timestamp
                # Sales happen before the concert date
                if concert.status == 'completed':
                    # Sales were between 90 days before and concert date
                    days_before = random.randint(1, 90)
                    purchase_time = concert.event_date - timedelta(days=days_before)
                else:  # scheduled
                    # Sales are between now and 90 days before concert
                    days_before = random.randint(1, 90)
                    purchase_time = concert.event_date - timedelta(days=days_before)
                    # Ensure not in future
                    if purchase_time > datetime.utcnow():
                        purchase_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                
                # Add random time
                hour = random.randint(8, 22)
                minute = random.randint(0, 59)
                purchase_time = purchase_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Select payment method
                payment_method = random.choice(self.PAYMENT_METHODS)
                
                # Generate customer ID
                customer_id = f"cust_{random.randint(1, 100000):06d}"
                
                sale = TicketSale(
                    sale_id=f"sale_{sale_counter+1:06d}",
                    concert_id=concert.concert_id,
                    customer_id=customer_id,
                    ticket_tier=tier,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    purchase_timestamp=purchase_time,
                    payment_method=payment_method
                )
                ticket_sales.append(sale)
                sale_counter += 1
        
        return ticket_sales

    def validate_data_quality(self) -> Dict[str, any]:
        """Validate data quality and referential integrity."""
        issues = []
        warnings = []
        
        print("\nValidating data quality...")
        
        # Check that data has been generated
        if not self.artists:
            issues.append("No artists generated")
        if not self.venues:
            issues.append("No venues generated")
        if not self.concerts:
            issues.append("No concerts generated")
        if not self.ticket_sales:
            warnings.append("No ticket sales generated")
        
        # Validate referential integrity
        artist_ids = {a.artist_id for a in self.artists}
        venue_ids = {v.venue_id for v in self.venues}
        concert_ids = {c.concert_id for c in self.concerts}
        
        # Check concert references
        for concert in self.concerts:
            if concert.artist_id not in artist_ids:
                issues.append(f"Concert {concert.concert_id} references non-existent artist {concert.artist_id}")
            if concert.venue_id not in venue_ids:
                issues.append(f"Concert {concert.concert_id} references non-existent venue {concert.venue_id}")
        
        # Check ticket sale references
        for sale in self.ticket_sales:
            if sale.concert_id not in concert_ids:
                issues.append(f"Ticket sale {sale.sale_id} references non-existent concert {sale.concert_id}")
        
        # Validate value ranges
        for artist in self.artists:
            if not (0 <= artist.popularity_score <= 100):
                issues.append(f"Artist {artist.artist_id} has invalid popularity score: {artist.popularity_score}")
        
        for venue in self.venues:
            if not (100 <= venue.capacity <= 200000):
                warnings.append(f"Venue {venue.venue_id} has unusual capacity: {venue.capacity}")
        
        for concert in self.concerts:
            if concert.total_attendance and concert.total_attendance > 500000:
                warnings.append(f"Concert {concert.concert_id} has unusually high attendance: {concert.total_attendance}")
            
            for tier, price in concert.ticket_prices.items():
                if not (0 < price <= 10000):
                    warnings.append(f"Concert {concert.concert_id} has unusual price for {tier}: ${price}")
        
        for sale in self.ticket_sales:
            if not (1 <= sale.quantity <= 20):
                warnings.append(f"Ticket sale {sale.sale_id} has unusual quantity: {sale.quantity}")
            
            expected_total = sale.quantity * sale.unit_price
            if abs(sale.total_price - expected_total) > 0.01:
                issues.append(f"Ticket sale {sale.sale_id} has incorrect total price calculation")
        
        # Check data volume
        if len(self.artists) < 1000:
            warnings.append(f"Only {len(self.artists)} artists generated (recommended: 1000+)")
        if len(self.venues) < 500:
            warnings.append(f"Only {len(self.venues)} venues generated (recommended: 500+)")
        if len(self.concerts) < 10000:
            warnings.append(f"Only {len(self.concerts)} concerts generated (recommended: 10000+)")
        if len(self.ticket_sales) < 50000:
            warnings.append(f"Only {len(self.ticket_sales)} ticket sales generated (recommended: 50000+)")
        
        # Print results
        if issues:
            print(f"✗ Found {len(issues)} data quality issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"  - {issue}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")
        else:
            print("✓ No data quality issues found")
        
        if warnings:
            print(f"⚠ Found {len(warnings)} warnings:")
            for warning in warnings[:10]:  # Show first 10
                print(f"  - {warning}")
            if len(warnings) > 10:
                print(f"  ... and {len(warnings) - 10} more")
        else:
            print("✓ No warnings")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'stats': {
                'artists': len(self.artists),
                'venues': len(self.venues),
                'concerts': len(self.concerts),
                'ticket_sales': len(self.ticket_sales)
            }
        }
    
    def export_to_csv(self, output_dir: str = 'generated_data') -> Dict[str, str]:
        """Export generated data to CSV files."""
        import csv
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        files = {}
        
        # Export artists
        artists_file = os.path.join(output_dir, 'artists.csv')
        with open(artists_file, 'w', newline='', encoding='utf-8') as f:
            if self.artists:
                writer = csv.DictWriter(f, fieldnames=[
                    'artist_id', 'name', 'genre', 'popularity_score', 
                    'formation_date', 'members', 'spotify_id', 'created_at', 'updated_at'
                ])
                writer.writeheader()
                for artist in self.artists:
                    row = artist.model_dump()
                    row['genre'] = '|'.join(row['genre'])
                    row['members'] = '|'.join(row['members'])
                    row['formation_date'] = row['formation_date'].isoformat() if row['formation_date'] else ''
                    row['created_at'] = row['created_at'].isoformat()
                    row['updated_at'] = row['updated_at'].isoformat()
                    writer.writerow(row)
        files['artists'] = artists_file
        print(f"✓ Exported {len(self.artists)} artists to {artists_file}")
        
        # Export venues
        venues_file = os.path.join(output_dir, 'venues.csv')
        with open(venues_file, 'w', newline='', encoding='utf-8') as f:
            if self.venues:
                writer = csv.DictWriter(f, fieldnames=[
                    'venue_id', 'name', 'city', 'state', 'country', 'capacity',
                    'venue_type', 'address', 'postal_code', 'created_at', 'updated_at'
                ])
                writer.writeheader()
                for venue in self.venues:
                    row = venue.model_dump()
                    row['created_at'] = row['created_at'].isoformat()
                    row['updated_at'] = row['updated_at'].isoformat()
                    writer.writerow(row)
        files['venues'] = venues_file
        print(f"✓ Exported {len(self.venues)} venues to {venues_file}")
        
        # Export concerts
        concerts_file = os.path.join(output_dir, 'concerts.csv')
        with open(concerts_file, 'w', newline='', encoding='utf-8') as f:
            if self.concerts:
                writer = csv.DictWriter(f, fieldnames=[
                    'concert_id', 'artist_id', 'venue_id', 'event_date',
                    'ticket_prices', 'total_attendance', 'revenue', 'status',
                    'created_at', 'updated_at'
                ])
                writer.writeheader()
                for concert in self.concerts:
                    row = concert.model_dump()
                    # Convert ticket_prices dict to string
                    row['ticket_prices'] = '|'.join([f"{k}:{v}" for k, v in row['ticket_prices'].items()])
                    row['event_date'] = row['event_date'].isoformat()
                    row['created_at'] = row['created_at'].isoformat()
                    row['updated_at'] = row['updated_at'].isoformat()
                    writer.writerow(row)
        files['concerts'] = concerts_file
        print(f"✓ Exported {len(self.concerts)} concerts to {concerts_file}")
        
        # Export ticket sales
        sales_file = os.path.join(output_dir, 'ticket_sales.csv')
        with open(sales_file, 'w', newline='', encoding='utf-8') as f:
            if self.ticket_sales:
                writer = csv.DictWriter(f, fieldnames=[
                    'sale_id', 'concert_id', 'customer_id', 'ticket_tier',
                    'quantity', 'unit_price', 'total_price', 'purchase_timestamp',
                    'payment_method', 'created_at', 'updated_at'
                ])
                writer.writeheader()
                for sale in self.ticket_sales:
                    row = sale.model_dump()
                    row['purchase_timestamp'] = row['purchase_timestamp'].isoformat()
                    row['created_at'] = row['created_at'].isoformat()
                    row['updated_at'] = row['updated_at'].isoformat()
                    writer.writerow(row)
        files['ticket_sales'] = sales_file
        print(f"✓ Exported {len(self.ticket_sales)} ticket sales to {sales_file}")
        
        return files
    
    def export_to_json(self, output_dir: str = 'generated_data') -> Dict[str, str]:
        """Export generated data to JSON files."""
        import json
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        files = {}
        
        # Export artists
        artists_file = os.path.join(output_dir, 'artists.json')
        with open(artists_file, 'w', encoding='utf-8') as f:
            data = [artist.model_dump(mode='json') for artist in self.artists]
            json.dump(data, f, indent=2, default=str)
        files['artists'] = artists_file
        print(f"✓ Exported {len(self.artists)} artists to {artists_file}")
        
        # Export venues
        venues_file = os.path.join(output_dir, 'venues.json')
        with open(venues_file, 'w', encoding='utf-8') as f:
            data = [venue.model_dump(mode='json') for venue in self.venues]
            json.dump(data, f, indent=2, default=str)
        files['venues'] = venues_file
        print(f"✓ Exported {len(self.venues)} venues to {venues_file}")
        
        # Export concerts
        concerts_file = os.path.join(output_dir, 'concerts.json')
        with open(concerts_file, 'w', encoding='utf-8') as f:
            data = [concert.model_dump(mode='json') for concert in self.concerts]
            json.dump(data, f, indent=2, default=str)
        files['concerts'] = concerts_file
        print(f"✓ Exported {len(self.concerts)} concerts to {concerts_file}")
        
        # Export ticket sales
        sales_file = os.path.join(output_dir, 'ticket_sales.json')
        with open(sales_file, 'w', encoding='utf-8') as f:
            data = [sale.model_dump(mode='json') for sale in self.ticket_sales]
            json.dump(data, f, indent=2, default=str)
        files['ticket_sales'] = sales_file
        print(f"✓ Exported {len(self.ticket_sales)} ticket sales to {sales_file}")
        
        return files
    
    def upload_to_s3(self, bucket_name: str, prefix: str = 'synthetic-data') -> Dict[str, str]:
        """Upload generated data to S3 bucket."""
        import boto3
        import json
        from io import StringIO
        
        s3_client = boto3.client('s3')
        uploaded_files = {}
        
        print(f"\nUploading data to S3 bucket: {bucket_name}")
        
        # Upload artists as JSON
        artists_key = f"{prefix}/artists.json"
        artists_data = json.dumps([a.model_dump(mode='json') for a in self.artists], default=str)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=artists_key,
            Body=artists_data,
            ContentType='application/json'
        )
        uploaded_files['artists'] = f"s3://{bucket_name}/{artists_key}"
        print(f"✓ Uploaded artists to {uploaded_files['artists']}")
        
        # Upload venues as JSON
        venues_key = f"{prefix}/venues.json"
        venues_data = json.dumps([v.model_dump(mode='json') for v in self.venues], default=str)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=venues_key,
            Body=venues_data,
            ContentType='application/json'
        )
        uploaded_files['venues'] = f"s3://{bucket_name}/{venues_key}"
        print(f"✓ Uploaded venues to {uploaded_files['venues']}")
        
        # Upload concerts as JSON
        concerts_key = f"{prefix}/concerts.json"
        concerts_data = json.dumps([c.model_dump(mode='json') for c in self.concerts], default=str)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=concerts_key,
            Body=concerts_data,
            ContentType='application/json'
        )
        uploaded_files['concerts'] = f"s3://{bucket_name}/{concerts_key}"
        print(f"✓ Uploaded concerts to {uploaded_files['concerts']}")
        
        # Upload ticket sales as JSON
        sales_key = f"{prefix}/ticket_sales.json"
        sales_data = json.dumps([s.model_dump(mode='json') for s in self.ticket_sales], default=str)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=sales_key,
            Body=sales_data,
            ContentType='application/json'
        )
        uploaded_files['ticket_sales'] = f"s3://{bucket_name}/{sales_key}"
        print(f"✓ Uploaded ticket sales to {uploaded_files['ticket_sales']}")
        
        return uploaded_files
