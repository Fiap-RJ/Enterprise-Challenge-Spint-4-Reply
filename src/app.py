import streamlit as st
import pandas as pd
import plotly.express as px
from data_connector import get_mock_feature_store_data, get_mock_prediction

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Manutenção Preditiva",
    page_icon="🔧",
    layout="wide"
)

# --- Funções com Cache ---
@st.cache_data(ttl=60) # Armazena o resultado por 60 segundos para evitar buscas repetidas
def load_data():
    """
    Carrega os dados da feature store (usando a função mock).
    O decorador @st.cache_data garante que não recarregamos os dados a cada interação.
    """
    return get_mock_feature_store_data()

# --- Título e Atualização ---
st.title("🔧 Dashboard de Manutenção Preditiva")

if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear() # Limpa o cache para forçar a recarga dos dados

# Carrega os dados mais recentes
df_features = load_data()

# --- Visão Geral (Home Page) ---
st.markdown("<br>", unsafe_allow_html=True)
st.header("Visão Geral do Status das Máquinas")

# Verifica se há dados para exibir
if df_features.empty:
    st.warning("⚠️ Nenhum dado disponível no momento. Tente atualizar os dados.")
else:
    # Classifica as máquinas por status
    critical_machines = []
    alert_machines = []
    normal_machines = []
    
    for _, row in df_features.iterrows():
        machine_id = row['machine_id']
        vib_media = row['vib_media_5h']
        temp_max = row['temp_max_24h']
        
        # Define status da vibração
        if vib_media > 4.5:
            vib_color = "red"
            vib_status = "Crítico"
        elif vib_media > 3.5:
            vib_color = "orange"
            vib_status = "Atenção"
        else:
            vib_color = "green"
            vib_status = "Normal"
        
        # Define status da temperatura
        if temp_max > 90:
            temp_color = "red"
            temp_status = "Alta"
        elif temp_max > 80:
            temp_color = "orange"
            temp_status = "Moderada"
        else:
            temp_color = "green"
            temp_status = "Normal"
        
        # Determina status geral da máquina
        if vib_color == "red" or temp_color == "red":
            overall_status = "CRÍTICO"
            critical_machines.append((machine_id, row, vib_media, temp_max, vib_status, temp_status))
        elif vib_color == "orange" or temp_color == "orange":
            overall_status = "ATENÇÃO"
            alert_machines.append((machine_id, row, vib_media, temp_max, vib_status, temp_status))
        else:
            overall_status = "NORMAL"
            normal_machines.append((machine_id, row, vib_media, temp_max, vib_status, temp_status))
    
    # Exibe resumo de status
    col_summary1, col_summary2, col_summary3 = st.columns(3)
    
    with col_summary1:
        st.metric(
            label="🔴 Máquinas Críticas",
            value=len(critical_machines),
            delta="Requer ação imediata" if len(critical_machines) > 0 else "Nenhuma"
        )
    
    with col_summary2:
        st.metric(
            label="🟡 Máquinas em Alerta",
            value=len(alert_machines),
            delta="Monitorar de perto" if len(alert_machines) > 0 else "Nenhuma"
        )
    
    with col_summary3:
        st.metric(
            label="🟢 Máquinas Normais",
            value=len(normal_machines),
            delta="Funcionando bem"
        )
    
    # Adiciona espaçamento entre resumo e máquinas com problemas
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Exibe apenas máquinas com problemas (críticas e em alerta)
    machines_with_issues = critical_machines + alert_machines
    
    if machines_with_issues:
        st.subheader("🚨 Máquinas que Requerem Atenção")
        
        # Define as colunas para os cartões (máximo 5 colunas)
        num_issue_machines = len(machines_with_issues)
        columns = st.columns(min(num_issue_machines, 5))
        
        # Itera sobre máquinas com problemas
        for i, (machine_id, row, vib_media, temp_max, vib_status, temp_status) in enumerate(machines_with_issues):
            # Determina se é crítico ou alerta
            is_critical = vib_media > 4.5 or temp_max > 90
            
            # Cria o cartão dentro de uma coluna
            col_index = i % len(columns)
            with columns[col_index]:
                # Container para o cartão da máquina
                with st.container():
                    if is_critical:
                        st.markdown(f"### 🔴 {machine_id}")
                    else:
                        st.markdown(f"### 🟡 {machine_id}")
                    
                    # Métricas lado a lado
                    col_vib, col_temp = st.columns(2)
                    
                    with col_vib:
                        # Determina se a vibração está fora do padrão
                        vib_out_of_range = vib_media > 3.5
                        vib_label = "⚠️ Vibração" if vib_out_of_range else "Vibração"
                        
                        st.metric(
                            label=vib_label, 
                            value=vib_media,
                            delta=vib_status,
                            delta_color="off"
                        )
                    
                    with col_temp:
                        # Determina se a temperatura está fora do padrão
                        temp_out_of_range = temp_max > 80
                        temp_label = "⚠️ Temperatura" if temp_out_of_range else "Temperatura"
                        
                        st.metric(
                            label=temp_label, 
                            value=temp_max,
                            delta=temp_status,
                            delta_color="off"
                        )
                    
                    # Status geral da máquina
                    if is_critical:
                        overall_status = "CRÍTICO"
                        overall_color = "red"
                    else:
                        overall_status = "ATENÇÃO"
                        overall_color = "orange"
                    
                    # Aplica cor ao texto do status
                    st.markdown(f"**Status Geral:** <span style='color: {overall_color}; font-weight: bold;'>{overall_status}</span>", unsafe_allow_html=True)
                    
                    # Aplica o CSS para colorir os cartões
                    vib_color = "red" if vib_media > 4.5 else "orange"
                    st.markdown(f"""
                    <style>
                    .stMetric[data-testid='stMetric']:nth-child({i+1}) .st-ae {{
                        color: {vib_color};
                    }}
                    </style>
                    """, unsafe_allow_html=True)
    else:
        st.success("🎉 Todas as máquinas estão funcionando normalmente!")

