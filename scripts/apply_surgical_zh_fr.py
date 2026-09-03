#!/usr/bin/env python3
"""Corrections chirurgicales + réparation des unités mal collées."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CH = ROOT / "src" / "content" / "chapters"

# Répare « dix mille pieds » → « dix 3,3 km » (万丈 ≈ 33 km)
# et « dix mille kilomètres » → « dix 500 km » (万里 ≈ 5 000 km)
GLOBAL_FIXES = [
    ("dix 3,3 kilomètres", "33 kilomètres"),
    ("cent 3,3 kilomètres", "330 kilomètres"),
    ("dix 500 kilomètres", "5 000 kilomètres"),
    ("150000 kilomètres", "150 000 kilomètres"),
    ("400000 kilomètres", "400 000 kilomètres"),
    ("250000 kilomètres", "250 000 kilomètres"),
    ("5000 kilomètres", "5 000 kilomètres"),
    ("2500 kilomètres", "2 500 kilomètres"),
    ("1500 kilomètres", "1 500 kilomètres"),
]

# (relative path under chapters, old, new)
SURGICAL: list[tuple[str, str, str]] = [
    (
        "tome-2/0105-le-royaume-du-ji-dune-ere-passee.md",
        "À l'âge de dix ans, il avait déjà atteint le stade de la Formation du Noyau",
        "En dix ans de pratique, il avait déjà atteint le stade de la Formation du Noyau",
    ),
    (
        "tome-2/0105-le-royaume-du-ji-dune-ere-passee.md",
        "le roi du pays intégra une secte",
        "le prince héritier du pays intégra une secte",
    ),
    (
        "tome-2/0105-le-royaume-du-ji-dune-ere-passee.md",
        "Avec une culture n'atteignant que le stade avancé de l'Âme Naissante",
        "Avec une culture n'atteignant que le stade initial de l'Âme Naissante",
    ),
    (
        "tome-2/0105-le-royaume-du-ji-dune-ere-passee.md",
        "Tout ce qui se trouvait dans un rayon de six mètres autour de lui",
        "Tout ce qui se trouvait dans un rayon de plusieurs dizaines de mètres autour de lui",
    ),
    (
        "tome-2/0105-le-royaume-du-ji-dune-ere-passee.md",
        "dix marionnettes de niveau Formation de l'Âme",
        "dix cadavres raffinés de niveau Formation de l'Âme",
    ),
    (
        "tome-2/0105-le-royaume-du-ji-dune-ere-passee.md",
        "En ces trois mille années, le simple fait de prononcer son nom suffisait à faire frissonner les plus braves.\n",
        "En ces trois mille années, le simple fait de prononcer son nom suffisait à faire frissonner les plus braves. Le nombre de cultivateurs tombés sous sa main dépasse l'entendement ; certains prétendent même que la chute du monde antique de la culture tient, pour une large part, à ces trois millénaires de massacres.\n",
    ),
    (
        "tome-2/0106-rang.md",
        "Quant aux transitions entre les rangs 3 à 4 ou 5 à 6",
        "Quant aux transitions entre les rangs 3 à 4 ou 4 à 5",
    ),
    (
        "tome-2/0106-rang.md",
        "lisière sud de la Vallée Jue Ming",
        "lisière nord de la Vallée Jue Ming",
    ),
    (
        "tome-2/0108-vieux-ami.md",
        "un maître des attaques surprises",
        "un maître hors pair du vol",
    ),
    (
        "tome-2/0120-le-retour-de-wang-lin.md",
        "Tu ne peux pas refuser ton frère aîné. Je suis un brute, mais je suis le seul à t'aimer vraiment.",
        "Surtout, n'accepte pas le frère aîné : c'est une bête à face humaine. Moi seul t'aime vraiment.",
    ),
    (
        "tome-3/0145-formation-du-noyau-2.md",
        "continua sa course vers le nord. Selon les informations de Sang Muya, la ville de Nan Dou se trouvait à environ 150 000 kilomètres au nord",
        "continua sa course vers le sud. Selon les informations de Sang Muya, la ville de Nan Dou se trouvait à environ 150 000 kilomètres au sud",
    ),
    (
        "tome-3/0160-la-formation-du-noyau.md",
        "Huitième Seigneur Démon Extrême",
        "Seigneur Démon des Huit Extrêmes",
    ),
    (
        "tome-3/0173-le-second-demon.md",
        "un python d'un mètre trente de long",
        "un python d'une trentaine de mètres de long",
    ),
    (
        "tome-3/0173-le-second-demon.md",
        "le python à corne de cent pieds de long",
        "le python à corne d'une trentaine de mètres de long",
    ),
    (
        "tome-3/0200-yun-fei.md",
        "elle mesurait déjà plus de 16 mètres de large",
        "elle mesurait déjà plus de cent soixante mètres de large",
    ),
    (
        "tome-3/0200-yun-fei.md",
        "après n'avoir parcouru que 33 mètres",
        "après n'avoir parcouru que cinq kilomètres",
    ),
    (
        "tome-3/0200-yun-fei.md",
        "Tu Mo Yun",
        "Mo Yun",
    ),
    (
        "tome-4/0266-cultivateur-de-xue-yue.md",
        "Cette neige est incandescente... Elle ne peut pas être fondue !",
        "Cette neige ne fond pas !",
    ),
    (
        "tome-4/0300-jade-celeste-1.md",
        "unifier la Planète Da Lou",
        "unifier la planète Tian Dun",
    ),
    (
        "tome-4/0340-messager-de-suzaku.md",
        "mais nul n'ignora que ce cri différait",
        "mais personne ne savait que ce cri différait",
    ),
    (
        "tome-4/0340-messager-de-suzaku.md",
        "Tie Yun et Lu Fei",
        "Tie Yan et Lu Fei",
    ),
    (
        "tome-5/0414-richesse.md",
        "Zhen Fengxiao",
        "Chen Fengxiao",
    ),
    (
        "tome-5/0414-richesse.md",
        "Zheng Fengxiao",
        "Chen Fengxiao",
    ),
    (
        "tome-5/0430-messager.md",
        "je l'ai choisi comme candidat principal pour mon plan !",
        "je l'ai désigné comme exécutant de mon plan Suzaku !",
    ),
    (
        "tome-5/0430-messager.md",
        "il reste le candidat principal !",
        "il demeure l'exécutant !",
    ),
    (
        "tome-5/0430-messager.md",
        "L'Aîné a donné ce chapeau de paille à une autre personne. Tu devrais la connaître, elle s'appelle Zi Xin !",
        "L'Aîné a donné ce chapeau de paille à quatre personnes. Il en reste une que tu devrais connaître : elle s'appelle Zi Xin !",
    ),
    (
        "tome-5/0450-domaine-des-mille-illusions-de-la-luxure.md",
        "La Liu Mei de la Secte Xuan Dao",
        "La Liu Mei de la Secte Tian Dao",
    ),
    (
        "tome-6/0475-bai-wei.md",
        "tu as gaspillé ma fondation céleste",
        "tu as détruit ma fondation céleste",
    ),
    (
        "tome-6/0475-bai-wei.md",
        "Une fois que je serai revenu sur la planète Tian Yun, je t'en donnerai une nouvelle !",
        "Une fois que je serai revenu sur la planète Tian Yun, je t'en donnerai une nouvelle ! Allons-y : c'est le grand anniversaire des dix mille ans de notre maître, je ne saurais arriver en retard.",
    ),
    (
        "tome-6/0475-bai-wei.md",
        "Cette boutique possède-t-elle de l'encre noire ?",
        "Cette boutique possède-t-elle du liquide de neige d'encre ?",
    ),
    (
        "tome-6/0486-les-7-veritables-disciples-de-lomniscient.md",
        "La plupart des cultivateurs de la planète Tian Yun ne pratiquent que durant quelques millénaires, et très peu dépassent les dix mille ans.",
        "Parmi ses disciples, hormis une infime minorité, la plupart ne cultivent que depuis un millénaire environ, et très peu dépassent les dix mille ans.",
    ),
    (
        "tome-6/0486-les-7-veritables-disciples-de-lomniscient.md",
        "Sois un véritable disciple pendant 100 ans et tu recevras un sort céleste de faible qualité",
        "Sois l'un des sept véritables disciples pendant mille ans et tu recevras un sort céleste de faible qualité",
    ),
    (
        "tome-6/0486-les-7-veritables-disciples-de-lomniscient.md",
        "Être l'un des véritables disciples pendant 1 000 ans te permet d'obtenir un autre sort céleste de faible qualité.",
        "Être l'un des sept véritables disciples pendant dix mille ans te permet d'obtenir un autre sort céleste de faible qualité.",
    ),
    (
        "tome-6/0486-les-7-veritables-disciples-de-lomniscient.md",
        "Le véritable disciple de la division verte, Li Shengnan, l'est depuis plus de 1 000 ans. Il y a cent ans, il a reçu de Maître un sort céleste complet de faible qualité. Il est toujours en culture fermée pour l'étudier. À sa sortie, sa puissance sera d'un niveau inimaginable !",
        "La véritable disciple de la division verte, Li Shengnan, l'est depuis plus de mille ans. Il y a cent ans, elle a reçu de Maître un sort céleste complet de faible qualité. Elle est toujours en culture fermée pour l'étudier. À sa sortie, sa puissance sera d'un niveau inimaginable !",
    ),
    (
        "tome-6/0542-lepreuve-des-generaux-demons.md",
        "Cité Démoniaque Antique",
        "Grande Muraille Antique",
    ),
    (
        "tome-6/0615-les-traces-de-la-cupidite.md",
        "le temps ralentit à l'intérieur",
        "le temps peut s'inverser à l'intérieur",
    ),
    (
        "tome-6/0615-les-traces-de-la-cupidite.md",
        "Bien qu'elle puisse ralentir le temps",
        "Bien qu'elle puisse inverser le temps",
    ),
    (
        "tome-7/0743-li-yuan.md",
        "Wang Lin franchit le second stade et passa directement au-dessus des deux individus.",
        "Wang Lin fit un second pas et passa directement au-dessus des deux individus.",
    ),
    (
        "tome-7/0785-resurrection.md",
        "Ce processus dura près de dix ans",
        "Ce processus dura près de dix jours",
    ),
    (
        "tome-7/0793-maitre-flamespark.md",
        "la tablette fragmentaire sur laquelle ils se trouvaient commencer à trembler violemment. Ce n'était pas seulement une partie de la tablette, mais l'intégralité du fragment.",
        "le continent fragmentaire sur lequel ils se trouvaient commencer à trembler violemment. Ce n'était pas seulement une partie du continent, mais l'intégralité du fragment.",
    ),
    (
        "tome-7/0825-les-pensees-du-dieu-sanglant-2.md",
        "une flamme verte singulière",
        "une flamme rouge singulière",
    ),
    (
        "tome-7/0840-lappel-venant-de-linterieur-du-corps-du-serpent-aux-yeux-de-lune.md",
        "Li Yunzi",
        "Lie Yunzi",
    ),
    (
        "tome-7/0840-lappel-venant-de-linterieur-du-corps-du-serpent-aux-yeux-de-lune.md",
        "Songun",
        "Gongsun",
    ),
    (
        "tome-7/0871-lenfant.md",
        "nourrir son Âme Naissante. Cela permit aux blessures subies lors de son combat contre Russell",
        "nourrir son esprit originel. Cela permit aux blessures subies lors de son combat contre Luo Su",
    ),
]


def apply_in_file(path: pathlib.Path, old: str, new: str) -> int:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return 0
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    return 1


def main() -> None:
    global_n = 0
    for old, new in GLOBAL_FIXES:
        for p in CH.rglob("*.md"):
            text = p.read_text(encoding="utf-8")
            if old in text:
                p.write_text(text.replace(old, new), encoding="utf-8")
                global_n += text.count(old)
    print(f"global unit repairs: {global_n}")

    missing = []
    ok = 0
    for rel, old, new in SURGICAL:
        path = CH / rel
        if not path.exists():
            missing.append(f"MISSING FILE {rel}")
            continue
        n = apply_in_file(path, old, new)
        if n:
            ok += 1
        else:
            missing.append(f"NO MATCH {rel}: {old[:80]}")
    print(f"surgical ok={ok}/{len(SURGICAL)}")
    for m in missing:
        print(m)


if __name__ == "__main__":
    main()
