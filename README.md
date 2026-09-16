# wsi-patch-extracao-cancer-mama

Este repositório contém o pipeline de aquisição, processamento e estruturação de dados desenvolvido como parte do Trabalho de Conclusão de Curso em Ciência da Computação. 

O projeto tem como objetivo principal investigar a influência das representações cromáticas na classificação de imagens histopatológicas, utilizando arquiteturas de Redes Neurais Convolucionais (CNNs), sendo elas ResNet50, EfficientNetV2 e ConvNeXtV2.

---

## Metodologia e Pipeline de Dados

O foco dos scripts presentes neste repositório é a etapa de **Preparação do Dataset**, convertendo Whole Slide Images (WSIs) e máscaras de anotação em um conjunto de dados estruturado e rotulado para o treinamento dos modelos de Deep Learning.

O pipeline é composto por 5 etapas automatizadas:

1. **Extração de Patches (Tile Scraper):** 
   Realiza o download paralelizado de tiles (recortes) de lâminas histopatológicas a partir de um servidor remoto. Inclui mecanismos de tolerância a falhas (HTTP Retries) e descarte automático de regiões sem tecido (fundo branco), otimizando o armazenamento e o processamento computacional.

2. **Mapeamento e Validação Visão Geral:** 
   Reconstrói uma miniatura da WSI original a partir dos patches individuais extraídos, gerando mapas de coordenadas (JSON) para referenciamento espacial e imagens base para a criação de máscaras de segmentação.

3. **Rotulagem Automática Baseada em Máscaras:** 
   Cruza as coordenadas espaciais de cada tile extraído com uma máscara de validação. Através da detecção de canais cromáticos específicos (análise de espectro verde/RGB), o algoritmo classifica matematicamente cada tile em três categorias distintas: `NORMAL`, `BORDA` e `TUMOR`.

4. **Estruturação do Dataset Final:** 
   Lê o arquivo `.csv` gerado na etapa de rotulagem e orquestra a movimentação física dos arquivos para uma estrutura de diretórios padronizada (`dataset/ID_CLASSIFICACAO/CLASSE`), pronta para ser consumida por instâncias do `torch.utils.data.DataLoader`.

5. **Reconstrução e Validação Visual (Overlay):** 
   Gera um mapa de calor sobre a miniatura da WSI original, destacando em vermelho as áreas classificadas como "TUMOR" e em amarelo as áreas de "BORDA", permitindo a validação qualitativa do processo de rotulagem.

---

## Tecnologias Utilizadas

A base deste pipeline de processamento foi construída sobre as seguintes tecnologias:
- **Python 3.12.9**
- **NumPy:** Processamento matricial, detecção de proporção de pixels (fundo) e operações lógicas em canais de cor.
- **Pillow (PIL):** Manipulação, redimensionamento, rotação e criação de overlays (composições alfa) nas imagens histopatológicas.
- **Requests & urllib3:** Gerenciamento de sessões HTTP e requisições em lote com concorrência (`ThreadPoolExecutor`).

---

##  Instruções de Uso e Configuração

### 1. Execução
Os scripts Python devem ser executados seguindo a ordem numérica de sua nomenclatura (1, 2, 3, 4 e 5), uma vez que um arquivo depende da saída gerada pelo anterior para funcionar. 

**Nota sobre validação:** Os scripts 2 e 5 são voltados exclusivamente para testes e validação visual, permitindo a visualização da lâmina inteira reconstituída e com a sobreposição do mapa de calor.

**Nota sobre acesso aos dados:** Considerando a forma de aquisição das lâminas disponível, o arquivo 1 foi implementado para buscar os tiles (recortes) diretamente em um servidor em nuvem. Por se tratar de um ambiente com acesso restrito, não será possível replicar essa extração diretamente sem as devidas permissões. Caso deseje replicar este estudo, o leitor poderá adaptar a lógica de extração e salvamento do script 1 para o seu caso de uso (imagens locais, por exemplo). Para que os demais códigos funcionem corretamente, é estritamente necessário manter o padrão de nomenclatura no salvamento dos arquivos, permitindo que a expressão regular `padrao = re.compile(r"X(\d+)_Y(\d+)")` consiga extrair e identificar as coordenadas dos *tiles*. 

Em complemento, o arquivo config.json possui algumas variáveis que também tem correlação com o método de aquisição do arquivo 1, logo, inicio_x, limite_maximo_x, inicio_y, limite_maximo_y, base_url e slide_path poderão ser adaptadas ou completamente removidas. ps: o nivel_zoom foi usado em outros .py apenas para renomeação, deixar ele como vazio ("") para evitar erros e não precisar adaptar.

### 2. Dependências
Recomenda-se a criação de um ambiente virtual (venv) para evitar conflitos de dependências. Com o ambiente ativo, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
