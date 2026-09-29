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

os.makedirs(
    "outputs",
    exist_ok=True
)

CSV_SAIDA = os.path.join(
    "outputs",
    "patches_master.csv"
)

# ==========================================
# CARREGA SPLITS
# ==========================================

splits = {}

for nome_split in ["train", "val", "test"]:

    caminho_csv = os.path.join(
        "outputs",
        f"{nome_split}.csv"
    )

    if not os.path.exists(caminho_csv):

        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_csv}"
        )

    with open(
        caminho_csv,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            splits[
                row["paciente"]
            ] = nome_split

# ==========================================
# PROCESSAMENTO
# ==========================================

linhas = []

total_pacientes = len(splits)

print()
print(f"Pacientes encontrados: {total_pacientes}")
print()

for paciente in sorted(splits):

    split = splits[paciente]

    paciente_id = paciente.split("_")[0]
    tipo = paciente.split("_")[-1]

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

    with open(
        csv_labels,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            classe_patch = row["classe"]

            # ==========================
            # FILTROS
            # ==========================

            if (
                classe_patch == "NORMAL"
                and not USAR_NORMAL
            ):
                continue

            if (
                classe_patch == "BORDA"
                and not USAR_BORDA
            ):
                continue

            if (
                classe_patch == "TUMOR"
                and not USAR_TUMOR
            ):
                continue

            arquivo = row["arquivo"]

            caminho_imagem = os.path.join(
                DATASET_PATH,
                paciente,
                "level_4",
                arquivo
            )

            if not os.path.exists(
                caminho_imagem
            ):

                print(
                    f"Imagem não encontrada:"
                )
                print(caminho_imagem)

                continue

            linhas.append([
                arquivo,
                paciente,
                paciente_id,
                tipo,
                row["x"],
                row["y"],
                row["tumor_pct"],
                classe_patch,
                split,
                caminho_imagem
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
        "paciente",
        "id",
        "tipo",
        "x",
        "y",
        "tumor_pct",
        "classe",
        "split",
        "caminho"
    ])

    writer.writerows(linhas)

# ==========================================
# ESTATÍSTICAS
# ==========================================

train_count = sum(
    1 for l in linhas
    if l[8] == "train"
)

val_count = sum(
    1 for l in linhas
    if l[8] == "val"
)

test_count = sum(
    1 for l in linhas
    if l[8] == "test"
)

print()
print("===================================")
print("PATCHES MASTER GERADO")
print("===================================")

print(
    f"Treino: {train_count}"
)

print(
    f"Validação: {val_count}"
)

print(
    f"Teste: {test_count}"
)

print(
    f"Total: {len(linhas)}"
)

print()
print(
    f"Arquivo salvo em:"
)

print(CSV_SAIDA)