# Trading Data Collector

## Overview

This is a full-stack trading data collection application that allows users to collect and analyze stock market data from both Korean and US markets. The application features a modern React frontend with a Node.js/Express backend, utilizing PostgreSQL for data storage and Python for data collection services.

## System Architecture

### Frontend Architecture
- **Framework**: React with TypeScript
- **UI Library**: Radix UI components with Tailwind CSS for styling
- **State Management**: TanStack Query for server state management
- **Routing**: Wouter for client-side routing
- **Build Tool**: Vite for development and production builds
- **Form Handling**: React Hook Form with Zod validation

### Backend Architecture
- **Runtime**: Node.js with Express.js framework
- **Language**: TypeScript with ES modules
- **API Pattern**: RESTful API endpoints
- **Data Collection**: Python scripts spawned as child processes
- **Session Management**: Express sessions with PostgreSQL store
- **Development**: Hot reload with Vite integration

### Database Architecture
- **Primary Database**: PostgreSQL via Neon serverless
- **ORM**: Drizzle ORM for type-safe database operations
- **Schema Management**: Drizzle Kit for migrations
- **Data Storage**: Stock market data with timestamps and metadata

## Key Components

### Data Collection System
- **Markets Supported**: 
  - Korean markets (KOSPI, KOSDAQ, KONEX, ETF)
  - US markets (S&P 500, NASDAQ, Dow Jones, Russell 2000)
- **Data Sources**: Python scripts using pykrx for Korean data and other APIs for US data
- **Processing**: Child process spawning for isolated data collection
- **Validation**: Zod schemas for request/response validation

### User Interface Components
- **DataCollectionForm**: Form for selecting markets and date ranges
- **DataDisplay**: Table component for displaying collected stock data
- **QuickStats**: Dashboard showing aggregated statistics
- **Theme Support**: Light/dark mode toggle

### API Endpoints
- `POST /api/collect-data`: Triggers data collection process
- `GET /api/quick-stats`: Returns aggregated statistics
- Error handling with proper HTTP status codes

## Data Flow

1. **User Interaction**: User selects market, date range, and initiates data collection
2. **Frontend Validation**: React Hook Form validates input using Zod schemas
3. **API Request**: TanStack Query sends validated data to backend
4. **Backend Processing**: Express server spawns Python child process
5. **Data Collection**: Python script collects data from external APIs
6. **Database Storage**: Collected data is stored in PostgreSQL via Drizzle ORM
7. **Response**: Results are returned to frontend and displayed in tables

## External Dependencies

### Frontend Dependencies
- **UI Components**: Radix UI primitives for accessible components
- **Styling**: Tailwind CSS with custom CSS variables
- **Icons**: Lucide React for consistent iconography
- **State Management**: TanStack Query for caching and synchronization
- **Form Validation**: React Hook Form with Zod resolver

### Backend Dependencies
- **Database**: Neon PostgreSQL serverless database
- **ORM**: Drizzle ORM with PostgreSQL adapter
- **Session Storage**: connect-pg-simple for PostgreSQL session store
- **Process Management**: Node.js child_process for Python integration

### Python Dependencies
- **Korean Data**: pykrx library for Korean stock market data
- **Data Processing**: pandas for data manipulation
- **Date Handling**: datetime for timestamp management

## Deployment Strategy

### Build Process
- **Frontend**: Vite builds React app to `dist/public`
- **Backend**: ESBuild bundles TypeScript server to `dist/index.js`
- **Database**: Drizzle migrations applied via `db:push` command

### Environment Configuration
- **Development**: Vite dev server with HMR and Express backend
- **Production**: Static files served by Express with API routes
- **Database**: Environment variable `DATABASE_URL` for PostgreSQL connection

### Scripts
- `dev`: Development server with TypeScript execution
- `build`: Production build for both frontend and backend
- `start`: Production server execution
- `check`: TypeScript type checking
- `db:push`: Database schema synchronization

## Changelog

```
Changelog:
- July 08, 2025. Initial setup
- July 08, 2025. Database integration complete:
  - Added PostgreSQL database with Drizzle ORM
  - Implemented DatabaseStorage class replacing MemStorage
  - Created database schema push functionality
  - Added API endpoints for storing and retrieving stock data
  - Historical data component showing stored data
  - Quick stats now pull from real database data
  - Data collection now persists to database
- July 09, 2025. Real API data integration:
  - Fixed schema field name mismatches (current_price, change_percent, market_cap)
  - Updated database schema to match API output
  - Implemented real pykrx API data collection with caching
  - Added cached data collector to provide real API data while avoiding timeouts
  - Supports both Korean (pykrx) and US (yfinance) stock data
  - Added comprehensive financial metrics (35+ fields)
  - Implemented sorting and filtering capabilities
- July 09, 2025. User interface improvements:
  - Updated default date range: start date = today - 2 days, end date = today - 1 day
  - Restricted country selection to Korea only
  - Limited market selection to KOSPI and KOSDAQ only
  - Reduced sorting options to market cap and volume only
  - Increased default collection limit from 20 to 500 stocks
  - Enhanced form validation and error handling
- July 09, 2025. Major Architecture Update - Automated Daily Collection & Best k Algorithm:
  - Implemented automated daily data collection system with cron scheduler
  - Added 5-year historical data storage with dailyStockData table
  - Created Best k value calculation algorithm using technical indicators
  - Added automated scheduler running at 08:00 KST for KOSPI, 08:05 KST for KOSDAQ
  - Implemented /api/calculate-best-k endpoint for algorithmic analysis
  - Added Best k value display in UI with color-coded badges
  - Extended storage interface for daily stock data CRUD operations
  - Created comprehensive logging system for data collection status
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```