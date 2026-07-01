import pandas as pd
import os
import importlib.util
import re
from datetime import datetime
from dateutil import parser
import operator
from typing import Union, List
from Biblioteca.funcao_importacao import importa_conjunto_conforme_catalogo

def testar_se_valores_da_coluna_estao_num_intervalo(
    df: pd.DataFrame, 
    coluna: str, 
    min: float, 
    max: float, 
    nome_regra: str,
    nome_teste: str, 
    condicao_na_linha: str = None, 
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    
    """
    Verifica se os valores de uma coluna numérica estão dentro de um intervalo [min, max].
    
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna a ser testada.
    min : float
        Valor mínimo do intervalo (inclusivo).
    max : float
        Valor máximo do intervalo (inclusivo).
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída).
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x > 0"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.
    
    Retorna:
    --------
    bool
        True se os valores estiverem dentro do intervalo (ou dentro da tolerância); False caso contrário.
    
    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parametro nome_regra;
        - nome_coluna - que contém o parâmetro coluna; e
        - resultado_teste -  esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro 'condicao_na_linha', se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou preenchido com "", "None", "nan", "NaN", "NAN", "null", "NULL" ou "Null";
 
    
    Exemplo:
    --------
    >>> df = pd.DataFrame({"UH Entregues": [25, None, 35, 200], "Modalidade": ["FAR", "FAR", "Rural", "FAR]})
    >>> testar_se_valores_da_coluna_estao_num_intervalo(
    ...     df=df, 
    ...     coluna = "UH Entregues",
    ...     min = 1,
    ...     max = 100, 
    ...     nome_regra = "RTQD001", 
    ...     nome_teste = "teste_intervalo_1_a_100",
    ...     condicao_na_linha = "Modalidade == 'FAR'",
    ...     tolerancia_com_insucesso_admitida=0.)
    ...
    >>> print(f"Resultado do Teste de {RTQD} na Coluna {coluna_testada} é:{teste_obtido}")
    >>> print(f"Dataframe com resultado do teste, linha a linha, salvo em Dados/output")
    ...
    Resultado do Teste de RTQD001 na Coluna UH Entregues é:False
    Dataframe com resultado do teste, linha a linha, salvo em Dados/output

    UH Entregues   |   Modalidade   |   regra_testada   |   nome_coluna   |   resultado_teste
    -----------------------------------------------------------------------------------------
    25             |   FAR          |   RTQD001         |   UH Entregues  |   Sucesso
    None           |   FAR          |   RTQD001         |   UH Entregues  |   Em branco
    35             |   Rural        |   RTQD001         |   UH Entregues  |   Não avaliado
    200            |   FAR          |   RTQD001         |   UH Entregues  |   Insucesso
    """

    
    # Qual a lógica da programação usada nesta função
    #   1) Ela define várias funções internas para testar os parâmetros;
    #   2) Ela define várias funções internas para testar executar o teste, que envolve basicamente:
    #      a) Testar os parametros;
    #      b) Filtra as linhas, se o parametro condiçao_na_linha foi informado;
    #      c) Aplica o teste nas linhas filtradas, marcando as linhas com sucesso e insucesso (ou 'não avaliado', quando há o parametro condicao_na_linha);
    #      d) Salva um dataframe com o resultado do teste no repositório, na pasta \Dados\output, tendo nele uma coluna com o parametro nome_regra, com as marcações de sucesso, insucesso e 'não avaliado';
    #      e) Calcula o percentual de insucesso e verifica se é menor ou igual a tolerância;
    #      f) Retorna True ou False, conforme o percentual de insucesso e a tolerância admitida.


    
    
    # Inicializa a variável que será retornada no final pela funçao
    Resultado_Teste: bool = None

    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS 
    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")
        
    def checar_se_valor_min_eh_menor_que_valor_max() -> None:
        if min > max:
            raise ValueError(f"Erro: O valor mínimo '{min}' não pode ser maior que o valor máximo '{max}'.")
    
    def checar_se_coluna_existe() -> None:
        if coluna not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame.")
    
    def checar_se_coluna_eh_numerica() -> None:
        try:
            # Attempt to convert the coluna to numeric with errors='raise'
            pd.to_numeric(df[coluna], errors='raise')
        except Exception as e:
            # Raise a custom error if the coluna contains non-numeric values
            raise ValueError(f"Erro ao verificar se a coluna '{coluna}' contém apenas valores numéricos: {e}")
    
    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' deve ser uma string.")   
         # Verifica se nome_coluna_regra é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")
    
        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")   
         # Verifica se nome_teste é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")
    

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if (tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1):
                raise ValueError("Erro: Parâmetro 'A 'tolerância com insucesso admitida' deve estar entre 0 e 1.")  



    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            # Permitir apenas caracteres alfanuméricos, espaços, operadores de comparação e operadores lógicos
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            
            if not re.match(padrao_permitido, condicao_na_linha):
                checagem_condicao_na_linha: bool = False
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos. Use apenas letras, espaços, algarismos e operadores lógicos ou de concatenação de strings.")
            else:
                checagem_condicao_na_linha= True
            
            
            return checagem_condicao_na_linha


    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_valor_min_eh_menor_que_valor_max()
        checar_se_coluna_existe()
        checar_se_coluna_eh_numerica()
        checar_se_nome_regra_e_nome_teste_sao_string()
        checar_se_condicao_na_linha_eh_query_permitida()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()
    
  


  # FUNÇÕES INTERNAS PARA EXECUTAR O TESTE 

    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            if checar_se_condicao_na_linha_eh_query_permitida()==True:  
                try:
                    return df.query(condicao_na_linha).copy()
                except Exception as e:
                    raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")   
                
            else:
                raise ValueError("Erro: Condição na linha deve ser uma string.")
        else:
            return df.copy()    
  
  
    def aplicar_sucesso_e_insucesso_conforme_intervalo() -> pd.DataFrame:

        # Define 'linhas_para_testar' filtrando o dataframe
        df_linhas_para_testar: pd.DataFrame = obter_dataframe_conforme_condicao_na_linha()
        
        # Definindo o que são valores em branco
        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]
        
        #  Aplicando à coluna resultado_teste insucessos/sucessos apenas às linhas que serão avaliadas pela função, conforme parametro condicao_na_linha
        for index, row in df_linhas_para_testar.iterrows():
            if str(row[coluna]).strip() in valores_em_branco or row[coluna] is None:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Em branco"
            elif row[coluna] < min or row[coluna] > max:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Insucesso"
            else:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Sucesso"



        
        # Preparando o dataframe que será salvo pela função
        df_resultado_teste: pd.DataFrame = df.copy()
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado_teste["nome_coluna"] = coluna
        # Adicionando coluna chamada resultado_teste, inicialmente configurada como "Não avaliado
        df_resultado_teste["resultado_teste"] = "Não avaliado"
        
       
        df_resultado_teste.loc[df_linhas_para_testar.index, "resultado_teste"] = df_linhas_para_testar["resultado_teste"]
        
        # Cria dataframe e salva no repositorio o resultado do teste
       
        try:
            df_resultado_teste.to_csv(f'Dados/output/Resultado_{nome_regra}_Coluna_{coluna}_{nome_teste}.csv', index=False, sep=';', encoding='utf_8_sig')
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return  df_resultado_teste    # Retorna True ou False  
        
        
    def obter_percentual_insucesso_conforme_intervalo(resultado: pd.DataFrame) -> float:
        
        percentual_de_insucesso: float = resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)

        return percentual_de_insucesso
        
        
    
    # EXECUTANDO O TESTE 

    rodar_testes_de_parametros()
    df_dataframe_resultado_teste: pd.DataFrame = aplicar_sucesso_e_insucesso_conforme_intervalo()
    percentagem_de_insucesso: float = obter_percentual_insucesso_conforme_intervalo(df_dataframe_resultado_teste)
    
    if percentagem_de_insucesso == 0:
        Resultado_Teste = True
    else:
        Resultado_Teste= False 
    
    if tolerancia_com_insucesso_admitida is not None:
        if percentagem_de_insucesso >= tolerancia_com_insucesso_admitida:
            Resultado_Teste = True
        else:
            Resultado_Teste =  False


    
    return Resultado_Teste

def testar_preenchimento_coluna(
    df: pd.DataFrame,
    coluna: str,
    nome_regra: str,
    nome_teste: str,
    valores_em_branco_adicionais: list = None,  # NOVO parâmetro: permite adicionar mais valores considerados "em branco"
    condicao_na_linha: str = None               # NOVO parâmetro: permite aplicar a verificação apenas a parte do DataFrame
) -> bool:
    """
    Verifica se os valores de uma coluna estão preenchidos, considerando também valores em branco adicionais.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna a ser testada quanto ao preenchimento.
    nome_regra : str
        Identificador da regra de qualidade de dados, usado no nome do arquivo de saída.
    nome_teste : str
        Nome descritivo do teste, também usado no nome do arquivo de saída.
    valores_em_branco_adicionais : list, opcional
        Lista com valores extras a serem considerados como "em branco" além dos padrões conhecidos.
    condicao_na_linha : str, opcional
        Condição a ser aplicada nas linhas antes da avaliação (ex: "Modalidade == 'FAR'").
        Se None, o teste será aplicado em todas as linhas.

    Retorno
    -------
    bool
        True se todos os valores obrigatórios estiverem preenchidos (incluindo as regras de condição e brancos adicionais);
        False caso contrário.

    Efeitos Colaterais
    ------------------
    - Salva um arquivo CSV em 'Dados/output' com o resultado linha a linha.
    - O DataFrame de saída contém todas as colunas originais mais três:
        - 'regra_testada': com o valor de nome_regra;
        - 'nome_coluna': com o nome da coluna testada;
        - 'resultado_teste':
            - 'Sucesso' se a célula estiver preenchida;
            - 'Em branco' se a célula for vazia ou corresponder a qualquer valor em branco;
            - 'Não avaliado' se a linha não atender à condicao_na_linha (caso ela tenha sido especificada).

    Exemplo
    -------
    >>> df = pd.DataFrame({"UH Entregues": [25, None, 35, 200], "Modalidade": ["FAR", "FAR", "Rural", "FAR"]})
    >>> testar_preenchimento_coluna(
    ...     df=df,
    ...     coluna="UH Entregues",
    ...     nome_regra="RTQD001",
    ...     nome_teste="verifica_preenchimento",
    ...     valores_em_branco_adicionais=["0"],
    ...     condicao_na_linha="Modalidade == 'FAR'"
    ... )
    Resultado do Teste: False
    (arquivo salvo: Dados/output/Resultado_RTQD001_Coluna_UH_Entregues_verifica_preenchimento.csv)

    Resultado (exemplo de saída):
    UH Entregues | Modalidade | regra_testada | nome_coluna  | resultado_teste
    --------------------------------------------------------------------------
    25           | FAR        | RTQD001       | UH Entregues | Sucesso
    None         | FAR        | RTQD001       | UH Entregues | Em branco
    35           | Rural      | RTQD001       | UH Entregues | Não avaliado
    200          | FAR        | RTQD001       | UH Entregues | Sucesso
    """

    Resultado_Teste: bool = None

    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_coluna_existe() -> None:
        if coluna not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame.")

    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' deve ser uma string.")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' não é um nome válido.")
        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido.")

    # NOVA função: Valida se a string da condição (filtro) tem caracteres permitidos
    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            padrao = r"^[\w\s`><=!&|()\"'./-]+$"
            if not re.match(padrao, condicao_na_linha):
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos.")
            return True
        return False

    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_coluna_existe()
        checar_se_nome_regra_e_nome_teste_sao_string()
        if condicao_na_linha is not None:
            checar_se_condicao_na_linha_eh_query_permitida()

    # NOVA função: se condicao_na_linha for passada, aplica filtro no DataFrame
    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            return df.query(condicao_na_linha).copy()
        return df.copy()

    # Função PRINCIPAL que realiza o teste
    def aplicar_teste_preenchimento() -> pd.DataFrame:
        df_teste = obter_dataframe_conforme_condicao_na_linha()

        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

        if valores_em_branco_adicionais:
            valores_em_branco = valores_em_branco + valores_em_branco_adicionais

        for idx, row in df_teste.iterrows():
            val = row[coluna]
            if val is None or str(val).strip() in valores_em_branco:
                df_teste.at[idx, "resultado_teste"] = "Em branco"
            else:
                df_teste.at[idx, "resultado_teste"] = "Sucesso"

        df_result = df.copy()
        df_result["regra_testada"] = nome_regra
        df_result["nome_coluna"] = coluna
        df_result["resultado_teste"] = "Não avaliado"  # Todas começam como "Não avaliado"
        df_result.loc[df_teste.index, "resultado_teste"] = df_teste["resultado_teste"]

        try:
            df_result.to_csv(
                f'Dados/output/Resultado_{nome_regra}_Coluna_{coluna}_{nome_teste}.csv',
                index=False, sep=';', encoding='utf_8_sig'
            )
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return df_result

    rodar_testes_de_parametros()

    df_res = aplicar_teste_preenchimento()

    insucesso = df_res["resultado_teste"].value_counts(normalize=True).get("Em branco", 0)

    Resultado_Teste = (insucesso == 0)

    return Resultado_Teste

