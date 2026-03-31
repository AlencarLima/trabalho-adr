import pandas as pd
import numpy as np
import random 

CHUNK_DURATION = 2.0 # Os pedaços recebidos tem duração de 2 segundos
MAX_BUFFER_SEC = 25.0 # O buffer tem capacidade máxima de 25 segundos

#          240p, 360p, 720p, 1080p, 4K (por exemplo)
BITRATES = [500, 1500, 3000, 5000, 8000]

def througput_based(banda_kbps, buffer_atual):
    """
    Método baseado em throughput da rede. Mais Tput -> Melhor bitrate requisitado. E vice-versa
    """

    # Tratamento de estouro do buffer. 
    if (buffer_atual + CHUNK_DURATION) > MAX_BUFFER_SEC:
        return 0
    
    #  Fator de segurança, utilizar 80% da banda atual
    banda = banda_kbps * 0.8

    # Verifica qual bitrate requisitar, dependendo da banda
    bitrate_requisitado = BITRATES[0]
    for bitrate in BITRATES:
        if bitrate < banda:
            bitrate_requisitado = bitrate

    return bitrate_requisitado


def buffer_based(buffer_atual):
    """
    Método baseado no buffer disponível. Pouco buffer disponível -> Menos bitrate é requisitado. E vice-versa
    """

    # Tratamento de estouro do buffer
    if (buffer_atual + CHUNK_DURATION) > MAX_BUFFER_SEC:
        return 0


    RESERVA = 5.0
    ZONA_CRESCIMENTO = 20.0
    ZONA_SEGURA = RESERVA + ZONA_CRESCIMENTO


    # Se possui 5 segundos ou menos de buffer, requisita o menor bitrate possível
    if buffer_atual <= RESERVA:
        return BITRATES[0]
    
    # Se possui 25 segundos ou mais de buffer, requista o maior bitrate possível
    elif buffer_atual >= ZONA_SEGURA:
        return BITRATES[-1]

    # Se tiver entre 6 e 24 segundos de buffer disponível (zona de crescimento), escolhe o bitrate de forma proporcional, em crescimento linear
    else:

        # 1. Descobre a porcentagem de preenchimento desta zona (Gera um valor de 0.0 a 1.0)
        # Ex: Se o buffer é 15s, ele está na metade da zona de crescimento (Fator = 0.5)
        fator = (buffer_atual - RESERVA) / ZONA_CRESCIMENTO

        # 2. Mapeia essa porcentagem para os índices da lista de bitrates (que vai de 0 a 4)
        # Ex: 0.5 * 4 = Índice 2.0
        indice = fator * (len(BITRATES) - 1)

        # 3. Arredonda para o número inteiro mais próximo
        indice_final = int(round(indice))


        return BITRATES[indice_final]
    


def proximo_estado_rede(estado_atual, cenario):
    """
    Processo Estocástico: Cadeia de Markov.
    Estados: 0 = Ruim, 1 = Normal, 2 = Ótima
    """

    # No cenário volátil a rede oscila constantemente entre os estados
    if cenario == 'volátil':
        matriz_transicao = {
            0: [0.40, 0.40, 0.20],
            1: [0.30, 0.40, 0.30],
            2: [0.20, 0.40, 0.40]
        }
    
    # No cenário de congestionamento, quando caí para o estado ruim tende a continuar nele (pelo congestinamento)
    elif cenario == 'congestionamento':
        matriz_transicao = {
            0: [0.95, 0.05, 0.00],
            1: [0.10, 0.70, 0.20],
            2: [0.30, 0.20, 0.50]
        }
    
    # Cenário estável, onde a rede tende a se manter no estado que estiver no momento
    else:
        matriz_transicao = {
            0: [0.90, 0.10, 0.00],
            1: [0.05, 0.90, 0.05],
            2: [0.00, 0.10, 0.90]
        }
    
    return np.random.choice([0,1,2], p=matriz_transicao[estado_atual])


def gerar_banda_atual(estado):
    """
    Gera a banda atual baseado no estado. Utiliza a Distribuição Normal
    """

    if estado == 0: # Ruim
        banda = random.gauss(300, 150) # Média de 300Kbps e desvio padrão de 150Kbps
    
    elif estado == 1: # Normal
        banda = random.gauss(2500, 600) # Média de 2500Kbps e desvio padrão de 600Kbps
    
    else: # Ótima
        banda = random.gauss(8000, 1000) # Média de 8000Kbps e desvio padrão de 1000Kbps


    return max(100.0, banda)



def gerar_trace_rede(tempo_simulacao, cenario):
    """Gera o comportamento da rede de antemão, para que a comparação seja justa"""
    trace = []
    estado_atual = 1 # Começa no Normal
    
    for tempo_seg in range(tempo_simulacao):
        estado_atual = proximo_estado_rede(estado_atual, cenario)
        banda = gerar_banda_atual(estado_atual)
        
        trace.append({
            'Tempo (s)': tempo_seg,
            'Estado': estado_atual,
            'Banda (Kbps)': banda
        })
    return trace


