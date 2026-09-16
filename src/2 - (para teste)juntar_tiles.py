import os
import re
import json
from PIL import Image

# CARREGA CONFIGURAÇÕES
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


slide_id = config["slide_id"]
classificacao = config["classificacao"]
nivel_zoom = config["nivel_zoom"]

pasta_principal = config["pasta_principal"]

tamanho_tile_original = config["tamanho_tile_original"]
fator_reducao = config["fator_reducao"]

# CAMINHOS AUTOMÁTICOS
nome_pasta_base = f"{slide_id}_{classificacao}"

pasta_entrada = os.path.join(
    pasta_principal,
    nome_pasta_base,
    f"level_{nivel_zoom}"
)

diretorio_destino = os.path.join("dataset_info", str(slide_id))

os.makedirs(diretorio_destino, exist_ok=True)

arquivo_saida = os.path.join(
    diretorio_destino,
    f"MAPA_VALIDACAO_{slide_id}_{classificacao}.jpg"
)

# FUNÇÃO PRINCIPAL
def gerar_mapa_visao_geral(
    pasta_tiles,
    nome_saida,
    tamanho_tile_original=256,
    fator_reducao=8
):

    print("Mapeando arquivos na pasta...")

    max_x = 0
    max_y = 0
    tiles = {}

    padrao = re.compile(r"X(\d+)_Y(\d+)")

    for arquivo in os.listdir(pasta_tiles):

        if arquivo.lower().endswith(".jpg"):

            match = padrao.search(arquivo)

            if match:

                x = int(match.group(1))
                y = int(match.group(2))

                max_x = max(max_x, x)
                max_y = max(max_y, y)

                tiles[(x, y)] = os.path.join(
                    pasta_tiles,
                    arquivo
                )

    if not tiles:
        print("Nenhum tile encontrado.")
        return

    print(f"Foram encontrados {len(tiles)} tiles válidos.")

    tamanho_reduzido = (
        tamanho_tile_original // fator_reducao
    )

    largura_original = (
        (max_x + 1) * tamanho_reduzido
    )

    altura_original = (
        (max_y + 1) * tamanho_reduzido
    )

    canvas_largura = altura_original
    canvas_altura = largura_original

    print(
        f"Criando miniatura da lâmina "
        f"({canvas_largura} x {canvas_altura})"
    )

    cor_fundo = (60, 60, 60)

    canvas = Image.new(
        "RGB",
        (canvas_largura, canvas_altura),
        cor_fundo
    )

    print("Construindo mapa...")

    for (x, y), caminho_arquivo in tiles.items():

        try:

            img_tile = Image.open(
                caminho_arquivo
            )

            img_tile = img_tile.resize(
                (
                    tamanho_reduzido,
                    tamanho_reduzido
                )
            )

            img_tile_rotacionada = (
                img_tile.transpose(
                    Image.Transpose.ROTATE_270
                )
            )

            novo_x = (
                altura_original
                - (y * tamanho_reduzido)
                - tamanho_reduzido
            )

            novo_y = (
                x * tamanho_reduzido
            )

            canvas.paste(
                img_tile_rotacionada,
                (novo_x, novo_y)
            )

        except Exception as e:

            print(
                f"Erro ao processar "
                f"{caminho_arquivo}: {e}"
            )

    print("Salvando mapa principal...")

    canvas.save(
        nome_saida,
        "JPEG",
        quality=90
    )

    mask_path = nome_saida.replace(
        ".jpg",
        "_MASK.png"
    )

    canvas.save(
        mask_path,
        "PNG"
    )

    print(
        f"Máscara para anotação criada: "
        f"{mask_path}"
    )

    meta = {

        "slide_id": slide_id,
        "classificacao": classificacao,

        "max_x": max_x,
        "max_y": max_y,

        "tamanho_tile_original": tamanho_tile_original,

        "fator_reducao": fator_reducao,

        "tamanho_reduzido": tamanho_reduzido,

        "largura_original": largura_original,
        "altura_original": altura_original,

        "canvas_largura": canvas_largura,
        "canvas_altura": canvas_altura
    }

    json_path = nome_saida.replace(
        ".jpg",
        ".json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            meta,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"Metadados salvos: "
        f"{json_path}"
    )

    print(
        f"Mapa salvo com sucesso: "
        f"{nome_saida}"
    )

# EXECUÇÃO
if __name__ == "__main__":

    gerar_mapa_visao_geral(
        pasta_entrada,
        arquivo_saida,
        tamanho_tile_original=tamanho_tile_original,
        fator_reducao=fator_reducao
    )