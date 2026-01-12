import type { SeasonPreview as SeasonPreviewType } from '../types';

interface SeasonPreviewProps {
  preview: SeasonPreviewType;
}

export function SeasonPreview({ preview }: SeasonPreviewProps) {
  return (
    <div className="max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">
          Season {preview.seasonNumber} Preview
        </h2>
        <p className="text-sm text-amber-600 dark:text-amber-400 font-medium">
          No spoilers - Guidance for viewing ahead
        </p>
      </div>

      <div className="space-y-8">
        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-blue-500 pb-2">
            Themes to Watch For
          </h3>
          <div className="space-y-4">
            {preview.themes.map((theme, index) => (
              <div key={index} className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <h4 className="font-bold text-lg text-blue-900 dark:text-blue-300 mb-2">
                  {theme.name}
                </h4>
                <p className="text-gray-700 dark:text-gray-300">{theme.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-purple-500 pb-2">
            Symbols and Motifs
          </h3>
          <div className="space-y-4">
            {preview.symbols.map((symbol, index) => (
              <div key={index} className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <h4 className="font-bold text-lg text-purple-900 dark:text-purple-300 mb-2">
                  {symbol.name}
                </h4>
                <p className="text-gray-700 dark:text-gray-300 mb-2">{symbol.description}</p>
                <p className="text-sm text-purple-700 dark:text-purple-400 italic">
                  {symbol.significance}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-green-500 pb-2">
            Questions to Consider
          </h3>
          <div className="space-y-3">
            {preview.questions.map((question, index) => (
              <div key={index} className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <p className="font-semibold text-green-900 dark:text-green-300 mb-1">
                  {question.text}
                </p>
                {question.context && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                    {question.context}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