# Adiciona espaçamento entre seções
st.markdown("---")
st.markdown("<br>", unsafe_allow_html=True)

# --- Gráficos Comparativos ---
st.header("📊 Análise Comparativa")

# Gráficos de barras para comparação rápida (apenas máquinas com problemas)
if not df_features.empty:
    # Filtra máquinas com vibração fora do padrão
    vib_problem_machines = df_features[df_features['vib_media_5h'] > 3.5].copy()
    
    # Filtra máquinas com temperatura fora do padrão
    temp_problem_machines = df_features[df_features['temp_max_24h'] > 80].copy()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        if not vib_problem_machines.empty:
            st.subheader("⚠️ Vibração Fora do Padrão (Média das Últimas 5h)")
            
            # Cria DataFrame com cores baseadas no status
            vib_chart_data = vib_problem_machines[['machine_id', 'vib_media_5h']].copy()
            vib_chart_data['Status'] = vib_chart_data['vib_media_5h'].apply(
                lambda x: 'Crítico' if x > 4.5 else 'Atenção'
            )
            
            # Cria gráfico de barras com cores usando Plotly
            fig_vib = px.bar(
                vib_chart_data, 
                x='machine_id', 
                y='vib_media_5h',
                color='Status',
                color_discrete_map={'Crítico': '#FF0000', 'Atenção': '#FFA500'},
                title="Vibração por Máquina",
                labels={'vib_media_5h': 'Vibração (m/s²)', 'machine_id': 'Máquina'}
            )
            
            fig_vib.update_layout(
                showlegend=True,
                height=400,
                xaxis_title="Máquina",
                yaxis_title="Vibração (m/s²)"
            )
            
            st.plotly_chart(fig_vib, use_container_width=True)
            
            # Adiciona legenda de cores
            st.markdown("""
            <div style='margin-top: 10px;'>
                <span style='color: red; font-weight: bold;'>●</span> Crítico (>4.5 m/s²) &nbsp;&nbsp;
                <span style='color: orange; font-weight: bold;'>●</span> Atenção (3.5-4.5 m/s²)
            </div>
            """, unsafe_allow_html=True)
        else:
            st.subheader("✅ Vibração - Todas Normais")
            st.success("Todas as máquinas estão com vibração dentro do padrão normal.")
    
    with col_chart2:
        if not temp_problem_machines.empty:
            st.subheader("⚠️ Temperatura Fora do Padrão (Máxima das Últimas 24h)")
            
            # Cria DataFrame com cores baseadas no status
            temp_chart_data = temp_problem_machines[['machine_id', 'temp_max_24h']].copy()
            temp_chart_data['Status'] = temp_chart_data['temp_max_24h'].apply(
                lambda x: 'Alta' if x > 90 else 'Moderada'
            )
            
            # Cria gráfico de barras com cores usando Plotly
            fig_temp = px.bar(
                temp_chart_data, 
                x='machine_id', 
                y='temp_max_24h',
                color='Status',
                color_discrete_map={'Alta': '#FF0000', 'Moderada': '#FFA500'},
                title="Temperatura por Máquina",
                labels={'temp_max_24h': 'Temperatura (°C)', 'machine_id': 'Máquina'}
            )
            
            fig_temp.update_layout(
                showlegend=True,
                height=400,
                xaxis_title="Máquina",
                yaxis_title="Temperatura (°C)"
            )
            
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # Adiciona legenda de cores
            st.markdown("""
            <div style='margin-top: 10px;'>
                <span style='color: red; font-weight: bold;'>●</span> Alta (>90°C) &nbsp;&nbsp;
                <span style='color: orange; font-weight: bold;'>●</span> Moderada (80-90°C)
            </div>
            """, unsafe_allow_html=True)
        else:
            st.subheader("✅ Temperatura - Todas Normais")
            st.success("Todas as máquinas estão com temperatura dentro do padrão normal.")
