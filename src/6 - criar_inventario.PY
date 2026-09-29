import os
import csv
import json

# ==========================================
# CONFIG
# ==========================================

with open(
    "config/config_dataset.json",
    "r",
    encoding="utf-8"
) as f:

    config = json.load(f)

DATASET_PATH = config["dataset_path"]
DATASET_INFO_PATH = config["dataset_info_path"]

USAR_NORMAL = config["usar_normal"]
USAR_BORDA = config["usar_borda"]
USAR_TUMOR = config["usar_tumor"]

# ==========================================
# SAÍDA
# ==========================================

os.makedirs("outputs", exist_ok=True)

CSV_SAIDA = os.path.join(
    "outputs",
    "pacientes.csv"
)

linhas = []

# ==========================================
# PACIENTES
# ==========================================

for pasta in sorted(os.listdir(DATASET_PATH)):

    caminho_paciente = os.path.join(
        DATASET_PATH,
        pasta
    )

    if not os.path.isdir(caminho_paciente):
        continue

    partes = pasta.split("_")

    if len(partes) < 2:
        continue

    paciente_id = partes[0]
    tipo = partes[-1]

    csv_labels = os.path.join(
        DATASET_INFO_PATH,
        paciente_id,
        f"{paciente_id}_labels_tiles.csv"
    )

    if not os.path.exists(csv_labels):

        print(
            f"CSV não encontrado: {csv_labels}"
        )

        continue

    normal = 0
    borda = 0
    tumor = 0

    with open(
        csv_labels,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            classe = row["classe"]

            if classe == "NORMAL":
                normal += 1

            elif classe == "BORDA":
                borda += 1

            elif classe == "TUMOR":
                tumor += 1

    total = 0

    if USAR_NORMAL:
        total += normal

    if USAR_BORDA:
        total += borda

    if USAR_TUMOR:
        total += tumor

    linhas.append([
        pasta,
        paciente_id,
        tipo,
        normal,
        borda,
        tumor,
        total
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
        "paciente",
        "id",
        "tipo",
        "normal",
        "borda",
        "tumor",
        "total"
    ])

    writer.writerows(linhas)

# ==========================================
# RESUMO
# ==========================================

total_pacientes = len(linhas)

total_normal = sum(
    int(l[3]) for l in linhas
)

total_borda = sum(
    int(l[4]) for l in linhas
)

total_tumor = sum(
    int(l[5]) for l in linhas
)

total_patches = sum(
    int(l[6]) for l in linhas
)

print()
print("===================================")
print("INVENTÁRIO CONCLUÍDO")
print("===================================")
print(f"Pacientes : {total_pacientes}")
print(f"NORMAL    : {total_normal}")
print(f"BORDA     : {total_borda}")
print(f"TUMOR     : {total_tumor}")
print(f"TOTAL     : {total_patches}")
print()
print(f"CSV gerado: {CSV_SAIDA}")