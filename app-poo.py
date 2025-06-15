import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.set_page_config(page_title="Balanço de Energia ONS", layout="wide")

@st.cache_data
def carregar_dados():
    url_csv = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_2023.csv"
    response = requests.get(url_csv)
    if response.status_code == 200:
        with open("dados.csv", "wb") as arquivo:
            arquivo.write(response.content)
        df = pd.read_csv("dados.csv", sep=';')
        df.columns = ['id_subsistema', 'nom_subsistema', 'din_instante', 'val_gerhidraulica', 'val_gertermica', 'val_gereolica', 'val_gersolar', 'val_carga', 'val_intercambio']
        numeric_cols = ['val_gerhidraulica', 'val_gertermica', 'val_gereolica', 'val_gersolar', 'val_carga', 'val_intercambio']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['din_instante'] = pd.to_datetime(df['din_instante'])
        return df
    else:
        st.error("Erro ao baixar os dados.")
        return None

class GraficosEnergia:
    def __init__(self, siglas_subsistema):
        self.siglas_subsistema = siglas_subsistema

    def grafico_pizza(self, sizes, sigla_desejada):
        st.subheader("Porcentagem de cada tipo de geração")
        labels = ['Hidráulica', 'Térmica', 'Eólica', 'Solar']
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        ax1.set_title(f'Porcentagem de cada tipo de geração para {self.siglas_subsistema.get(sigla_desejada)}')
        st.pyplot(fig1)

    def grafico_barras_tipo(self, sizes, soma_geracao, sigla_desejada):
        st.subheader("Geração de Energia por Tipo")
        labels = ['Hidráulica', 'Térmica', 'Eólica', 'Solar']
        fig2, ax2 = plt.subplots()
        bars = ax2.bar(labels, sizes, color=['blue', 'red', 'green', 'orange'])
        ax2.set_ylabel('Geração (MWh)')
        ax2.set_title(f'Geração de Energia por Tipo para {self.siglas_subsistema.get(sigla_desejada)}')
        for bar, size in zip(bars, sizes):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2, f'{(size/soma_geracao)*100:.1f}%', ha='center', va='center', color='white')
        st.pyplot(fig2)

    def grafico_barras_balanco(self, values, sigla_desejada):
        st.subheader("Geração, Carga e Intercâmbio")
        labels2 = ['Total Gerado', 'Carga', 'Intercâmbio']
        fig3, ax3 = plt.subplots()
        bars2 = ax3.bar(labels2, values, color=['green', 'red', 'blue'])
        for bar, value in zip(bars2, values):
            ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{value:,.2f} MWh', ha='center', va='bottom', color='black')
        ax3.set_ylabel('MWh')
        ax3.set_title(f'Geração, Carga e Intercâmbio para {self.siglas_subsistema.get(sigla_desejada)}')
        st.pyplot(fig3)

class BalancoEnergiaApp:
    def __init__(self):
        self.siglas_subsistema = {
            'NE': 'Nordeste',
            'SE': 'Sudeste/Centro-Oeste',
            'N': 'Norte',
            'S': 'Sul',
            'SIN': 'Sistema Interligado Nacional'
        }
        self.df = carregar_dados()

    def run(self):
        if self.df is not None:
            st.title("Balanço de Energia por Subsistema (ONS 2023)")

            siglas_disponiveis = self.df['id_subsistema'].unique().tolist()
            sigla_desejada = st.selectbox(
                "Escolha o subsistema:",
                siglas_disponiveis,
                format_func=lambda x: self.siglas_subsistema.get(x, x)
            )

            df_filtrado = self.df[self.df['id_subsistema'] == sigla_desejada]

            soma_gerhidraulica = df_filtrado['val_gerhidraulica'].sum()
            soma_gertermica = df_filtrado['val_gertermica'].sum()
            soma_gereolica = df_filtrado['val_gereolica'].sum()
            soma_gersolar = df_filtrado['val_gersolar'].sum()
            soma_geracao = soma_gerhidraulica + soma_gertermica + soma_gereolica + soma_gersolar
            soma_carga = df_filtrado['val_carga'].sum()
            intercambio = df_filtrado['val_intercambio'].sum()

            dados_sistema = {
                'Variável': [
                    'Geração Hidráulica', 'Geração Térmica', 'Geração Eólica',
                    'Geração Solar', 'Total da Geração', 'Carga'
                ],
                'Valor (MWh)': [
                    soma_gerhidraulica, soma_gertermica, soma_gereolica,
                    soma_gersolar, soma_geracao, soma_carga
                ]
            }
            df_sistema = pd.DataFrame(dados_sistema)
            st.subheader("Tabela Resumo")
            st.dataframe(df_sistema.style.format({'Valor (MWh)': '{:,.2f}'}), use_container_width=True)

            # Gráficos usando a classe de gráficos
            sizes = [soma_gerhidraulica, soma_gertermica, soma_gereolica, soma_gersolar]
            graficos = GraficosEnergia(self.siglas_subsistema)
            graficos.grafico_pizza(sizes, sigla_desejada)
            graficos.grafico_barras_tipo(sizes, soma_geracao, sigla_desejada)
            values = [soma_geracao, soma_carga, intercambio]
            graficos.grafico_barras_balanco(values, sigla_desejada)

if __name__ == "__main__":
    app = BalancoEnergiaApp()
    app.run()