def simulador_streaming(trace_rede, cenario_rede, nome_algoritmo):
    """
    Simulador de Streaming Orientado a Traces (Trace-Driven Simulation).
    O algoritmo percorre um trace pré-gerado, garantindo que diferentes
    algoritmos ABR sejam avaliados exatamente sob as mesmas condições de rede.
    """
    # --- VARIÁVEIS DE ESTADO DO PLAYER ---
    buffer_atual = 0.0
    historico = []

    download_em_andamento = False
    progresso_download_kb = 0.0
    tamanho_chunk_kb = 0.0
    bitrate_requisitado = 0

    # O coração da simulação: avança no tempo de 1 em 1 segundo
    for instante in trace_rede:
        
        # 1. FASE DE LEITURA (Ambiente)
        # Extrai as condições da rede daquele exato segundo do Trace
        tempo_seg = instante['Tempo (s)']
        banda_atual = instante['Banda (Kbps)']
        estado_rede = instante['Estado']

        # 2. FASE DE AUDITORIA (Métricas de QoE)
        # Verifica se ocorreu o esgotamento do buffer (Stall) ANTES de consumir o vídeo.
        # Ignoramos o tempo 0 porque é o momento de inicialização (Startup).
        travamento = (buffer_atual == 0.0) if tempo_seg > 0 else False

        # 3. FASE DE PLAYBACK (Consumo)
        # Simula o usuário assistindo ao vídeo: a cada segundo real, consome 1s de vídeo.
        if buffer_atual > 0:
            buffer_atual -= 1.0

        # 4. FASE DE DECISÃO ABR (Camada de Aplicação)
        # O "Cadeado": O algoritmo só é consultado se a placa de rede estiver ociosa.
        if not download_em_andamento:
            
            # Direciona para a lógica do algoritmo escolhido
            if nome_algoritmo == 'Throughput-Based':
                bitrate_requisitado = througput_based(banda_atual, buffer_atual)
            elif nome_algoritmo == 'Buffer-Based':
                bitrate_requisitado = buffer_based(buffer_atual)
            
            # Se o algoritmo pedir um vídeo (bitrate > 0), inicia a requisição
            if bitrate_requisitado > 0:
                download_em_andamento = True
                # Calcula o peso total do arquivo a ser baixado (Kbps * Duração do Chunk)
                tamanho_chunk_kb = bitrate_requisitado * CHUNK_DURATION
                progresso_download_kb = 0.0

        # Salva o status do bitrate para o log antes que um download muito rápido termine
        # dentro da mesma iteração, garantindo a fidelidade dos dados gerados.
        bitrate_log = bitrate_requisitado if download_em_andamento else 0

        # 5. FASE DE DOWNLOAD (Camada de Transporte Simulada)
        if download_em_andamento:
            # A banda dita o quão rápido o chunk é transferido neste segundo
            progresso_download_kb += banda_atual
            
            # Se o download atingiu ou ultrapassou o tamanho do arquivo:
            if progresso_download_kb >= tamanho_chunk_kb:
                # O vídeo chega ao player e alimenta o buffer
                buffer_atual += CHUNK_DURATION
                download_em_andamento = False # Libera a rede para o próximo chunk

        # 6. FASE DE REGISTRO (Logging)
        # Mapeamento do código numérico do estado para texto legível
        nome_estado = {0: 'Ruim', 1: 'Normal', 2: 'Ótima'}[estado_rede]
        
        historico.append({
                'Tempo (s)': tempo_seg,
                'Algoritmo': nome_algoritmo,
                'Cenário': cenario_rede.capitalize(),
                'Estado da Rede': nome_estado,
                'Banda da Rede (Kbps)': round(banda_atual, 2),
                'Bitrate Escolhido (Kbps)': bitrate_log,
                'Ocupação do Buffer (s)': round(buffer_atual, 2),
                'Travamento (Stall)': travamento
        })
    
    # Retorna todos os logs estruturados para análise
    return pd.DataFrame(historico)


cenarios_teste = ['estável', 'volátil', 'congestionamento']
algoritmos = ['Throughput-Based', 'Buffer-Based']

dataframes = []

for cenario in cenarios_teste:
    print(f"Gerando trace de rede para o cenário: {cenario.capitalize()}")
    trace = gerar_trace_rede(600, cenario)


    for algoritmo in algoritmos:
        print(f"Rodando: {algoritmo}...")

        df_temporario = simulador_streaming(trace, cenario, algoritmo)

        dataframes.append(df_temporario)

df_final = pd.concat(dataframes, ignore_index=True)

df_final.to_excel("./dados/dados_finais.xlsx", index=False)
