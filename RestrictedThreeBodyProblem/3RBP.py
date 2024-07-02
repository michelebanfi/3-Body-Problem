import torch
import pandas as pd
import numpy as np
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR
import time

diego = False
import sys
if diego:
    sys.path.append("D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/Utils")
    from DataEvaluator import evaluate
    from DataLoader import loadData
    from Losses import NormalizedMeanSquaredError

    sys.path.append("D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/Benchmarks")
    from GRU import GRU
    from LSTM import LSTM

    sys.path.append("D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/Reservoirs")
    from GRUReservoir import GRUReservoir
    from LSTMReservoir import LSTMReservoir
    from ESNReservoir import ESNReservoir
else:
    from Utils.DataEvaluator import evaluate
    from Utils.DataLoader import loadData
    from Benchmarks.GRU import GRU
    from Reservoirs.GRUReservoir import GRUReservoir
    from Reservoirs.ESNReservoir import ESNReservoir
    from Benchmarks.LSTM import LSTM
    from Reservoirs.LSTMReservoir import LSTMReservoir

import matplotlib.pyplot as plt

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print("Working on:", device)
print(30*"-")

# Define sequences length
pred_len = 100
input_len = 100

# Define the model parameters
io_size = 2
num_epochs = 20

### LOAD DATA
# Load the data
print("Loading data...")
train_t, train_dataloader, val_t, val_dataloader = loadData(pred_len, input_len, file="3BP", train_samples=100, val_samples=10)
print("Train batches:", len(train_dataloader))
print("Train input sequences:", len(train_dataloader.dataset))
print("Validation batches:", len(val_dataloader))
print("Validation input sequences:", len(val_dataloader.dataset))
print(30*"-")

model = ESNReservoir(io_size, 128, io_size, pred_len=pred_len).to(device)
modelBenchmark = LSTM(io_size, 128, io_size, num_layers=1, pred_len=pred_len).to(device)

### RESERVOIR
# Define training setup
criterion = NormalizedMeanSquaredError
# optimizer
optimizer = optim.Adam(model.parameters(), lr=0.001)
# scheduler
scheduler = StepLR(optimizer, step_size=5, gamma=0.5)
print("Reservoir training...")
# start counting the time
start = time.time()
# Train the model
val_results, train_losses = (
    evaluate(num_epochs, criterion, optimizer, model, train_dataloader, val_dataloader, device, scheduler))
# stop counting the time
end = time.time()
print('Time elapsed: ', end - start, "s")
print(30*"-")

### BENCHMARK MODEL
print("Benchmark training...")
# training setup
# criterion
criterion = NormalizedMeanSquaredError
# optimizer
optimizer = optim.Adam(modelBenchmark.parameters(), lr=0.001)
# scheduler
scheduler = StepLR(optimizer, step_size=5, gamma=0.5)
# start counting the time
start = time.time()
# Train the benchmark model
val_results_benchmark, train_losses_benchmark = (
    evaluate(num_epochs, criterion, optimizer, modelBenchmark, train_dataloader, val_dataloader, device, scheduler))
# stop counting the time
end = time.time()
print('Time elapsed: ', end - start, "s")
print(30*"-")

### PLOTS
# Plotting the predictions
plt.figure(figsize=(15, 15))

how_many_plots = min(4, len(val_dataloader.dataset))
n_sequences = len(val_dataloader.dataset)
sequence_to_plot = torch.randint(0, n_sequences, (how_many_plots,))

batch_size = val_results['targets'][0].size(0)
batch_to_plot = torch.randint(0, batch_size, (how_many_plots,))

for plot in range(how_many_plots - how_many_plots%2):
    seq = sequence_to_plot[plot].item()
    batch = batch_to_plot[plot].item()
    # Plotting the predictions
    plt.subplot(how_many_plots // 2, 2, plot + 1)
    plt.plot(val_results['inputs'][seq][batch,:,0].cpu(), val_results['inputs'][seq][batch,:,1].cpu(), label='Input')
    plt.plot(val_results['targets'][seq][batch,:,0].cpu(), val_results['targets'][seq][batch,:,1].cpu(), label='Target')
    plt.plot(val_results['predictions'][seq][batch,:,0].cpu(), val_results['predictions'][seq][batch,:,1].cpu(), label='Predicted (Reservoir)')
    plt.plot(val_results_benchmark['predictions'][seq][batch,:,0].cpu(), val_results_benchmark['predictions'][seq][batch,:,1].cpu(), label='Predicted (Benchmark)')
    plt.xlabel('Time step')
    plt.legend()
    plt.grid()

plt.tight_layout()
if diego:
    plt.savefig('D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/RestrictedThreeBodyProblem/Media/3BP_prediction.png')
else:
    plt.savefig('Media/3BP_prediction.png')
plt.close()

