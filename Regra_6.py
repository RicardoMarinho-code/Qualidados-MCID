import pandas as pd


def regra_6(df):
    """
    Regra 6:
    As colunas

    - mcmv_ogu_08_txt_nome_construtora_entidade
    - mcmv_ogu_09_txt_cnpj_construtora_entidade
    - mcmv_ogu_10_txt_nome_empreendimento

    não podem conter os valores:

    #N/D, #NOME?, #VALOR!, #REF! ou #DIV/0!
    """

    resultado = df.copy()

    termos_invalidos = [
        "#N/D",
        "#NOME?",
        "#VALOR!",
        "#REF!",
        "#DIV/0!"
    ]

    colunas = [
        "mcmv_ogu_08_txt_nome_construtora_entidade",
        "mcmv_ogu_09_txt_cnpj_construtora_entidade",
        "mcmv_ogu_10_txt_nome_empreendimento"
    ]

    condicao = pd.Series(True, index=resultado.index)

    for coluna in colunas:
        contem_termo_invalido = (
            resultado[coluna]
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(termos_invalidos)
        )

        condicao &= ~contem_termo_invalido

    resultado["Resultado_Teste_Regra_6"] = condicao.map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado