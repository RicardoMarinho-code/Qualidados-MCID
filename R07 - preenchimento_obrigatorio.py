import pandas as pd


def regra_7(df):
    """
    Regra 7:
    Os campos marcados como obrigatórios na ficha de metadados
    devem estar preenchidos.

    A obrigatoriedade é definida pela coluna
    "Obrigatoriedade de preenchimento" = "Sim".

    Para cada campo obrigatório é criada uma coluna de resultado,
    indicando "Sucesso" ou "Insucesso".
    """

    resultado = df.copy()

    # Lê a ficha de metadados
    metadados = pd.read_excel(
        "202507_mcmv_ogu_contratacao_metadados 2.xlsx",
        sheet_name=1
    )

    # Remove espaços dos nomes das colunas
    metadados.columns = metadados.columns.str.strip()

    # Obtém as colunas obrigatórias
    colunas_obrigatorias = (
        metadados.loc[
            metadados["Obrigatoriedade de preenchimento"]
            .astype(str)
            .str.strip()
            .str.upper() == "SIM",
            "Nome reduzido"
        ]
        .astype(str)
        .str.strip()
        .tolist()
    )

    # Valida cada coluna obrigatória
    for coluna in colunas_obrigatorias:

        nome_resultado = f"Resultado_Teste_Regra_7_{coluna}"

        # Caso a coluna não exista no arquivo
        if coluna not in resultado.columns:
            resultado[nome_resultado] = "Insucesso"
            print(f"Coluna obrigatória não encontrada: {coluna}")
            continue

        preenchido = (
            resultado[coluna].notna()
            &
            (
                resultado[coluna]
                .astype(str)
                .str.strip()
                != ""
            )
        )

        resultado[nome_resultado] = preenchido.map({
            True: "Sucesso",
            False: "Insucesso"
        })

    return resultado