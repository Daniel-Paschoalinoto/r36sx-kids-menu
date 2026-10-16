# Guia passo a passo

🇬🇧 [English](../en/GUIDE.md)

## 0. Antes de começar

- Faça uma **cópia completa do cartão SD** para o computador (copie tudo). Se algo der errado, é só copiar de volta.
- Você precisa de um computador com Windows (Linux/macOS também servem) e um leitor de cartão.
- O cartão SD tem uma pasta chamada **`cubegm`** (o programa e o menu do aparelho). É ela que alteramos.

## 1. Jeito mais rápido: o pacote pronto

1. Baixe o `R36SX-Kids-Menu-…-pt-BR.zip` na pasta [`packs`](../../packs) do projeto (clique no arquivo e depois no botão de download).
2. Abra o zip. Copie as pastas **`cubegm`** e **`roms`** para a **raiz do cartão SD**. Quando o Windows perguntar, escolha **Substituir / Mesclar**.
3. Coloque o cartão no aparelho. Pronto.

O pacote usa as imagens de exemplo e as cores padrão. Para personalizar, use o gerador abaixo.

## 2. Montar do seu jeito

### 2.1 Instalar o Python (uma vez)
Baixe o Python 3.11 ou mais novo em <https://www.python.org/downloads/>. No instalador marque **"Add python.exe to PATH"**.

### 2.2 Onde colocar cada coisa

| Pasta / arquivo | O que colocar |
|---|---|
| `stock/` | A pasta **`cubegm`** do seu cartão SD (original, sem alterações). Resultado: `stock/cubegm/rkgame` |
| `my_files/` | **Suas imagens**: `photo.jpg` (tela de abertura), `mascot.png` (menus), `font.ttf` opcional |
| `config.toml` | **Suas escolhas** (cores, textos, idioma, recursos). Abra no Bloco de Notas |
| `r36skit/data/strings/` | Todos os textos do menu por idioma (`en.json`, `pt-BR.json`) |

### 2.3 Confira se o seu aparelho é suportado
Abra um terminal na pasta do projeto (no Windows: digite `cmd` na barra de endereço da pasta) e rode:

```bash
python build.py --check
```

`OK - compatible firmware` → pode continuar. Se não, leia [COMPATIBILIDADE](COMPATIBILIDADE.md).

### 2.4 Edite o `config.toml`
Abra no Bloco de Notas. Cada linha tem uma anotação em inglês e português. As mais úteis:

| Opção | Significado |
|---|---|
| `language` | `"en"` ou `"pt-BR"` |
| `console_name` | Título curto no topo das telas (até ~16 letras) |
| `[splash] big_text / small_text` | As duas linhas da tela de abertura, ex.: `"R36S"` e `"da Ana"` |
| `photo` | Arquivo da sua foto em `my_files`. `photo_focus_x/y` movem o recorte quadrado para o rosto (0–1), `photo_zoom` aproxima |
| `mascot` | Imagem dos menus (personagem, logo…) – é recortada em 4:3 |
| `[colors]` | Seis cores em `#RRGGBB`. Pesquise "seletor de cores" na web |
| `[features]` | Liga (`true`) ou desliga (`false`) cada recurso extra |

### 2.5 Gerar
Dê dois cliques em **`build.bat`** (Windows) ou rode `./build.sh`. Na primeira vez ele instala os pacotes necessários (precisa de internet uma vez). Leva alguns segundos.

Veja as imagens em **`output/preview`**. Não gostou? Mude o `config.toml` e gere de novo – é seguro, nada toca no cartão ainda.

### 2.6 Copiar para o cartão SD
Copie tudo que está dentro de **`output`** (as pastas `cubegm` e `roms`) para a raiz do cartão, **Substituir / Mesclar**. **Não** copie a pasta `preview`.

## 3. Usando o aparelho

| Você faz | O que acontece |
|---|---|
| **L1 / R1** | Alterna entre Jogos, Vídeos, Músicas, Fotos |
| **A** | Abrir / entrar |
| **X** sobre um jogo da lista | Exclui o jogo, a capa e os arquivos de mesmo nome (pergunta antes) |
| **X** sobre um slot em Pausa → Carregar / Salvar | Exclui aquele save (pergunta antes) |
| Ligar segurando **B** | Pula o "abrir último jogo" e vai ao menu |

**Onde coloco meus arquivos?**

| O quê | Onde no cartão SD |
|---|---|
| Jogos | `roms/` (subpastas à vontade, ex.: `roms/corrida/`) |
| Capas | `roms/images/<nome exato do arquivo do jogo sem extensão>.png`, 240×240 |
| Vídeos / Músicas / Fotos | pastas `Movie`, `Music`, `Photo` |

Dicas: jogos de **Mega Drive** precisam terminar em `.md` (renomeie `.bin` → `.md`). Jogos de **PlayStation** abrem pelo arquivo `.cue` (o `.bin` fica escondido ao lado).

## 4. Personalizar mais

- **Mudar um texto** (botões, dicas…): edite `r36skit/data/strings/pt-BR.json` (ou seu idioma) e gere de novo. Mantenha curto – as caixas são pequenas.
- **Novo idioma:** copie `en.json` para `es.json`, traduza os valores (não os nomes à esquerda) e use `language = "es"`. Letras fora do alfabeto latino básico precisam de uma fonte que as tenha: coloque em `my_files/font.ttf` e use `font = "my_files/font.ttf"`.
- **Caixa de dicas:** edite `"tips"` → `"lines"` no arquivo de idioma (até 2 linhas).
- **Desligar um recurso:** `[features]` no `config.toml`.

## 5. Problemas comuns

| Problema | Solução |
|---|---|
| `python` não é reconhecido | Reinstale o Python marcando *Add python.exe to PATH*; abra a janela de novo |
| *Não encontrei o rkgame* | `stock/` precisa conter `cubegm/rkgame` (copie a pasta do cartão) |
| *rkgame não é a versão suportada* | Seu firmware é outro ou já foi modificado. Use a cópia **original**. Veja [COMPATIBILIDADE](COMPATIBILIDADE.md) |
| O aparelho mostra o menu antigo | Os arquivos não foram substituídos. Copie de novo com *Substituir* |
| Imagem estranha/preta | Use JPG/PNG comum; confira `output/preview` antes |
| O aparelho não liga | Copie de volta o backup do cartão (por isso você fez) |
| Jogo sem capa | O nome da capa deve ser igual ao do arquivo do jogo, `.png`, 240×240, em `roms/images` |
| O `.bin` de um jogo de PlayStation aparece | Ligue `hide_bin_files` no `config.toml` |
