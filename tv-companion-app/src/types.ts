export interface Theme {
  name: string;
  description: string;
}

export interface Symbol {
  name: string;
  description: string;
  significance: string;
}

export interface Question {
  text: string;
  context?: string;
}

export interface SeasonPreview {
  seasonNumber: number;
  themes: Theme[];
  symbols: Symbol[];
  questions: Question[];
}

export interface ThemeExploration {
  theme: string;
  examples: string[];
  analysis: string;
}

export interface StoryArc {
  name: string;
  description: string;
  status: 'ongoing' | 'resolved' | 'introduced';
}

export interface EpisodeRecap {
  episodeNumber: number;
  episodeTitle: string;
  themeExplorations: ThemeExploration[];
  symbolsUsed: Symbol[];
  storyArcs: StoryArc[];
  keyMoments: string[];
}

export interface SeasonRecap {
  seasonNumber: number;
  overallThemes: Theme[];
  symbolsUsed: Symbol[];
  completedArcs: StoryArc[];
  ongoingArcs: StoryArc[];
  openQuestions: Question[];
  nextSeasonSetup?: string;
}

export interface Episode {
  number: number;
  title: string;
  recap: EpisodeRecap;
}

export interface Season {
  number: number;
  title?: string;
  preview: SeasonPreview;
  episodes: Episode[];
  recap: SeasonRecap;
}

export interface Show {
  id: string;
  title: string;
  description: string;
  seasons: Season[];
}

export interface UserProgress {
  showId: string;
  currentSeason: number;
  currentEpisode: number;
}
