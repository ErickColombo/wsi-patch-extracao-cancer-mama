import os
import csv
import json
import shutil

# ==========================================
# CARREGA CONFIGURAÇÕES
# ==========================================
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


slide_id = config["slide_id"]
classificacao = config["classificacao"]
nivel_zoom = config["nivel_zoom"]
pasta_principal = config["pasta_principal"]

# ==========================================
# CAMINHOS AUTOMÁTICOS
# ==========================================
nome_pasta_base = f"{slide_id}_{classificacao}"

# 1. Aponta para o CSV na nova pasta dataset_info
diretorio_info = os.path.join("dataset_info", str(slide_id))
CSV_LABELS = os.path.join(
    diretorio_info, 
    f"{slide_id}_labels_tiles.csv"
)

# 2. Caminho de origem dos tiles (mantido igual)
PASTA_TILES = os.path.join(
    pasta_principal,
    nome_pasta_base,
    f"level_{nivel_zoom}"
)

# 3. Nova pasta principal do dataset
PASTA_SAIDA = os.path.join(
    "dataset",
    nome_pasta_base
)

# ==========================================
# CRIA PASTAS
# ==========================================
os.makedirs(
    os.path.join(PASTA_SAIDA, "NORMAL"),
    exist_ok=True
)

os.makedirs(
    os.path.join(PASTA_SAIDA, "BORDA"),
    exist_ok=True
)

os.makedirs(
    os.path.join(PASTA_SAIDA, "TUMOR"),
    exist_ok=True
)

# ==========================================
# PROCESSA CSV
# ==========================================
copiados = 0
nao_encontrados = 0

with open(
    CSV_LABELS,
    "r",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        arquivo = row["arquivo"]
        classe = row["classe"]

        origem = os.path.join(
            PASTA_TILES,
            arquivo
        )

        destino = os.path.join(
            PASTA_SAIDA,
            classe,
            arquivo
        )

        if os.path.exists(origem):

            shutil.copy2(
                origem,
                destino
            )

            copiados += 1

        else:

            print(
                f"Arquivo não encontrado: "
                f"{arquivo}"
            )

            nao_encontrados += 1

# ==========================================
# RESUMO
# ==========================================
print()
print("Processamento concluído.")
print(f"Paciente: {slide_id}")
print(f"Classificação: {classificacao}")
print(f"Copiados: {copiados}")
print(f"Não encontrados: {nao_encontrados}")
print(f"Destino: {PASTA_SAIDA}")