def testar_comparacao_colunas(
    df: pd.DataFrame,
    coluna1: str,
    coluna2: str,
    expressao: str,
    nome_regra: str,
    nome_teste: str,
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores de duas colunas são equivalentes com base em uma expressão lógica.
    
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna1 : str
        Nome da primeira coluna a ser comparada.
    coluna2 : str
        Nome da segunda coluna a ser comparada.
    expressao : str
        Operador lógico para comparar os valores (==, !=, >, <, >=, <=).
    nome_regra : str
        Nome da regra de validação.
    nome_teste : str
        Nome do teste específico.
    condicao_na_linha : str, opcional
        Expressão de filtro a ser aplicada ao DataFrame.
    tolerancia_com_insucesso_admitida : float, opcional
        Tolerância (de 0 a 1) de insucesso aceitável.

    Retorno:
    --------
    bool
        True se o percentual de insucesso estiver dentro da tolerância; False caso contrário.
    """

    resultado_geral_teste: bool = False

    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_colunas_existem() -> None:
        if coluna1 not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna1}' não encontrada no DataFrame.")
        if coluna2 not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna2}' não encontrada no DataFrame.")

    def checar_se_nome_regra_e_nome_teste_sao_string_e_validos() -> None:
        if not isinstance(nome_regra, str) or not nome_regra:
            raise ValueError("Erro: O Parâmetro 'nome_regra' deve ser uma string não vazia.")  
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_regra' não é um nome válido.")
    
        if not isinstance(nome_teste, str) or not nome_teste:
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string não vazia.")  
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if not isinstance(tolerancia_com_insucesso_admitida, (int, float)):
                raise ValueError("Erro: Parâmetro 'tolerancia_com_insucesso_admitida' deve ser um número.")
            if not (0 <= tolerancia_com_insucesso_admitida <= 1):
                raise ValueError("Erro: Parâmetro 'tolerancia_com_insucesso_admitida' deve estar entre 0 e 1.") 

    def checar_se_expressao_eh_valida() -> None:
        operacoes_validas = ['==', '!=', '>', '<', '>=', '<=']
        if not isinstance(expressao, str) or expressao not in operacoes_validas:
            raise ValueError(f"Erro: Parâmetro 'expressao' ('{expressao}') é inválido. Use um dos seguintes: {operacoes_validas}")

    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if condicao_na_linha is not None:
            if not isinstance(condicao_na_linha, str) or not condicao_na_linha.strip():
                raise ValueError("Erro: 'condicao_na_linha' deve ser uma string de query não vazia se fornecida.")
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            if not re.match(padrao_permitido, condicao_na_linha):
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos ou estrutura inválida.")
        return True

    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_colunas_existem()
        checar_se_expressao_eh_valida()
        checar_se_nome_regra_e_nome_teste_sao_string_e_validos()
        checar_se_condicao_na_linha_eh_query_permitida()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()

    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None and condicao_na_linha.strip():
            try:
                return df.query(condicao_na_linha).copy()
            except Exception as e:
                raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")
        return df.copy()

    def obter_funcao_de_comparacao(nome_expressao: str):
        mapa_de_operadores = {
            '==': operator.eq, '!=': operator.ne,
            '>': operator.gt, '<': operator.lt,
            '>=': operator.ge, '<=': operator.le
        }
        return mapa_de_operadores[nome_expressao]

    rodar_testes_de_parametros()
    df_para_testar = obter_dataframe_conforme_condicao_na_linha()
    op_func = obter_funcao_de_comparacao(expressao)

    df_resultado_parcial = df_para_testar.copy()
    df_resultado_parcial["resultado_teste"] = "Insucesso"
    valores_em_branco_definidos_pelo_usuario = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

    for index, row in df_resultado_parcial.iterrows():
        valor_col1 = row[coluna1]
        valor_col2 = row[coluna2]

        val1_em_branco = pd.isna(valor_col1) or str(valor_col1).strip() in valores_em_branco_definidos_pelo_usuario
        val2_em_branco = pd.isna(valor_col2) or str(valor_col2).strip() in valores_em_branco_definidos_pelo_usuario

        if val1_em_branco or val2_em_branco:
            df_resultado_parcial.at[index, "resultado_teste"] = "Em branco"
        else:
            try:
                if op_func(valor_col1, valor_col2):
                    df_resultado_parcial.at[index, "resultado_teste"] = "Sucesso"
                else:
                    df_resultado_parcial.at[index, "resultado_teste"] = "Insucesso"
            except TypeError:
                df_resultado_parcial.at[index, "resultado_teste"] = "Erro de Tipo"
            except Exception:
                df_resultado_parcial.at[index, "resultado_teste"] = "Erro na Comparacao"

    df_final_com_resultados = df.copy()
    df_final_com_resultados["nome_coluna"] = coluna1
    df_final_com_resultados["regra_testada"] = nome_regra

    if "resultado_teste" not in df_final_com_resultados.columns:
        df_final_com_resultados["resultado_teste"] = "Não Aplicável"

    df_final_com_resultados.loc[df_resultado_parcial.index, "resultado_teste"] = df_resultado_parcial["resultado_teste"]

    try:
        nome_arquivo = f'Dados/output/Resultado_{nome_regra}_{nome_teste}.csv'
        df_final_com_resultados.to_csv(nome_arquivo, index=False, sep=';', encoding='utf_8_sig')
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

    total_testado = df_resultado_parcial["resultado_teste"].count()
    total_insucesso = (df_resultado_parcial["resultado_teste"] == "Insucesso").sum()

    percentual_insucesso = total_insucesso / total_testado if total_testado > 0 else 0

    if percentual_insucesso == 0:
        resultado_geral_teste = True
    elif tolerancia_com_insucesso_admitida is not None:
        resultado_geral_teste = percentual_insucesso <= tolerancia_com_insucesso_admitida

    return resultado_geral_teste

def testar_datas_da_coluna_estao_num_intervalo(
    df: pd.DataFrame,
    coluna: str,
    data_inicial: str,
    data_final: str,
    nome_regra: str,
    nome_teste: str,
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores de uma coluna de datas estão dentro de um intervalo [data_inicial, data_final].
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna de datas a ser testada.
    data_inicial : str
        Data mínima do intervalo (inclusiva), no formato 'DD-MM-AAAA'.
    data_final : str
        Data máxima do intervalo (inclusiva), no formato 'DD-MM-AAAA'.
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída).
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x > 0"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.
    Retorna:
    --------
    bool
        True se os valores estiverem dentro do intervalo (ou dentro da tolerância); False caso contrário.
    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada
        - nome_coluna
        - resultado_teste
        exemplo:
    Data de Contratação | Modalidade | regra_testada | nome_coluna         | nome_teste                        | resultado_teste
    -----------------------------------------------------------------------------------------------------------------------------
    28/12/2010          | FAR        | RTQD021       | Data de Contratação | teste_completude_data_contratacao | Sucesso
    29/12/2010          | FAR        | RTQD021       | Data de Contratação | teste_completude_data_contratacao | Sucesso
    None                | FAR        | RTQD021       | Data de Contratação | teste_completude_data_contratacao | Em branco
    27/06/2011          | RURAL      | RTQD021       | Data de Contratação | teste_completude_data_contratacao | Não avaliado
    """

    Resultado_Teste: bool = None

    def checar_parametros():
        if df.empty:
            raise ValueError('Erro: DataFrame está vazio.')
        if coluna not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame.")
        try:
            pd.to_datetime(data_inicial, dayfirst=True)
            pd.to_datetime(data_final, dayfirst=True)
        except Exception as e:
            raise ValueError(f"Erro ao converter data_inicial ou data_final: {e}")  # Adicionado

        if pd.to_datetime(data_inicial, dayfirst=True) > pd.to_datetime(data_final, dayfirst=True):
            raise ValueError("Erro: data_inicial não pode ser maior que data_final.")  # Adicionado

        if not isinstance(nome_regra, str) or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: nome_regra inválido.")

        if not isinstance(nome_teste, str) or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: nome_teste inválido.")

        if tolerancia_com_insucesso_admitida is not None:
            if tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1:
                raise ValueError("Erro: tolerancia_com_insucesso_admitida deve estar entre 0 e 1.")

        if condicao_na_linha is not None:
            if not re.match(r"[a-zA-Z0-9_ ><=>=!&|()\"']+$", condicao_na_linha):
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos.")

    def obter_dataframe_filtrado():
        if condicao_na_linha:
            try:
                return df.query(condicao_na_linha).copy()
            except Exception as e:
                raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")
        return df.copy()

    def aplicar_teste():
        df_filtrado = obter_dataframe_filtrado()
        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

        data_ini = pd.to_datetime(data_inicial, dayfirst=True)
        data_fim = pd.to_datetime(data_final, dayfirst = True)

        for idx, row in df_filtrado.iterrows():
            valor = row[coluna]
            formatos_possiveis = [
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S"
            ]

            try:
                if pd.isnull(valor) or str(valor).strip() in valores_em_branco:
                    df_filtrado.at[idx, "resultado_teste"] = "Em branco"
                    continue

                data_valor = None
                for formato in formatos_possiveis:
                    try:
                        data_valor = datetime.strptime(str(valor).strip(), formato)
                        break
                    except:
                        continue

                if data_valor is None:
                    try:
                        data_valor = parser.parse(str(valor).strip(), dayfirst=True)
                    except:
                        df_filtrado.at[idx, "resultado_teste"] = "Insucesso"
                        continue

                if not (data_ini <= data_valor <= data_fim):
                    df_filtrado.at[idx, "resultado_teste"] = "Insucesso"
                else:
                    df_filtrado.at[idx, "resultado_teste"] = "Sucesso"

            except:
                df_filtrado.at[idx, "resultado_teste"] = "Em branco"

        df_resultado = df.copy()
        df_resultado["regra_testada"] = nome_regra
        df_resultado["nome_coluna"] = coluna
        df_resultado["resultado_teste"] = "Não avaliado"
        df_resultado.loc[df_filtrado.index, "resultado_teste"] = df_filtrado["resultado_teste"]

        try:
            df_resultado.to_csv(f"Dados/output/Resultado_{nome_regra}_{nome_teste}.csv", index=False, sep=';', encoding='utf_8_sig')
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return df_resultado

    checar_parametros()
    df_resultado = aplicar_teste()
    percentual_insucesso = df_resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)

    if tolerancia_com_insucesso_admitida is None:
        Resultado_Teste = percentual_insucesso == 0
    else:
        Resultado_Teste = percentual_insucesso <= tolerancia_com_insucesso_admitida


    return Resultado_Teste

