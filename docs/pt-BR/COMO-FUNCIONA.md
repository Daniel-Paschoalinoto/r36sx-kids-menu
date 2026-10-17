# Como funciona (para curiosos)

🇬🇧 [English](../en/HOW-IT-WORKS.md)

Você **não** precisa disto para usar o projeto.

## O aparelho

O `icube` inicia o `rkgame`, um programa ELF **MIPS** de 32 bits little-endian que desenha toda a interface e roda os emuladores (`cubegm/cores/*.so`). As imagens ficam em arquivos zip com extensão `.cpd`:

| Arquivo | Conteúdo |
|---|---|
| `UI_Res.cpd` | Fundos de tela cheia, **BGRA** cru 640×480 (`MovieBg`, `MusicBg`, `PhotoBg`, `DOWNLOAD` = página de Jogos) |
| `resource.cpd` | Lista de jogos (`menu.raw`), menu de pausa (`game.raw`), teclado de busca (`search.raw`), tela de carregando, rodapés. As folhas são **RGB565** com um cabeçalho que lista o retângulo de cada peça |
| `ui_<idioma>.cpd` | A folha do menu de pausa (`game.raw`) de cada um dos 25 idiomas |
| `language/*.raw` | Rótulos de texto, 25 quadros (um por idioma) em BGRA |
| `xgame-logo.bmp` | Tela de abertura (BMP 32 bits) |

`r36skit/art/` redesenha essas imagens com o Pillow. Ele lê os retângulos das próprias folhas do aparelho, então as posições sempre batem.

## Os patches de código (`r36skit/patches/`)

O programa é alterado por **ganchos**: um `j cave; nop` colocado sobre uma instrução, que pula para um espaço livre (uma "caverna") dentro de funções que nunca são chamadas. A caverna roda nosso código (montado com o Keystone) e volta.

| Módulo | O que faz |
|---|---|
| `menu_lock.py` | Só 3 botões de mídia + Jogos; esconde ajustes / e-books / lista de consoles |
| `listfilter.py` | Esconde `.bin` e a pasta `images` na lista de jogos |
| `resume_covers.py` | Miniaturas de capa (+ imagem "sem capa"), abre o jogo ao ligar **só se o aparelho foi desligado jogando** (o arquivo `cubegm/lastgame.txt` é apagado quando o jogo termina ou quando uma partida não retoma) |
| `deletegame.py` | X → confirma → roda `delgame.sh` (apaga jogo, arquivos do cue, de mesmo nome e capas) |
| `deletesave.py` | X sobre um slot de save → confirma → exclui |
| `apply.py` | Roda todos; confere o SHA-256 antes |

O `elfpatch.py` grava por endereço virtual e confere os bytes originais antes de trocar ("só altera se for o esperado, ou se já estiver alterado"). Os scripts de shell rodam por `system()`, que funciona no aparelho.

## Dar suporte a outro firmware

1. Abra o `rkgame` no Ghidra (MIPS, 32 bits, little-endian).
2. Encontre cada endereço de gancho e caverna; atualize as constantes no topo de cada módulo (`HOOK`, `CAVE`, bytes originais).
3. Adicione o novo SHA-256 em `SUPPORTED_RKGAME_SHA256` (transforme em lista) e teste em aparelho real. Envie um pull request.

## Testes

`python -m pytest` confere os textos em todos os idiomas, os tamanhos das imagens, as mensagens de erro da configuração e (se você colocar seus arquivos originais em `stock/`) se os patches se aplicam.
