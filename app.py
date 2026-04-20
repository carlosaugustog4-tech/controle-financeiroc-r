import streamlit as st
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

#_______________________________________________________________Conexão com Firebase___________________________________________________
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

#_______________________________________________________________Usuários_______________________________________________________________
usuarios = {
    "carlos": "19982410",
    "rayssa": "19982410"
}

#_______________________________________________________________Controle de sessão______________________________________________________
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

if "dados_carregados" not in st.session_state:
    st.session_state["dados_carregados"] = False

if 'salario' not in st.session_state:
    st.session_state["salario"] = {}

if 'gastos' not in st.session_state:
    st.session_state["gastos"] = {}

#_______________________________________________________________Carregar dados____________________________________________________________
def carregar_dados():
    doc = db.collection("controle_financeiro").document("casal").get()

    if doc.exists:
        dados = doc.to_dict()
        st.session_state["salario"] = dados.get("salario", {})
        st.session_state["gastos"] = dados.get("gastos", {})

#_______________________________________________________________Salvar dados_______________________________________________________________
def salvar_dados():
    db.collection("controle_financeiro").document("casal").set({
        "salario": st.session_state["salario"],
        "gastos": st.session_state["gastos"]
    }, merge=True)

# __________________________________________ TELA DE LOGIN __________________________________________
if st.session_state["usuario"] is None:

    st.title("🔐 Login")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user in usuarios and usuarios[user] == senha:
            st.session_state["usuario"] = user
            st.session_state["dados_carregados"] = False
            st.success("Login realizado!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    st.stop()

#_______________________________________________________________APP_______________________________________________________________

st.title("📊❤️ Controle Financeiro ❤️📊")
st.write(f"👤 Usuário: {st.session_state['usuario']}")
st.write("C&R 👩🏽‍❤️‍👨🏻")

#_______________________________________________________________Data_______________________________________________________________
hoje = datetime.datetime.now()

meses = []
for i in range(12):
    data = hoje - datetime.timedelta(days=30 * i)
    meses.append(data.strftime('%Y-%m'))

meses = list(dict.fromkeys(meses))
mes = st.selectbox('🗓️ Data 🗓️', meses)


if not st.session_state["dados_carregados"]:
    carregar_dados()
    st.session_state["dados_carregados"] = True

# __________________________________________ SALÁRIO __________________________________________

salario_mes = st.session_state['salario'].get(mes, 0)

st.subheader('💰 Salário do Mês 💰')

salario = st.number_input("Salário", min_value=0.0)

if st.button('Adicionar Salário'):
    st.session_state['salario'][mes] = salario
    salvar_dados()
    st.success(f'Salário de R$ {salario} salvo para {mes}')

salario_mes = st.session_state['salario'].get(mes, 0)

st.write(f'R$ {salario_mes}')

# __________________________________________ GASTOS __________________________________________

st.subheader('💸 Gastos 💸')

if mes not in st.session_state['gastos']:
    st.session_state['gastos'][mes] = []

with st.form("form_gasto"):
    descricao = st.text_input("Descrição de Gastos")
    valor_gasto = st.number_input("Valor Gasto", min_value=0.0)

    submitted = st.form_submit_button("Adicionar Gasto")

    if submitted:
        if descricao and valor_gasto > 0:
            st.session_state['gastos'][mes].append({
                'desc': descricao,
                'valor': valor_gasto,
                'usuario': st.session_state["usuario"]  # 🔥 quem adicionou
            })
            salvar_dados()
            st.success("Gasto Adicionado!")
        else:
            st.warning("Preencha os dados corretamente")

gastos_mes = st.session_state['gastos'][mes]

st.subheader("🗃️ Lista de Gastos 🗃️")

if len(gastos_mes) == 0:
    st.write("Sem Gastos")
else:
    for i, gasto in enumerate(gastos_mes):
        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(f"{gasto['desc']} - R$ {gasto['valor']} (👤 {gasto.get('usuario', '')})")

        with col2:
            if st.button("❌", key=f"del_{mes}_{i}"):
                st.session_state['gastos'][mes].pop(i)
                salvar_dados()
                st.rerun()

# __________________________________________ RESUMO __________________________________________

total_gastos = sum(g["valor"] for g in gastos_mes)

st.subheader("🗄️ Total de Gastos 🗄️")
st.write(f"R$ {total_gastos}")

saldo = salario_mes - total_gastos

st.subheader("⚖️ Saldo do Mês ⚖️")

if saldo < 0:
    st.markdown(f"<h2 style='color:red'>R$ {saldo}</h2>", unsafe_allow_html=True)
else:
    st.markdown(f"<h2 style='color:green'>R$ {saldo}</h2>", unsafe_allow_html=True)
