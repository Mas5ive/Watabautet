import { SummaryResult, SummarySize, User, LibraryItem, Language, LibraryEntry } from '../types';

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const mockLogin = async (username: string): Promise<User> => {
  await delay(800);
  if (username.toLowerCase() === 'error') throw new Error('User not found in the chaotic void.');
  return { username };
};

export const mockRegister = async (username: string): Promise<User> => {
  await delay(800);
  if (username.toLowerCase() === 'exists') throw new Error('This identity is already stolen.');
  return { username };
};

export const mockExtractSummary = async (url: string, size: SummarySize, language: Language): Promise<SummaryResult> => {
  await delay(2000); // Simulate processing time

  if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
    throw new Error('INVALID SOURCE DETECTED. SYSTEM REJECTS NON-VIDEO DATA.');
  }

  const isRu = language === 'RU';

  const baseContentEn = [
    "The video discusses the inevitable collapse of digital silence.",
    "Key figure Wata Bautet argues for louder, more aggressive data interpretation.",
    "Conclusion: Noise is information. Silence is a lie."
  ];

  const baseContentRu = [
    "В видео обсуждается неизбежный коллапс цифровой тишины.",
    "Ключевая фигура Вата Баутет выступает за более громкую и агрессивную интерпретацию данных.",
    "Вывод: Шум — это информация. Тишина — это ложь."
  ];

  let content: string[] = [];

  if (size === SummarySize.SHORT) {
    content = isRu
      ? ["Анализ видео подтвержден: Истина скрыта в помехах. Конец связи."]
      : ["Video analysis confirms: The truth is hidden in the static. End of line."];
  } else if (size === SummarySize.MEDIUM) {
    content = isRu ? baseContentRu : baseContentEn;
  } else {
    content = isRu
      ? [
        ...baseContentRu,
        "Детальный анализ таймкода 04:20 выявляет скрытые сообщения в фоновых артефактах.",
        "Спикер использует диалектический материализм для деконструкции внимания зрителя.",
        "Вердикт: 8/10 рейтинг энергии. Рекомендовано для киберпанков и дата-майнеров."
      ]
      : [
        ...baseContentEn,
        "Detailed analysis of timestamp 04:20 reveals hidden messages in the background artifacts.",
        "The speaker uses dialectic materialism to deconstruct the viewer's attention span.",
        "Final verdict: 8/10 energy rating. Recommended for cyber-punks and data-miners."
      ];
  }

  return {
    title: "ANALYSIS REPORT: " + url.slice(-11),
    content,
    size,
    language
  };
};

export const mockSaveToLibrary = async (summary: SummaryResult): Promise<boolean> => {
  await delay(500);
  return true;
};

// --- New Library Functions ---

const TITLES = [
  "Why The Internet Is Leaking",
  "Cyberpunk Aesthetics in 2024",
  "React vs The Void: A Framework War",
  "How to Cook Data",
  "The Silence of the LANs",
  "Digital Decay: A Documentary",
  "Speedrunning Reality",
  "CSS Grid is a Prison",
  "TypeScript: The Strict Father",
  "Mascots Taking Over The World"
];

export const mockGetLibrary = async (): Promise<LibraryItem[]> => {
  await delay(1000);

  // Generate 50 items
  return Array.from({ length: 50 }, (_, i) => {
    // Generate various combinations
    // Item 0 will have EVERYTHING (6 buttons) for testing
    const isFullSet = i === 0;

    const entries: LibraryEntry[] = [];

    // Helper to add entry
    const add = (s: SummarySize, l: Language) => {
      entries.push({
        size: s,
        language: l,
        content: l === 'EN' ? [`Mock content for ${s} (EN)`] : [`Тестовый контент для ${s} (RU)`]
      });
    };

    if (isFullSet) {
      add(SummarySize.SHORT, 'EN');
      add(SummarySize.SHORT, 'RU');
      add(SummarySize.MEDIUM, 'EN');
      add(SummarySize.MEDIUM, 'RU');
      add(SummarySize.LONG, 'EN');
      add(SummarySize.LONG, 'RU');
    } else {
      // Random assortment
      if (Math.random() > 0.3) add(SummarySize.SHORT, Math.random() > 0.5 ? 'EN' : 'RU');
      if (Math.random() > 0.5) add(SummarySize.MEDIUM, 'EN');
      if (Math.random() > 0.8) add(SummarySize.MEDIUM, 'RU');
      if (Math.random() > 0.6) add(SummarySize.LONG, 'EN');
    }

    return {
      id: `lib-${i}`,
      videoId: `v-${1000 + i}`,
      title: `${TITLES[i % TITLES.length]} #${i + 1}`,
      entries
    };
  });
};

export const mockDeleteSummary = async (id: string): Promise<boolean> => {
  await delay(600);
  return true;
};