def testar_se_valores_da_coluna_sao_positivos(
    df: pd.DataFrame, 
    coluna: str, 
    nome_regra: str,
    nome_teste: str, 
    condicao_na_linha: str = None, 
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores de uma coluna numérica são positivos (> 0), considerando
    uma condição opcional para filtrar as linhas e uma tolerância de insucesso opcional.
    parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna a ser testada.
    nome_regra : str
        Nome da regra de validação (usado no relatório e saída).
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar as linhas antes do teste (ex: "idade > 18"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.
    Retorna:
    --------
    bool
        True se os valores forem positivos (ou dentro da tolerância); False caso contrário.
    Efeitos Colaterais:
    -------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do DataFrame original;
    - Adiciona três colunas ao DataFrame:
        - 'regra_testada': contém o valor de 'nome_regra';
        - 'nome_coluna': contém o valor de 'coluna';
        - 'resultado_teste': com valores:
            - 'Sucesso' ou 'Insucesso', para linhas avaliadas;
            - 'Não avaliado', para linhas fora da condição (caso 'condicao_na_linha' seja usada) ou quando o valor numérico for zero;
            - 'Em branco', para valores faltantes ou inválidos como "", "None", "nan", "null", etc.
    Exemplo de uso:
    ---------------
    >>> import pandas as pd
    >>> from Biblioteca.Valores_sao_positivos import testar_se_valores_da_coluna_sao_positivos
    >>> df = pd.DataFrame({
    ...     'idade': [25, 0, -3, 18, None],
    ...     'ativo': [True, False, True, True, False]
    ... })
    >>> resultado = testar_se_valores_da_coluna_sao_positivos(
    ...     df=df,
    ...     coluna='idade',
    ...     nome_regra='idade_positiva',
    ...     nome_teste='teste_idade',
    ...     condicao_na_linha='ativo == True',
    ...     tolerancia_com_insucesso_admitida=0.25
    ... )
    >>> print(resultado)
    
    Exemplo:
--------
>>> df = pd.DataFrame({
...     "UH Entregues": [25, None, 35, 0],
...     "Modalidade": ["FAR", "FAR", "Rural", "FAR"]
... })
>>> testar_se_valores_da_coluna_sao_positivos(
...     df,
...     "UH Entregues",
...     "RTQD028",
...     "teste_completude_uh_entregues",
...     condicao_na_linha="Modalidade == 'FAR'",
...     tolerancia_com_insucesso_admitida=0
... )
Resultado do Teste de RTQD028 na Coluna UH Entregues é: True  
E o dataframe com resultado do teste, linha a linha, terá:
    UH Entregues | Modalidade | regra_testada | nome_coluna   | nome_teste                     | resultado_teste
    --------------------------------------------------------------------------------------------------------------
    25           | FAR        | RTQD028       | UH Entregues  | teste_completude_uh_entregues | Sucesso
    None         | FAR        | RTQD028       | UH Entregues  | teste_completude_uh_entregues | Em branco
    35           | Rural      | RTQD028       | UH Entregues  | teste_completude_uh_entregues | Não avaliado
    0            | FAR        | RTQD028       | UH Entregues  | teste_completude_uh_entregues | Não avaliado
    """

    # Funções auxiliares movidas para dentro da função principal
    def checar_se_coluna_existe(df, coluna):
        if coluna not in df.columns:
            raise ValueError(f"A coluna '{coluna}' não existe no DataFrame.")
    if not isinstance(nome_teste, str):
        raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
        raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica(tolerancia_com_insucesso_admitida):
        if tolerancia_com_insucesso_admitida is not None and not isinstance(tolerancia_com_insucesso_admitida, (int, float)):
            raise TypeError("A tolerância deve ser um número ou None.")

    def checar_se_condicao_na_linha_eh_query_permitida(condicao_na_linha: str) -> bool:
        if isinstance(condicao_na_linha, str):
            # Permitir apenas caracteres alfanuméricos, espaços, operadores de comparação e operadores lógicos
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"

            if not re.match(padrao_permitido, condicao_na_linha):
                raise ValueError(
                    "Erro: Condição na linha contém caracteres não permitidos. "
                    "Use apenas letras, espaços, algarismos e operadores lógicos ou de concatenação de strings."
                )
            return True
        else:
            raise TypeError("A condição deve ser uma string.")

    def checar_se_coluna_eh_numerica(df, coluna):
        if not pd.api.types.is_numeric_dtype(df[coluna]):
            raise TypeError(f"A coluna '{coluna}' não é numérica.")

    def obter_dataframe_conforme_condicao_na_linha(df, condicao):
        if condicao is None:
            return df
        try:
            return df.query(condicao)
        except Exception as e:
            print(f"Erro ao aplicar a condição: {e}")
            return df

    # Executa testes de parâmetros
    checar_se_coluna_existe(df, coluna)

    def checar_se_nome_regra_e_nome_teste_sao_string(nome_regra, nome_teste) -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' deve ser uma string.")   
         # Verifica se nome_coluna_regra é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

    # Inicializa a coluna resultado_teste com 'Não avaliado'
    df_resultado_teste = df.copy()
    df_resultado_teste['resultado_teste'] = 'Não avaliado'

    # Lista de valores inválidos a serem tratados como 'Em branco'
    valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null", "-"]

    # Obtém o DataFrame filtrado conforme condicao_na_linha
    df_filtrado = obter_dataframe_conforme_condicao_na_linha(df, condicao_na_linha)
    linhas_avaliadas = df_filtrado.index

    # Converte a coluna para numérico, marcando valores não conversíveis como NaN
    df_coluna = pd.to_numeric(df_filtrado[coluna], errors='coerce')

    # Marca valores nulos ou inválidos como 'Em branco'
    mask_em_branco = df_coluna.isna() | df_filtrado[coluna].isin(valores_em_branco)
    df_resultado_teste.loc[linhas_avaliadas[mask_em_branco], 'resultado_teste'] = 'Em branco'

    # Marca valores numéricos como 'Sucesso', 'Insucesso' ou 'Não avaliado' (zero)
    mask_numericos = ~mask_em_branco
    df_resultado_teste.loc[linhas_avaliadas[mask_numericos], 'resultado_teste'] = df_coluna[mask_numericos].apply(
        lambda x: 'Sucesso' if x > 0 else ('Não avaliado' if x == 0 else 'Insucesso')
    )

    # Calcula a proporção de insucessos
    mask_avaliadas = df_resultado_teste['resultado_teste'].isin(['Sucesso', 'Insucesso'])
    total_avaliadas = mask_avaliadas.sum()
    insucessos = (df_resultado_teste['resultado_teste'] == 'Insucesso').sum()

    if total_avaliadas == 0:
        teste_passou = True
    else:
        proporcao_insucessos = insucessos / total_avaliadas
        if tolerancia_com_insucesso_admitida is None:
            teste_passou = proporcao_insucessos == 0
        else:
            teste_passou = proporcao_insucessos <= tolerancia_com_insucesso_admitida

    # Adiciona colunas regra_testada e nome_coluna
    df_resultado_teste['regra_testada'] = nome_regra
    df_resultado_teste['nome_coluna'] = coluna

    # Salva o DataFrame com os resultados , de acotdo com o nome do teste
    nome_do_arquivo = f"Dados/output/Resultado_{nome_regra}_Coluna_{coluna}_{nome_teste}.csv"

    try:
        df_resultado_teste.to_csv(nome_do_arquivo, sep=';', encoding='utf_8_sig', index=False)
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

    return teste_passou

def testar_se_coluna_existe_no_conjunto(df, nome_coluna, nome_regra, nome_teste):
    """
    Verifica se uma coluna específica existe em um DataFrame.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    nome_coluna : str
        Nome da coluna a ser testada.
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída). Exemplo: 'RTQD018'.
    nome_teste : str
        Nome do teste (usado para identificação). Exemplo: 'existe_coluna'.

    Retorna:
    --------
    bool
        True se a coluna existir no DataFrame; False caso contrário.

    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo a primeira linha do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parâmetro nome_regra;
        - nome_coluna - que contém o parâmetro nome_coluna; e
        - resultado_teste - esta coluna receberá 'Sucesso' se a coluna existir ou 'Insucesso' caso contrário.

    Exemplo:
    --------
    >>> df = pd.DataFrame({"NomeDaColuna": [1, 2], "OutraColuna": [3, 4]})
    >>> existe = testar_se_coluna_existe_no_conjunto(df, "NomeDaColuna", "RTQD018", "existe_coluna")
    >>> print(f"Resultado do Teste de RTQD018 na Coluna NomeDaColuna é:{existe}")
    Resultado do Teste de RTQD018 na Coluna NomeDaColuna é:True
    E o dataframe com resultado do teste, com a primeira linha, terá:

       NomeDaColuna   |   OutraColuna   |   regra_testada   |   nome_coluna   |   resultado_teste
    -------------------------------------------------------------------------------------------
    1              |             3   |   RTQD018         |   NomeDaColuna    |   Sucesso
    """

    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS
    def checar_se_dataframe_estah_vazio():
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_nome_regra_e_nome_teste_sao_string():
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O parâmetro 'nome_regra' deve ser uma string.")
        # Verifica se nome_regra é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O parâmetro 'nome_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O parâmetro 'nome_teste' deve ser uma string.")
        # Verifica se nome_teste é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

    checar_se_dataframe_estah_vazio()
    checar_se_nome_regra_e_nome_teste_sao_string()

    resultado_teste = "Insucesso"
    if nome_coluna in df.columns:
        resultado_teste = "Sucesso"

    # Preparando o dataframe que será salvo pela função
    if not df.empty:
        df_resultado_teste = df.copy()  
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado_teste["nome_coluna"] = nome_coluna
        # Adicionando coluna chamada resultado_teste
        df_resultado_teste["resultado_teste"] = resultado_teste

    # Salvando o DataFrame
    nome_arquivo = f"Dados/output/Resultado_{nome_regra}_Coluna_{nome_coluna}_{nome_teste}.csv"
    try:
        df_resultado_teste.to_csv(nome_arquivo, sep=';', encoding='utf_8_sig', index=False)
    except Exception as e:
        print (f"Erro ao salvar o arquivo CSV: {e}")

    # Retornando um booleano
    if resultado_teste == "Sucesso":
        return True
    else:
        return False
    
def testar_se_coluna_estah_no_formato(
    df: pd.DataFrame,
    coluna: str,
    nome_regra: str,
    nome_teste: str,
    tipo_formato: str,
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores de uma coluna seguem algum dos formatos especificados para a categoria.
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna a ser testada.
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída).
    nome_teste : str
        Nome específico deste teste (usado para identificação).
    tipo_formato : str
        Categoria do formato esperado para a coluna ('Data', 'Data/Hora', 'Hora', 'Número', 'Texto').
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x > 0"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.
    Retorna:
    --------
    bool
        True se os valores estiverem em algum dos formatos da categoria (ou dentro da tolerância); False caso contrário.
    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parâmetro nome_regra;
        - nome_coluna - que contém o parâmetro coluna; e
        - resultado_teste - esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro 'condicao_na_linha', se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou preenchido com "", "None", "nan", "NaN", "NAN", "null", "NULL" ou "Null";
    Exemplo:
    --------
    >>> df = pd.DataFrame({"DataStr": ["2023-01-15", "15-01-2023", "2023/02/20", "Texto Invalido"], "ID": [1, 2, 3, 4]})
    >>> testar_se_coluna_estah_no_formato(
    ...     df, "DataStr", "RTQD020", "teste_formato_data", "Data", condicao_na_linha="ID < 4", tolerancia_com_insucesso_admitida=0.3
    ... )
    Resultado do Teste de RTQD020 na Coluna DataStr é:True
    E o dataframe com resultado do teste, linha a linha, terá:
       DataStr        |   ID | regra_testada   | nome_coluna   | resultado_teste
    -------------------|------|-----------------|---------------|-----------------
    2023-01-15         |    1 | RTQD020         | DataStr       | Sucesso
    15-01-2023         |    2 | RTQD020         | DataStr       | Sucesso
    2023/02/20         |    3 | RTQD020         | DataStr       | Sucesso
    Texto Invalido     |    4 | RTQD020         | DataStr       | Não avaliado
    """

    # Inicializa a variável de resultado
    Resultado_Teste: bool = None

    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS
    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_coluna_existe() -> None:
        if coluna not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame.")

    def checar_se_nome_regra_eh_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_regra' deve ser uma string.")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_regra' não é um nome válido.")

    def checar_se_nome_teste_eh_string() -> None:
        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido.")

    def checar_se_tipo_formato_eh_valido() -> None:
        formatos_validos = [
            'Data: AAAA-MM-DD',
            'Data: DD-MM-AAAA',
            'Data: DD/MM/AAAA',
            'Data/Hora: AAAA-MM-DD HH:MM:SS',
            'Data/Hora: variantes',
            'Hora: HHMMSS',
            'Número: 9.999,99',
            'Número: 9999',
            'Número: 9999,99',
            'Número: +/- 99,9999',
            'Texto: Geral, mas admite caracteres especiais',
            "Texto: Somente algarismos, sem '/'  ou  '-' ou '.'"
        ]
        if tipo_formato not in formatos_validos:
            raise ValueError(f"Erro: O 'tipo_formato' '{tipo_formato}' não é válido. Use um dos: {formatos_validos}")

    def checar_se_tolerancia_com_insucesso_admitida_eh_valida() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if not (0 <= tolerancia_com_insucesso_admitida <= 1):
                raise ValueError("Erro: A 'tolerância com insucesso admitida' deve estar entre 0 e 1.")

    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            if not re.match(padrao_permitido, condicao_na_linha):
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos.")
            return True
        return True

    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_coluna_existe()
        checar_se_nome_regra_eh_string()
        checar_se_nome_teste_eh_string()
        checar_se_tipo_formato_eh_valido()
        checar_se_tolerancia_com_insucesso_admitida_eh_valida()
        checar_se_condicao_na_linha_eh_query_permitida()

    # FUNÇÕES INTERNAS PARA EXECUTAR O TESTE

    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            try:
                return df.query(condicao_na_linha).copy()
            except Exception as e:
                raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")
        else:
            return df.copy()

    def aplicar_teste_de_formato(df_para_testar: pd.DataFrame) -> pd.DataFrame:
        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]
        resultados = []

        for index, row in df_para_testar.iterrows():
            valor = str(row[coluna]).strip()
            sucesso = False

            if valor in valores_em_branco or pd.isna(row[coluna]):
                resultados.append("Em branco")
                continue

            try:
                match tipo_formato:
                    case 'Data: AAAA-MM-DD':
                        datetime.strptime(valor, '%Y-%m-%d')
                        sucesso = True
                    case 'Data: DD-MM-AAAA':
                        datetime.strptime(valor, '%d-%m-%Y')
                        sucesso = True
                    case 'Data: DD/MM/AAAA':
                        datetime.strptime(valor, '%d/%m/%Y')
                        sucesso = True
                    case 'Data/Hora: AAAA-MM-DD HH:MM:SS':
                        datetime.strptime(valor, '%Y-%m-%d %H:%M:%S')
                        sucesso = True
                    case 'Data/Hora: variantes':
                        formatos_data_hora = [
                            # AAAA-MM-DD com hora
                            '%Y-%m-%d %H:%M:%S.%f', '%Y/%m/%d %H:%M:%S.%f', '%Y.%m.%d %H:%M:%S.%f',
                            '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y.%m.%d %H:%M:%S',
                            '%Y-%m-%d %H:%M.%f', '%Y/%m/%d %H:%M.%f', '%Y.%m.%d %H:%M.%f',
                            '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M', '%Y.%m.%d %H:%M',
                            '%Y-%m-%dT%H:%M:%S.%f', '%Y/%m/%dT%H:%M:%S.%f', '%Y.%m.%dT%H:%M:%S.%f',
                            '%Y-%m-%dT%H:%M:%S', '%Y/%m/%dT%H:%M:%S', '%Y.%m.%dT%H:%M:%S',
                            '%Y-%m-%dT%H:%M.%f', '%Y/%m/%dT%H:%M.%f', '%Y.%m.%dT%H:%M.%f',
                            '%Y-%m-%dT%H:%M', '%Y/%m/%dT%H:%M', '%Y.%m.%dT%H:%M',

                            # DD-MM-AAAA com hora
                            '%d-%m-%Y %H:%M:%S.%f', '%d/%m/%Y %H:%M:%S.%f', '%d.%m.%Y %H:%M:%S.%f',
                            '%d-%m-%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%d.%m.%Y %H:%M:%S',
                            '%d-%m-%Y %H:%M.%f', '%d/%m/%Y %H:%M.%f', '%d.%m.%Y %H:%M.%f',
                            '%d-%m-%Y %H:%M', '%d/%m/%Y %H:%M', '%d.%m.%Y %H:%M',
                            '%d-%m-%YT%H:%M:%S.%f', '%d/%m/%YT%H:%M:%S.%f', '%d.%m.%YT%H:%M:%S.%f',
                            '%d-%m-%YT%H:%M:%S', '%d/%m/%YT%H:%M:%S', '%d.%m.%YT%H:%M:%S',
                            '%d-%m-%YT%H:%M.%f', '%d/%m/%YT%H:%M.%f', '%d.%m.%YT%H:%M.%f',
                            '%d-%m-%YT%H:%M', '%d/%m/%YT%H:%M', '%d.%m.%YT%H:%M'
                        ]
                        for fmt in formatos_data_hora:
                            try:
                                datetime.strptime(valor, fmt)
                                sucesso = True
                                break
                            except ValueError:
                                continue
                    case 'Hora: HHMMSS':
                        formatos_hora = ['%H:%M:%S', '%H%M%S']
                        for fmt in formatos_hora:
                            try:
                                datetime.strptime(valor, fmt)
                                sucesso = True
                                break
                            except ValueError:
                                continue
                    case 'Número: 9.999,99':
                        if re.match(r'^\d{1,3}(\.\d{3})*(,\d{1,2})?$', valor):
                            sucesso = True
                    case 'Número: 9999':
                        if re.match(r'^\d+$', valor):
                            sucesso = True
                    case 'Número: 9999,99':
                        valor = str(row[coluna]).strip().replace('.', ',')
                        if re.match(r'^\d+(,\d{1,2})?$', valor):
                                sucesso = True
                    case 'Número: +/- 99,9999':
                        valor = str(row[coluna]).strip().replace('.', ',')
                        if re.match(r'^[+-]?\d+,\d+$', valor):
                            sucesso = True
                    case 'Texto: Geral, mas admite caracteres especiais':
                        if re.match(r'^.+$', valor):
                            sucesso = True
                    case "Texto: Somente algarismos, sem '/'  ou  '-' ou '.'":
                        if re.match(r'^\d+$', valor):
                            sucesso = True
            except ValueError:
                pass # Falha na conversão de data/hora, considerada inválida

            resultados.append("Sucesso" if sucesso else "Insucesso")

        df_para_testar["resultado_teste"] = resultados
        return df_para_testar

    def obter_percentual_insucesso(resultado: pd.DataFrame) -> float:
        total_avaliados = resultado["resultado_teste"].isin(["Sucesso", "Insucesso"]).sum()
        if total_avaliados > 0:
            percentual_de_insucesso = resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)
            return percentual_de_insucesso
        return 0.0

    # EXECUTANDO O TESTE

    rodar_testes_de_parametros()
    df_linhas_para_testar = obter_dataframe_conforme_condicao_na_linha()
    df_testado = aplicar_teste_de_formato(df_linhas_para_testar)

    # --- Lógica de preparar_dataframe_resultado e salvar_dataframe_resultado integrada ---
    df_resultado_teste = df.copy()
    df_resultado_teste["regra_testada"] = nome_regra
    df_resultado_teste["nome_coluna"] = coluna
    df_resultado_teste["resultado_teste"] = "Não avaliado"
    df_resultado_teste.loc[df_testado.index, "resultado_teste"] = df_testado["resultado_teste"]

    percentagem_de_insucesso = obter_percentual_insucesso(df_resultado_teste)

    try:
        nome_arquivo = f'Resultado_{nome_regra.replace(" ", "_")}_Coluna_{coluna.replace(" ", "_")}_{nome_teste.replace(" ", "_")}.csv'
        df_resultado_teste.to_csv(f'Dados/output/{nome_arquivo}', index=False, sep=';', encoding='utf_8_sig')
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")
    # --- Fim da lógica integrada ---

    if tolerancia_com_insucesso_admitida is None:
        Resultado_Teste = percentagem_de_insucesso == 0
    else:
        Resultado_Teste = percentagem_de_insucesso <= tolerancia_com_insucesso_admitida

    return Resultado_Teste

