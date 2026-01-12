# TV Show Companion App

A spoiler-free companion application for TV show viewers that provides thematic analysis, symbol tracking, and episode recaps without revealing future plot points.

## Features

### 🎬 Season Previews
Before starting a new season, view:
- **Themes to Watch For**: Key thematic elements explored in the season
- **Symbols and Motifs**: Important visual and narrative symbols to pay attention to
- **Questions to Consider**: Thought-provoking questions to enhance your viewing experience

### 📺 Episode Recaps
After watching each episode, explore:
- **Theme Exploration**: How the episode developed major themes with specific examples
- **Symbols Used**: Symbolic elements and their significance in the episode
- **Story Arcs**: Current status of ongoing storylines (introduced, ongoing, or resolved)
- **Key Moments**: Important events and scenes from the episode

### 🎭 Season Recaps
After completing a season, get:
- **Overall Themes**: Comprehensive analysis of the season's thematic elements
- **Symbols and Motifs**: Season-wide symbolic patterns
- **Story Arcs**: Summary of completed and ongoing narrative threads
- **Open Questions**: Questions to consider for upcoming seasons
- **Next Season Setup**: What to expect moving forward (spoiler-free)

## Spoiler Protection

The app includes built-in spoiler protection:
- Season previews unlock only when you're ready to start that season
- Episode recaps only appear after you've marked episodes as watched
- Season recaps unlock only after completing all episodes
- Your progress is automatically saved in browser storage

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open your browser and navigate to the local development server (typically `http://localhost:5173`)

### Build for Production

```bash
npm run build
```

## How to Use

1. **Start a New Show**: The app loads with Breaking Bad Season 1 as sample data
2. **View Season Preview**: Click on "📖 Preview" to see themes and questions before watching
3. **Watch Episodes**: Watch episodes on your preferred platform
4. **Mark Episodes Watched**: Click the "✓" button next to each episode after watching
5. **Read Recaps**: Click episode numbers to view detailed thematic analysis
6. **Complete Season**: After all episodes, view the comprehensive season recap
7. **Track Progress**: Your viewing progress is automatically saved

## Tech Stack

- **React** with TypeScript for type-safe component development
- **Vite** for fast development and building
- **Tailwind CSS** for modern, responsive styling
- **LocalStorage** for persistent user progress tracking

## Project Structure

```
src/
├── components/          # React components
│   ├── SeasonPreview.tsx
│   ├── EpisodeRecap.tsx
│   └── SeasonRecap.tsx
├── data/               # Show data
│   └── sampleShow.ts
├── types.ts            # TypeScript type definitions
└── App.tsx             # Main application component
```

## Adding New Shows

To add a new show, create a new file in `src/data/` following the structure in `sampleShow.ts`:

```typescript
import { Show } from '../types';

export const myShow: Show = {
  id: 'show-id',
  title: 'Show Title',
  description: 'Show description',
  seasons: [
    // Add season data...
  ]
};
```

Then import and use it in `App.tsx`.

## Data Model

The app uses a structured data model:
- **Show**: Contains all seasons
- **Season**: Contains preview, episodes, and recap
- **Episode**: Contains detailed recap information
- **Themes**: Conceptual elements explored
- **Symbols**: Visual/narrative motifs
- **Story Arcs**: Ongoing narrative threads

## Future Enhancements

Potential features for future development:
- Multiple show support with show selector
- User accounts with cloud sync
- Community-contributed content
- Export notes and observations
- Integration with streaming platforms
- Mobile app version
- Custom themes and color schemes

## Contributing

This is a sample project. To extend it:
1. Add more shows to the data folder
2. Create new component variants
3. Add additional analysis categories
4. Implement backend storage
5. Add social features

## License

See LICENSE file for details.

## Sample Content

The app includes sample data for Breaking Bad Season 1 to demonstrate all features. This content is for demonstration purposes and showcases the type of analysis the app provides.
