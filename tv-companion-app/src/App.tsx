import { useState, useEffect } from 'react';
import type { Show, UserProgress } from './types';
import { sampleShow } from './data/sampleShow';
import { SeasonPreview } from './components/SeasonPreview';
import { EpisodeRecap } from './components/EpisodeRecap';
import { SeasonRecap } from './components/SeasonRecap';
import { ShowForm } from './components/ShowForm';

type ViewType = 'season-preview' | 'episode-recap' | 'season-recap' | 'home' | 'manage-shows' | 'add-show';

function App() {
  const [shows, setShows] = useState<Show[]>(() => {
    const saved = localStorage.getItem('tvCompanionShows');
    if (saved) {
      return JSON.parse(saved);
    }
    return [sampleShow];
  });
  const [currentShowId, setCurrentShowId] = useState<string>(() => {
    const saved = localStorage.getItem('currentShowId');
    return saved || sampleShow.id;
  });
  const show = shows.find(s => s.id === currentShowId) || shows[0];

  const [progress, setProgress] = useState<UserProgress>(() => {
    const saved = localStorage.getItem(`userProgress-${currentShowId}`);
    return saved ? JSON.parse(saved) : {
      showId: currentShowId,
      currentSeason: 0,
      currentEpisode: 0
    };
  });
  const [viewType, setViewType] = useState<ViewType>('home');
  const [selectedSeason, setSelectedSeason] = useState<number>(1);
  const [selectedEpisode, setSelectedEpisode] = useState<number>(1);

  useEffect(() => {
    localStorage.setItem('tvCompanionShows', JSON.stringify(shows));
  }, [shows]);

  useEffect(() => {
    localStorage.setItem('currentShowId', currentShowId);
  }, [currentShowId]);

  useEffect(() => {
    localStorage.setItem(`userProgress-${currentShowId}`, JSON.stringify(progress));
  }, [progress, currentShowId]);

  useEffect(() => {
    const saved = localStorage.getItem(`userProgress-${currentShowId}`);
    setProgress(saved ? JSON.parse(saved) : {
      showId: currentShowId,
      currentSeason: 0,
      currentEpisode: 0
    });
  }, [currentShowId]);

  const saveShow = (newShow: Show) => {
    const existing = shows.find(s => s.id === newShow.id);
    if (existing) {
      setShows(shows.map(s => s.id === newShow.id ? newShow : s));
    } else {
      setShows([...shows, newShow]);
    }
    setCurrentShowId(newShow.id);
    setViewType('home');
  };

  const deleteShow = (showId: string) => {
    if (shows.length === 1) {
      alert('Cannot delete the last show');
      return;
    }
    if (confirm('Are you sure you want to delete this show?')) {
      const newShows = shows.filter(s => s.id !== showId);
      setShows(newShows);
      if (currentShowId === showId) {
        setCurrentShowId(newShows[0].id);
      }
      localStorage.removeItem(`userProgress-${showId}`);
    }
  };

  const markEpisodeWatched = (seasonNum: number, episodeNum: number) => {
    if (seasonNum > progress.currentSeason ||
        (seasonNum === progress.currentSeason && episodeNum > progress.currentEpisode)) {
      setProgress({
        ...progress,
        currentSeason: seasonNum,
        currentEpisode: episodeNum
      });
    }
  };

  const canViewSeasonPreview = (seasonNum: number) => {
    return seasonNum <= progress.currentSeason + 1;
  };

  const canViewEpisodeRecap = (seasonNum: number, episodeNum: number) => {
    if (seasonNum < progress.currentSeason) return true;
    if (seasonNum === progress.currentSeason && episodeNum <= progress.currentEpisode) return true;
    return false;
  };

  const canViewSeasonRecap = (seasonNum: number) => {
    const season = show.seasons.find(s => s.number === seasonNum);
    if (!season) return false;
    return canViewEpisodeRecap(seasonNum, season.episodes.length);
  };

  const renderView = () => {
    if (viewType === 'add-show') {
      return <ShowForm onSave={saveShow} onCancel={() => setViewType('home')} />;
    }

    if (viewType === 'manage-shows') {
      return (
        <div className="max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Manage Shows</h2>

          <div className="space-y-4">
            {shows.map(s => (
              <div key={s.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white">{s.title}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{s.description}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {s.seasons.length} season{s.seasons.length !== 1 ? 's' : ''}
                  </p>
                </div>
                <div className="flex gap-2">
                  {s.id !== currentShowId && (
                    <button
                      onClick={() => {
                        setCurrentShowId(s.id);
                        setViewType('home');
                      }}
                      className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                    >
                      Switch
                    </button>
                  )}
                  {s.id === currentShowId && (
                    <span className="px-3 py-1 bg-green-600 text-white rounded text-sm">
                      Current
                    </span>
                  )}
                  <button
                    onClick={() => deleteShow(s.id)}
                    className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => setViewType('add-show')}
            className="mt-6 w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
          >
            + Add New Show
          </button>
        </div>
      );
    }

    const season = show.seasons.find(s => s.number === selectedSeason);
    if (!season) return null;

    switch (viewType) {
      case 'season-preview':
        if (!canViewSeasonPreview(selectedSeason)) {
          return (
            <div className="max-w-4xl mx-auto p-6 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <h3 className="text-xl font-bold text-red-900 dark:text-red-300 mb-2">
                Spoiler Protection Active
              </h3>
              <p className="text-red-700 dark:text-red-400">
                You need to watch more episodes to unlock this season preview.
              </p>
            </div>
          );
        }
        return <SeasonPreview preview={season.preview} />;

      case 'episode-recap':
        if (!canViewEpisodeRecap(selectedSeason, selectedEpisode)) {
          return (
            <div className="max-w-4xl mx-auto p-6 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <h3 className="text-xl font-bold text-red-900 dark:text-red-300 mb-2">
                Spoiler Protection Active
              </h3>
              <p className="text-red-700 dark:text-red-400">
                Watch this episode first to unlock the recap and analysis.
              </p>
            </div>
          );
        }
        const episode = season.episodes.find(e => e.number === selectedEpisode);
        return episode ? <EpisodeRecap recap={episode.recap} /> : null;

      case 'season-recap':
        if (!canViewSeasonRecap(selectedSeason)) {
          return (
            <div className="max-w-4xl mx-auto p-6 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <h3 className="text-xl font-bold text-red-900 dark:text-red-300 mb-2">
                Spoiler Protection Active
              </h3>
              <p className="text-red-700 dark:text-red-400">
                Complete the entire season to unlock the full season recap.
              </p>
            </div>
          );
        }
        return <SeasonRecap recap={season.recap} />;

      default:
        return (
          <div className="max-w-4xl mx-auto p-6">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-8 rounded-lg shadow-lg mb-8">
              <h2 className="text-4xl font-bold mb-4">{show.title}</h2>
              <p className="text-lg mb-4">{show.description}</p>
              <div className="bg-white/20 p-4 rounded">
                <p className="font-semibold">Your Progress:</p>
                <p>Season {progress.currentSeason || 'Not started'}, Episode {progress.currentEpisode || 'Not started'}</p>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h3 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
                How It Works
              </h3>
              <div className="space-y-4 text-gray-700 dark:text-gray-300">
                <div className="border-l-4 border-blue-500 pl-4">
                  <h4 className="font-bold text-lg mb-2">Before Each Season</h4>
                  <p>View the Season Preview to understand themes, symbols, and questions to consider while watching.</p>
                </div>
                <div className="border-l-4 border-green-500 pl-4">
                  <h4 className="font-bold text-lg mb-2">After Each Episode</h4>
                  <p>Read the Episode Recap to explore how themes were developed, symbols used, and story arcs progressed.</p>
                </div>
                <div className="border-l-4 border-purple-500 pl-4">
                  <h4 className="font-bold text-lg mb-2">After Each Season</h4>
                  <p>Get the complete Season Recap with full story arc analysis and open questions for upcoming seasons.</p>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <h1
                className="text-2xl font-bold text-gray-900 dark:text-white cursor-pointer"
                onClick={() => setViewType('home')}
              >
                TV Companion
              </h1>
              <div className="flex items-center gap-2">
                <select
                  value={currentShowId}
                  onChange={(e) => {
                    setCurrentShowId(e.target.value);
                    setViewType('home');
                  }}
                  className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white text-sm"
                >
                  {shows.map(s => (
                    <option key={s.id} value={s.id}>{s.title}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewType('manage-shows')}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Manage Shows
              </button>
              <button
                onClick={() => setViewType('add-show')}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                + Add Show
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {(viewType === 'manage-shows' || viewType === 'add-show') ? (
          <div>
            {renderView()}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            <aside className="lg:col-span-1">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sticky top-8">
                <h3 className="font-bold text-lg mb-4 text-gray-900 dark:text-white">Navigation</h3>

              <div className="space-y-4">
                {show.seasons.map(season => (
                  <div key={season.number} className="border-b border-gray-200 dark:border-gray-700 pb-4">
                    <h4 className="font-semibold mb-2 text-gray-800 dark:text-gray-200">
                      Season {season.number}
                    </h4>

                    <button
                      onClick={() => {
                        setSelectedSeason(season.number);
                        setViewType('season-preview');
                      }}
                      className={`w-full text-left px-3 py-2 rounded mb-2 text-sm ${
                        canViewSeasonPreview(season.number)
                          ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-800'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                      }`}
                      disabled={!canViewSeasonPreview(season.number)}
                    >
                      📖 Preview
                    </button>

                    <div className="space-y-1 mb-2">
                      {season.episodes.map(episode => (
                        <div key={episode.number} className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setSelectedSeason(season.number);
                              setSelectedEpisode(episode.number);
                              setViewType('episode-recap');
                            }}
                            className={`flex-1 text-left px-3 py-1 rounded text-sm ${
                              canViewEpisodeRecap(season.number, episode.number)
                                ? 'bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-800'
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                            }`}
                            disabled={!canViewEpisodeRecap(season.number, episode.number)}
                          >
                            E{episode.number}
                          </button>
                          <button
                            onClick={() => markEpisodeWatched(season.number, episode.number)}
                            className="px-2 py-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 rounded text-xs"
                            title="Mark as watched"
                          >
                            ✓
                          </button>
                        </div>
                      ))}
                    </div>

                    <button
                      onClick={() => {
                        setSelectedSeason(season.number);
                        setViewType('season-recap');
                      }}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${
                        canViewSeasonRecap(season.number)
                          ? 'bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-800'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                      }`}
                      disabled={!canViewSeasonRecap(season.number)}
                    >
                      📊 Season Recap
                    </button>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => {
                    if (confirm('Reset all progress?')) {
                      setProgress({
                        showId: show.id,
                        currentSeason: 0,
                        currentEpisode: 0
                      });
                      setViewType('home');
                    }
                  }}
                  className="w-full px-3 py-2 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-200 rounded text-sm hover:bg-red-200 dark:hover:bg-red-800"
                >
                  Reset Progress
                </button>
              </div>
            </div>
          </aside>

            <main className="lg:col-span-3">
              {renderView()}
            </main>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
