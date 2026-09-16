import os
import csv
import json
from PIL import Image, ImageDraw

# CARREGA CONFIGURAÇÕES
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


slide_id = config["slide_id"]
classificacao = config["classificacao"]

# ARQUIVOS AUTOMÁTICOS
diretorio_info = os.path.join("dataset_info", str(slide_id))

os.makedirs(diretorio_info, exist_ok=True)

MAPA_ORIGINAL = os.path.join(
    diretorio_info,
    f"MAPA_VALIDACAO_{slide_id}_{classificacao}.jpg"
)

JSON_META = os.path.join(
    diretorio_info,
    f"MAPA_VALIDACAO_{slide_id}_{classificacao}.json"
)

CSV_LABELS = os.path.join(
    diretorio_info,
    f"{slide_id}_labels_tiles.csv"
)

SAIDA = os.path.join(
    diretorio_info,
    f"MAPA_VALIDACAO_{slide_id}_{classificacao}_RECONSTRUIDO.png"
)

# METADADOS
with open(JSON_META, "r", encoding="utf-8") as f:
    meta = json.load(f)

tamanho_reduzido = meta["tamanho_reduzido"]
altura_original = meta["altura_original"]


# CARREGA MAPA
img = Image.open(MAPA_ORIGINAL).convert("RGBA")

overlay = Image.new(
    "RGBA",
    img.size,
    (0, 0, 0, 0)
)

draw = ImageDraw.Draw(overlay)

# DESENHA TILES
with open(CSV_LABELS, "r", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        x = int(row["x"])
        y = int(row["y"])

        classe = row["classe"]

        if classe == "NORMAL":
            continue

        novo_x = (
            altura_original
            - (y * tamanho_reduzido)
            - tamanho_reduzido
        )

        novo_y = (
            x * tamanho_reduzido
        )

        x1 = novo_x
        y1 = novo_y

        x2 = novo_x + tamanho_reduzido
        y2 = novo_y + tamanho_reduzido

        if classe == "TUMOR":

            cor = (
                255, 0, 0, 120
            )

        elif classe == "BORDA":

            cor = (
                255, 255, 0, 120
            )

        draw.rectangle(
            [x1, y1, x2, y2],
            fill=cor
        )

# JUNTA IMAGEM + OVERLAY
resultado = Image.alpha_composite(
    img,
    overlay
)

resultado.save(SAIDA)

print(f"Reconstrução salva: {SAIDA}")