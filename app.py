import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(layout="wide")

# =========================
# 🔐 FIREBASE
# =========================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# =========================
# 👤 USUÁRIOS
# =========================
usuarios = {
    "carlos": "19982410",
    "rayssa": "19982410"
}

# =========================
# ⚙️ SESSION STATE
# =========================
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

if "dados_carregados" not in st.session_state:
    st.session_state["dados_carregados"] = False

if "salario" not in st.session_state:
    st.session_state["salario"] = {}

if "gastos" not in st.session_state:
    st.session_state["gastos"] = {}

# =========================
# 🔄 FIREBASE
# =========================
def carregar_dados():
    doc = db.collection("controle_financeiro").document("casal").get()
    if doc.exists:
        dados = doc.to_dict()
        st.session_state["salario"] = dados.get("salario", {})
        st.session_state["gastos"] = dados.get("gastos", {})

def salvar_dados():
    db.collection("controle_financeiro").document("casal").set({
        "salario": st.session_state["salario"],
        "gastos": st.session_state["gastos"]
    }, merge=True)

# =========================
# 🔐 LOGIN
# =========================
if st.session_state["usuario"] is None:

    st.title("🔐 Login")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user in usuarios and usuarios[user] == senha:
            st.session_state["usuario"] = user
            st.session_state["dados_carregados"] = False
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    st.stop()
    
    
# =========================
# MENU
# =========================
pagina = st.radio("", ["📊 Análise", "➕ Nova Transação"], horizontal=True)


# =========================
# 📅 DATA
# =========================
hoje = datetime.datetime.now()

meses = []
for i in range(6):
    data = hoje - datetime.timedelta(days=30 * i)
    meses.append(data.strftime('%Y-%m'))

meses = list(dict.fromkeys(meses))  # remove duplicados

mes = st.selectbox("📅 Mês", meses)

if not st.session_state["dados_carregados"]:
    carregar_dados()
    st.session_state["dados_carregados"] = True



# =========================
# 📊 ANALISE
# =========================
if pagina == "📊 Análise":

    st.title("")

    st.subheader("💰 Controle Financeiro")
    
    salario_mes = st.session_state['salario'].get(mes, 0)
    gastos_mes = st.session_state['gastos'].get(mes, [])

    total_gastos = sum(g["valor"] for g in gastos_mes)
    saldo = salario_mes - total_gastos

    c1, c2, c3 = st.columns(3)

    c1.metric("Receita", f"R$ {salario_mes:.2f}")
    c2.metric("Despesas", f"R$ {total_gastos:.2f}")
    c3.metric("Saldo", f"R$ {saldo:.2f}")

    st.divider()

    # ✏️ EDITAR RECEITA
    st.subheader("✏️ Editar Receita")

    novo_salario = st.number_input(
        "Valor da receita do mês",
        value=float(salario_mes)
    )

    if st.button("Salvar Receita"):
        st.session_state['salario'][mes] = novo_salario
        salvar_dados()
        st.success("Receita atualizada!")
        st.rerun()

    st.divider()

    # 📊 GRÁFICO
    categorias = {}
    for g in gastos_mes:
        cat = g.get("categoria", "Outros")
        categorias[cat] = categorias.get(cat, 0) + g["valor"]

    if categorias:
        df = pd.DataFrame({
            "Categoria": list(categorias.keys()),
            "Valor": list(categorias.values())
        })

        fig = px.pie(df, names="Categoria", values="Valor", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados ainda")

    st.divider()

    # 🗃️ LISTA DE GASTOS
    st.subheader("🗃️ Lista de Gastos")

    if len(gastos_mes) == 0:
        st.write("Sem gastos")
    else:
        for i, gasto in enumerate(gastos_mes):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(
                    f"{gasto['desc']} - R$ {gasto['valor']} "
                    f"(👤 {gasto.get('usuario','')})"
                )

            with col2:
                if st.button("❌", key=f"del_{mes}_{i}"):
                    st.session_state['gastos'][mes].pop(i)
                    salvar_dados()
                    st.rerun()

# =========================
# ➕ NOVA TRANSAÇÃO
# =========================
if pagina == "➕ Nova Transação":

    st.subheader("Nova Despesa")

    with st.form("form_transacao"):

        tipo = st.selectbox("Tipo", ["Despesa"])
        valor = st.number_input("Valor", min_value=0.0)

        categoria = st.selectbox(
            "Categoria",
            ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde"]
        )

        descricao = st.text_input("Descrição")

        if st.form_submit_button("Adicionar"):

            if tipo == "Receita":
                st.session_state['salario'][mes] = st.session_state['salario'].get(mes, 0) + valor

            else:
                if mes not in st.session_state['gastos']:
                    st.session_state['gastos'][mes] = []

                st.session_state['gastos'][mes].append({
                    "desc": descricao,
                    "valor": valor,
                    "categoria": categoria,
                    "usuario": st.session_state["usuario"]
                })

            salvar_dados()
            st.success("Salvo com sucesso!")
            st.rerun()
