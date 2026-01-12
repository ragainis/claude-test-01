import type { EpisodeRecap as EpisodeRecapType } from '../types';

interface EpisodeRecapProps {
  recap: EpisodeRecapType;
}

export function EpisodeRecap({ recap }: EpisodeRecapProps) {
  return (
    <div className="max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">
          Episode {recap.episodeNumber}: {recap.episodeTitle}
        </h2>
        <p className="text-sm text-amber-600 dark:text-amber-400 font-medium">
          Analysis and Recap
        </p>
      </div>

      <div className="space-y-8">
        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-blue-500 pb-2">
            Theme Exploration
          </h3>
          <div className="space-y-6">
            {recap.themeExplorations.map((exploration, index) => (
              <div key={index} className="bg-blue-50 dark:bg-blue-900/20 p-5 rounded-lg">
                <h4 className="font-bold text-xl text-blue-900 dark:text-blue-300 mb-3">
                  {exploration.theme}
                </h4>
                <div className="mb-3">
                  <p className="font-semibold text-sm text-gray-700 dark:text-gray-300 mb-2">
                    Examples:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                    {exploration.examples.map((example, idx) => (
                      <li key={idx} className="ml-4">{example}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-blue-100 dark:bg-blue-900/40 p-3 rounded">
                  <p className="font-semibold text-sm text-blue-800 dark:text-blue-300 mb-1">
                    Analysis:
                  </p>
                  <p className="text-gray-800 dark:text-gray-200">{exploration.analysis}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-purple-500 pb-2">
            Symbols Used
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
          <div className="space-y-3">
            {recap.storyArcs.map((arc, index) => (
              <div key={index} className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-bold text-green-900 dark:text-green-300 mb-1">
                    {arc.name}
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 text-sm">{arc.description}</p>
                </div>
                <span className={`ml-4 px-3 py-1 rounded-full text-xs font-semibold ${
                  arc.status === 'introduced' ? 'bg-yellow-200 text-yellow-800' :
                  arc.status === 'ongoing' ? 'bg-blue-200 text-blue-800' :
                  'bg-green-200 text-green-800'
                }`}>
                  {arc.status}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200 border-b-2 border-orange-500 pb-2">
            Key Moments
          </h3>
          <ul className="space-y-2">
            {recap.keyMoments.map((moment, index) => (
              <li key={index} className="bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg text-gray-700 dark:text-gray-300 flex items-start">
                <span className="text-orange-500 font-bold mr-3">{index + 1}.</span>
                <span>{moment}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
