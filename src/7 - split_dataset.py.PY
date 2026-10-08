import os
import csv
import json
import random

# ==========================================
# CONFIG
# ==========================================

with open(
    "config/config_dataset.json",
    "r",
    encoding="utf-8"
) as f:

    config = json.load(f)

PCT_TREINO = config["percentual_treino"]
PCT_VAL = config["percentual_validacao"]
PCT_TESTE = config["percentual_teste"]

SEED = config["seed"]

USAR_MGN = config.get(
    "usar_mgn",
    True
)

USAR_BGN = config.get(
    "usar_bgn",
    True
)

USAR_NRM = config.get(
    "usar_nrm",
    True
)

random.seed(SEED)

# ==========================================
# ENTRADA
# ==========================================

PACIENTES_CSV = os.path.join(
    "outputs",
    "pacientes.csv"
)

if not os.path.exists(PACIENTES_CSV):

    raise FileNotFoundError(
        f"Arquivo não encontrado: {PACIENTES_CSV}"
    )

# ==========================================
# LEITURA
# ==========================================

pacientes = []

with open(
    PACIENTES_CSV,
    "r",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        row["normal"] = int(row["normal"])
        row["borda"] = int(row["borda"])
        row["tumor"] = int(row["tumor"])
        row["total"] = int(row["total"])

        pacientes.append(row)

# ==========================================
# SEPARA POR CLASSE
# ==========================================

mgn = [
    p for p in pacientes
    if p["tipo"].upper() == "MGN"
]

bgn = [
    p for p in pacientes
    if p["tipo"].upper() == "BGN"
]

nrm = [
    p for p in pacientes
    if p["tipo"].upper() == "NRM"
]

# ==========================================
# FILTROS
# ==========================================

if not USAR_MGN:
    mgn = []

if not USAR_BGN:
    bgn = []

if not USAR_NRM:
    nrm = []

# ==========================================
# DISTRIBUIÇÃO BALANCEADA
# ==========================================

def distribuir_grupo(lista):

    if len(lista) == 0:
        return [], [], []

    random.shuffle(lista)

    total_patches = sum(
        p["total"] for p in lista
    )

    alvo_train = total_patches * PCT_TREINO
    alvo_val = total_patches * PCT_VAL
    alvo_test = total_patches * PCT_TESTE

    lista = sorted(
        lista,
        key=lambda x: x["total"],
        reverse=True
    )

    train = []
    val = []
    test = []

    soma_train = 0
    soma_val = 0
    soma_test = 0

    for paciente in lista:

        deficits = {
            "train": alvo_train - soma_train,
            "val": alvo_val - soma_val,
            "test": alvo_test - soma_test
        }

        destino = max(
            deficits,
            key=deficits.get
        )

        if destino == "train":

            train.append(paciente)
            soma_train += paciente["total"]

        elif destino == "val":

            val.append(paciente)
            soma_val += paciente["total"]

        else:

            test.append(paciente)
            soma_test += paciente["total"]

    return train, val, test

# ==========================================
# SPLIT POR CLASSE
# ==========================================

mgn_train, mgn_val, mgn_test = distribuir_grupo(mgn)

bgn_train, bgn_val, bgn_test = distribuir_grupo(bgn)

nrm_train, nrm_val, nrm_test = distribuir_grupo(nrm)

train = (
    mgn_train +
    bgn_train +
    nrm_train
)

val = (
    mgn_val +
    bgn_val +
    nrm_val
)

test = (
    mgn_test +
    bgn_test +
    nrm_test
)

# ==========================================
# SALVAR CSV
# ==========================================

os.makedirs(
    "outputs",
    exist_ok=True
)

def salvar_csv(nome, dados):

    caminho = os.path.join(
        "outputs",
        nome
    )

    with open(
        caminho,
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

        for p in dados:

            writer.writerow([
                p["paciente"],
                p["id"],
                p["tipo"],
                p["normal"],
                p["borda"],
                p["tumor"],
                p["total"]
            ])

# ==========================================
# GERA ARQUIVOS
# ==========================================

salvar_csv("train.csv", train)
salvar_csv("val.csv", val)
salvar_csv("test.csv", test)

# ==========================================
# RELATÓRIO
# ==========================================

def resumo(nome, dados):

    patches = sum(
        int(p["total"])
        for p in dados
    )

    mgn_count = sum(
        1 for p in dados
        if p["tipo"].upper() == "MGN"
    )

    bgn_count = sum(
        1 for p in dados
        if p["tipo"].upper() == "BGN"
    )

    nrm_count = sum(
        1 for p in dados
        if p["tipo"].upper() == "NRM"
    )

    return (
        f"{nome}\n"
        f"Pacientes: {len(dados)}\n"
        f"MGN: {mgn_count}\n"
        f"BGN: {bgn_count}\n"
        f"NRM: {nrm_count}\n"
        f"Patches: {patches}\n\n"
    )

texto = ""

texto += resumo(
    "TREINO",
    train
)

texto += resumo(
    "VALIDACAO",
    val
)

texto += resumo(
    "TESTE",
    test
)

with open(
    os.path.join(
        "outputs",
        "relatorio.txt"
    ),
    "w",
    encoding="utf-8"
) as f:

    f.write(texto)

# ==========================================
# RESUMO FINAL
# ==========================================

print()
print("===================================")
print("SPLIT CONCLUÍDO")
print("===================================")
print(texto)

print("Arquivos gerados:")
print("outputs/train.csv")
print("outputs/val.csv")
print("outputs/test.csv")
print("outputs/relatorio.txt")