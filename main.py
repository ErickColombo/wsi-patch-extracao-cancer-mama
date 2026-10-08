import os
import json
import pandas as pd
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights
import timm

# ==========================================
# 1. CLASSE DO DATASET
# ==========================================
class HistopathologyDataset(Dataset):
    def __init__(self, csv_path, split, config_path="config_dataset.json", transform=None):
        self.transform = transform
        
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.df = pd.read_csv(csv_path)
        self.df = self.df[self.df["split"] == split]

        classes_permitidas = []
        if self.config.get("usar_normal", True): classes_permitidas.append("NORMAL")
        if self.config.get("usar_tumor", True): classes_permitidas.append("TUMOR")
        if self.config.get("usar_borda", False): classes_permitidas.append("BORDA")
            
        self.df = self.df[self.df["classe"].isin(classes_permitidas)].reset_index(drop=True)
        print(f"[{split.upper()}] Carregado: {len(self.df)} patches mapeados (Filtro: {classes_permitidas}).")

    def __len__(self):
        return len(self.df)

    def _carregar_imagem(self, caminho):
        img = Image.open(caminho).convert("RGB")
        img_np = np.array(img)

        if self.config.get("modo_rgb"):
            return Image.fromarray(img_np)

        if self.config.get("modo_grayscale"):
            gray = Image.fromarray(img_np).convert("L")
            gray = np.array(gray)
            gray = np.stack([gray, gray, gray], axis=-1)
            return Image.fromarray(gray)

        if self.config.get("canal_r"):
            canal = img_np[:, :, 0]
        elif self.config.get("canal_g"):
            canal = img_np[:, :, 1]
        elif self.config.get("canal_b"):
            canal = img_np[:, :, 2]
        else:
            raise ValueError("Erro: Nenhuma representação ativada no JSON.")

        canal = np.stack([canal, canal, canal], axis=-1)
        return Image.fromarray(canal)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        caminho = os.path.normpath(row["caminho"])
        img = self._carregar_imagem(caminho)

        tipo = row["tipo"]
        label = 1 if tipo == "MGN" else 0

        if self.transform:
            img = self.transform(img)

        return img, label

# ==========================================
# 2. DATA AUGMENTATION
# ==========================================
def get_transforms():
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    train_transform = transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomChoice([
            transforms.RandomRotation((0, 0)),
            transforms.RandomRotation((90, 90)),
            transforms.RandomRotation((180, 180)),
            transforms.RandomRotation((270, 270)),
        ]),
        transforms.ToTensor(),
        normalize
    ])
    val_test_transform = transforms.Compose([
        transforms.ToTensor(),
        normalize
    ])
    return train_transform, val_test_transform

# ==========================================
# 3. CONSTRUÇÃO DO MODELO
# ==========================================
def build_model(model_name="resnet50"):
    print(f"Construindo arquitetura: {model_name}...")
    if model_name == "resnet50":
        model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        model.fc = nn.Linear(model.fc.in_features, 1)
    elif model_name == "efficientnet_v2":
        model = efficientnet_v2_s(weights=EfficientNet_V2_S_Weights.IMAGENET1K_V1)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, 1)
    elif model_name == "convnext_v2":
        model = timm.create_model('convnextv2_tiny', pretrained=True, num_classes=1)
    else:
        raise ValueError(f"Modelo {model_name} não suportado.")
    return model

# ==========================================
# 4. MOTOR DE TREINAMENTO
# ==========================================
def treinar_modelo(model, train_loader, val_loader, device, epochs=50, caminho_salvar='melhor_modelo.pth'):
    criterion = nn.BCEWithLogitsLoss() 
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-2)

    best_val_loss = float('inf')
    patience = 10
    patience_counter = 0

    model.to(device)

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        for images, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Treino]"):
            images, labels = images.to(device), labels.to(device).float()
            optimizer.zero_grad()
            outputs = model(images).squeeze()
            if outputs.dim() == 0: outputs = outputs.unsqueeze(0) 
            
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * images.size(0)
            
        train_loss /= len(train_loader.dataset)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, labels in tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Valid]"):
                images, labels = images.to(device), labels.to(device).float()
                outputs = model(images).squeeze()
                if outputs.dim() == 0: outputs = outputs.unsqueeze(0)
                
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                
        val_loss /= len(val_loader.dataset)
        print(f"--> Fim da Epoch {epoch+1} | Loss Treino: {train_loss:.4f} | Loss Valid: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), caminho_salvar)
            print(f"    [*] Melhoria detectada. Pesos salvos em: {caminho_salvar}")
        else:
            patience_counter += 1
            print(f"    [!] Sem melhoria. Paciência: {patience_counter}/{patience}")
            if patience_counter >= patience:
                print("\nEarly Stopping ativado.")
                break

# ==========================================
# 5. EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    ARQUIVO_CSV = os.path.join("outputs", "patches_master.csv") 
    ARQUIVO_JSON = "config_dataset.json"  
    MODELO_ESCOLHIDO = "resnet50" 
    MODO_TESTE_RAPIDO = True 
    BATCH_SIZE = 8 
    NUM_WORKERS = 0 
    
    # SISTEMA DE PASTAS
    PASTA_DADOS = f"dados_{MODELO_ESCOLHIDO}"
    os.makedirs(PASTA_DADOS, exist_ok=True)
    CAMINHO_PESOS = os.path.join(PASTA_DADOS, "melhor_modelo.pth")

    print("="*50)
    print(f"INÍCIO DO EXPERIMENTO - {MODELO_ESCOLHIDO.upper()}")
    print(f"Os resultados serão salvos na pasta: {PASTA_DADOS}/")
    print("="*50)

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

    train_transform, val_transform = get_transforms()

    df_temp = pd.read_csv(ARQUIVO_CSV)
    splits_disponiveis = df_temp["split"].unique()
    val_split_name = "val" if "val" in splits_disponiveis else "valid" if "valid" in splits_disponiveis else "validacao"
    
    train_dataset = HistopathologyDataset(ARQUIVO_CSV, split="train", config_path=ARQUIVO_JSON, transform=train_transform)
    val_dataset = HistopathologyDataset(ARQUIVO_CSV, split=val_split_name, config_path=ARQUIVO_JSON, transform=val_transform)

    if MODO_TESTE_RAPIDO:
        train_dataset = Subset(train_dataset, range(min(64, len(train_dataset))))
        val_dataset = Subset(val_dataset, range(min(32, len(val_dataset))))

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    model = build_model(model_name=MODELO_ESCOLHIDO)
    
    treinar_modelo(model, train_loader, val_loader, device, epochs=5, caminho_salvar=CAMINHO_PESOS)