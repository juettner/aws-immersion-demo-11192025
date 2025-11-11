# Product Overview

Concert Data Platform - AWS Data Readiness & AI Demo

A comprehensive data platform demonstrating AWS data services, machine learning capabilities, and AI-powered insights for the concert and live entertainment industry.

## Core Purpose

Showcase modern data engineering and AI/ML practices by ingesting, processing, and analyzing concert data from multiple sources, providing predictive analytics, recommendations, and an AI-powered chatbot interface.

## Key Features

- **Data Ingestion**: Multi-source data collection (Spotify, Ticketmaster APIs, file uploads in CSV/JSON/XML)
- **Real-time Streaming**: Kinesis-based event processing with Lambda
- **Data Warehouse**: Redshift with optimized schema and stored procedures
- **ETL Pipeline**: AWS Glue jobs with fuzzy matching deduplication
- **Data Governance**: Lake Formation for access control and audit logging
- **ML Models**: Venue popularity ranking, ticket sales prediction, recommendation engine
- **AI Chatbot**: Amazon Bedrock AgentCore with conversation memory, code interpreter, and browser tools
- **Web Interface**: React-based dashboard and chat interface

## Domain Models

- **Artist**: ID, name, genre, popularity score (Spotify integration)
- **Venue**: ID, name, location, capacity, type (Ticketmaster integration)
- **Concert**: ID, artist, venue, event date, pricing, attendance, revenue
- **Ticket Sale**: ID, concert, customer, quantity, price, timestamp

## Current Development Phase

AI/ML enhancement and chatbot development. Core data ingestion, ETL, and ML models are complete.