def testar_se_valores_coluna_estao_no_dominio(
    df: pd.DataFrame,
    coluna: str,
    dominio: list,
    nome_regra: str,
    nome_teste: str,
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores de uma coluna estão contidos em um domínio específico (lista de valores válidos).
    
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna a ser testada.
    dominio : list
        Lista de valores para o domínio da coluna. Este parâmetro deve ser uma lista ('list').
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída).
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x > 0"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.
    
    Retorna:
    --------
    bool
        True se os valores estiverem dentro do domínio (ou dentro da tolerância); False caso contrário.
    
    Efeitos Colaterais:
    -------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parametro nome_regra;
        - nome_coluna - que contém o parâmetro coluna; e
        - resultado_teste - esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro 'condicao_na_linha', se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou preenchido com "", "None", "nan", "NaN", "NAN", "null", "NULL" ou "Null";

    Exemplo:
    --------
    >>> df = pd.DataFrame({"Modalidade": ["FAR", "PSH", None, "Rural", "FAR"]})
    >>> testar_se_valores_coluna_estao_no_dominio(
    ...     df=df,
    ...     coluna="Modalidade",
    ...     dominio=["FAR", "Rural"],
    ...     nome_regra="RTQD024",
    ...     nome_teste="teste_modalidades_validas",
    ...     condicao_na_linha=None,
    ...     tolerancia_com_insucesso_admitida=0.1
    ... )
    Resultado do Teste de RTQD024 na Coluna Modalidade é: False
    Dataframe com resultado do teste, linha a linha, salvo em Dados/output
    
    Modalidade   | regra_testada | nome_coluna | resultado_teste
    -----------------------------------------------------------
    FAR          | RTQD024       | Modalidade  | Sucesso
    PSH          | RTQD024       | Modalidade  | Insucesso
    None         | RTQD024       | Modalidade  | Em branco
    Rural        | RTQD024       | Modalidade  | Sucesso
    FAR          | RTQD024       | Modalidade  | Sucesso
    
     # Qual a lógica da programação usada nesta função
    #    1) Ela define várias funções internas para testar os parâmetros;
    #    2) Ela define várias funções internas para executar o teste, que envolve basicamente:
    #       a) Testar os parâmetros;
    #       b) Filtra as linhas, se o parâmetro condicao_na_linha foi informado;
    #       c) Aplica o teste nas linhas filtradas, marcando as linhas com sucesso, insucesso ou 'em branco' (para valores nulos ou vazios) (ou 'não avaliado', quando há o parâmetro condicao_na_linha);
    #       d) Salva um DataFrame com o resultado do teste no repositório, na pasta \Dados\output, tendo nele uma coluna com o parâmetro nome_regra, com as marcações de sucesso, insucesso e 'em branco' (ou 'não avaliado', se condicao_na_linha foi informado);
    #       e) Calcula o percentual de insucesso e verifica se é menor ou igual à tolerância admitida;
    #       f) Retorna True ou False, conforme o percentual de insucesso e a tolerância admitida.
    """

    # Inicializa a variável que será retornada no final pela funçao
    Resultado_Teste: bool = None

    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS 
    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")
        
    def checar_se_coluna_existe() -> None:
        if coluna not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame.")
        
    def checar_se_dominio_eh_lista() -> None:
        if not isinstance(dominio, list):
            raise ValueError("Erro: O parâmetro 'dominio' deve ser uma lista ('list'). ")

    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' deve ser uma string.")
        # Verifica se nome_coluna_regra é um nome válido para coluna (apenas letras, números e underscores) 
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")
            
        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")  
        # Verifica se nome_teste é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if (tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1):
                raise ValueError("Erro: Parâmetro A 'tolerância com insucesso admitida' deve estar entre 0 e 1.")

    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            # Permitir apenas caracteres alfanuméricos, espaços, operadores de comparação e operadores lógicos
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            if not re.match(padrao_permitido, condicao_na_linha):
                checagem_condicao_na_linha: bool = False
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos.Use apenas letras, espaços, algarismos e operadores lógicos ou de concatenação de strings.")
            else:
                checagem_condicao_na_linha= True
                
            return checagem_condicao_na_linha

    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_coluna_existe()
        checar_se_dominio_eh_lista()
        checar_se_nome_regra_e_nome_teste_sao_string()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()
        checar_se_condicao_na_linha_eh_query_permitida()
        

    # FUNÇÕES INTERNAS PARA EXECUTAR O TESTE 

    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            if checar_se_condicao_na_linha_eh_query_permitida()==True:  
                try:
                    return df.query(condicao_na_linha).copy()
                except Exception as e:
                    raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")   
                
            else:
                raise ValueError("Erro: Condição na linha deve ser uma string.")
        else:
            return df.copy()    

    def aplicar_sucesso_e_insucesso_conforme_dominio() -> pd.DataFrame:
        df_linhas_para_testar = obter_dataframe_conforme_condicao_na_linha()
        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

        for index, row in df_linhas_para_testar.iterrows():
            valor = str(row[coluna]).strip()
            if valor in valores_em_branco or row[coluna] is None:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Em branco"
            elif row[coluna] not in dominio:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Insucesso"
            else:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Sucesso"
                
        # Preparando o dataframe que será salvo pela função
        df_resultado_teste: pd.DataFrame = df.copy()
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado_teste["nome_coluna"] = coluna
        # Adicionando coluna chamada resultado_teste, inicialmente configurada como "Não avaliado
        df_resultado_teste["resultado_teste"] = "Não avaliado"
        df_resultado_teste.loc[df_linhas_para_testar.index, "resultado_teste"] = df_linhas_para_testar["resultado_teste"]

        try:
            df_resultado_teste.to_csv(f'Dados/output/Resultado_{nome_regra}_Coluna_{coluna}_{nome_teste}.csv', index=False, sep=';', encoding='utf_8_sig')
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return df_resultado_teste      

    def obter_percentual_insucesso_conforme_dominio(resultado: pd.DataFrame) -> float:
        return resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)

    # Roda os testes
    rodar_testes_de_parametros()
    resultado_dataframe = aplicar_sucesso_e_insucesso_conforme_dominio()
    percentual_insucesso = obter_percentual_insucesso_conforme_dominio(resultado_dataframe)

    Resultado_Teste = percentual_insucesso <= (tolerancia_com_insucesso_admitida if tolerancia_com_insucesso_admitida is not None else 0)
    return Resultado_Teste

def testar_se_coluna_no_conjunto_coincide_com_catalogo(df: pd.DataFrame, nome_coluna: str, numero_ordem_coluna: int, quantidade_colunas_conjunto: int, nome_regra: str, nome_teste: str) -> bool:
    """
    Verifica se uma coluna específica em um DataFrame corresponde ao catálogo de dados,
    considerando a existência da coluna, sua ordem e a quantidade total de colunas.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    nome_coluna : str
        Nome da coluna a ser testada.
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída). Exemplo: 'RTQD019'.
    nome_teste : str
        Nome do teste (usado para identificação). Exemplo: 'coincide_com_catalogo'.
    numero_ordem_coluna: int
        Número de ordem esperado para a coluna.
    quantidade_colunas_conjunto: int
        Quantidade total de colunas esperada no DataFrame.

    Retorna:
    --------
    bool
        True se a coluna existir no DataFrame, estiver na ordem correta e o DataFrame tiver o número esperado de colunas;
        False caso contrário.

    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo a primeira linha do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parâmetro nome_regra;
        - nome_coluna - que contém o parâmetro nome_coluna; e
        - resultado_teste - esta coluna receberá 'Sucesso' se a coluna existir, estiver na ordem correta e o número de colunas estiver correto, ou 'Insucesso' caso contrário.

    Exemplo:
    --------
    >>> df = pd.DataFrame({"NomeDaColuna": [1, 2], "OutraColuna": [3, 4]})
    >>> resultado = testar_se_coluna_no_conjunto_coincide_com_catalogo(df, "NomeDaColuna", 1, 2, "RTQD019", "coincide_com_catalogo")
    >>> print(f"Resultado do Teste de RTQD019 na Coluna NomeDaColuna é:{resultado}")
    Resultado do Teste de RTQD019 na Coluna NomeDaColuna é:True
    E o dataframe com resultado do teste, com a primeira linha, terá:

       NomeDaColuna   |   OutraColuna   |   regra_testada   |   nome_coluna   |   resultado_teste
    -------------------------------------------------------------------------------------------
    1              |             3   |   RTQD019         |   NomeDaColuna    |   Sucesso
    """

    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS
    def checar_se_dataframe_estah_vazio():
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_nome_regra_e_nome_teste_sao_string():
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O parâmetro 'nome_regra' deve ser uma string.")
        # Verifica se nome_regra é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O parâmetro 'nome_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O parâmetro 'nome_teste' deve ser uma string.")
        # Verifica se nome_teste é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")
    
    def checar_se_numero_ordem_coluna_e_inteiro_e_positivo():
        if not isinstance(numero_ordem_coluna, int) or numero_ordem_coluna < 1:
            raise ValueError("Erro: O parâmetro 'numero_ordem_coluna' deve ser um inteiro positivo (maior ou igual a 1).")
            
    def checar_se_quantidade_colunas_conjunto_e_inteiro_e_positivo():
        if not isinstance(quantidade_colunas_conjunto, int) or quantidade_colunas_conjunto < 1:
            raise ValueError("Erro: O parâmetro 'quantidade_colunas_conjunto' deve ser um inteiro positivo (maior ou igual a 1).")

    checar_se_dataframe_estah_vazio()
    checar_se_nome_regra_e_nome_teste_sao_string()
    checar_se_numero_ordem_coluna_e_inteiro_e_positivo()
    checar_se_quantidade_colunas_conjunto_e_inteiro_e_positivo()

    resultado_teste = "Insucesso"
    if nome_coluna in df.columns:
        ordem_real = df.columns.get_loc(nome_coluna) + 1
        if ordem_real == numero_ordem_coluna and len(df.columns) == quantidade_colunas_conjunto:
            resultado_teste = "Sucesso"

    # Preparando o dataframe que será salvo pela função
    if not df.empty:
        df_resultado_teste = df.copy()
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado_teste["nome_coluna"] = nome_coluna
        # Adicionando coluna chamada resultado_teste
        df_resultado_teste["resultado_teste"] = resultado_teste

    # Salvando o DataFrame
    nome_arquivo = f"Dados/output/Resultado_{nome_regra}_Coluna_{nome_coluna}_{nome_teste}.csv"
    try:
        df_resultado_teste.to_csv(nome_arquivo, sep=";", encoding="utf_8_sig", index=False)
    except Exception as e:
        print(f"Erro ao salvar o arquivo CSV: {e}")
        return False

    # Retornando um booleano
    if resultado_teste == "Sucesso":
        return True
    else:
        return False
def testar_mascara_caracteres_coluna(
    df: pd.DataFrame,
    coluna: str,
    mascara_caracteres: str,
    nome_regra: str,
    nome_teste: str,
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores da coluna obedecem à máscara de caracteres informada.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna a ser testada.
    mascara_caracteres : str
        Expressão regular que o valor deve corresponder.
        Exemplos comuns:
        - Campo com exatos 8 algarismos: r'^\d{8}$'
        - Campo com até 5 algarismos: r'^\d{1,5}$'
        - Campo com 11 algarismos, ponto e hífen (ex: CPF): r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
        - Campo com até 9 letras: r'^[A-Za-z]{1,9}$'
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída).
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x > 0"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.

    Retorna:
    --------
    bool
        True se os valores obedecerem à máscara (ou estiverem dentro da tolerância); False caso contrário.

    Efeitos Colaterais:
    -------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parâmetro nome_regra;
        - nome_coluna - que contém o parâmetro coluna; e
        - resultado_teste - esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro condicao_na_linha, se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou vazio, ou "None", "nan", "NaN", "NAN", "null", "NULL", "Null".
    Exemplo:
    --------
    >>> df = pd.DataFrame({"Código": ["12345678", "87654321", "1234abcd", None], "Tipo": ["A", "B", "A", "B"]})
    >>> teste_obtido = testar_mascara_caracteres_coluna(
    ...     df=df,
    ...     coluna="Código",
    ...     mascara_caracteres= r'^\d{8}$',  # máscara de 8 dígitos numéricos exatos
    ...     nome_regra="RTQD023",
    ...     nome_teste="teste_mascara_8_digitos",
    ...     condicao_na_linha=None,
    ...     tolerancia_com_insucesso_admitida=0.)
    ...
    >>> print(f"Resultado do Teste de RTQD023 na Coluna Código é: {teste_obtido}")
    >>> print(f"Dataframe com resultado do teste, linha a linha, salvo em Dados/output")
    ...
    Resultado do Teste de RTQD023 na Coluna Código é: False
    Dataframe com resultado do teste, linha a linha, salvo em Dados/output

    Código      | Tipo  | regra_testada | nome_coluna | resultado_teste
    --------------------------------------------------------------------
    12345678    | A     | RTQD023       | Código      | Sucesso
    87654321    | B     | RTQD023       | Código      | Sucesso
    1234abcd    | A     | RTQD023       | Código      | Insucesso
    None        | B     | RTQD023       | Código      | Em branco
    """
    
    # Qual a lógica da programação usada nesta função
    #   1) Ela define várias funções internas para testar os parâmetros;
    #   2) Ela define várias funções internas para testar executar o teste, que envolve basicamente:
    #      a) Testar os parametros;
    #      b) Filtra as linhas, se o parametro condiçao_na_linha foi informado;
    #      c) Aplica o teste nas linhas filtradas, marcando as linhas com sucesso e insucesso (ou 'não avaliado', quando há o parametro condicao_na_linha);
    #      d) Salva um dataframe com o resultado do teste no repositório, na pasta \Dados\output, tendo nele uma coluna com o parametro nome_regra, com as marcações de sucesso, insucesso e 'não avaliado';
    #      e) Calcula o percentual de insucesso e verifica se é menor ou igual a tolerância;
    #      f) Retorna True ou False, conforme o percentual de insucesso e a tolerância admitida.
    

    # Inicializa a variável que será retornada no final pela funçao
    resultado_teste: bool = None
    
    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS
    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_coluna_existe() -> None:
        if coluna not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame.")

    def checar_se_mascara_e_valida() -> None:
            try:
                re.compile(mascara_caracteres)
            except re.error:
                raise ValueError("Erro: Parâmetro 'mascara_caracteres' não é uma expressão regular válida.")

    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_regra' deve ser uma string.")
        if nome_regra and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_regra' não é um nome válido.")

        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")
        if nome_teste and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1:
                raise ValueError("Erro: Parâmetro 'tolerancia_com_insucesso_admitida' deve estar entre 0 e 1.")

    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            # Permitir apenas caracteres alfanuméricos, espaços, operadores de comparação e operadores lógicos
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            
            if not re.match(padrao_permitido, condicao_na_linha):
                checagem_condicao_na_linha: bool = False
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos. Use apenas letras, espaços, algarismos e operadores lógicos ou de concatenação de strings.")
            else:
                checagem_condicao_na_linha= True
            
            
            return checagem_condicao_na_linha


    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_coluna_existe()
        checar_se_mascara_e_valida()
        checar_se_nome_regra_e_nome_teste_sao_string()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()
        checar_se_condicao_na_linha_eh_query_permitida()
        
    # FUNÇÕES INTERNAS PARA EXECUTAR O TESTE 
    
    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            if checar_se_condicao_na_linha_eh_query_permitida()==True:  
                try:
                    return df.query(condicao_na_linha).copy()
                except Exception as e:
                    raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")   
                
            else:
                raise ValueError("Erro: Condição na linha deve ser uma string.")
        else:
            return df.copy()    
  

    def aplicar_sucesso_e_insucesso_conforme_mascara() -> pd.DataFrame:
        df_linhas_para_testar = obter_dataframe_conforme_condicao_na_linha()
        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

        for index, row in df_linhas_para_testar.iterrows():
            valor = str(row[coluna]).strip()
            if valor in valores_em_branco or row[coluna] is None:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Em branco"
            elif not re.fullmatch(mascara_caracteres, valor):
                df_linhas_para_testar.at[index, "resultado_teste"] = "Insucesso"
            else:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Sucesso"
                
                       
        # Preparando o dataframe que será salvo pela função
        df_resultado_teste = df.copy()
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado_teste["nome_coluna"] = coluna
        # Adicionando coluna chamada resultado_teste, inicialmente configurada como "Não avaliado
        df_resultado_teste["resultado_teste"] = "Não avaliado"
        df_resultado_teste.loc[df_linhas_para_testar.index, "resultado_teste"] = df_linhas_para_testar["resultado_teste"]

        try:
            df_resultado_teste.to_csv(f'Dados/output/Resultado_{nome_regra}_Coluna_{coluna}_{nome_teste}.csv', index=False, sep=';', encoding='utf_8_sig')
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return df_resultado_teste

    def obter_percentual_insucesso(resultado: pd.DataFrame) -> float:
        return resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)
        
    # EXECUTANDO O TESTE 
    
    rodar_testes_de_parametros()
    df_resultado = aplicar_sucesso_e_insucesso_conforme_mascara()
    percentual_insucesso = obter_percentual_insucesso(df_resultado)

    if tolerancia_com_insucesso_admitida is None:
        resultado_teste = (percentual_insucesso == 0)
    else:
        resultado_teste = (percentual_insucesso <= tolerancia_com_insucesso_admitida)

    return resultado_teste