else:
    st.info("📊 Gráficos não disponíveis - nenhum dado para exibir.")

# Adiciona espaçamento entre seções
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("<br>", unsafe_allow_html=True)

# --- Visão Detalhada e Previsão (Por Máquina) ---
st.header("Análise Detalhada e Previsão de Falha")

# Seletor para escolher a máquina (inclui todas as máquinas)
if not df_features.empty:
    # Cria lista de máquinas com status para o seletor
    machine_options = []
    for _, row in df_features.iterrows():
        machine_id = row['machine_id']
        vib_media = row['vib_media_5h']
        temp_max = row['temp_max_24h']
        
        # Determina status para exibição no seletor
        if vib_media > 4.5 or temp_max > 90:
            status_icon = "🔴"
            status_text = "CRÍTICO"
        elif vib_media > 3.5 or temp_max > 80:
            status_icon = "🟡"
            status_text = "ATENÇÃO"
        else:
            status_icon = "🟢"
            status_text = "NORMAL"
        
        machine_options.append(f"{status_icon} {machine_id} ({status_text})")
    
    selected_machine_display = st.selectbox(
        "Selecione uma máquina para análise detalhada:",
        machine_options
    )
    
    # Extrai o ID da máquina da seleção
    selected_machine = selected_machine_display.split(" ")[1]  # Remove emoji e status
    
    # Filtra os dados para a máquina selecionada
    machine_details = df_features[df_features['machine_id'] == selected_machine].iloc[0]
else:
    st.warning("⚠️ Nenhuma máquina disponível para análise detalhada.")
    selected_machine = None
    machine_details = None

