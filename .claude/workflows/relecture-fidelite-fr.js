export const meta = {
  name: 'relecture-fidelite-fr',
  description: 'Relit les chapitres FR de Renegade Immortal contre le chinois Qidian aligné (tmp/zh_aligned), corrige sens/omissions/noms, vérifie par un second agent',
  phases: [{ title: 'Relecture', detail: 'un agent par lot de chapitres, corrections appliquées directement' }, { title: 'Verification', detail: 'second agent : vérifie chaque correction via git diff' }],
}

// args : { chapters: [n, ...] } ou { from, to } ; batch (défaut 5) ; verify (défaut true)
const ROOT = 'C:/Users/Marc/Documents/1G1R/_Programmation/renegade-immortal-fr'
const size = args.batch || 5
let ns = args.chapters
if (!ns) { const ex = new Set(args.exclude || []); ns = []; for (let i = args.from; i <= args.to; i++) if (!ex.has(i)) ns.push(i) }
const batches = []
for (let i = 0; i < ns.length; i += size) batches.push(ns.slice(i, i + size))
const verify = args.verify !== false
const model = args.model // ex. 'haiku' quand la limite hebdomadaire Sonnet est atteinte ; sinon modèle de la session
const TYPES = ['contresens', 'omission', 'ajout', 'nom', 'terme', 'style']

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    chapters: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          n: { type: 'number' },
          status: { type: 'string', enum: ['fidele', 'corrige', 'incertain'] },
          corrections: { type: 'array', items: { type: 'object', properties: { type: { type: 'string', enum: TYPES }, old: { type: 'string' }, new: { type: 'string' }, why: { type: 'string' } }, required: ['type', 'old', 'new', 'why'] } },
          flags: { type: 'array', items: { type: 'string' } },
        },
        required: ['n', 'status', 'corrections', 'flags'],
      },
    },
  },
  required: ['chapters'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    checked: { type: 'number' },
    reverted: { type: 'array', items: { type: 'object', properties: { n: { type: 'number' }, what: { type: 'string' }, why: { type: 'string' } }, required: ['n', 'what', 'why'] } },
    notes: { type: 'array', items: { type: 'string' } },
  },
  required: ['checked', 'reverted', 'notes'],
}

const pad = (n) => String(n).padStart(4, '0')

function reviewPrompt(chs) {
  const list = chs.map(pad).join(', ')
  return `Tu es traducteur spécialiste du xianxia (Renegade Immortal / 仙逆, d'Er Gen). Tu relis des chapitres français déjà traduits (depuis l'anglais) pour qu'ils soient FIDÈLES au chinois : la traduction la plus fidèle possible, tout en restant compréhensible et naturelle en français. Dépôt : ${ROOT}. Chapitres de ton lot : ${list}.

FICHIERS (utilise Glob/Read, jamais de devinette de chemin)
- FR (à corriger) : src/content/chapters/tome-*/NNNN-*.md (frontmatter YAML entre --- puis le texte ; ne touche JAMAIS au frontmatter).
- Chinois (SOURCE DU SENS, complet et déjà découpé selon les chapitres Wuxiaworld) : tmp/zh_aligned/NNNN_*.txt, un seul fichier par chapitre. Les chapitres 43 à 71 y sont dans leur version intégrale d'origine (Qidian les a condensés depuis) ; l'anglais suit cette version intégrale.
- Anglais (Wuxiaworld, dont le FR a été tiré) : tmp/en/Book */NNNN - *.txt (parfois NNNNa/NNNNb). Aide pour retrouver le sens, jamais référence : si EN et ZH divergent, le ZH a raison. Quelques passages du ZH n'existent pas chez Wuxiaworld ni en FR (ch. 236, 596, 975, 1067, 1247) : ne les traduis pas, signale-les dans flags.
- Noms : tmp/relecture/glossaire_noms_wiki.txt (chinois | pinyin | nom du wiki Fandom xian-ni) fait autorité avec les fichiers sources. NE LIS PAS et ne te fie PAS à glossaire-entites.md, glossary.txt ni au dossier wiki/ du dépôt.

CE QU'IL FAUT VÉRIFIER, paragraphe par paragraphe, en lisant chaque chapitre EN ENTIER
1. contresens : faux sens, négations/sujets inversés, qui fait quoi à qui, ordre des événements, nombres, durées, rangs.
2. omission : phrase ou proposition du chinois absente du FR → ajoute-la, traduite en français. ATTENTION : avant d'ajouter, vérifie dans les chapitres voisins FR (N-1, N+1) que le contenu n'y figure pas déjà (frontières décalées). Ne rajoute JAMAIS un contenu déjà présent ailleurs.
3. ajout : contenu du FR absent du chinois → supprime-le.
4. nom : noms de personnes en pinyin, forme du glossaire wiki, écrits pareil partout ; sectes, lieux, techniques, objets : garde la forme française déjà utilisée dans le corpus, corrige seulement l'incohérence ou le faux sens.
5. terme : anglais ou chinois résiduel → français (SAUF le vocabulaire xianxia gardé : Senior, Junior, Dao, Daoïste) ; terme de culture rendu autrement que l'usage du corpus.
6. style : uniquement une phrase incompréhensible ou un calque de l'anglais qui gêne la lecture ; une faute de français seulement si elle gêne le sens.

CONVENTIONS À RESPECTER (ne pas les « corriger »)
- 筑基 = Établissement des Fondations ; 结丹 = Formation du Noyau ; 元婴 = Âme Naissante ; 婴变 = Transformation de l'Âme ; 化神 = Formation de l'Âme ; 问鼎 = Ascendant ; 空劫 = Tribulation du Vide ; 斗邪派 = Secte de la Lutte contre le Mal ; 极境 = Royaume Ji ; 血海 = Mer de Sang. Pour les autres rangs et termes, suis la forme déjà utilisée dans le chapitre et le corpus (grep si besoin). Suis les caractères de la source : p. ex. 大娄 (Da Lou) et 大罗 (Da Luo) sont deux noms distincts.
- UNITÉS : AUCUN changement d'unité de mesure, de monnaie ou de temps (pieds, mètres, li, zhang, minutes…) : garde exactement l'unité qui est dans le FR. Ne corrige un nombre que s'il est manifestement faux par rapport au chinois, sans changer d'unité.
- Ne réécris PAS le style, ne reformule pas ce qui est correct, ne change pas la ponctuation française existante. Corrections minimales et ciblées.
- N'invente aucun terme. En cas de doute sur un terme/passage : ne modifie pas, signale-le dans flags.

COMMENT CORRIGER
- Applique chaque correction directement avec l'outil Edit sur le fichier FR (old_string court et unique, new_string corrigé). Ne modifie QUE les fichiers FR de tes chapitres : pas d'autres fichiers, pas de script, pas de git add/commit.
- Si un chapitre est fidèle : n'édite rien (status "fidele").
- Termine en renvoyant le résultat structuré : pour chaque chapitre, statut, la liste des corrections (type parmi ${TYPES.join('/')}, old/new courts, motif citant le chinois), et flags pour les doutes importants uniquement.`
}

