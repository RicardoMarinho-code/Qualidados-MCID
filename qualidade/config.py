# -*- coding: utf-8 -*-
"""Configuracao central do sistema de qualidade de dados.

O nome da planilha do governo NAO fica fixo no codigo: e lido do arquivo .env
(variavel ARQUIVO_DADOS). Use o .env.example como modelo.
"""

import os
from dotenv import load_dotenv

# Carrega variaveis do arquivo .env (se existir).
load_dotenv()

# --------------------------------------------------------------------------- #
# Parametros vindos do ambiente (.env)
# --------------------------------------------------------------------------- #
ARQUIVO_DADOS = os.getenv("ARQUIVO_DADOS", "Amostra de Dados.csv")
ARQUIVO_RELATORIO = "relatorio_qualidade.csv"
TOLERANCIA_VALOR = float(os.getenv("TOLERANCIA_VALOR", "1.0"))

# Delimitador do CSV.
DELIMITADOR = ";"
# --------------------------------------------------------------------------- #
# Nomes das colunas relevantes (conforme cabecalho do arquivo)
# --------------------------------------------------------------------------- #
COL_NOME_EMPREENDIMENTO = "mcmv_ogu_10_txt_nome_empreendimento"
COL_VAL_ORIGINAL = "mcmv_ogu_18_val_contratado_original"
COL_VAL_APORTE = "mcmv_ogu_19_val_aporte_adicional"
COL_VAL_TOTAL = "mcmv_ogu_20_val_contratado_total"
COL_BLN_VIGENTE = "mcmv_ogu_36_bln_vigente"
COL_BLN_NOVO_MCMV = "mcmv_ogu_37_bln_novo_mcmv"
COL_QTD_ENTREGUES_2023 = "mcmv_ogu_38_qtd_entregues_2023"

# Valores aceitos para colunas booleanas.
VALORES_BOOLEANOS = {"sim", "nao", "não"}
