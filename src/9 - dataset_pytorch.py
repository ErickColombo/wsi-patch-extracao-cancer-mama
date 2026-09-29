import json
import pandas as pd
import numpy as np

from PIL import Image

import torch
from torch.utils.data import Dataset


class HistopathologyDataset(Dataset):

    def __init__(
        self,
        csv_path,
        split,
        config_path="config/config_dataset.json",
        transform=None
    ):

        self.transform = transform

        with open(
            config_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.config = json.load(f)

        self.df = pd.read_csv(csv_path)

        self.df = self.df[
            self.df["split"] == split
        ].reset_index(drop=True)

        print(
            f"{split}: "
            f"{len(self.df)} patches"
        )

    def __len__(self):

        return len(self.df)

    # ==========================================
    # CONVERSÃO DE REPRESENTAÇÃO CROMÁTICA
    # ==========================================

    def _carregar_imagem(self, caminho):

        img = Image.open(
            caminho
        ).convert("RGB")

        img_np = np.array(img)

        # ==========================================
        # RGB
        # ==========================================

        if self.config["modo_rgb"]:

            return Image.fromarray(img_np)

        # ==========================================
        # GRAYSCALE
        # ==========================================

        if self.config["modo_grayscale"]:

            gray = Image.fromarray(
                img_np
            ).convert("L")

            gray = np.array(gray)

            gray = np.stack(
                [gray, gray, gray],
                axis=-1
            )

            return Image.fromarray(gray)

        # ==========================================
        # CANAL R
        # ==========================================

        if self.config["canal_r"]:

            canal = img_np[:, :, 0]

        # ==========================================
        # CANAL G
        # ==========================================

        elif self.config["canal_g"]:

            canal = img_np[:, :, 1]

        # ==========================================
        # CANAL B
        # ==========================================

        elif self.config["canal_b"]:

            canal = img_np[:, :, 2]

        else:

            raise ValueError(
                "Nenhuma representação selecionada "
                "no config_dataset.json"
            )

        canal = np.stack(
            [canal, canal, canal],
            axis=-1
        )

        return Image.fromarray(canal)

    # ==========================================
    # ITEM
    # ==========================================

    def __getitem__(self, idx):

        row = self.df.iloc[idx]

        caminho = row["caminho"]

        img = self._carregar_imagem(
            caminho
        )

        # ==========================================
        # LABEL
        # ==========================================

        tipo = row["tipo"]

        label = (
            1
            if tipo == "MGN"
            else 0
        )

        if self.transform:

            img = self.transform(img)

        return img, label