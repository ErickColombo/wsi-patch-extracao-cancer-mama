import requests
import os
import time
import io
import json
import numpy as np
from PIL import Image
import concurrent.futures
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# CARREGA CONFIGURAÇÕES
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

slide_id = config["slide_id"]
classificacao = config["classificacao"]

nivel_zoom = config["nivel_zoom"]
max_threads = config["max_threads"]

inicio_x = config["inicio_x"]
limite_maximo_x = config["limite_maximo_x"]

inicio_y = config["inicio_y"]
limite_maximo_y = config["limite_maximo_y"]

base_url = config["base_url"]
slide_path = config[f"slide_path"]
print("slide_path:")
print(slide_path)

print("\nrepr(slide_path):")
print(repr(slide_path))

pasta_principal = config["pasta_principal"]



# CONFIGURAÇÃO DE SESSÃO HTTP
def criar_sessao_http():
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=max_threads,
        pool_maxsize=max_threads * 2
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


http_session = criar_sessao_http()

# ESTRUTURA DE PASTAS E CACHE
nome_pasta_base = f"{slide_id}_{classificacao}"

save_directory = os.path.join(
    pasta_principal,
    nome_pasta_base,
    f"level_{nivel_zoom}"
)

os.makedirs(save_directory, exist_ok=True)

cache_file = os.path.join(
    save_directory,
    "cache_processados.txt"
)

cache_lock = threading.Lock()


def carregar_cache():
    cache = set()

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            for linha in f:
                cache.add(linha.strip())

    return cache


def salvar_no_cache(cache_key):
    with cache_lock:
        with open(cache_file, "a") as f:
            f.write(f"{cache_key}\n")


tiles_processados = carregar_cache()

# FUNÇÃO DE PROCESSAMENTO
def process_and_save_tile(level, x, y, save_dir):


    #print(response.url)
    cache_key = f"{level}_{x}_{y}"

    if cache_key in tiles_processados:
        return True

    params = {
        "iLevel": level,
        "iX": x,
        "iY": y,
        "strSlidePath": slide_path,
        "iLight": 0,
        "iContrast": 0,
        "fGamma": 1,
        "iRgbRed": 0,
        "iRgbGreen": 0,
        "iRgbBlue": 0,
        "boolGrayscale": "false",
        "boolNegative": "false",
        "strFreeUploadUrl": "",
        "iFluorescenceNum": 0,
        "iFluorescenceChannel": 0,
        "iFlatNumber": -1,
        "channels": ""
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    max_tentativas = 3

    for tentativa in range(1, max_tentativas + 1):

        try:
            response = http_session.get(
                base_url,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200 or len(response.content) < 1024:
                print(
                    f"Vazio/Inválido: X{x} Y{y} "
                    f"(Status: {response.status_code}, "
                    f"Tamanho: {len(response.content)} bytes)"
                )

                salvar_no_cache(cache_key)
                return False

            img_bytes = response.content

            img = Image.open(
                io.BytesIO(img_bytes)
            ).convert("L")

            img_np = np.array(img)

            # Branco puro ou muito vidro
            if np.all(img_np == 255):
                print(f"Vidro: X{x} Y{y} ignorado.")

                salvar_no_cache(cache_key)
                return True

            pixels_brancos = np.sum(img_np > 235)
            proporcao_branco = pixels_brancos / img_np.size

            # Muito fundo
            if proporcao_branco > 0.85:
                print(
                    f"Muito Vidro: X{x} Y{y} "
                    f"é {proporcao_branco:.1%} fundo."
                )

                salvar_no_cache(cache_key)
                return True

            filename = f"patch_L{level}_X{x}_Y{y}.jpg"

            with open(
                os.path.join(save_dir, filename),
                "wb"
            ) as f:
                f.write(img_bytes)

            print(
                f"Salvo: L{level} X{x} Y{y}"
            )

            salvar_no_cache(cache_key)

            return True

        except (requests.exceptions.RequestException, Exception) as e:

            if tentativa < max_tentativas:

                print(
                    f"Retentando X{x} Y{y} "
                    f"(Tentativa {tentativa}/{max_tentativas})..."
                )

                time.sleep(1.5 * tentativa)

            else:

                print(
                    f"Erro definitivo em X{x} Y{y}: {e}"
                )

                return False

# EXECUÇÃO PARALELA
if __name__ == "__main__":

    print(f"Iniciando varredura do nível {nivel_zoom}")
    print(
        f"Intervalo X: [{inicio_x} -> {limite_maximo_x}] "
        f"| Intervalo Y: [{inicio_y} -> {limite_maximo_y}]"
    )
    print(f"Salvando em: {save_directory}")
    print(
        f"Cache atual: {len(tiles_processados)} "
        f"imagens ignoradas ou já baixadas."
    )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_threads
    ) as executor:

        futuros = []

        for x in range(inicio_x, limite_maximo_x):
            for y in range(inicio_y, limite_maximo_y):

                cache_key = f"{nivel_zoom}_{x}_{y}"

                if cache_key in tiles_processados:
                    continue

                futuros.append(
                    executor.submit(
                        process_and_save_tile,
                        nivel_zoom,
                        x,
                        y,
                        save_directory
                    )
                )

                time.sleep(0.1)

        for futuro in concurrent.futures.as_completed(futuros):
            pass

    print("Extração concluída.")