import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gestão Financeira Pro", page_icon="🚀", layout="wide")
ARQUIVO_DADOS = 'meu_financeiro.json'

# --- 2. FUNÇÕES DE DADOS ---
def carregar_dados():
    # Estrutura padrão caso o arquivo não exista
    padrao = {
        "renda": 0.0, 
        "transacoes": [], 
        "metas_pct": {"Necessidades": 50, "Desejos": 30, "Investimentos": 20}
    }
    
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                # Garante que a chave 'metas_pct' exista (para quem vem de versões anteriores)
                if "metas_pct" not in dados:
                    dados["metas_pct"] = padrao["metas_pct"]
                return dados
        except:
            return padrao
    return padrao

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- 3. INTERFACE DO SISTEMA ---
def main():
    st.title("🚀 Meu Controle Financeiro 3.0")
    st.markdown("---")

    dados = carregar_dados()

    # --- BARRA LATERAL (CONFIGURAÇÕES) ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # 1. Renda
        st.subheader("1. Sua Renda")
        nova_renda = st.number_input(
            "Renda Líquida (R$)", 
            value=float(dados.get("renda", 0.0)), 
            step=50.0
        )
        
        st.divider()
        
        # 2. Personalizar Metas
        st.subheader("2. Personalizar Metas (%)")
        st.info("Defina quanto % do salário vai para cada área.")
        
        # Sliders para ajustar porcentagem
        meta_nec = st.slider("Necessidades (Contas, Casa)", 0, 100, dados["metas_pct"]["Necessidades"])
        meta_des = st.slider("Desejos (Lazer, Compras)", 0, 100, dados["metas_pct"]["Desejos"])
        meta_inv = st.slider("Investimentos/Dívidas", 0, 100, dados["metas_pct"]["Investimentos"])
        
        total_pct = meta_nec + meta_des + meta_inv
        if total_pct != 100:
            st.warning(f"⚠️ Atenção: A soma das porcentagens está em {total_pct}%. O ideal é 100%.")
        
        # Botão para Salvar Configurações
        if st.button("💾 Atualizar Configurações"):
            dados["renda"] = nova_renda
            dados["metas_pct"] = {
                "Necessidades": meta_nec,
                "Desejos": meta_des,
                "Investimentos": meta_inv
            }
            salvar_dados(dados)
            st.success("Configurações salvas!")
            st.rerun()

    # --- PAINEL PRINCIPAL ---

    # 1. Adicionar Gasto
    with st.expander("➕ Registrar Novo Gasto", expanded=True):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1:
            desc = st.text_input("Descrição", placeholder="Ex: Mercado mensal")
        with c2:
            valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0)
        with c3:
            cat = st.selectbox("Categoria", ["Necessidades", "Desejos", "Investimentos"])
        with c4:
            st.write("")
            st.write("") # Espaço para alinhar botão
            if st.button("Lançar"):
                if desc and valor > 0:
                    nova = {
                        "id": str(datetime.now().timestamp()), # ID único para poder apagar depois
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "descricao": desc,
                        "valor": valor,
                        "categoria": cat
                    }
                    dados["transacoes"].append(nova)
                    salvar_dados(dados)
                    st.success("Adicionado!")
                    st.rerun()
                else:
                    st.error("Preencha descrição e valor!")

    st.divider()

    # 2. Dashboard Inteligente
    if dados["renda"] > 0:
        total_gasto = sum(t["valor"] for t in dados["transacoes"])
        saldo = dados["renda"] - total_gasto
        
        # KPI Cards
        k1, k2, k3 = st.columns(3)
        k1.metric("Renda Mensal", f"R$ {dados['renda']:.2f}")
        k2.metric("Total Gasto", f"R$ {total_gasto:.2f}")
        k3.metric("Saldo Livre", f"R$ {saldo:.2f}", delta_color="normal" if saldo > 0 else "inverse")

        st.subheader("📊 Acompanhamento de Metas")
        
        # Processar Gastos por Categoria
        gastos_cat = {"Necessidades": 0.0, "Desejos": 0.0, "Investimentos": 0.0}
        
        for t in dados["transacoes"]:
            c_nome = t["categoria"]
            # Compatibilidade com versões antigas
            if "Necessidade" in c_nome: c_nome = "Necessidades"
            elif "Desejo" in c_nome: c_nome = "Desejos"
            elif "Investimento" in c_nome: c_nome = "Investimentos"
            
            if c_nome in gastos_cat:
                gastos_cat[c_nome] += t["valor"]

        # Exibir Barras Personalizadas
        col_metas = st.columns(3)
        chaves = list(dados["metas_pct"].keys()) # ["Necessidades", "Desejos", "Investimentos"]
        
        for i, categoria in enumerate(chaves):
            porcentagem_definida = dados["metas_pct"][categoria] / 100
            meta_valor = dados["renda"] * porcentagem_definida
            gasto_atual = gastos_cat.get(categoria, 0.0)
            
            with col_metas[i]:
                st.write(f"**{categoria}** ({dados['metas_pct'][categoria]}%)")
                st.write(f"R$ {gasto_atual:.2f} / R$ {meta_valor:.2f}")
                
                if meta_valor > 0:
                    progresso = min(gasto_atual / meta_valor, 1.0)
                    cor_barra = "green" if gasto_atual <= meta_valor else "red"
                    st.progress(progresso)
                    if gasto_atual > meta_valor:
                        st.caption(f"🚨 Passou R$ {gasto_atual - meta_valor:.2f}")
                else:
                    st.progress(0)

    # 3. Gerenciar Histórico (Tabela + Excluir)
    st.divider()
    st.subheader("📝 Gerenciar Histórico")
    
    if dados["transacoes"]:
        # Criar tabela visual
        df = pd.DataFrame(dados["transacoes"])
        # Selecionar colunas bonitas
        df_visual = df[["data", "descricao", "categoria", "valor"]]
        st.dataframe(df_visual.iloc[::-1], use_container_width=True, hide_index=True)
        
        # Área de Exclusão
        with st.expander("🗑️ Excluir um lançamento errado"):
            st.warning("Cuidado: A exclusão não pode ser desfeita.")
            # Criar lista de opções para o selectbox
            opcoes = [f"{i} | {t['data']} - {t['descricao']} (R$ {t['valor']})" for i, t in enumerate(dados["transacoes"])]
            
            escolha = st.selectbox("Selecione o item para apagar:", opcoes)
            
            if st.button("Apagar Item Selecionado"):
                index_apagar = int(escolha.split(" | ")[0])
                item_removido = dados["transacoes"].pop(index_apagar)
                salvar_dados(dados)
                st.success(f"Item '{item_removido['descricao']}' removido!")
                st.rerun()
    else:
        st.info("Nenhuma transação registrada.")

if __name__ == "__main__":
    main()