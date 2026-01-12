import { useState } from 'react';
import type { Show, Season, Episode, Theme, Symbol, Question } from '../types';

interface ShowFormProps {
  onSave: (show: Show) => void;
  onCancel: () => void;
  existingShow?: Show;
}

export function ShowForm({ onSave, onCancel, existingShow }: ShowFormProps) {
  const [step, setStep] = useState(1);
  const [showData, setShowData] = useState<Partial<Show>>(
    existingShow || {
      id: '',
      title: '',
      description: '',
      seasons: []
    }
  );
  const [currentSeason, setCurrentSeason] = useState<Partial<Season>>({
    number: 1,
    title: '',
    preview: {
      seasonNumber: 1,
      themes: [],
      symbols: [],
      questions: []
    },
    episodes: [],
    recap: {
      seasonNumber: 1,
      overallThemes: [],
      symbolsUsed: [],
      completedArcs: [],
      ongoingArcs: [],
      openQuestions: []
    }
  });
  const [currentEpisode, setCurrentEpisode] = useState<Partial<Episode>>({
    number: 1,
    title: '',
    recap: {
      episodeNumber: 1,
      episodeTitle: '',
      themeExplorations: [],
      symbolsUsed: [],
      storyArcs: [],
      keyMoments: []
    }
  });

  const addTheme = (target: 'preview' | 'episode' | 'season') => {
    const theme: Theme = { name: '', description: '' };
    if (target === 'preview') {
      setCurrentSeason({
        ...currentSeason,
        preview: {
          ...currentSeason.preview!,
          themes: [...(currentSeason.preview?.themes || []), theme]
        }
      });
    }
  };

  const addSymbol = (target: 'preview' | 'episode' | 'season') => {
    const symbol: Symbol = { name: '', description: '', significance: '' };
    if (target === 'preview') {
      setCurrentSeason({
        ...currentSeason,
        preview: {
          ...currentSeason.preview!,
          symbols: [...(currentSeason.preview?.symbols || []), symbol]
        }
      });
    }
  };

  const addQuestion = (target: 'preview' | 'season') => {
    const question: Question = { text: '' };
    if (target === 'preview') {
      setCurrentSeason({
        ...currentSeason,
        preview: {
          ...currentSeason.preview!,
          questions: [...(currentSeason.preview?.questions || []), question]
        }
      });
    }
  };

  const saveEpisode = () => {
    if (currentEpisode.title && currentEpisode.number) {
      const episode: Episode = {
        number: currentEpisode.number,
        title: currentEpisode.title,
        recap: currentEpisode.recap!
      };
      setCurrentSeason({
        ...currentSeason,
        episodes: [...(currentSeason.episodes || []), episode]
      });
      setCurrentEpisode({
        number: (currentEpisode.number || 0) + 1,
        title: '',
        recap: {
          episodeNumber: (currentEpisode.number || 0) + 1,
          episodeTitle: '',
          themeExplorations: [],
          symbolsUsed: [],
          storyArcs: [],
          keyMoments: []
        }
      });
    }
  };

  const saveSeason = () => {
    if (currentSeason.number && currentSeason.preview && currentSeason.recap) {
      const season: Season = {
        number: currentSeason.number,
        title: currentSeason.title,
        preview: currentSeason.preview,
        episodes: currentSeason.episodes || [],
        recap: currentSeason.recap
      };
      setShowData({
        ...showData,
        seasons: [...(showData.seasons || []), season]
      });
      setCurrentSeason({
        number: (currentSeason.number || 0) + 1,
        title: '',
        preview: {
          seasonNumber: (currentSeason.number || 0) + 1,
          themes: [],
          symbols: [],
          questions: []
        },
        episodes: [],
        recap: {
          seasonNumber: (currentSeason.number || 0) + 1,
          overallThemes: [],
          symbolsUsed: [],
          completedArcs: [],
          ongoingArcs: [],
          openQuestions: []
        }
      });
      setStep(1);
    }
  };

  const saveShow = () => {
    if (showData.id && showData.title && showData.description) {
      const show: Show = {
        id: showData.id,
        title: showData.title,
        description: showData.description,
        seasons: showData.seasons || []
      };
      onSave(show);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
        {existingShow ? 'Edit Show' : 'Add New Show'}
      </h2>

      {step === 1 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Show Information</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Show ID (unique identifier)
            </label>
            <input
              type="text"
              value={showData.id}
              onChange={(e) => setShowData({ ...showData, id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              placeholder="e.g., breaking-bad"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Show Title
            </label>
            <input
              type="text"
              value={showData.title}
              onChange={(e) => setShowData({ ...showData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              placeholder="e.g., Breaking Bad"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={showData.description}
              onChange={(e) => setShowData({ ...showData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              rows={3}
              placeholder="Brief description of the show"
            />
          </div>

          <div className="flex gap-2 pt-4">
            <button
              onClick={() => setStep(2)}
              disabled={!showData.id || !showData.title || !showData.description}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              Next: Add Seasons
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Season {currentSeason.number} - Preview
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Season Title (optional)
            </label>
            <input
              type="text"
              value={currentSeason.title || ''}
              onChange={(e) => setCurrentSeason({ ...currentSeason, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              placeholder="e.g., Season 1"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Themes</label>
              <button
                onClick={() => addTheme('preview')}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                + Add Theme
              </button>
            </div>
            {currentSeason.preview?.themes.map((theme, idx) => (
              <div key={idx} className="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <input
                  type="text"
                  value={theme.name}
                  onChange={(e) => {
                    const updated = [...(currentSeason.preview?.themes || [])];
                    updated[idx] = { ...updated[idx], name: e.target.value };
                    setCurrentSeason({
                      ...currentSeason,
                      preview: { ...currentSeason.preview!, themes: updated }
                    });
                  }}
                  className="w-full px-2 py-1 mb-2 border rounded dark:bg-gray-600 dark:text-white"
                  placeholder="Theme name"
                />
                <textarea
                  value={theme.description}
                  onChange={(e) => {
                    const updated = [...(currentSeason.preview?.themes || [])];
                    updated[idx] = { ...updated[idx], description: e.target.value };
                    setCurrentSeason({
                      ...currentSeason,
                      preview: { ...currentSeason.preview!, themes: updated }
                    });
                  }}
                  className="w-full px-2 py-1 border rounded dark:bg-gray-600 dark:text-white"
                  rows={2}
                  placeholder="Theme description"
                />
              </div>
            ))}
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Symbols</label>
              <button
                onClick={() => addSymbol('preview')}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                + Add Symbol
              </button>
            </div>
            {currentSeason.preview?.symbols.map((symbol, idx) => (
              <div key={idx} className="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <input
                  type="text"
                  value={symbol.name}
                  onChange={(e) => {
                    const updated = [...(currentSeason.preview?.symbols || [])];
                    updated[idx] = { ...updated[idx], name: e.target.value };
                    setCurrentSeason({
                      ...currentSeason,
                      preview: { ...currentSeason.preview!, symbols: updated }
                    });
                  }}
                  className="w-full px-2 py-1 mb-2 border rounded dark:bg-gray-600 dark:text-white"
                  placeholder="Symbol name"
                />
                <textarea
                  value={symbol.description}
                  onChange={(e) => {
                    const updated = [...(currentSeason.preview?.symbols || [])];
                    updated[idx] = { ...updated[idx], description: e.target.value };
                    setCurrentSeason({
                      ...currentSeason,
                      preview: { ...currentSeason.preview!, symbols: updated }
                    });
                  }}
                  className="w-full px-2 py-1 mb-2 border rounded dark:bg-gray-600 dark:text-white"
                  rows={2}
                  placeholder="Symbol description"
                />
                <input
                  type="text"
                  value={symbol.significance}
                  onChange={(e) => {
                    const updated = [...(currentSeason.preview?.symbols || [])];
                    updated[idx] = { ...updated[idx], significance: e.target.value };
                    setCurrentSeason({
                      ...currentSeason,
                      preview: { ...currentSeason.preview!, symbols: updated }
                    });
                  }}
                  className="w-full px-2 py-1 border rounded dark:bg-gray-600 dark:text-white"
                  placeholder="Significance"
                />
              </div>
            ))}
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Questions to Consider</label>
              <button
                onClick={() => addQuestion('preview')}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                + Add Question
              </button>
            </div>
            {currentSeason.preview?.questions.map((question, idx) => (
              <div key={idx} className="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <textarea
                  value={question.text}
                  onChange={(e) => {
                    const updated = [...(currentSeason.preview?.questions || [])];
                    updated[idx] = { ...updated[idx], text: e.target.value };
                    setCurrentSeason({
                      ...currentSeason,
                      preview: { ...currentSeason.preview!, questions: updated }
                    });
                  }}
                  className="w-full px-2 py-1 mb-2 border rounded dark:bg-gray-600 dark:text-white"
                  rows={2}
                  placeholder="Question text"
                />
                <input
                  type="text"
                  value={question.context || ''}
                  onChange={(e) => {
                    const updated = [...(currentSeason.preview?.questions || [])];
                    updated[idx] = { ...updated[idx], context: e.target.value };
                    setCurrentSeason({
                      ...currentSeason,
                      preview: { ...currentSeason.preview!, questions: updated }
                    });
                  }}
                  className="w-full px-2 py-1 border rounded dark:bg-gray-600 dark:text-white"
                  placeholder="Context (optional)"
                />
              </div>
            ))}
          </div>

          <div className="flex gap-2 pt-4">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Back
            </button>
            <button
              onClick={() => setStep(3)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Next: Add Episodes
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Add Episodes ({currentSeason.episodes?.length || 0} added)
          </h3>

          <p className="text-sm text-gray-600 dark:text-gray-400">
            Note: For simplicity, you can skip detailed episode recaps and add them later.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Episode {currentEpisode.number} Title
            </label>
            <input
              type="text"
              value={currentEpisode.title}
              onChange={(e) => setCurrentEpisode({ ...currentEpisode, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              placeholder="Episode title"
            />
          </div>

          <button
            onClick={saveEpisode}
            disabled={!currentEpisode.title}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            Add Episode {currentEpisode.number}
          </button>

          <div className="flex gap-2 pt-4 border-t">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Back
            </button>
            <button
              onClick={() => setStep(4)}
              disabled={(currentSeason.episodes?.length || 0) === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              Next: Season Recap
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Season {currentSeason.number} Recap
          </h3>

          <p className="text-sm text-gray-600 dark:text-gray-400">
            Complete season recap (similar to preview but with full analysis)
          </p>

          <div className="flex gap-2 pt-4">
            <button
              onClick={() => setStep(3)}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Back
            </button>
            <button
              onClick={() => {
                saveSeason();
                if (confirm('Add another season?')) {
                  setStep(2);
                } else {
                  setStep(5);
                }
              }}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Save Season
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {step === 5 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Review and Save
          </h3>

          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded">
            <p className="font-semibold">{showData.title}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{showData.description}</p>
            <p className="text-sm mt-2">Seasons: {showData.seasons?.length || 0}</p>
          </div>

          <div className="flex gap-2 pt-4">
            <button
              onClick={saveShow}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Save Show
            </button>
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Add More Seasons
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
