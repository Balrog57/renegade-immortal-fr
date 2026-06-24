/**
 * Synopses détaillés des 13 tomes de Renegade Immortel.
 * Titres chinois officiels : Qidian (起点中文网), book 1264634.
 * Synopses : adaptations basées sur les sources disponibles
 * (Baidu Baike, Wuxiaworld, NovelFrance, Xian Ni Fandom Wiki, Webnovel).
 */

export interface BookSummary {
  book: number;
  title: string;
  titleFr: string;
  titleCn: string;
  rangeStart: number;
  rangeEnd: number;
  summary: string;
}

export const BOOK_SUMMARIES: BookSummary[] = [
  {
    book: 1,
    title: 'The Mediocre Youth',
    titleFr: 'Le Jeune Homme Médiocre',
    titleCn: '平庸少年',
    rangeStart: 1,
    rangeEnd: 64,
    summary: "Tome d'introduction. Dans le Pays de Zhao, Wang Lin — surnommé Tie Zhu dans son enfance en raison de sa santé fragile — grandit dans un petit village avec ses parents. Admis à la Secte Heng Yue après avoir échoué aux trois tests initiaux, il se voit attribuer le statut de disciple conditionnel : il dispose de cinq ans pour atteindre le niveau de Saint, sous peine d'être renvoyé. Ce tome présente les premières étapes de sa cultivation, sa rencontre avec son maître Zhang Hu et le sculpteur Zhou, ainsi que ses premières confrontations avec des disciples hostiles. L'intrigue pose les bases du monde de la cultivation : racines spirituelles, niveaux de pouvoir, et l'importance des ressources.",
  },
  {
    book: 2,
    title: 'The Bloody Image of Cultivation',
    titleFr: "L'Image Sanglante de la Cultivation",
    titleCn: '修真血影',
    rangeStart: 65,
    rangeEnd: 140,
    summary: "Wang Lin se heurte à la réalité brutale de la cultivation. Après avoir été contraint d'absorber une énergie spirituelle impure lors d'une épreuve piégée par son maître abusif, il doit trouver un moyen de purifier son corps. La mort de ses parents, assassinés par la famille Teng, marque un tournant décisif : Wang Lin comprend que la cultivation n'est pas qu'une quête spirituelle, mais un combat pour la survie. Ce tome le voit quitter la Secte Heng Yue, errer dans la Vallée Jueming, et poser les bases de sa réputation naissante. Plusieurs figures clés apparaissent, dont le Maître de la Vallée.",
  },
  {
    book: 3,
    title: 'Famous in the Sea of Devils',
    titleFr: 'Célèbre dans la Mer des Démons',
    titleCn: '扬名修魔海',
    rangeStart: 141,
    rangeEnd: 200,
    summary: "Poussé vers la Mer des Démons, région redoutée du monde de la cultivation, Wang Lin y rencontre Li Muwan, une jeune alchimiste de la Secte Luo He. Ensemble, ils affrontent des bêtes féroces, des brouillards mortels et des cultivateurs rivaux. Wang Lin commence à maîtriser des techniques offensives et à accumuler des trésors spirituels. Sa rencontre avec le puissant Situ Nan, un vieux fripon à la force terrifiante, marque un tournant : les deux hommes deviennent alliés. Wang Lin commence à se faire un nom dans les cercles souterrains de la cultivation.",
  },
  {
    book: 4,
    title: 'Clean Sweep',
    titleFr: 'Grand Ménage',
    titleCn: '风卷残云',
    rangeStart: 201,
    rangeEnd: 405,
    summary: "Wang Lin retourne au Pays de Zhao pour venger la mort de ses parents. En une série d'affrontements méthodiques, il élimine un à un les membres de la famille Teng et leurs alliés, y compris Teng Huayuan, le chef de clan. Ce tome présente la montée en puissance brutale de Wang Lin, qui passe d'un jeune cultivateur à une figure crainte. Il quitte ensuite sa planète natale pour explorer des mondes supérieurs, laissant derrière lui un royaume nettoyé de ses ennemis. Les thèmes de la solitude, du sacrifice et de la détermination s'imposent durablement.",
  },
  {
    book: 5,
    title: 'Cultivation Planet Crystal',
    titleFr: 'Le Cristal de la Planète de Cultivation',
    titleCn: '修星之晶',
    rangeStart: 406,
    rangeEnd: 471,
    summary: "Wang Lin explore une planète de cultivation oubliée et y découvre un cristal d'une pureté exceptionnelle, vestige d'une ère ancienne. Cette découverte lui permet de perfectionner ses techniques et d'accéder à des niveaux de cultivation supérieurs. Le cristal attire la convoitise de plusieurs sectes, forçant Wang Lin à défendre sa découverte. Ce tome marque une transition dans la maîtrise de Wang Lin, qui commence à comprendre les rouages profonds de la cultivation et l'importance des héritages ancestraux.",
  },
  {
    book: 6,
    title: 'Arriving on Tian Yun',
    titleFr: "L'Arrivée sur Tian Yun",
    titleCn: '初入天运',
    rangeStart: 472,
    rangeEnd: 658,
    summary: "Wang Lin arrive sur la planète Tian Yun, un monde dominé par la Secte du Destin Céleste, l'une des plus puissantes de l'Allheaven Star System. Pour y survivre et trouver des ressources, il s'engage dans des tournois de cultivation, gravit les échelons de la secte, et se forge une réputation. Il y rencontre des figures majeures : l'Omniscient (All-Seer), un vieil être mystérieux aux desseins cachés, ainsi que plusieurs génies locaux. Ce tome établit Wang Lin comme un acteur majeur de l'Allheaven Star System, et introduit les intrigues politiques entre sectes.",
  },
  {
    book: 7,
    title: 'Fame Shakes Allheaven Star System',
    titleFr: 'La Gloire Secoue le Système Stellaire Allheaven',
    titleCn: '名震罗天',
    rangeStart: 659,
    rangeEnd: 920,
    summary: "Le nom de Wang Lin résonne désormais dans tout l'Allheaven Star System. Ce tome voit l'intensification des affrontements avec des génies et des anciens du système stellaire. All-Seer, Situ Nan et plusieurs autres figures légendaires convergent autour de lui. Les héritages anciens — trésors, techniques, sectes disparues — deviennent des enjeux majeurs. Wang Lin doit naviguer entre alliances fragiles et trahisons, tout en approfondissant sa compréhension du Dao. Les thèmes de la solitude du puissant et du prix de l'immortalité s'intensifient.",
  },
  {
    book: 8,
    title: "Alliance's Secret",
    titleFr: "Le Secret de l'Alliance",
    titleCn: '联盟隐秘',
    rangeStart: 921,
    rangeEnd: 1140,
    summary: "L'Alliance, l'une des plus puissantes organisations de l'Allheaven Star System, cache un secret susceptible d'ébranler l'équilibre du monde. Wang Lin, devenu un acteur incontournable, se retrouve pris entre des forces titanesques : anciens dieux, démons et immortels. Les révélations sur ses origines, sur la nature de la cultivation et sur les véritables maîtres du système stellaire s'accumulent. Wang Lin est confronté à des choix impossibles qui détermineront le sort de ses proches. Ce tome approfondit considérablement la mythologie de l'œuvre.",
  },
  {
    book: 9,
    title: 'Peak of the Cloud Sea',
    titleFr: 'Le Sommet de la Mer des Nuages',
    titleCn: '云海之巅',
    rangeStart: 1141,
    rangeEnd: 1478,
    summary: "Wang Lin atteint le sommet de son art sur la Mer des Nuages, un carrefour entre les mondes où se jouent les destinées des cultivateurs. Confronté à des ennemis dont la puissance défie l'imagination, il doit puiser dans des ressources insoupçonnées — y compris dans les liens mystérieux qui le rattachent à des divinités anciennes. Ce tome marque l'apogée de sa puissance et le début de sa quête pour retrouver ce qu'il a perdu, notamment Li Muwan. Les thèmes du sacrifice et de la persévérance atteignent leur paroxysme.",
  },
  {
    book: 10,
    title: 'Rampage Through the Inner Realm',
    titleFr: 'Ruée dans le Royaume Intérieur',
    titleCn: '叱咤界内',
    rangeStart: 1479,
    rangeEnd: 1613,
    summary: "Wang Lin fait irruption dans le Royaume Intérieur, un espace où les règles mêmes de la cultivation sont distordues. Alliances de circonstances, trahisons sanglantes, sacrifices de personnages secondaires : rien n'est trop pour atteindre ses objectifs. Sa puissance atteint des sommets inédits, mais le prix à payer devient de plus en plus lourd — ses ennemis comme ses proches en subissent les conséquences. Ce tome présente plusieurs confrontations d'envergure cosmique et fait évoluer Wang Lin vers une forme de détachement tragique.",
  },
  {
    book: 11,
    title: 'Mysteries of the Ancient Era',
    titleFr: "Les Mystères de l'Ère Ancienne",
    titleCn: '远古谜团',
    rangeStart: 1614,
    rangeEnd: 1793,
    summary: "Les mystères de l'ère ancienne se dévoilent enfin. Tuo Sen, un dieu ancien (Ancient God) d'une puissance terrifiante, fait irruption dans la trame narrative. Wang Lin doit comprendre ce qu'il est vraiment — son corps, ses origines, sa place dans l'univers — et ce qu'il peut devenir. Le Continent de l'Immortel, les héritages divins, la Perle du Ciel Insondable (Heaven Defying Bead) : tous les fils narratifs convergent vers une vérité qui dépasse l'imagination. Ce tome est considéré comme un pivot majeur de l'œuvre.",
  },
  {
    book: 12,
    title: 'Tenth Sun of the Immortal Astral Continent',
    titleFr: 'Le Dixième Soleil du Continent Astral Immortel',
    titleCn: '仙罡第十阳',
    rangeStart: 1794,
    rangeEnd: 2002,
    summary: "Le Continent Astral Immortel est en feu. Wang Lin, devenu l'un des Empereurs Divins les plus puissants de son époque, affronte le Clan Céleste (Chosen Immortal Clan) dans une guerre d'une ampleur cosmique. Autour de lui gravitent des figures légendaires — Qing Lin, Zhou Yi, Bei Lou, l'Ancien Dieux Tu Si — dans une danse mortelle où chaque pas peut être le dernier. La lumière du dixième soleil s'élève, et avec elle, l'espoir d'un nouvel ordre. Ce tome est le plus long de l'œuvre (209 chapitres) et contient certaines des batailles les plus emblématiques.",
  },
  {
    book: 13,
    title: 'Light of the Coming End',
    titleFr: 'La Lumière de la Fin',
    titleCn: '灯火阑珊',
    rangeStart: 2003,
    rangeEnd: 2088,
    summary: "L'affrontement final. Wang Lin, face à ses dernières épreuves, marche vers le destin qu'il s'est forgé au fil de plus de deux mille chapitres de combats, de pertes et de renaissance. Les réponses aux questions fondamentales de l'œuvre — la nature du Dao, le prix de l'immortalité, la possibilité de transcender le cycle des réincarnations — trouvent ici leur résolution. La lumière de la fin n'est pas destruction : elle est le prix de l'immortalité véritable. L'ultime page de Renegade Immortel se tourne sur une note de transcendance, où le renégat d'hier devient la légende de demain.",
  },
];

export function getBookSummary(book: number): BookSummary | undefined {
  return BOOK_SUMMARIES.find(b => b.book === book);
}