import pandas as pd


def regra_5(df):
    """
    Regra 5:
    O arquivo deve conter todos os campos presentes na ficha de metadados.

    A lista de campos esperados é obtida da coluna
    "Nome reduzido" da planilha de metadados.

    Caso exista pelo menos um campo ausente, todas as linhas
    recebem "Insucesso". Caso contrário, recebem "Sucesso".
    """

    resultado = df.copy()

    # Lê a ficha de metadados
    metadados = pd.read_excel(
        "202507_mcmv_ogu_contratacao_metadados 2.xlsx",
        sheet_name=1
    )
    
    # Remove espaços dos nomes das colunas
    metadados.columns = metadados.columns.str.strip()

    # Obtém os nomes das colunas esperadas
    colunas_esperadas = (
        metadados["Nome reduzido"]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "NaN", "None"], pd.NA)
        .dropna()
        .tolist()
    )

    # Colunas existentes no CSV
    colunas_csv = (
        pd.Index(df.columns)
        .astype(str)
        .str.strip()
        .tolist()
    )

    # Verifica quais colunas estão faltando
    colunas_faltando = [
        coluna
        for coluna in colunas_esperadas
        if coluna not in colunas_csv
    ]

    # Preenche a coluna de resultado
    if len(colunas_faltando) == 0:
        resultado["Resultado_Teste_Regra_5"] = "Sucesso"
        print("Regra 5: Todas as colunas da ficha de metadados estão presentes.")
    else:
        resultado["Resultado_Teste_Regra_5"] = "Insucesso"

        print("\nRegra 5: Colunas ausentes encontradas:")
        for coluna in colunas_faltando:
            print(f" - {coluna}")

    return resultado