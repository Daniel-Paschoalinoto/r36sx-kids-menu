# Compatibilidade

🇬🇧 [English](../en/COMPATIBILITY.md)

## O que foi testado

| | |
|---|---|
| Aparelho | Clone estilo "R36SX V2.6" (também vendido como família SF3000 / SF3500 / GB350 – **não confirmado**), HiChip HC1600A (HC16xx), MIPS32 ~900 MHz, 256 MB, tela 640×480 |
| Sistema | Linux 4.4.186, programa principal `rkgame`, lançador `icube`, pasta `cubegm` no cartão SD |
| SHA-256 do `rkgame` | `57d8b4fd85e0aab44d17a51d209879c3f98130d066b622142736b42ad08ddcb9` (1.178.732 bytes) |

Tudo foi testado em aparelho real, nessa única versão. **Outros modelos ou versões de firmware não foram testados.**

## Como a ferramenta protege você

As alterações de código foram escritas para exatamente esse `rkgame`. Antes de mudar qualquer coisa a ferramenta confere o SHA-256 do arquivo e cada byte que vai trocar. Se algo for diferente ela **para e não altera nada**. Ela nunca grava no seu cartão SD – você copia o resultado.

## Confira o seu

```bash
python build.py --check
```

- `OK` → suportado.
- `rkgame não é a versão suportada` → ou é outro firmware (ainda sem suporte) ou o arquivo já foi modificado. Use o `cubegm` **original** (um backup novo).

## Outros modelos

Os clones são parecidos mas vêm com firmwares diferentes. Se o seu tem pasta `cubegm` e arquivo `rkgame` ele *pode* ser parecido, mas outra versão exige reencontrar os endereços do código (engenharia reversa). Se você fizer isso, abra uma issue ou pull request – veja [COMO-FUNCIONA](COMO-FUNCIONA.md).

**Relatar seu modelo:** abra uma issue com o modelo "compatibility" e cole a saída de `python build.py --check` (ela mostra o SHA-256 do seu `rkgame`).
