# Qualidados-MCID

Sistema simples de **qualidade de dados** para a planilha do CDV / MCMV-OGU.
Cada regra de qualidade fica em seu proprio arquivo e o nome da planilha do
governo e configurado via `.env`.

## Instalacao

```bash
pip install -r requirements.txt
```

## Configuracao

Copie o modelo e ajuste o nome da planilha:

```bash
cp .env.example .env
```

`.env`:

```
ARQUIVO_DADOS=Amostra de Dados.csv
ARQUIVO_RELATORIO=relatorio_qualidade.csv
TOLERANCIA_VALOR=1.0
```

> O `.env` esta no `.gitignore` (contem o nome da planilha do governo).

## Uso

```bash
python main.py                       # usa ARQUIVO_DADOS do .env
python main.py "outra planilha.csv"  # sobrescreve o arquivo
```

Saida: resumo no console + `relatorio_qualidade.csv` detalhado
(colunas: `regra; linha; coluna; valor; detalhe`).

## Estrutura

```
.
├── main.py                  # ponto de entrada (CLI + resumo)
├── .env / .env.example      # nome da planilha e parametros
├── requirements.txt
├── R01 - soma_val_contratado_total.py   # uma funcao regra_N(df) por arquivo
├── R02 - distrato_exige_quantidade.py
├── ...                                  # (ver tabela de Regras abaixo)
├── R12 - quantidade_de_vigentes.py
└── qualidade/
    ├── config.py            # le o .env e nomes de colunas
    ├── io_dados.py          # leitura do CSV / gravacao do relatorio
    ├── ocorrencia.py        # dataclass Ocorrencia
    ├── utils.py             # parse de numero BR, normalizacao de nome
    ├── executor.py          # orquestra as regras
    └── regras/              # implementacao em pacote (separada dos R01..R12)
```

## Regras

Cada arquivo `RNN - ...py` contem uma funcao `regra_N(df)` que recebe o
`DataFrame` e devolve uma copia com uma coluna `Resultado_Teste_Regra_N`
marcada como `Sucesso` ou `Insucesso` por linha.

| Arquivo | Descricao |
|---|---|
| `R01 - soma_val_contratado_total.py` | `val_contratado_total` = `val_contratado_original` + `val_aporte_adicional` |
| `R02 - distrato_exige_quantidade.py` | Se `situacao_obra` = distratado, `qtd_distratadas` > 0 |
| `R03 - quantidade_distratadas.py` | Se distratado, `qtd_distratadas` = `qtd_uh` − `qtd_entregues` |
| `R04 - data_termino_ate_referencia.py` | `dt_termino` (se preenchida) ≤ `dt_referencia` |
| `R05 - colunas_da_ficha_presentes.py` | Todos os campos da ficha de metadados existem no arquivo |
| `R06 - marcadores_de_erro.py` | Colunas de texto sem `#N/D`, `#NOME?`, `#VALOR!`, `#REF!`, `#DIV/0!` |
| `R07 - preenchimento_obrigatorio.py` | Campos marcados como obrigatorios na ficha estao preenchidos |
| `R08 - desembolso_ano_ate_total.py` | `desembolsado_no_ano` ≤ `val_desembolsado` |
| `R09 - desembolso_e_numerico.py` | `desembolsado_no_ano` contem valor numerico |
| `R10 - datas_dentro_do_intervalo.py` | Datas entre `01/01/2009` e `dt_referencia` |
| `R11 - entregues_ate_unidades.py` | `qtd_entregues` ≤ `qtd_uh` |
| `R12 - quantidade_de_vigentes.py` | `qtd_vigentes` = `qtd_uh` − `qtd_entregues` − `qtd_distratadas` |

> Valores nulos, vazios ou invalidos sao tratados como `0` nas regras numericas.
> Datas nao preenchidas sao consideradas `Sucesso` nas regras de data.

## Como adicionar uma nova regra

1. Crie um arquivo `RNN - descricao.py` com uma funcao `regra_N(df)` que
   recebe o `DataFrame` e devolve uma copia com a coluna
   `Resultado_Teste_Regra_N` (`Sucesso` / `Insucesso`).
2. Siga o padrao dos arquivos existentes para conversao de numeros (BR) e datas.
