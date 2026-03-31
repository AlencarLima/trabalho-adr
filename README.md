# trabalho-adr

Simulação de streaming adaptativo (ABR) em Python para comparar duas estratégias de escolha de bitrate sob diferentes condições de rede.

## Contexto do projeto

Este projeto modela um player de vídeo que baixa chunks de 2 segundos e precisa decidir, a cada instante, qual bitrate solicitar.
A decisão impacta diretamente a Qualidade de Experiência (QoE):

- bitrates maiores melhoram qualidade de imagem, mas aumentam risco de travamento;
- bitrates menores reduzem travamentos, mas podem piorar a qualidade visual.

A simulação usa traces de rede gerados por um processo estocástico (Cadeia de Markov), garantindo comparação justa entre algoritmos porque ambos rodam sobre o mesmo trace em cada cenário.

## O que o código faz

O script principal `simulacao_final.py`:

- define perfis de bitrate: 240p, 360p, 720p, 1080p e 4K (em Kbps);
- gera banda de rede por segundo com três estados: Ruim, Normal e Ótima;
- cria três cenários de rede:
  - estável;
  - volátil;
  - congestionamento;
- executa dois algoritmos ABR:
  - Throughput-Based: escolhe bitrate com base na banda atual (com fator de segurança);
  - Buffer-Based: escolhe bitrate com base na ocupação do buffer;
- simula o playback segundo a segundo e registra métricas (bitrate, buffer, stalls, etc.);
- exporta os resultados para planilha Excel.

## Requisitos

- Python 3.10+ (recomendado)
- Arquivo de dependências:
  - `requirements.txt`
- Bibliotecas utilizadas:
  - pandas
  - numpy
  - openpyxl (necessária para exportação .xlsx)

## Como rodar

1. Clone o repositório:

```bash
git clone https://github.com/AlencarLima/trabalho-adr.git
cd trabalho-adr
```

2. (Opcional, recomendado) crie e ative um ambiente virtual:

No Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Execute a simulação:

```bash
python simulacao_final.py
```

## Saída esperada

Ao final da execução, o script gera uma planilha com os dados consolidados:

- `dados_finais.xlsx`

A planilha inclui, entre outras colunas:

- tempo;
- algoritmo usado;
- cenário de rede;
- estado da rede;
- banda disponível;
- bitrate escolhido;
- ocupação do buffer;
- ocorrência de travamento (stall).

## Observações

- O tempo de simulação está configurado para 600 segundos por cenário.
- O buffer máximo do player é de 25 segundos.
- O chunk de vídeo tem duração de 2 segundos.