function verifyPrompt(chs) {
  const list = chs.map(pad).join(', ')
  return `Tu es relecteur-vérificateur de traduction xianxia (Renegade Immortal / 仙逆). Dépôt : ${ROOT}. Un autre agent vient de corriger les chapitres FR ${list} (src/content/chapters/tome-*/NNNN-*.md) contre le chinois (tmp/zh_aligned/NNNN_*.txt ; anglais Wuxiaworld en aide : tmp/en/Book */NNNN - *.txt ; noms : tmp/relecture/glossaire_noms_wiki.txt, wiki Fandom ; ne te fie pas aux glossaires du dépôt).
Fais "git diff -U2 -- <fichiers FR de ces chapitres>" et examine CHAQUE modification. Pour chacune, contrôle-la contre le chinois. Annule (rétablis l'ancien texte avec Edit) toute modification qui : est fausse ou discutable par rapport au chinois, ajoute un contenu déjà présent dans le chapitre voisin, invente un terme, introduit de l'anglais ou du chinois, change 化神 (= Formation de l'Âme) ou le vocabulaire xianxia gardé (Senior, Junior, Dao, Daoïste), remplace un nom en pinyin, CHANGE UNE UNITÉ de mesure/temps (l'unité du FR doit rester), ou réécrit le style sans nécessité. Garde les modifications correctes.
Ne touche à rien d'autre. Renvoie : combien de modifications contrôlées, la liste de celles annulées (chapitre, quoi, pourquoi) et des notes utiles.`
}

phase('Relecture')
const results = await pipeline(
  batches,
  (chs) => agent(reviewPrompt(chs), { label: 'relecture ' + pad(chs[0]) + '-' + pad(chs[chs.length - 1]), phase: 'Relecture', schema: REVIEW_SCHEMA, model }),
  async (rev, chs) => {
    if (!rev) return { chs, rev: null, ver: null }
    const changed = rev.chapters.filter((c) => c.corrections.length > 0).map((c) => c.n)
    if (!verify || changed.length === 0) return { chs, rev, ver: null }
    const ver = await agent(verifyPrompt(changed), { label: 'verif ' + pad(chs[0]) + '-' + pad(chs[chs.length - 1]), phase: 'Verification', schema: VERIFY_SCHEMA, model })
    return { chs, rev, ver }
  },
)
const ok = results.filter(Boolean)
let nCorr = 0, nReverted = 0
const flags = []
const byType = Object.fromEntries(TYPES.map((t) => [t, 0]))
const failed = batches.filter((b, i) => !results[i] || !results[i].rev)
const chapters = []
for (const r of ok) {
  if (!r.rev) continue
  for (const c of r.rev.chapters) {
    nCorr += c.corrections.length
    const types = Object.fromEntries(TYPES.map((t) => [t, 0]))
    for (const k of c.corrections) { types[k.type] = (types[k.type] || 0) + 1; byType[k.type] = (byType[k.type] || 0) + 1 }
    chapters.push({ n: c.n, status: c.status, nCorr: c.corrections.length, types, flags: c.flags })
  }
  if (r.ver) nReverted += r.ver.reverted.length
}
log('lots: ' + ok.length + '/' + batches.length + ', corrections: ' + nCorr + ', annulées par vérif: ' + nReverted + ', lots échoués: ' + failed.length)
return {
  summary: { batches: batches.length, chapters: ns.length, corrections: nCorr, byType, reverted: nReverted, failed },
  chapters,
  reverted: ok.flatMap((r) => (r.ver ? r.ver.reverted : [])),
}
