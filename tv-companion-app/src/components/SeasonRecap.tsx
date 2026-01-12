import type { SeasonRecap as SeasonRecapType } from '../types';

interface SeasonRecapProps {
  recap: SeasonRecapType;
}

export function SeasonRecap({ recap }: SeasonRecapProps) {
  return (
    <div className="max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">
          Season {recap.seasonNumber} Complete Recap
        </h2>
        <p className="text-sm text-amber-600 dark:text-amber-400 font-medium">
          Comprehensive analysis with no future spoilers
        </p>
      </div>

      <div className="space-y-8">
        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-blue-500 pb-2">
            Overall Themes
          </h3>
          <div className="space-y-4">
            {recap.overallThemes.map((theme, index) => (
              <div key={index} className="bg-blue-50 dark:bg-blue-900/20 p-5 rounded-lg">
                <h4 className="font-bold text-xl text-blue-900 dark:text-blue-300 mb-2">
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
            {recap.symbolsUsed.map((symbol, index) => (
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
            Story Arcs
          </h3>

          <div className="mb-6">
            <h4 className="font-semibold text-lg text-gray-700 dark:text-gray-300 mb-3">
              Completed Arcs
            </h4>
            <div className="space-y-3">
              {recap.completedArcs.map((arc, index) => (
                <div key={index} className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg border-l-4 border-green-500">
                  <h5 className="font-bold text-green-900 dark:text-green-300 mb-1">
                    {arc.name}
                  </h5>
                  <p className="text-gray-700 dark:text-gray-300 text-sm">{arc.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-lg text-gray-700 dark:text-gray-300 mb-3">
              Ongoing Arcs
            </h4>
            <div className="space-y-3">
              {recap.ongoingArcs.map((arc, index) => (
                <div key={index} className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border-l-4 border-blue-500">
                  <h5 className="font-bold text-blue-900 dark:text-blue-300 mb-1">
                    {arc.name}
                  </h5>
                  <p className="text-gray-700 dark:text-gray-300 text-sm">{arc.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-amber-500 pb-2">
            Open Questions for Next Season
          </h3>
          <div className="space-y-3">
            {recap.openQuestions.map((question, index) => (
              <div key={index} className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg">
                <p className="font-semibold text-amber-900 dark:text-amber-300 mb-1">
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

        {recap.nextSeasonSetup && (
          <section>
            <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-indigo-500 pb-2">
              Looking Ahead
            </h3>
            <div className="bg-indigo-50 dark:bg-indigo-900/20 p-5 rounded-lg">
              <p className="text-gray-700 dark:text-gray-300">{recap.nextSeasonSetup}</p>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
