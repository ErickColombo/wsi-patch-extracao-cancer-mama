import os
import re
import json
import csv
import numpy as np
from PIL import Image

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

PASTA_TILES = os.path.join(
    pasta_principal,
    nome_pasta_base,
    f"level_{nivel_zoom}"
)

ARQUIVO_MASK = (
    f"MAPA_VALIDACAO_{slide_id}_{classificacao}_MASK.png"
)

ARQUIVO_JSON = (
    f"MAPA_VALIDACAO_{slide_id}_{classificacao}.json"
)

CSV_SAIDA = (
    f"{slide_id}_labels_tiles.csv"
)

# ==========================================
# CARREGA METADADOS
# ==========================================
with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
    meta = json.load(f)

max_x = meta["max_x"]
max_y = meta["max_y"]

tamanho_reduzido = meta["tamanho_reduzido"]

altura_original = meta["altura_original"]
largura_original = meta["largura_original"]

# ==========================================
# CARREGA MÁSCARA
# ==========================================
mask = np.array(
    Image.open(ARQUIVO_MASK).convert("RGB")
)

# ==========================================
# DETECÇÃO DO VERDE
# ==========================================
def calcular_percentual_verde(crop):

    verde = (
        (crop[:, :, 0] < 80) &
        (crop[:, :, 1] > 180) &
        (crop[:, :, 2] < 80)
    )

    return float(verde.mean() * 100)

# ==========================================
# PROCESSAMENTO
# ==========================================
padrao = re.compile(r"X(\d+)_Y(\d+)")

linhas = []

for arquivo in os.listdir(PASTA_TILES):

    if not arquivo.lower().endswith(".jpg"):
        continue

    match = padrao.search(arquivo)

    if not match:
        continue

    x = int(match.group(1))
    y = int(match.group(2))

    novo_x = (
        altura_original
        - (y * tamanho_reduzido)
        - tamanho_reduzido
    )

    novo_y = (
        x * tamanho_reduzido
    )

    crop = mask[
        novo_y:novo_y+tamanho_reduzido,
        novo_x:novo_x+tamanho_reduzido
    ]

    pct_verde = calcular_percentual_verde(crop)

    # ======================================
    # CLASSIFICAÇÃO
    # ======================================

    if pct_verde == 0:

        classe = "NORMAL"

    elif pct_verde <= 30:

        classe = "BORDA"

    else:

        classe = "TUMOR"

    linhas.append([
        arquivo,
        x,
        y,
        round(pct_verde, 2),
        classe,
        slide_id
    ])

# ==========================================
# SALVA CSV
# ==========================================
with open(
    CSV_SAIDA,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "arquivo",
        "x",
        "y",
        "tumor_pct",
        "classe",
        "id"
    ])

    writer.writerows(linhas)

print(f"CSV gerado: {CSV_SAIDA}")

# ==========================================
# ESTATÍSTICAS
# ==========================================
normal = sum(1 for l in linhas if l[4] == "NORMAL")
borda = sum(1 for l in linhas if l[4] == "BORDA")
tumor = sum(1 for l in linhas if l[4] == "TUMOR")

print()
print("Resumo:")
print(f"NORMAL: {normal}")
print(f"BORDA : {borda}")
print(f"TUMOR : {tumor}")
print(f"TOTAL : {len(linhas)}")