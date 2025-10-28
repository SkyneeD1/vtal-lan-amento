import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Lançamentos", page_icon="🧠", layout="centered")

st.title("🧠 Lançamentos")
st.subheader("📋 Cole sua tabela:")

texto = st.text_area("Cole aqui:", height=300)

if st.button("🚀 Processar"):
    if texto.strip() == "":
        st.warning("⚠️ Cole os dados no campo acima.")
    else:
        linhas = texto.strip().splitlines()

        # 🔥 Junta linhas quebradas
        linhas_corrigidas = []
        linha_acumulada = ""

        for linha in linhas:
            linha_check = linha.strip()
            if any(x in linha_check.upper() for x in ["CÁLCULO LIQUIDADO", "VERSÃO", "PÁG", "DESCRIÇÃO DO BRUTO"]):
                continue  # Ignorar cabeçalhos e rodapés

            numeros = re.findall(r'[\d\.,]+', linha_check)
            if len(numeros) >= 3:  # agora há pelo menos Valor Corrigido, Juros e Total
                if linha_acumulada:
                    linha_completa = linha_acumulada + " " + linha_check
                    linhas_corrigidas.append(linha_completa.strip())
                    linha_acumulada = ""
                else:
                    linhas_corrigidas.append(linha_check.strip())
            else:
                linha_acumulada += " " + linha_check

        if linha_acumulada:
            linhas_corrigidas.append(linha_acumulada.strip())

        # 🏗️ Processamento das linhas corrigidas
        dados = []
        for linha in linhas_corrigidas:
            numeros = re.findall(r'[\d\.,]+', linha)

            if len(numeros) >= 3:
                valor_corrigido = numeros[-3]
                juros = numeros[-2]

                try:
                    valor_corrigido = float(valor_corrigido.replace('.', '').replace(',', '.'))
                    juros = float(juros.replace('.', '').replace(',', '.'))
                except:
                    valor_corrigido, juros = 0.0, 0.0

                descricao = linha
                for num in numeros[-3:]:
                    descricao = descricao.rsplit(num, 1)[0]
                descricao = descricao.strip().upper()

                dados.append([descricao, valor_corrigido, juros])

        df = pd.DataFrame(dados, columns=['Descricao', 'Valor Corrigido', 'Juros'])

        # 🔥 Agrupamento por verba consolidada
        def agrupar_verba(descricao):
            if "FGTS" in descricao and "MULTA" not in descricao:
                return "FGTS"
            if "MULTA SOBRE FGTS" in descricao:
                return "MULTA FGTS"

            prefixos_reflexos = ["13º", "FÉRIAS", "AVISO", "REPOUSO"]

            if any(descricao.startswith(prefixo) for prefixo in prefixos_reflexos):
                if "SOBRE" in descricao:
                    partes = descricao.split("SOBRE", 1)
                    verba = partes[1].strip()
                    return verba
                else:
                    return descricao
            else:
                return descricao

        df['Verba Consolidada'] = df['Descricao'].apply(agrupar_verba)

        resultado = df.groupby('Verba Consolidada')[['Valor Corrigido', 'Juros']].sum().reset_index()

        st.success("✅ Processamento concluído!")

        st.subheader("📊 Resultado Consolidado (sem coluna Total):")

        # ➕ Adiciona linha de total geral
        linha_total = pd.DataFrame([[
            "TOTAL GERAL",
            resultado['Valor Corrigido'].sum(),
            resultado['Juros'].sum()
        ]], columns=['Verba Consolidada', 'Valor Corrigido', 'Juros'])

        resultado_com_total = pd.concat([resultado, linha_total], ignore_index=True)

        # 🔧 Formatação brasileira
        resultado_exibicao = resultado_com_total.copy()
        for col in ['Valor Corrigido', 'Juros']:
            resultado_exibicao[col] = resultado_exibicao[col].apply(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        st.dataframe(resultado_exibicao)
