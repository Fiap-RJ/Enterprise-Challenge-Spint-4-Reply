import os
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd
import streamlit as st
from data_connector import get_feature_store_data, get_historical_data, get_prediction

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Manutenção Preditiva",
    page_icon="🔧",
    layout="wide"
)

# Função para carregar dados com cache
@st.cache_data(ttl=300)  # 5 minutos de cache
def load_data():
    """Carrega os dados da feature store"""
    return get_feature_store_data()


def formatar_status(vib_media: float, temp_max: float) -> tuple:
    """Formata o status com base nos valores de vibração e temperatura"""
    # Status da vibração baseado na ISO 10816/20816
    if vib_media > 7.1:
        vib_status = "CRÍTICO"
        vib_color = "red"
    elif vib_media > 4.5:
        vib_status = "ATENÇÃO"
        vib_color = "orange"
    else:
        vib_status = "NORMAL"
        vib_color = "green"
    
    # Status da temperatura
    if temp_max > 90:
        temp_status = "ALTA"
        temp_color = "red"
    elif temp_max > 80:
        temp_status = "MODERADA"
        temp_color = "orange"
    else:
        temp_status = "NORMAL"
        temp_color = "green"
    
    # Status geral (o pior status entre vibração e temperatura)
    if "CRÍTICO" in [vib_status, temp_status] or temp_max > 100:
        overall_status = "CRÍTICO"
    elif "ATENÇÃO" in [vib_status, temp_status] or "ALTA" in [vib_status, temp_status] or "MODERADA" in [vib_status, temp_status]:
        overall_status = "ATENÇÃO"
    else:
        overall_status = "NORMAL"
    
    return {
        'vib_status': vib_status,
        'vib_color': vib_color,
        'temp_status': temp_status,
        'temp_color': temp_color,
        'overall_status': overall_status
    }

# Inicialização do estado da sessão
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

st.title("🔧 Dashboard de Monitoramento Preditivo")

if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.session_state.last_update = datetime.now()

# Carrega os dados
df_features = load_data()

if df_features.empty:
    st.warning("⚠️ Nenhum dado disponível no momento. Verifique a conexão com o banco de dados.")
else:
    # Processa os dados
    critical_machines = []
    alert_machines = []
    normal_machines = []
    
    for _, row in df_features.iterrows():
        machine_id = row['machine_id']
        vib_media = row.get('vib_media_5h', 0)
        temp_max = row.get('temp_max_24h', 0)
        
        # Obtém o status formatado
        status = formatar_status(vib_media, temp_max)
        
        # Obtém a previsão do modelo pela api ou Mock
        prediction = get_prediction_from_api({
            'machine_id': machine_id,
            'vib_media_5h': vib_media,
            'temp_max_24h': temp_max,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Adiciona aos grupos correspondentes
        machine_data = {
            'id': machine_id,
            'row': row,
            'vib_media': vib_media,
            'temp_max': temp_max,
            'vib_status': status['vib_status'],
            'temp_status': status['temp_status'],
            'probability': prediction.get('probability', 0),
            'prediction_status': prediction.get('alert_status', 'DESCONHECIDO'),
            'last_updated': row.get('timestamp_processamento', datetime.utcnow().isoformat())
        }
        
        if status['overall_status'] == "CRÍTICO":
            critical_machines.append(machine_data)
        elif status['overall_status'] == "ATENÇÃO":
            alert_machines.append(machine_data)
        else:
            normal_machines.append(machine_data)
    
    # Exibe o status de atualização
    last_update = st.session_state.last_update or datetime.now()
    st.caption(f"Última atualização: {last_update.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Seção de status
    st.header("📊 Visão Geral")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🔴 Crítico", 
            len(critical_machines),
            "Máquina(s) com falha iminente" if critical_machines else "Sem problemas críticos"
        )
    
    with col2:
        st.metric(
            "🟡 Atenção", 
            len(alert_machines),
            "Máquina(s) para monitorar" if alert_machines else "Tudo normal"
        )
    
    with col3:
        st.metric(
            "🟢 Normal", 
            len(normal_machines),
            "Máquina(s) operando normalmente"
        )
    
    # Seção de alertas
    if critical_machines or alert_machines:
        st.header("🚨 Alertas")
        
        # Exibe máquinas críticas
        if critical_machines:
            st.error("### 🔴 Máquinas Críticas")
            for machine in critical_machines:
                with st.expander(f"{machine['id']} - Probabilidade de falha: {machine['probability']*100:.1f}%"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Vibração", f"{machine['vib_media']} mm/s", machine['vib_status'])
                    with col2:
                        st.metric("Temperatura", f"{machine['temp_max']}°C", machine['temp_status'])
                    st.progress(machine['probability'], "Probabilidade de falha")
        
        # Exibe máquinas em alerta
        if alert_machines:
            st.warning("### 🟠 Máquinas em Alerta")
            for machine in alert_machines:
                with st.expander(f"{machine['id']} - Atenção necessária"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Vibração", f"{machine['vib_media']} mm/s", machine['vib_status'])
                    with col2:
                        st.metric("Temperatura", f"{machine['temp_max']}°C", machine['temp_status'])
                    st.progress(machine['probability'], "Probabilidade de falha")
    
    # Seção de todas as máquinas
    st.header("📋 Todas as Máquinas")
    for machine in critical_machines + alert_machines + normal_machines:
        status_color = "red" if machine in critical_machines else "orange" if machine in alert_machines else "green"
        with st.container():
            st.subheader(f"{machine['id']} - Status: :{status_color}[{machine['prediction_status']}]")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                st.metric("Vibração Média (5h)", 
                         f"{machine['vib_media']} mm/s", 
                         machine['vib_status'])
            
            with col2:
                st.metric("Temperatura Máx (24h)", 
                         f"{machine['temp_max']}°C", 
                         machine['temp_status'])
            
            with col3:
                st.metric("Probabilidade de Falha", 
                         f"{machine['probability']*100:.1f}%")
                st.progress(machine['probability'])
            
            # Gráfico de histórico
            st.caption(f"Última atualização: {machine['last_updated']}")
            st.markdown("---")

st.markdown("---")
st.caption("Sistema de Monitoramento Preditivo - Desenvolvido para FIAP")