# Exibe os detalhes da máquina em duas colunas
if machine_details is not None:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Medidores Atuais")
        
        # Vibração com normalização mais inteligente
        vib_value = machine_details['vib_media_5h']
        vib_progress = min(vib_value / 5.0, 1.0)  # Limita a 100%
        
        # Status da vibração
        if vib_value > 4.5:
            vib_status = "🔴 Crítico"
            vib_out_of_range = True
        elif vib_value > 3.5:
            vib_status = "🟡 Atenção"
            vib_out_of_range = True
        else:
            vib_status = "🟢 Normal"
            vib_out_of_range = False
        
        # Destaca se a vibração está fora do padrão
        if vib_out_of_range:
            st.markdown(f"**⚠️ Vibração (média 5h):** <span style='color: red; font-weight: bold;'>{vib_value} m/s²</span> - {vib_status}", unsafe_allow_html=True)
        else:
            st.write(f"**Vibração (média 5h):** {vib_value} m/s² - {vib_status}")
        
        st.progress(vib_progress)
        
        # Temperatura com normalização mais inteligente
        temp_value = machine_details['temp_max_24h']
        temp_progress = min(temp_value / 100.0, 1.0)  # Limita a 100%
        
        # Status da temperatura
        if temp_value > 90:
            temp_status = "🔴 Alta"
            temp_out_of_range = True
        elif temp_value > 80:
            temp_status = "🟡 Moderada"
            temp_out_of_range = True
        else:
            temp_status = "🟢 Normal"
            temp_out_of_range = False
        
        # Destaca se a temperatura está fora do padrão
        if temp_out_of_range:
            st.markdown(f"**⚠️ Temperatura (máx 24h):** <span style='color: red; font-weight: bold;'>{temp_value} °C</span> - {temp_status}", unsafe_allow_html=True)
        else:
            st.write(f"**Temperatura (máx 24h):** {temp_value} °C - {temp_status}")
        
        st.progress(temp_progress)
        
        # Status geral da máquina
        if vib_value > 4.5 or temp_value > 90:
            overall_status = "CRÍTICO"
            overall_color = "red"
        elif vib_value > 3.5 or temp_value > 80:
            overall_status = "ATENÇÃO"
            overall_color = "orange"
        else:
            overall_status = "NORMAL"
            overall_color = "green"
            
        # Aplica cor ao texto do status
        st.markdown(f"**Status Geral da Máquina:** <span style='color: {overall_color}; font-weight: bold;'>{overall_status}</span>", unsafe_allow_html=True)
        
        try:
            timestamp = pd.to_datetime(machine_details['timestamp_processamento']).strftime('%d/%m/%Y %H:%M:%S')
            st.info(f"Dados atualizados em: {timestamp}")
        except Exception as e:
            st.warning(f"Erro ao processar timestamp: {e}")
    
    
    with col2:
        st.subheader("Executar Previsão de Falha")
        st.write("Clique no botão abaixo para usar o modelo de ML (simulado) e obter uma previsão de falha com base nos dados atuais.")
    
        if st.button("Executar Previsão Agora", key=f"predict_{selected_machine}"):
            try:
                # Pega as features da máquina selecionada
                features_for_prediction = machine_details.to_dict()
                
                # Chama a função de predição mockada
                with st.spinner("Executando o modelo..."):
                    prediction_result = get_mock_prediction(features_for_prediction)
                
                # Exibe o resultado da predição
                st.subheader("Resultado da Previsão")
                
                prob = prediction_result['probability']
                status = prediction_result['alert_status']
                
                if status == "CRÍTICO":
                    st.error(f"**Status:** {status}")
                elif status == "ALERTA":
                    st.warning(f"**Status:** {status}")
                else:
                    st.success(f"**Status:** {status}")
    
                st.write(f"**Probabilidade de Falha nas próximas 24h:** {prob:.0%}")
                
            except Exception as e:
                st.error(f"Erro ao executar previsão: {e}")
else:
    st.info("ℹ️ Selecione uma máquina para ver os detalhes e executar previsões.")