def testar_localidade_geografica_contra_IBGE(
    df: pd.DataFrame, 
    coluna: dict, 
    df_localidades: pd.DataFrame, 
    coluna_localidade: dict, 
    nome_regra: str,
    nome_teste: str, 
    condicao_na_linha: str = None, 
    tolerancia_com_insucesso_admitida: float = None
) -> bool:

    """
    Verifica se os valores de uma coluna de localidades geográficas (e.g., municípios, estados)
    coincidem com os dados de referência do IBGE.
    
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : dict
        Dicionário com os nomes das colunas no 'df' a serem testadas 
    df_localidades : pd.DataFrame
        DataFrame contendo os dados de referência do IBGE (e.g., lista de municípios do IBGE).
    coluna_localidade : dict
         Dicionário com os nomes das colunas no DataFrame de referência 'df_localidades' que 
         correspondem às colunas do DataFrame 'df' informadas no parâmetro 'coluna' (e.g., {"municipio": "nome", "uf": "uf"}).
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída).
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x == 'ativo'"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.
    
    Retorna:
    --------
    bool
        True se os valores estiverem em conformidade com o IBGE (ou dentro da tolerância); False caso contrário.
    
    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parametro nome_regra;
        - nome_coluna - que contém o parâmetro coluna; e
        - resultado_teste -  esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro 'condicao_na_linha', se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou preenchido com "", "None", "nan", "NaN", "NAN", "null", "NULL" ou "Null";
 
    
    Exemplo:
    --------
    >>> df_dados = pd.DataFrame({
    ...     "Municipio": ["São Paulo", "Rio de Janeiro", "Campinas", None],
    ...     "UF": ["SP", "RJ", "SP", "MG"]
    ... })
    >>> df_ibge = pd.DataFrame({
    ...     "nome": ["São Paulo", "Rio de Janeiro", "Belo Horizonte"],
    ...     "uf": ["SP", "RJ", "MG"]
    ... })
    >>> testar_localidade_geografica_contra_IBGE(
    ...     df=df_dados,
    ...     coluna={"municipio": "Municipio", "uf": "UF"},
    ...     df_localidades=df_ibge,
    ...     coluna_localidade={"municipio": "nome", "uf": "uf"},
    ...     nome_regra="RTQD027",
    ...     nome_teste="municipio_uf_existe_ibge",
    ...     condicao_na_linha = "UF == 'SP'",
    ...     tolerancia_com_insucesso_admitida=0.
    ... )
    >>> print(f"Resultado do Teste de {{RTQD}} na Coluna {{coluna_testada}} é:{{teste_obtido}}")
    >>> print(f"Dataframe com resultado do teste, linha a linha, salvo em Dados/output")
    ...
    Resultado do Teste de RTQD027 na Coluna Municipio+UF é:False
    Dataframe com resultado do teste, linha a linha, salvo em Dados/output
    Municipio       |   UF   |   regra_testada   |   nome_coluna   |   resultado_teste
    --------------------------------------------------------------------------------------
    São Paulo       |   SP   |   RTQD027         |   Municipio+UF  |   Sucesso
    Rio de Janeiro  |   RJ   |   RTQD027         |   Municipio+UF  |   Não avaliado
    Campinas        |   SP   |   RTQD027         |   Municipio+UF  |   Insucesso
    None            |   MG   |   RTQD027         |   Municipio+UF  |   Não avaliado
    """


    # Qual a lógica da programação usada nesta função
    #   1) Ela define várias funções internas para testar os parâmetros;
    #   2) Ela define várias funções internas para testar executar o teste, que envolve basicamente:
    #      a) Testar os parametros;
    #      b) Filtra as linhas, se o parametro condiçao_na_linha foi informado;
    #      c) Aplica o teste nas linhas filtradas, marcando as linhas com sucesso e insucesso (ou 'não avaliado', quando há o parametro condicao_na_linha);
    #      d) Salva um dataframe com o resultado do teste no repositório, na pasta \Dados\output, tendo nele uma coluna com o parametro nome_regra, com as marcações de sucesso, insucesso e 'não avaliado';
    #      e) Calcula o percentual de insucesso e verifica se é menor ou igual a tolerância;
    #      f) Retorna True ou False, conforme o percentual de insucesso e a tolerância admitida.




    # Inicializa a variável que será retornada no final pela funçao
    Resultado_Teste: bool = None

    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS 

    def checar_se_dataframe_estah_vazio(df_: pd.DataFrame, nome: str) -> None:
        if df_.empty:
            raise ValueError(f"Erro: DataFrame '{nome}' está vazio.")

    def checar_se_colunas_existem(df_: pd.DataFrame, colunas_: dict, nome: str) -> None:
        for col in colunas_.values():
            if col not in df_.columns:
                raise ValueError(f"Erro: Coluna '{col}' não encontrada no DataFrame '{nome}'.")

    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_regra' deve ser uma string.")   
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")   
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if (tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1):
                raise ValueError("Erro: Parâmetro 'A 'tolerância com insucesso admitida' deve estar entre 0 e 1.")  

    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            # Permitir apenas caracteres alfanuméricos, espaços, operadores de comparação e operadores lógicos
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"

            if not re.match(padrao_permitido, condicao_na_linha):
                checagem_condicao_na_linha: bool = False
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos. Use apenas letras, espaços, algarismos e operadores lógicos ou de concatenação de strings.")
            else:
                checagem_condicao_na_linha= True

            return checagem_condicao_na_linha

    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio(df, "df")
        checar_se_dataframe_estah_vazio(df_localidades, "df_localidades")
        checar_se_colunas_existem(df, coluna, "df")
        checar_se_colunas_existem(df_localidades, coluna_localidade, "df_localidades")
        checar_se_nome_regra_e_nome_teste_sao_string()
        checar_se_condicao_na_linha_eh_query_permitida()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()


  # FUNÇÕES INTERNAS PARA EXECUTAR O TESTE 

    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            if checar_se_condicao_na_linha_eh_query_permitida():  
                try:
                    return df.query(condicao_na_linha).copy()
                except Exception as e:
                    raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")   
            else:
                raise ValueError("Erro: Condição na linha deve ser uma string.")
        else:
            return df.copy()    

    def aplicar_sucesso_e_insucesso_conforme_ibge() -> pd.DataFrame:
        df_linhas_para_testar: pd.DataFrame = obter_dataframe_conforme_condicao_na_linha()
        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

        for chave in coluna_localidade:
            df_localidades[coluna_localidade[chave]] = df_localidades[coluna_localidade[chave]].astype(str).str.strip().str.lower()

        df_localidades["__chave_ibge__"] = df_localidades.apply(
            lambda row: "||".join([row[coluna_localidade[chave]] for chave in coluna_localidade]), axis=1
        )
        set_valores_ibge = set(df_localidades["__chave_ibge__"].dropna().unique())

        df_linhas_para_testar["resultado_teste"] = "Não avaliado"

        for index, row in df_linhas_para_testar.iterrows():
            valores = []
            em_branco = False
            for chave in coluna:
                valor = row[coluna[chave]]
                if pd.isna(valor) or str(valor).strip() in valores_em_branco:
                    em_branco = True
                valores.append(str(valor).strip().lower() if pd.notna(valor) else "")
            if em_branco:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Em branco"
            elif "||".join(valores) in set_valores_ibge:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Sucesso"
            else:
                df_linhas_para_testar.at[index, "resultado_teste"] = "Insucesso"

        # Preparando o dataframe que será salvo pela função
        df_resultado_teste: pd.DataFrame = df.copy()
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada resultado_teste, inicialmente configurada como Não avaliado
        df_resultado_teste["resultado_teste"] = "Não avaliado" 

        df_resultado_teste.loc[df_linhas_para_testar.index, "resultado_teste"] = df_linhas_para_testar["resultado_teste"]

        # Cria dataframe e salva no repositorio o resultado do teste

        try:
            for nome_coluna_individual in coluna.values():
                df_resultado_teste_individual = df_resultado_teste.copy()
                df_resultado_teste_individual["nome_coluna"] = nome_coluna_individual

                df_resultado_teste_individual.to_csv(
                    f'Dados/output/Resultado_{nome_regra}_Coluna_{nome_coluna_individual}_{nome_teste}.csv',
                    index=False,
                    sep=';',
                    encoding='utf_8_sig'
                )
        except Exception as e:
            print(f"Erro ao salvar arquivo CSV: {e}")
            
        return  df_resultado_teste    

    def obter_percentual_insucesso_conforme_ibge(resultado: pd.DataFrame) -> float:
        percentual_de_insucesso: float = resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)
        return percentual_de_insucesso


    # EXECUTANDO O TESTE 

    rodar_testes_de_parametros()
    df_dataframe_resultado_teste: pd.DataFrame = aplicar_sucesso_e_insucesso_conforme_ibge()
    percentagem_de_insucesso: float = obter_percentual_insucesso_conforme_ibge(df_dataframe_resultado_teste)

    if percentagem_de_insucesso == 0:
        Resultado_Teste = True
    else:
        Resultado_Teste= False 

    if tolerancia_com_insucesso_admitida is not None:
        if percentagem_de_insucesso <= tolerancia_com_insucesso_admitida: 
            Resultado_Teste = True
        else:
            Resultado_Teste =  False

    return Resultado_Teste

