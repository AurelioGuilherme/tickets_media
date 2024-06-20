import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd
import plotly.express as px

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        st.error(e)

def calculate_daily_average(conn, agente):
    today = date.today().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(nota) FROM notas WHERE date(data) = ? AND agente = ?", (today, agente))
    row = cursor.fetchone()
    return row[0] if row[0] is not None else 0.0

def calculate_monthly_average(conn, agente):
    this_month = datetime.now().strftime("%Y-%m")
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(nota) FROM notas WHERE strftime('%Y-%m', data) = ? AND agente = ?", (this_month, agente))
    row = cursor.fetchone()
    return row[0] if row[0] is not None else 0.0

def fetch_user_notes(conn, agente):
    cursor = conn.cursor()
    cursor.execute("SELECT ticket, data, nota FROM notas WHERE agente = ?", (agente,))
    rows = cursor.fetchall()
    return rows

def run_query(query,conn):

    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Erro ao executar a query: {e}")
    finally:
        conn.close()

def fetch_daily_averages(conn, agente):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date(data) as dia, AVG(nota) as media
        FROM notas
        WHERE agente = ?
        GROUP BY date(data)
        ORDER BY dia
    """, (agente,))
    rows = cursor.fetchall()
    return rows

        

def main():
    conn = create_connection("tickets_database.db")
    
    if conn is None:
        st.error("**Erro ao conectar ao banco de dados**")
        return
    
    cursor = conn.cursor()
    
    if "show_cadastro" not in st.session_state:
        st.session_state.show_cadastro = False

    if "usuario" not in st.session_state:
        st.session_state.usuario = None

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        if st.session_state.usuario is None:
            with st.form(key='login_form'):
                usuario = st.text_input('**Qual o seu RA?**')
                submit_button = st.form_submit_button(label='ENTRAR')

                if submit_button:
                    cursor.execute("SELECT ra, nome, senha FROM pessoas WHERE ra = ? OR nome = ?", (usuario, usuario))
                    user = cursor.fetchone()

                    if user:
                        st.session_state.usuario = user
                    else:
                        st.warning("Usuário não encontrado. Por favor, cadastre-se.")
                        st.session_state.show_cadastro = True
        
        if st.session_state.usuario:
            with st.form(key='senha_form'):
                senha = st.text_input('Digite sua senha:', type="password")
                senha_submit_button = st.form_submit_button(label='VALIDAR')

                if senha_submit_button:
                    if len(st.session_state.usuario) >= 3 and senha == st.session_state.usuario[2]:
                        st.success("Login realizado com sucesso!")
                        st.session_state.logged_in = True
                    else:
                        st.error("Senha incorreta!")
                        st.session_state.usuario = None  # Reset to allow retry

    if st.session_state.show_cadastro:
        with st.form(key='cadastro_form'):
            novo_nome = st.text_input('Nome:')
            novo_ra = st.text_input('RA:')
            nova_senha = st.text_input('Senha:', type="password")
            cadastro_submit_button = st.form_submit_button(label='CADASTRAR')

            if cadastro_submit_button:
                cursor.execute("INSERT INTO pessoas (ra, nome,  senha) VALUES (?, ?, ?)",
                               (novo_ra, novo_nome, nova_senha))
                conn.commit()
                st.success("Cadastro realizado com sucesso!")
                st.session_state.show_cadastro = False

    if st.session_state.logged_in:
        st.title(f"Bem-vindo, {st.session_state.usuario[1]}!")
        if st.session_state.usuario[1] == 'TESTE':
            query = st.text_area("**Digite sua consulta SQL aqui:**")
            if st.button("Executar"):
                if query.strip():
                    result = run_query(query,conn)
                    if result is not None:
                        st.write("Resultado da consulta:")
                        st.dataframe(result)
                else:
                    st.warning("Por favor, insira uma consulta SQL.")

        
        # Função para atualizar e exibir médias
        def update_and_show_averages():
            agente = st.session_state.usuario[0]  # RA do agente logado
            daily_avg = calculate_daily_average(conn, agente)
            monthly_avg = calculate_monthly_average(conn, agente)
            st.write(f"**Média de notas hoje:** {daily_avg:.2f}")
            st.write(f"**Média de notas este mês:** {monthly_avg:.2f}")



        with st.form(key='ticket_form'):
            ticket = st.text_input('Digite o ticket:')
            nota = st.radio('Selecione a nota (0 a 10):', options=list(range(11)))
            ticket_submit_button = st.form_submit_button(label='Enviar')

            if ticket_submit_button:
                data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute("INSERT INTO notas (ticket, agente, data, nota) VALUES (?, ?, ?, ?)",
                                   (ticket, st.session_state.usuario[0], data_atual, nota))
                    conn.commit()
                    st.success("Ticket e nota enviados com sucesso!")
                    
            

                except sqlite3.IntegrityError as e:
                    
                    st.error(f"**Ticket já inserido**")

        with st.expander('mostrar tickets e notas'):# Exibir notas do usuário em uma tabela
            # Exibir notas do usuário em uma tabela usando Pandas
            notas_usuario = fetch_user_notes(conn, st.session_state.usuario[0])
            st.write("---")
            st.write("## Notas Registradas:")
            if notas_usuario:
                update_and_show_averages()
                df_notas = pd.DataFrame(notas_usuario, columns=["Ticket", "Data", "Nota"])
                st.dataframe(df_notas)
                daily_averages = fetch_daily_averages(conn, st.session_state.usuario[0])
                if daily_averages:
                    df_daily_avg = pd.DataFrame(daily_averages, columns=["Dia", "Média"])
                    fig = px.bar(df_daily_avg, x='Dia', y='Média', title='Média de Notas por Dia')
                    st.plotly_chart(fig)
                else:
                    st.write("Nenhuma média de notas disponível para exibir.")

            else:
                update_and_show_averages()
                st.write("Nenhuma nota registrada.")


        
        st.write('---')


        if st.button("Sair"):
            st.session_state.logged_in = False
            st.session_state.usuario = None
            st.session_state.show_cadastro = None
    

if __name__ == "__main__":
    main()