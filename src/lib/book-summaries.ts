/**
 * Synopsis officiels des 13 tomes de Renegade Immortel.
 * Sources : adaptations des résumés disponibles sur le Xian Ni Fandom Wiki,
 * Wuxiaworld, et NovelFrance, basés sur le titre et l'arc narratif
 * de chaque tome (plages de chapitres 1–2088).
 */

export interface BookSummary {
  book: number;
  title: string;
  titleFr: string;
  rangeStart: number;
  rangeEnd: number;
  summary: string;
}

export const BOOK_SUMMARIES: BookSummary[] = [
  {
    book: 1,
    title: 'The Mediocre Youth',
    titleFr: 'Le Jeune Homme Médiocre',
    rangeStart: 1,
    rangeEnd: 64,
    summary: "Dans un village reculé du Pays de Zhao, un jeune garçon au talent médiocre nommé Tie Zhu — dont le vrai nom est Wang Lin — voit sa vie basculer le jour où il intègre la Secte Heng Yue après avoir échoué à tous les tests. Méprisé par ses pairs pour son manque de talent, il s'accroche à la volonté de ses parents et commence son long chemin sur la voie de la cultivation. C'est ici que tout commence : un adolescent ordinaire face à un monde où seul le pouvoir compte.",
  },
  {
    book: 2,
    title: 'The Bloody Image of Cultivation',
    titleFr: "L'Image Sanglante de la Cultivation",
    rangeStart: 65,
    rangeEnd: 140,
    summary: "Wang Lin s'éveille lentement à la réalité brutale de la cultivation. Confronté à la jalousie de ses pairs et aux complots internes de la secte, il survit grâce à son intelligence et à sa ruse. Le monde de la cultivation lui révèle son vrai visage : un univers sans pitié où chaque avancée se paye au prix du sang. Wang Lin commence à comprendre que la voie de l'immortalité exige des sacrifices qu'aucun mortel ne devrait avoir à consentir.",
  },
  {
    book: 3,
    title: 'Famous in the Sea of Devils',
    titleFr: 'Célèbre dans la Mer des Démons',
    rangeStart: 141,
    rangeEnd: 200,
    summary: "Poussé hors de sa secte par un maître abusif, Wang Lin s'enfonce dans la Mer des Démons, une zone redoutée où même les cultivateurs confirmés disparaissent. Au cœur de ce territoire hostile, il rencontre Li Muwan, une jeune alchimiste dont le destin sera lié au sien à travers les siècles. Ensemble, ils affrontent bêtes féroces et cultivateurs cruels, tandis que le nom de Wang Lin commence à se répandre dans l'ombre.",
  },
  {
    book: 4,
    title: 'Clean Sweep',
    titleFr: 'Grand Ménage',
    rangeStart: 201,
    rangeEnd: 405,
    summary: "De retour dans le Pays de Zhao, Wang Lin y affronte ses ennemis jurés — la famille Teng et ses alliés. Dans un déchaînement de violence froide et calculée, il exécute sa vengeance avec une précision impitoyable. Devenu un cultivateur redouté, il quitte sa planète natale pour s'élever dans les rangs supérieurs du monde de la cultivation, laissant derrière lui le souvenir d'un jeune homme médiocre transformé en tueur légendaire.",
  },
  {
    book: 5,
    title: 'Cultivation Planet Crystal',
    titleFr: 'Le Cristal de la Planète de Cultivation',
    rangeStart: 406,
    rangeEnd: 471,
    summary: "Wang Lin explore les secrets d'une planète de cultivation oubliée et y découvre un cristal d'une pureté exceptionnelle, vestige d'un âge ancien. Cette découverte marque un tournant dans sa maîtrise : ses techniques évoluent, sa compréhension du Dao s'approfondit. Mais le cristal attire aussi la convoitise de sectes entières, et Wang Lin doit défendre sa découverte au prix de nouveaux affrontements.",
  },
  {
    book: 6,
    title: 'Arriving on Tian Yun',
    titleFr: "L'Arrivée sur Tian Yun",
    rangeStart: 472,
    rangeEnd: 658,
    summary: "Wang Lin pose le pied sur la planète Tian Yun, un monde dominé par la puissante Secte du Destin Céleste. Pour y survivre, il doit gravir les échelons, participer à des tournois mortels et affronter des génies locaux qui n'ont jamais connu de défaite. Sa progression fulgurante attire l'attention de l'Omniscient, un vieil être mystérieux dont les desseins dépassent l'entendement.",
  },
  {
    book: 7,
    title: 'Fame Shakes Allheaven Star System',
    titleFr: 'La Gloire Secoue le Système Stellaire Allheaven',
    rangeStart: 659,
    rangeEnd: 920,
    summary: "Le nom de Wang Lin résonne désormais à travers tout le système stellaire Allheaven. L'Omniscient, Situ Nan, All-Seer — des figures légendaires convergent autour de lui. Entre alliances fragiles et trahisons innombrables, Wang Lin s'enfonce dans les mystères des héritages anciens, manipule des forces qui le dépassent et forge son propre chemin au mépris des conventions du monde de la cultivation.",
  },
  {
    book: 8,
    title: "Alliance's Secret",
    titleFr: "Le Secret de l'Alliance",
    rangeStart: 921,
    rangeEnd: 1140,
    summary: "L'Alliance cache un secret qui pourrait ébranler l'équilibre du système stellaire. Wang Lin, devenu un acteur majeur malgré lui, se retrouve pris entre des forces titanesques : anciens dieux, démons et immortels. Les révélations sur ses origines et sur le monde dans lequel il vit s'accumulent, et chaque réponse soulève de nouvelles questions. Son cœur reste pourtant hanté par le souvenir de Li Muwan.",
  },
  {
    book: 9,
    title: 'Peak of the Cloud Sea',
    titleFr: 'Le Sommet de la Mer des Nuages',
    rangeStart: 1141,
    rangeEnd: 1478,
    summary: "Wang Lin atteint le sommet de son art sur la Mer des Nuages, un carrefour entre les mondes. Confronté à des ennemis dont la puissance défie l'imagination, il doit puiser dans des ressources insoupçonnées — y compris dans les liens mystérieux qui le rattachent à des divinités anciennes. Ce tome marque l'apogée de sa puissance et le début de sa quête pour retrouver ce qu'il a perdu.",
  },
  {
    book: 10,
    title: 'Rampage Through the Inner Realm',
    titleFr: 'Ruée dans le Royaume Intérieur',
    rangeStart: 1479,
    rangeEnd: 1613,
    summary: "Wang Lin fait irruption dans le Royaume Intérieur, un espace où les règles mêmes de la cultivation s'effondrent. Alliances, trahisons, sacrifices : rien n'est trop pour atteindre son but. Sa puissance atteint des sommets inédits, mais le prix à payer devient de plus en plus lourd — ses ennemis comme ses proches en paient le tribut.",
  },
  {
    book: 11,
    title: 'Mysteries of the Ancient Era',
    titleFr: "Les Mystères de l'Ère Ancienne",
    rangeStart: 1614,
    rangeEnd: 1793,
    summary: "Les mystères de l'ère ancienne se dévoilent enfin. Tuo Sen, un dieu ancien d'une puissance terrifiante, fait irruption dans la trame. Wang Lin doit comprendre ce qu'il est vraiment et ce qu'il peut devenir. Le Continent de l'Immortel, les héritages divins, la Perle du Ciel Insondable — tous les fils narratifs convergent vers une vérité qui dépasse l'imagination.",
  },
  {
    book: 12,
    title: 'Tenth Sun of the Immortal Astral Continent',
    titleFr: 'Le Dixième Soleil du Continent Astral Immortel',
    rangeStart: 1794,
    rangeEnd: 2002,
    summary: "Le Continent Astral Immortel est en feu. Wang Lin, devenu l'un des Empereurs Divins les plus puissants, affronte le Clan Céleste dans une guerre d'une ampleur cosmique. Autour de lui gravitent des figures légendaires — Qing Lin, Zhou Yi, Bei Lou — dans une danse mortelle où chaque pas peut être le dernier. La lumière du dixième soleil s'élève, et avec elle, l'espoir d'un nouvel ordre.",
  },
  {
    book: 13,
    title: 'Light of the Coming End',
    titleFr: 'La Lumière de la Fin',
    rangeStart: 2003,
    rangeEnd: 2088,
    summary: "L'affrontement final. Wang Lin, face à ses dernières épreuves, marche vers le destin qu'il s'est forgé au fil de plus de deux mille chapitres de combats, de pertes et de renaissance. La lumière de la fin n'est pas destruction — elle est le prix de l'immortalité véritable. L'ultime page de Renegade Immortel se tourne sur une note de transcendance, où le renégat d'hier devient la légende de demain.",
  },
];

export function getBookSummary(book: number): BookSummary | undefined {
  return BOOK_SUMMARIES.find(b => b.book === book);
}