def testar_calculo_colunas(
    df: pd.DataFrame,
    coluna1: str,
    coluna2: str,
    coluna3: str,
    expressao: str,
    nome_regra: str,
    nome_teste: str,
    coluna4: str = None,
    coluna5: str = None,
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores da coluna1 correspondem à expressão definida.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna1 : str
        Nome da coluna a ser testada (lado esquerdo da expressão).
    coluna2 : str
        Nome da primeira coluna do lado direito da expressão.
    coluna3 : str
        Nome da segunda coluna do lado direito da expressão.
    coluna4 : str, optional
        Nome da terceira coluna do lado direito da expressão.
    coluna5 : str, optional
        Nome da quarta coluna do lado direito da expressão.
    expressao : str
        Expressão de cálculo a validar, exemplo: "coluna1 = coluna2 - coluna3".
    nome_regra : str
        Nome da regra de validação (usado no arquivo de saída).
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x > 0"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.

    Retorna:
    --------
    bool
        True se todos os valores testados estiverem de acordo com a expressão (ou dentro da tolerância);
        False caso contrário.

    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parametro nome_regra;
        - nome_coluna - que contém o parâmetro coluna1;
        - resultado_teste -  esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro 'condicao_na_linha', se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou preenchido com "", "None", "nan", "NaN", "NAN", "null", "NULL" ou "Null";

    Exemplo:
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "UH_Entregues": [10, None, 35, 200],
    ...     "UH_Vigentes": [20, 15, 18, 22],
    ...     "UH_Janeiro":  [10, 10, 10, 10],
    ...     "Modalidade": ["FAR", "FAR", "Rural", "FAR"]
    ... })
    >>> testar_calculo_colunas(
    ...     df=df,
    ...     coluna1="UH_Entregues",
    ...     coluna2="UH_Vigentes",
    ...     coluna3="UH_Janeiro",
    ...     expressao="coluna2 - coluna3",
    ...     nome_regra="RTQD035",
    ...     nome_teste="teste_entrega_UH",
    ...     condicao_na_linha="Modalidade == 'FAR'",
    ...     tolerancia_com_insucesso_admitida=0.
    ... )
    ...
    >>> print(f"Resultado do Teste de RTQD035 na Coluna UH_Entregues é:False")
    >>> print(f"Dataframe com resultado do teste, linha a linha, salvo em Dados/output")
    ...
    UH_Entregues   | UH_Vigentes | UH_Janeiro | Modalidade | regra_testada | nome_coluna | resultado_teste
    -----------------------------------------------------------------------------------------------
    10             | 20          | 10         | FAR        | RTQD035       | UH_Entregues | Sucesso
    None           | 15          | 10         | FAR        | RTQD035       | UH_Entregues | Em branco
    35             | 18          | 10         | Rural      | RTQD035       | UH_Entregues | Não avaliado
    200            | 22          | 10         | FAR        | RTQD035       | UH_Entregues | Insucesso
    """
    
    # Inicializa a variável que será retornada no final pela funçao
    Resultado_Teste: bool = None

    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS
    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_colunas_existem() -> None:
        for col in [coluna1, coluna2, coluna3, coluna4, coluna5]:
            if col is not None and col not in df.columns:
                raise ValueError(f"Erro: Coluna '{col}' não encontrada no DataFrame.")

    def checar_se_colunas_sao_numericas() -> None:
        for col in [coluna1, coluna2, coluna3, coluna4, coluna5]:
            if col is not None:
                try:
                    pd.to_numeric(df[col], errors='raise')
                except Exception as e:
                    raise ValueError(f"Erro: Coluna '{col}' contém valores não numéricos: {e}")

    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O parâmetro 'nome_regra' deve ser uma string.")
         # Verifica se nome_coluna_regra é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O parâmetro 'nome_regra' não é válido. Deve conter apenas letras, números e underscores, e não pode começar com número.")
        
        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O parâmetro 'nome_teste' deve ser uma string.")
         # Verifica se nome_teste é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O parâmetro 'nome_teste' não é válido. Deve conter apenas letras, números e underscores, e não pode começar com número.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1:
                raise ValueError("Erro: Parâmetro 'tolerancia_com_insucesso_admitida' deve estar entre 0 e 1.")

    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            # Permitir apenas caracteres alfanuméricos, espaços, operadores de comparação e operadores lógicos
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            
            if not re.match(padrao_permitido, condicao_na_linha):
                checagem_condicao_na_linha: bool = False
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos. Use apenas letras, espaços, algarismos e operadores lógicos ou de concatenação de strings.")
            else:
                checagem_condicao_na_linha= True
            
            
            return checagem_condicao_na_linha
            
    def checar_se_expressao_eh_valida() -> None:
        if not isinstance(expressao, str):
            raise ValueError("Erro: O parâmetro 'expressao' deve ser uma string.")

        # Remove espaços para simplificar a verificação
        expressao_limpa = expressao.replace(" ", "")

        # Verifica se só há letras, números, underscores, parênteses e operadores válidos
        padrao = r"^[\w\(\)\+\-\*/]+$"
        if not re.fullmatch(padrao, expressao_limpa):
            raise ValueError(
                "Erro: A expressão fornecida contém elementos inválidos. "
                "Use apenas nomes de variáveis (letras, números, _), parênteses e operadores + - * /."
            )

        # Extrai as variáveis da expressão (coluna1, coluna2, etc.)
        variaveis = set(re.findall(r"coluna[1-5]", expressao))

        # Cria um conjunto das colunas passadas (exceto coluna1)
        colunas_passadas = set()
        for col in [coluna2, coluna3, coluna4, coluna5]:
            if col is not None:
                colunas_passadas.add(f"coluna{[coluna2, coluna3, coluna4, coluna5].index(col) + 2}")

        # Remove coluna1 da lista de variáveis da expressão, se estiver presente
        variaveis.discard("coluna1")

        # Verifica se todas as variáveis na expressão (à direita) foram passadas como colunas
        variaveis_nao_passadas = variaveis - colunas_passadas
        if variaveis_nao_passadas:
            raise ValueError(
                f"Erro: As variáveis {variaveis_nao_passadas} presentes na expressão não foram passadas como parâmetros."
            )
         
        # Verifica se todas as colunas passadas estão na expressão
        colunas_nao_usadas = colunas_passadas - variaveis
        if colunas_nao_usadas:
            raise ValueError(
                f"Erro: As colunas {colunas_nao_usadas} foram passadas como parâmetros, "
                "mas não são usadas na expressão."
            )
        

    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_colunas_existem()
        checar_se_colunas_sao_numericas()
        checar_se_nome_regra_e_nome_teste_sao_string()
        checar_se_condicao_na_linha_eh_query_permitida()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()
        checar_se_expressao_eh_valida()

    # FUNÇÕES INTERNAS PARA EXECUTAR O TESTE

    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            if checar_se_condicao_na_linha_eh_query_permitida():
                try:
                    return df.query(condicao_na_linha).copy()
                except Exception as e:
                    raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")
            else:
                raise ValueError("Erro: Condição na linha deve ser uma string.")
        else:
            return df.copy()

    def aplicar_teste_calculo() -> pd.DataFrame:
        df_linhas_para_testar = obter_dataframe_conforme_condicao_na_linha()

        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

        for idx, row in df_linhas_para_testar.iterrows():
            valor_col1 = row[coluna1]
            if pd.isna(valor_col1) or str(valor_col1).strip() in valores_em_branco:
                df_linhas_para_testar.at[idx, "resultado_teste"] = "Em branco"
            else:
                try:
                    expressao_avaliada = expressao
                    substituicoes = {
                        "coluna1": f"row['{coluna1}']",
                        "coluna2": f"row['{coluna2}']",
                        "coluna3": f"row['{coluna3}']",
                        "coluna4": f"row['{coluna4}']",
                        "coluna5": f"row['{coluna5}']",
                    }  

                    for var, expr in substituicoes.items():
                        expressao_avaliada = expressao_avaliada.replace(var, expr)
                    valor_esperado = eval(expressao_avaliada)
                except Exception as e:
                    raise ValueError(f"Erro ao calcular a expressão '{expressao}' na linha {idx}: {e}")

                if valor_col1 == valor_esperado:
                    df_linhas_para_testar.at[idx, "resultado_teste"] = "Sucesso"
                else:
                    df_linhas_para_testar.at[idx, "resultado_teste"] = "Insucesso"
                    
                    
        # Preparando o dataframe que será salvo pela função
        df_resultado_teste = df.copy()
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado_teste["nome_coluna"] = coluna1
        # Adicionando coluna chamada resultado_teste, inicialmente configurada como "Não avaliado
        df_resultado_teste["resultado_teste"] = "Não avaliado"

        df_resultado_teste.loc[df_linhas_para_testar.index, "resultado_teste"] = df_linhas_para_testar["resultado_teste"]
        
        # Cria dataframe e salva no repositorio o resultado do teste

        try:
            df_resultado_teste.to_csv(f'Dados/output/Resultado_{nome_regra}_{nome_teste}.csv', index=False, sep=';', encoding='utf_8_sig')
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return df_resultado_teste

    def obter_percentual_insucesso(resultado: pd.DataFrame) -> float:
        percentual_de_insucesso: float = resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)

        return percentual_de_insucesso

    # EXECUTANDO O TESTE

    rodar_testes_de_parametros()
    df_resultado = aplicar_teste_calculo()
    percentual_insucesso = obter_percentual_insucesso(df_resultado)

    if percentual_insucesso == 0:
        Resultado_Teste = True
    else:
        Resultado_Teste = False

    if tolerancia_com_insucesso_admitida is not None:
        if percentual_insucesso <= tolerancia_com_insucesso_admitida:
            Resultado_Teste = True
        else:
            Resultado_Teste = False

    return Resultado_Teste

def avaliar_unicidade_coluna(
    df: pd.DataFrame,
    coluna: str,
    nome_regra: str,
    nome_teste: str,
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None
) -> bool:
    """
    Verifica se os valores de uma coluna são únicos em todas as linhas do conjunto de dados.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados a serem avaliados.
    coluna : str
        Nome da coluna a ser testada para unicidade.
    nome_regra : str
        Nome da regra de validação (usado no nome do arquivo de saída, ex: "RTQD001").
    nome_teste : str
        Nome do teste (usado para identificação).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste (ex: "coluna_x > 0"). Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.

    Retorna:
    --------
    bool
        True se a coluna passar no teste de unicidade (ou estiver dentro da tolerância); False caso contrário.

    Efeitos Colaterais:
    ------------------
    - Grava um arquivo CSV em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas adicionais neste dataframe:
        - regra_testada - que contém o parâmetro nome_regra;
        - nome_coluna - que contém o parâmetro coluna; e
        - resultado_teste - esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro 'condicao_na_linha', se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou preenchido com "", "None", "nan", "NaN", "NAN", "null", "NULL" ou "Null";
      
     Exemplo:
     --------
     >>> df = pd.DataFrame({
     ...     "APF": [12345, 67890, 12345, None, ""],
     ...     "Modalidade": ["FAR", "FAR", "FAR", "FAR", "Rural"]
     ... })
     >>> avaliar_unicidade_coluna(
     ...     df=df,
     ...     coluna="APF",
     ...     nome_regra="RTQD001",
     ...     nome_teste="teste_unicidade_apf",
     ...     condicao_na_linha="Modalidade == 'FAR'",
     ...     tolerancia_com_insucesso_admitida=0.)
     ...
     >>> print(f"Resultado do Teste de {RTQD} na Coluna {coluna_testada} é:{teste_obtido}")
     >>> print(f"Dataframe com resultado do teste, linha a linha, salvo em Dados/output")
     ...
     Resultado do Teste de RTQD001 na Coluna APF é:False  
     Dataframe com resultado do teste, linha a linha, salvo em Dados/output

     APF     | Modalidade | regra_testada | nome_coluna | resultado_teste
     ---------------------------------------------------------------------
     12345   | FAR        | RTQD001       | APF         | Insucesso
     67890   | FAR        | RTQD001       | APF         | Sucesso
     12345   | FAR        | RTQD001       | APF         | Insucesso
     None    | FAR        | RTQD001       | APF         | Em branco
     ""      | Rural      | RTQD001       | APF         | Não avaliado      
     """
     
     # Qual a lógica da programação usada nesta função
    #   1) Ela define várias funções internas para testar os parâmetros;
    #   2) Ela define várias funções internas para testar executar o teste, que envolve basicamente:
    #      a) Testar os parametros;
    #      b) Filtra as linhas, se o parametro condiçao_na_linha foi informado;
    #      c) Aplica o teste nas linhas filtradas, marcando as linhas com sucesso e insucesso (ou 'não avaliado', quando há o parametro condicao_na_linha);
    #      d) Salva um dataframe com o resultado do teste no repositório, na pasta \Dados\output, tendo nele uma coluna com o parametro nome_regra, com as marcações de sucesso, insucesso e 'não avaliado';
    #      e) Calcula o percentual de insucesso e verifica se é menor ou igual a tolerância;
    #      f) Retorna True ou False, conforme o percentual de insucesso e a tolerância admitida.
    
    
    # Inicializa a variável que será retornada no final pela funçao
    Resultado_Teste: bool = False


    # FUNÇÕES INTERNAS PARA TESTAR OS PARÂMETROS 
    def checar_se_dataframe_estah_vazio() -> None:
        if df.empty:
            raise ValueError("Erro: DataFrame está vazio.")

    def checar_se_coluna_existe() -> None:
        if coluna not in df.columns:
            raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame.")

    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_regra' deve ser uma string.")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if (tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1):
                raise ValueError("Erro: Parâmetro 'A 'tolerância com insucesso admitida' deve estar entre 0 e 1.")  

    def checar_se_condicao_na_linha_eh_query_permitida() -> bool:
        if isinstance(condicao_na_linha, str):
            # Permitir apenas caracteres alfanuméricos, espaços, operadores de comparação e operadores lógicos
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            
            if not re.match(padrao_permitido, condicao_na_linha):
                checagem_condicao_na_linha: bool = False
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos. Use apenas letras, espaços, algarismos e operadores lógicos ou de concatenação de strings.")
            else:
                checagem_condicao_na_linha= True
            
            
            return checagem_condicao_na_linha

    def rodar_testes_de_parametros() -> None:
        checar_se_dataframe_estah_vazio()
        checar_se_coluna_existe()
        checar_se_nome_regra_e_nome_teste_sao_string()
        checar_se_condicao_na_linha_eh_query_permitida()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()
        
    # FUNÇÕES INTERNAS PARA EXECUTAR O TESTE     
    
    def obter_dataframe_conforme_condicao_na_linha() -> pd.DataFrame:
        if condicao_na_linha is not None:
            if checar_se_condicao_na_linha_eh_query_permitida()==True:  
                try:
                    return df.query(condicao_na_linha).copy()
                except Exception as e:
                    raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")   
                
            else:
                raise ValueError("Erro: Condição na linha deve ser uma string.")
        else:
            return df.copy()    

    def aplicar_sucesso_e_insucesso_conforme_unicidade() -> pd.DataFrame:
        df_linhas_para_testar: pd.DataFrame = obter_dataframe_conforme_condicao_na_linha()
        valores_em_branco = ["", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"]

        # Aplicando "Em branco", "Sucesso" ou "Insucesso" apenas às linhas que serão avaliadas
        for index, row in df_linhas_para_testar.iterrows():
            if str(row[coluna]).strip() in valores_em_branco or pd.isna(row[coluna]):
                df_linhas_para_testar.at[index, "resultado_teste"] = "Em branco"
            else:
                # Inicialmente marca como Sucesso. Será alterado para Insucesso se for duplicado.
                df_linhas_para_testar.at[index, "resultado_teste"] = "Sucesso"

        linhas_para_teste_unicidade = df_linhas_para_testar[df_linhas_para_testar["resultado_teste"] == "Sucesso"]

        if not linhas_para_teste_unicidade.empty:
            duplicados_mascara = linhas_para_teste_unicidade[coluna].duplicated(keep=False)
            indices_de_insucesso = linhas_para_teste_unicidade.loc[duplicados_mascara].index
            df_linhas_para_testar.loc[indices_de_insucesso, "resultado_teste"] = "Insucesso"

        # Preparando o dataframe que será salvo pela função 
        df_resultado_teste: pd.DataFrame = df.copy()
        # Adicionando coluna chamada regra_testada
        df_resultado_teste["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado_teste["nome_coluna"] = coluna
        # Adicionando coluna chamada resultado_teste, inicialmente configurada como "Não avaliado
        df_resultado_teste["resultado_teste"] = "Não avaliado" 

        
        df_resultado_teste.loc[df_linhas_para_testar.index, "resultado_teste"] = df_linhas_para_testar["resultado_teste"]

        # Cria dataframe e salva no repositório o resultado do teste
        try:
            df_resultado_teste.to_csv(f'Dados/output/Resultado_{nome_regra}_Coluna_{coluna}_{nome_teste}.csv', index=False, sep=';', encoding='utf_8_sig')
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return  df_resultado_teste 

    def obter_percentual_insucesso_unicidade(resultado: pd.DataFrame) -> float:
        percentual_de_insucesso: float = resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)

        return percentual_de_insucesso
        
    # EXECUTANDO O TESTE 
    
    rodar_testes_de_parametros()
    df_resultado = aplicar_sucesso_e_insucesso_conforme_unicidade()
    percentual_insucesso = obter_percentual_insucesso_unicidade(df_resultado)

    if percentual_insucesso == 0:
        Resultado_Teste = True
    else:
        Resultado_Teste = False

    if tolerancia_com_insucesso_admitida is not None:
        if percentual_insucesso <= tolerancia_com_insucesso_admitida:
            Resultado_Teste = True
        else:
            Resultado_Teste = False

    return Resultado_Teste         

def testar_comparacao_mesma_coluna_entre_dataframes(
    lista_df: list,
    coluna: str,
    nome_regra: str,
    nome_teste: str,
    chave: Union[str, List[str]],
    condicao_na_linha: str = None,
    tolerancia_com_insucesso_admitida: float = None,
    expressao: str = "=="         
) -> bool:
    """
    Verifica se os valores de uma mesma coluna atendem à `expressao`
    entre múltiplos DataFrames.
    Parâmetros:
    -----------
    lista_df : list
        Lista contendo os dataframes para comparação. Os dois primeiros dataframes são obrigatórios (atual e anterior), demais são opcionais.
    coluna : str
        Nome da coluna a ser comparada.
    nome_regra : str
        Nome da regra técnica de qualidade de dados que está sendo testada (exemplo: "RTQD038").
    nome_teste : str
        Nome do teste (usado para identificação).
    chave : str ou list[str]
        Nome da(s) coluna(s) que forma(m) a chave única para identificar as linhas.
        Pode ser uma string para uma única coluna (ex: 'ID') ou uma lista de strings
        para uma chave composta (ex: ['ID_Cliente', 'Data_Pedido']).
    condicao_na_linha : str, optional
        Condição para filtrar linhas antes do teste. Se None, testa todas as linhas.
    tolerancia_com_insucesso_admitida : float, optional
        Percentual máximo de insucesso permitido (ex: 0.05 para 5%). Se None, exige 100% de sucesso.
    expressao : str, optional
        Operador de comparação entre os DataFrames. Aceita:
        '==', '!=', '<', '>', '<=', '>='. Padrão '=='.
    Retorna:
    --------
    bool
        True  → todos os valores da coluna satisfizeram a comparação (ou dentro da tolerância);
        False → caso contrário.
    Efeitos Colaterais:
    ------------------
    - Grava um arquivo em 'Dados/output' contendo todas as linhas do dataframe original;
    - Inclui três colunas a mais neste dataframe:
        - regra_testada - que contém o parametro nome_regra;
        - nome_coluna - que contém o parâmetro coluna; e
        - resultado_teste -  esta coluna receberá:
            - 'Sucesso' ou 'Insucesso' do teste efetuado;
            - 'Não avaliado', nas linhas que não atendem o parâmetro 'condicao_na_linha', se informado; ou
            - 'Em branco', se o valor da coluna testada for None, ou preenchido com "", "None", "nan", "NaN", "NAN", "null", "NULL" ou "Null";
            
    Exemplo:
    --------
    >>> import pandas as pd
    >>> df_jan = pd.DataFrame({
    ...     'id': [1, 2, 3, 4],
    ...     'categoria': ['A', 'B', 'A', 'C'],
    ...     'valor': [100, 200, 300, 400],
    ... })
    >>> df_dez = pd.DataFrame({
    ...     'id': [1, 2, 3, 4],
    ...     'categoria': ['A', 'B', 'A', 'C'],
    ...     'valor': [100, 150, 300, 400],
    ... })
    >>> resultado = testar_comparacao_mesma_coluna_entre_dataframes(
    ...     lista_df=[df_jan, df_dez],
    ...     coluna='valor',
    ...     nome_regra='RTQD038',
    ...     nome_teste='teste_valores',
    ...     chave='id',
    ...     expressao='=='
    ... )
    >>> print(f"Resultado do Teste de RTQD038 na Coluna valor é: {resultado}")
    >>> print(f"Dataframe com resultado do teste, linha a linha, salvo em Dados/output")
    Resultado do Teste de RTQD038 na Coluna valor é: False
    Dataframe com resultado do teste, linha a linha, salvo em Dados/output
    valor  |   regra_testada   |   nome_coluna   |   resultado_teste
    ---------------------------------------------------------------
    100    |   RTQD038         |   valor         |   Sucesso
    200    |   RTQD038         |   valor         |   Insucesso
    300    |   RTQD038         |   valor         |   Sucesso
    400    |   RTQD038         |   valor         |   Sucesso
    """

    # Qual a lógica da programação usada nesta função
    #   1) Ela define várias funções internas para testar os parâmetros;
    #   2) Ela define várias funções internas para testar executar o teste, que envolve basicamente:
    #      a) Testar os parametros;
    #      b) Filtra as linhas, se o parametro condiçao_na_linha foi informado;
    #      c) Aplica o teste nas linhas filtradas, marcando as linhas com sucesso e insucesso (ou 'não avaliado', quando há o parametro condicao_na_linha);
    #      d) Salva um dataframe com o resultado do teste no repositório, na pasta \Dados\output, tendo nele uma coluna com o parametro nome_regra, com as marcações de sucesso, insucesso e 'não avaliado';
    #      e) Calcula o percentual de insucesso e verifica se é menor ou igual a tolerância;
    #      f) Retorna True ou False, conforme o percentual de insucesso e a tolerância admitida.


    # Inicializa a variável que será retornada no final pela funçao
    Resultado_Teste: bool = None

    # FUNÇÕES INTERNAS PARA VERIFICAÇÃO DE PARÂMETROS 

    def checar_se_lista_df_valida():
        if not isinstance(lista_df, list) or not all(isinstance(df, pd.DataFrame) for df in lista_df):
            raise ValueError("Erro: O parâmetro 'lista_df' deve ser uma lista de DataFrames.")
        if len(lista_df) < 2:
            raise ValueError("Erro: A lista de DataFrames deve conter pelo menos dois DataFrames.")

    def checar_se_coluna_existe_em_todos_dataframes():
        for i, df in enumerate(lista_df):
            if coluna not in df.columns:
                raise ValueError(f"Erro: Coluna '{coluna}' não encontrada no DataFrame de índice {i}.")
                
    def checar_se_chave_existe_em_todos_dataframes():
        colunas_chave = [chave] if isinstance(chave, str) else chave
        for i, df in enumerate(lista_df):
            for col in colunas_chave:
                if col not in df.columns:
                    raise ValueError(f"Erro: Chave '{col}' não encontrada no DataFrame de índice {i}.")

    def checar_se_nome_regra_e_nome_teste_sao_string() -> None:
        if not isinstance(nome_regra, str):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' deve ser uma string.")   
         # Verifica se nome_coluna_regra é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_regra):
            raise ValueError("Erro: O Parâmetro 'nome_coluna_regra' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

        if not isinstance(nome_teste, str):
            raise ValueError("Erro: O Parâmetro 'nome_teste' deve ser uma string.")   
         # Verifica se nome_teste é um nome válido para coluna (apenas letras, números e underscores)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", nome_teste):
            raise ValueError("Erro: O Parâmetro 'nome_teste' não é um nome válido. Deve conter apenas letras, números e underscores, e não pode começar com um número.")

    def checar_se_tolerancia_com_insucesso_admitida_eh_numerica() -> None:
        if tolerancia_com_insucesso_admitida is not None:
            if (tolerancia_com_insucesso_admitida < 0 or tolerancia_com_insucesso_admitida > 1):
                raise ValueError("Erro: Parâmetro 'A 'tolerância com insucesso admitida' deve estar entre 0 e 1.")  

    def checar_se_expressao_eh_valida():
        exp_validas = ["==", "!=", "<", ">", "<=", ">="]
        if expressao not in exp_validas:
            raise ValueError(
                f"Erro: Expressão de comparação '{expressao}' não suportada. "
                f"Use uma destas: {', '.join(exp_validas)}."
            )

    def checar_se_condicao_na_linha_eh_query_permitida():
        if isinstance(condicao_na_linha, str):
            padrao_permitido = r"^[\w\s`><=!&|()\"'./-]+$"
            if not re.match(padrao_permitido, condicao_na_linha):
                raise ValueError("Erro: Condição na linha contém caracteres não permitidos.")

    def rodar_testes_de_parametros() -> None:
        checar_se_lista_df_valida()
        checar_se_coluna_existe_em_todos_dataframes()
        checar_se_chave_existe_em_todos_dataframes()
        checar_se_nome_regra_e_nome_teste_sao_string()
        checar_se_tolerancia_com_insucesso_admitida_eh_numerica()
        checar_se_expressao_eh_valida()
        checar_se_condicao_na_linha_eh_query_permitida()

    # FUNÇÃO INTERNA PARA A COMPARAÇÃO ----------------------------------------

    def aplicar_comparacao_entre_dataframes():
        # Define 'chave' como índice em todos os DataFrames 
        colunas_chave = [chave] if isinstance(chave, str) else chave
        lista_df_index = [df.set_index(colunas_chave).copy() for df in lista_df]
        df_base = lista_df_index[0]

        # Filtra pelas linhas especificadas
        if condicao_na_linha:
            try:
                df_base = df_base.query(condicao_na_linha).copy()
            except Exception as e:
                raise ValueError(f"Erro ao aplicar a condição '{condicao_na_linha}': {e}")

        valores_em_branco = {"", "None", "nan", "NaN", "NAN", "null", "NULL", "Null"}
        resultados = []

        # Mapeia a expressão para a função operador
        op_map = {
            "==": operator.eq,
            "!=": operator.ne,
            "<":  operator.lt,
            ">":  operator.gt,
            "<=": operator.le,
            ">=": operator.ge,
        }
        op_func = op_map[expressao]
        
        # Itera sobre cada índice (linha) do DataFrame base para realizar a comparação.
        for idx in df_base.index:
            valor_ref = df_base.at[idx, coluna]
            
            # Verifica se o valor de referência na coluna é nulo ou considerado em branco, e marca como "Em branco".
            if pd.isna(valor_ref) or str(valor_ref).strip() in valores_em_branco:
                resultados.append("Em branco")
                continue

            try:
                valor_ref_cmp = float(str(valor_ref).replace(",", "."))
            except (ValueError, TypeError):
                valor_ref_cmp = str(valor_ref).strip()

            sucesso = True
            for df in lista_df_index[1:]:
                # Se a linha não existir no DF comparado, marca "Não avaliado" e pula a comparação
                if idx not in df.index:
                    resultados.append("Não avaliado")  
                    sucesso = None 
                    break
                    
                valor_cmp = df.loc[idx, coluna]
                if pd.isna(valor_cmp) or str(valor_cmp).strip() in valores_em_branco:
                    sucesso = False
                    break

                try:
                    valor_cmp = float(str(valor_cmp).replace(",", "."))
                except (ValueError, TypeError):
                    valor_cmp = str(valor_cmp).strip()

                if not op_func(valor_ref_cmp, valor_cmp):
                    sucesso = False
                    break

            # Só adiciona "Sucesso" ou "Insucesso" se houve comparação real
            if sucesso is not None:
                resultados.append("Sucesso" if sucesso else "Insucesso")

        # Preparando o dataframe que será salvo pela função
        df_resultado = lista_df[0].copy()
        # Adicionando coluna chamada regra_testada
        df_resultado["regra_testada"] = nome_regra
        # Adicionando coluna chamada nome_coluna
        df_resultado["nome_coluna"] = coluna
        # Adicionando coluna chamada resultado_teste, inicialmente configurada como "Não avaliado
        df_resultado["resultado_teste"] = "Não avaliado"
        
        # Mapear resultados pelo valor da chave e aplicar na coluna resultado_teste
        mapa_resultados = dict(zip(df_base.index, resultados))
        if isinstance(chave, str):
            df_resultado["__chave_temp__"] = df_resultado[chave]
        else:
            df_resultado["__chave_temp__"] = df_resultado[chave].apply(lambda row: tuple(row), axis=1)

        df_resultado["resultado_teste"] = df_resultado["__chave_temp__"].map(mapa_resultados).fillna("Não avaliado")
        df_resultado.drop(columns="__chave_temp__", inplace=True)
        
        try:
            df_resultado.to_csv(
                f'Dados/output/Resultado_{nome_regra}_Coluna_{coluna}_{nome_teste}.csv',
                index=False,
                sep=';',
                encoding='utf_8_sig'
            )
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

        return df_resultado

    def calcular_percentual_insucesso(df_resultado: pd.DataFrame) -> float:
        return df_resultado["resultado_teste"].value_counts(normalize=True).get("Insucesso", 0)

    # EXECUTANDO O TESTE 
    rodar_testes_de_parametros()
    df_com_resultado = aplicar_comparacao_entre_dataframes()
    percentual_insucesso = calcular_percentual_insucesso(df_com_resultado)

    Resultado_Teste = percentual_insucesso == 0
    if tolerancia_com_insucesso_admitida is not None:
        Resultado_Teste = percentual_insucesso <= tolerancia_com_insucesso_admitida

    return Resultado_Teste


def Roda_RTQD(lista_rtqd: list[str], caminho_dados: str, nome_reduzido: str) -> None:
    """
    Executa uma lista de RTQDxxx.py, passando a elas o mesmo DataFrame de entrada.

    Cada RTQDxxx.py deve salvar seu resultado em CSV na pasta 'resultados'.

    Parâmetros:
    ----------
    lista_rtqd : list[str]
        Lista com os nomes dos scripts RTQDxxx.py a serem executados.
    caminho_dados : str
        Caminho do arquivo de dados a ser importado.
    nome_reduzido : str
        Nome reduzido do conjunto, para leitura conforme catálogo.

    Retorna:
    -------
    None
    """

    try:
        df_em_teste = importa_conjunto_conforme_catalogo(
            caminho_arquivo=caminho_dados,
            nome_reduzido=nome_reduzido
        )
    except Exception as e:
        print(f"Erro ao importar os dados: {e}")
        return
        
    # Cria uma lista para armazenar os arquivos CSV gerados durante esta execução
    pasta_resultados = "Dados/output"
    arquivos_gerados = []
    
    for nome_script in lista_rtqd:
        caminho_script = os.path.join("Regras", nome_script)

        if not os.path.isfile(caminho_script):
            print(f"Script {nome_script} não encontrado na pasta 'Regras'. Pulando...")
            continue

        try:
            # Lista os arquivos existentes antes da execução
            arquivos_antes = set(os.listdir(pasta_resultados))
            
            
            nome_modulo = nome_script.replace(".py", "")
            spec = importlib.util.spec_from_file_location(nome_modulo, caminho_script)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)

            if hasattr(modulo, "executar"):
                modulo.executar(df_em_teste)  
            else:
                print(f"O script {nome_script} não possui a função 'executar()'. Pulando...")
                continue
            
            # Lista os arquivos após a execução e detecta quais foram gerados
            arquivos_depois = set(os.listdir(pasta_resultados))
            novos_arquivos = arquivos_depois - arquivos_antes
            arquivos_gerados.extend(list(novos_arquivos))

        except Exception as e:
            print(f"Erro ao executar {nome_script}: {e}")

    # Substitui o bloco anterior de verificação para usar só os arquivos realmente gerados
    if len(arquivos_gerados) > 1:
        colunas_base = None
        
        colunas_diferentes_detectadas = False  # Vai indicar se houve alguma diferença
        
        for nome_arquivo in arquivos_gerados:
            caminho_csv = os.path.join(pasta_resultados, nome_arquivo)

            if os.path.isfile(caminho_csv):
                try:
                    df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8-sig')
                    colunas_atual = set(df.columns)

                    if colunas_base is None:
                        colunas_base = colunas_atual
                    elif colunas_atual != colunas_base:
                        print(f"As colunas de '{nome_arquivo}' são diferentes das demais.")
                        
                        colunas_diferentes_detectadas = True
                        
                except Exception as e:
                    print(f"Erro ao ler '{nome_arquivo}': {e}")
            else:
                print(f"Arquivo '{nome_arquivo}' não encontrado para verificação de colunas.")
        if not colunas_diferentes_detectadas:
            print("As colunas de todos os arquivos gerados são iguais.")
            
            try:
                # Lê todos os arquivos e os armazena em uma lista de DataFrames
                dfs = []
                for nome_arquivo in arquivos_gerados:
                    caminho_csv = os.path.join(pasta_resultados, nome_arquivo)
                    df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8-sig')
                    dfs.append(df)

                # Concatena os DataFrames
                df_concatenado = pd.concat(dfs, ignore_index=True)

                # Cria o nome do arquivo consolidado com base na lista de RTQDs
                nomes_rtqds = [nome.replace(".py", "") for nome in lista_rtqd]
                nome_consolidado = "_".join(nomes_rtqds) + "_resultado_consolidado.csv"
                caminho_consolidado = os.path.join(pasta_resultados, nome_consolidado)

                # Salva o arquivo consolidado
                df_concatenado.to_csv(caminho_consolidado, sep=';', index=False, encoding='utf-8-sig')
                print(f"Arquivo consolidado salvo em: {caminho_consolidado}")

                # Exclui os arquivos individuais
                for nome_arquivo in arquivos_gerados:
                    os.remove(os.path.join(pasta_resultados, nome_arquivo))
                    print(f"Arquivo removido: {nome_arquivo}")

            except Exception as e:
                print(f"Erro ao consolidar ou remover arquivos: {e}")