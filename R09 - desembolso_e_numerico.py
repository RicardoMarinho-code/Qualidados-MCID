import pandas as pd


def regra_9(df):
    """
    Regra 9:
    mcmv_ogu_33_vlr_desembolsado_no_ano_dt_referencia
    deve conter um valor numérico.

    Valores nulos, vazios ou inválidos são tratados como 0.
    """

    resultado = df.copy()

    coluna = (
        resultado["mcmv_ogu_33_vlr_desembolsado_no_ano_dt_referencia"]
        .astype(str)
        .str.strip()
    )

    # Considera nulos e vazios como 0
    coluna = coluna.replace(["", "nan", "NaN", "None"], "0")

    valor = pd.to_numeric(
        coluna.str.replace(".", "", regex=False)
              .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    resultado["Resultado_Teste_Regra_9"] = valor.notna().map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado