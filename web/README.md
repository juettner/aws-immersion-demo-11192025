# Concert Data Platform - Web Interface

React-based web interface for the Concert Data Platform, providing AI-powered analytics and chatbot capabilities.

## Features

- **Analytics Dashboard**: Visualize concert data, venue popularity, and ticket sales predictions
- **AI Chatbot**: Natural language interface for querying concert data and getting recommendations
- **Responsive Design**: Mobile-friendly interface with modern UI components

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **TanStack Query** for data fetching and caching
- **Axios** for API requests
- **Recharts** for data visualization
- **ESLint & Prettier** for code quality

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start development server
npm run dev

# The app will be available at http://localhost:5173
```

### Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality

```bash
# Run ESLint
npm run lint

# Format code with Prettier
npm run format

# Check formatting
npm run format:check
```

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   ├── Modal.tsx
│   ├── Loading.tsx
│   ├── ErrorBoundary.tsx
│   └── Layout.tsx
├── pages/           # Page components
│   ├── HomePage.tsx
│   ├── DashboardPage.tsx
│   └── ChatbotPage.tsx
├── services/        # API service layer
│   └── api.ts
├── hooks/           # Custom React hooks
│   └── useApi.ts
├── types/           # TypeScript type definitions
│   └── index.ts
├── config/          # Configuration
│   └── env.ts
├── context/         # React context providers
│   └── ThemeContext.tsx
├── styles/          # Global styles and theme
│   ├── global.css
│   └── theme.ts
├── App.tsx          # Main app component
└── main.tsx         # Entry point
```

## Environment Variables

Create a `.env.development` file:

```env
VITE_API_BASE_URL=http://localhost:3000/api
VITE_CHATBOT_API_URL=http://localhost:3000/api/chat
VITE_ANALYTICS_API_URL=http://localhost:3000/api/analytics
```

## Available Components

### UI Components

- **Button**: Customizable button with variants (primary, secondary, outline, danger)
- **Card**: Container component with header, body, and footer sections
- **Input**: Form input with label, error, and helper text support
- **Modal**: Overlay modal dialog with customizable size
- **Loading**: Loading spinner with optional text
- **ErrorBoundary**: Error boundary for graceful error handling
- **Layout**: Main layout with header, navigation, and footer

### Hooks

- **useApi**: Custom hooks for API queries and mutations with TanStack Query

## Next Steps

1. Implement chatbot interface components (Task 6.2)
2. Build analytics dashboard visualizations (Task 6.3)
3. Set up API Gateway and backend integration (Task 6.4)
