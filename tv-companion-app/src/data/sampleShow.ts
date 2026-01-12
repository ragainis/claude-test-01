import type { Show } from '../types';

export const sampleShow: Show = {
  id: 'breaking-bad',
  title: 'Breaking Bad',
  description: 'A high school chemistry teacher turned methamphetamine manufacturer',
  seasons: [
    {
      number: 1,
      title: 'Season 1',
      preview: {
        seasonNumber: 1,
        themes: [
          {
            name: 'Transformation',
            description: 'The journey from ordinary to extraordinary, and the costs of change'
          },
          {
            name: 'Morality and Choice',
            description: 'Exploring the gray areas between right and wrong'
          },
          {
            name: 'Family and Responsibility',
            description: 'The lengths one goes to for family and the consequences'
          }
        ],
        symbols: [
          {
            name: 'Color Green',
            description: 'Associated with money, greed, and transformation',
            significance: 'Watch for green objects and clothing as markers of change'
          },
          {
            name: 'The RV',
            description: 'A mobile laboratory and symbol of dual life',
            significance: 'Represents the secret world and freedom from society'
          },
          {
            name: 'Chemistry',
            description: 'Both literal science and metaphor for change',
            significance: 'Chemical reactions mirror character transformations'
          }
        ],
        questions: [
          {
            text: 'How do ordinary people justify extraordinary actions?',
            context: 'Consider the motivations behind character decisions'
          },
          {
            text: 'What does family really mean to each character?',
            context: 'Pay attention to family dynamics and obligations'
          },
          {
            text: 'Can someone change fundamentally, or do they reveal who they always were?',
            context: 'Watch for signs of transformation vs. revelation'
          }
        ]
      },
      episodes: [
        {
          number: 1,
          title: 'Pilot',
          recap: {
            episodeNumber: 1,
            episodeTitle: 'Pilot',
            themeExplorations: [
              {
                theme: 'Transformation',
                examples: [
                  'Walter\'s diagnosis becomes a catalyst for change',
                  'The contrast between classroom Walter and criminal Walter',
                  'Jesse\'s surprise at his former teacher\'s involvement'
                ],
                analysis: 'The episode establishes transformation as central - a dying man choosing to truly live, even if through crime'
              },
              {
                theme: 'Morality and Choice',
                examples: [
                  'Walter\'s decision to manufacture methamphetamine',
                  'The choice to spare or kill Krazy-8 and Emilio',
                  'Lying to family vs. providing for them'
                ],
                analysis: 'Every choice is presented with consequences, establishing the moral complexity of the series'
              }
            ],
            symbolsUsed: [
              {
                name: 'The RV',
                description: 'Introduced as the mobile lab',
                significance: 'First glimpse of Walter\'s secret life - mobility represents freedom from his mundane existence'
              },
              {
                name: 'Underwear',
                description: 'Walter in his underwear in the desert',
                significance: 'Vulnerability and stripping away of social facade'
              }
            ],
            storyArcs: [
              {
                name: 'Walter\'s Cancer Diagnosis',
                description: 'Terminal lung cancer as the inciting incident',
                status: 'introduced'
              },
              {
                name: 'Partnership with Jesse',
                description: 'Unlikely alliance between teacher and former student',
                status: 'introduced'
              },
              {
                name: 'Hank\'s Investigation',
                description: 'DEA agent unknowingly pursuing his brother-in-law',
                status: 'introduced'
              }
            ],
            keyMoments: [
              'Walter receives his cancer diagnosis',
              'First encounter with Jesse Pinkman',
              'The RV encounter with Krazy-8 and Emilio',
              'Creating the first batch of methamphetamine',
              'The cliffhanger with sirens approaching'
            ]
          }
        },
        {
          number: 2,
          title: 'Cat\'s in the Bag...',
          recap: {
            episodeNumber: 2,
            episodeTitle: 'Cat\'s in the Bag...',
            themeExplorations: [
              {
                theme: 'Morality and Choice',
                examples: [
                  'Walter\'s list of pros and cons for killing',
                  'The attempt to rationalize murder',
                  'Jesse\'s inability to follow through'
                ],
                analysis: 'Shows the psychological cost of crossing moral lines - even "justified" killing weighs heavily'
              },
              {
                theme: 'Consequences',
                examples: [
                  'The aftermath of the pilot\'s violence',
                  'Dealing with the bodies',
                  'Jesse\'s bathtub disaster'
                ],
                analysis: 'Actions have visceral, messy consequences that can\'t be neatly resolved'
              }
            ],
            symbolsUsed: [
              {
                name: 'The Basement',
                description: 'Jesse\'s basement where Krazy-8 is held',
                significance: 'Dark, confined space representing moral descent and imprisonment by choices'
              },
              {
                name: 'Chemistry',
                description: 'The hydrofluoric acid scene',
                significance: 'Science can\'t solve moral problems - even perfect chemistry fails when applied wrongly'
              }
            ],
            storyArcs: [
              {
                name: 'Partnership with Jesse',
                description: 'Learning to work together despite different approaches',
                status: 'ongoing'
              },
              {
                name: 'Disposing of Evidence',
                description: 'The challenge of covering their tracks',
                status: 'ongoing'
              },
              {
                name: 'Double Life',
                description: 'Balancing family life with criminal activity',
                status: 'ongoing'
              }
            ],
            keyMoments: [
              'Walter creates his kill list',
              'Jesse attempts to dissolve a body in the wrong container',
              'The bathtub crashes through the ceiling',
              'Krazy-8 remains alive in the basement',
              'Walter lies to Skyler about his whereabouts'
            ]
          }
        }
      ],
      recap: {
        seasonNumber: 1,
        overallThemes: [
          {
            name: 'Transformation',
            description: 'Walter White\'s evolution from mild-mannered teacher to criminal, revealing questions about identity and change'
          },
          {
            name: 'Family vs. Self',
            description: 'The tension between providing for family and personal agency, examining what we owe to others'
          },
          {
            name: 'Pride and Masculinity',
            description: 'How pride drives decisions and the concept of providing as masculine identity'
          }
        ],
        symbolsUsed: [
          {
            name: 'Color Symbolism',
            description: 'Green for money/greed, beige for mundane life, yellow for meth/danger',
            significance: 'Visual language that tracks character journeys and themes'
          },
          {
            name: 'The RV',
            description: 'Mobile lab representing freedom and criminality',
            significance: 'The space between two worlds - not quite home, not quite the streets'
          },
          {
            name: 'Chemistry Equipment',
            description: 'Beakers, formulas, reactions',
            significance: 'Control and precision contrasted with chaos of criminal world'
          }
        ],
        completedArcs: [
          {
            name: 'First Competitors',
            description: 'Dealing with Krazy-8 and Emilio',
            status: 'resolved'
          },
          {
            name: 'Initial Production',
            description: 'Successfully creating high-quality product',
            status: 'resolved'
          }
        ],
        ongoingArcs: [
          {
            name: 'Walter\'s Cancer Treatment',
            description: 'Undergoing treatment while hiding the source of money',
            status: 'ongoing'
          },
          {
            name: 'Partnership with Jesse',
            description: 'Developing working relationship and loyalty',
            status: 'ongoing'
          },
          {
            name: 'Hank\'s Investigation',
            description: 'DEA closing in on the new player in town',
            status: 'ongoing'
          },
          {
            name: 'Marriage Strain',
            description: 'Skyler\'s growing suspicion about Walter\'s behavior',
            status: 'ongoing'
          }
        ],
        openQuestions: [
          {
            text: 'How far will Walter go to protect his new enterprise?',
            context: 'His escalating actions suggest no clear limit'
          },
          {
            text: 'Will Hank discover the truth about Walter?',
            context: 'The dramatic irony of their relationship intensifies'
          },
          {
            text: 'Can Walter maintain his double life?',
            context: 'The lies are piling up and becoming harder to sustain'
          },
          {
            text: 'What is Walter really doing this for - family or himself?',
            context: 'His motivations seem increasingly complex'
          }
        ],
        nextSeasonSetup: 'The foundation is laid for expansion and escalation. Walter has proven he can produce superior product, but distribution and competition will bring new challenges. The collision course between his two worlds accelerates.'
      }
    }
  ]
};
