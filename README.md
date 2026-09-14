# Influência das Representações Cromáticas na Classificação de Imagens Histopatológicas

Este repositório contém o pipeline de aquisição, processamento e estruturação de dados desenvolvido como parte do Trabalho de Conclusão de Curso (TCC) em Ciência da Computação. 

O projeto tem como objetivo principal investigar a influência das representações cromáticas na classificação de imagens histopatológicas, utilizando arquiteturas de Redes Neurais Convolucionais (CNNs), sendo elas ResNet50, EfficientNetV2 e ConvNeXtV2.

##  Autor
**Erick Colombo**  
*Graduando em Ciência da Computação*

---

## Metodologia e Pipeline de Dados

O foco dos scripts presentes neste repositório é a etapa de **Preparação do Dataset (Data Preparation)**, convertendo Whole Slide Images (WSIs) brutas e máscaras de anotação em um conjunto de dados estruturado e rotulado para o treinamento dos modelos de Deep Learning.

O pipeline é composto por 5 etapas automatizadas:

1. **Extração de Patches (Tile Scraper):** 
   Realiza o download paralelizado de tiles (recortes) de lâminas histopatológicas em alta resolução a partir de um servidor remoto. Inclui mecanismos de tolerância a falhas (HTTP Retries) e descarte automático de regiões sem tecido (fundo branco), otimizando o armazenamento e o processamento computacional.

2. **Mapeamento e Validação Visão Geral:** 
   Reconstrói uma miniatura da WSI original a partir dos patches individuais extraídos, gerando mapas de coordenadas (JSON) para referenciamento espacial e imagens base para a criação de máscaras de segmentação.

3. **Rotulagem Automática Baseada em Máscaras:** 
   Cruza as coordenadas espaciais de cada tile extraído com uma máscara de validação. Através da detecção de canais cromáticos específicos (análise de espectro verde/RGB), o algoritmo classifica matematicamente cada tile em três categorias distintas: `NORMAL`, `BORDA` e `TUMOR`.

4. **Estruturação do Dataset Final:** 
   Lê o arquivo `.csv` gerado na etapa de rotulagem e orquestra a movimentação física dos arquivos para uma estrutura de diretórios padronizada (`dataset/ID_CLASSIFICACAO/CLASSE`), pronta para ser consumida por instâncias do `torch.utils.data.DataLoader`.

5. **Reconstrução e Validação Visual (Overlay):** 
   Gera um mapa de calor (bounding boxes translúcidas) sobre a WSI original, destacando em vermelho as áreas classificadas como "TUMOR" e em amarelo as áreas de "BORDA", permitindo a validação qualitativa do processo de rotulagem.

---

##  Tecnologias Utilizadas

A base deste pipeline de processamento foi construída sobre as seguintes tecnologias:
- **Python 3.12.9**
- **NumPy:** Processamento matricial, detecção de proporção de pixels (fundo) e operações lógicas em canais de cor.
- **Pillow (PIL):** Manipulação, redimensionamento, rotação e criação de overlays (composições alfa) nas imagens histopatológicas.
- **Requests & urllib3:** Gerenciamento de sessões HTTP e requisições em lote com concorrência (`ThreadPoolExecutor`).
- *(Futuro)* **PyTorch & Torchvision:** Treinamento e avaliação das arquiteturas CNN.

---

##  Instruções de Configuração e Uso

### 1. Dependências
Recomenda-se a criação de um ambiente virtual (venv) para evitar conflitos de dependências. Com o ambiente ativo, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt