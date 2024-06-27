import torch
import pandas as pd
import torch.nn as nn
import torch.optim as optim
import time

import sys
sys.path.append("D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/Utils")
from DataEvaluator import evaluate
from DataLoader import loadData

sys.path.append("D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/Benchmarks")
from LSTM import LSTM

sys.path.append("D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/Reservoirs")
from LSTMReservoir import LSTMReservoir

import matplotlib.pyplot as plt

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(device)

# Load data from CSV
df = pd.read_csv('D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/RestrictedThreeBodyProblem/Data/3BP.csv')
data = torch.tensor(df[['x', 'y']].values)

t = df['time'].values

# Define sequences length
pred_len = 200
input_len = 200

# Define the model parameters
io_size = 2
reservoir_size = 512
num_epochs = 1
num_layers = 2

### LOAD DATA
# Load the data
print("Loading data...")
train_t, train_dataloader, val_t, val_dataloader = loadData(data, t, pred_len, input_len)
print("Train batches:", len(train_dataloader))
print("Train input sequences:", len(train_dataloader.dataset))
print("Validation batches:", len(val_dataloader))
print("Validation input sequences:", len(val_dataloader.dataset))
print(30*"-")

# use the Reservoir
model = LSTMReservoir(io_size, reservoir_size, io_size, num_layers, pred_len=pred_len).to(device)
modelBenchmark = LSTM(io_size, reservoir_size, io_size, num_layers, pred_len=pred_len).to(device)

# NMSE weighted as criterion
def NormalizedMeanSquaredError(y_pred, y_true):
    pred_len = y_pred.size(1)
    batch_size = y_pred.size(0)

    squared_dist = torch.sum((y_true - y_pred)** 2, dim=2) # squared euclidean distances between predictions
    true_squared_norm = torch.sum(y_true ** 2, dim=2)
    nmse = squared_dist / true_squared_norm
    # actual (from above) shape: (batch size, prediction length)
    # as a neutral transformation for an overall error just take the mean on the prediction length and then on the batch size
    # WEIGHTED
    weights = torch.arange(start=1,end=pred_len+1,step=1)
    weights = weights/weights.sum()
    aggregated_nmse = torch.zeros(batch_size)
    for batch in range(batch_size):
        aggregated_nmse[batch] = torch.dot(nmse[batch], weights)
    # aggregated_nmse = torch.mean(torch.mean(nmse, dim=1), dim=0) # UNWEIGHTED
    aggregated_nmse = torch.mean(aggregated_nmse, dim=0)
    return aggregated_nmse



### RESERVOIR
# Define training setup
# criterion
criterion = NormalizedMeanSquaredError
# optimizer
optimizer = optim.Adam(model.parameters(), lr=0.001)
print("Reservoir training...")
# start counting the time
start = time.time()
# Train the model
val_results, train_losses = (
    evaluate(num_epochs, criterion, optimizer, model, train_dataloader, val_dataloader, device))
# stop counting the time
end = time.time()
print('Time elapsed: ', end - start, "s")
print(30*"-")



### BENCHMARK MODEL
print("Benchmark training...")
# training setup
optimizer = optim.Adam(modelBenchmark.parameters(), lr=0.001)
criterion = NormalizedMeanSquaredError
# start counting the time
start = time.time()
# Train the benchmark model
val_results_benchmark, train_losses_benchmark = (
    evaluate(num_epochs, criterion, optimizer, modelBenchmark, train_dataloader, val_dataloader, device))
# stop counting the time
end = time.time()
print('Time elapsed: ', end - start, "s")
print(30*"-")



### PLOTS
# Plotting the predictions
plt.figure(figsize=(15, 5))

how_many_plots = 4
n_runs = len(val_results['losses'])
run_to_plot = torch.randint(0, n_runs, (how_many_plots,))

batch_size = val_results['targets'][0].size(0)
batch_to_plot = torch.randint(0, batch_size, (how_many_plots,))

for plot in range(how_many_plots - how_many_plots%2):
    run = run_to_plot[plot].item()
    batch = batch_to_plot[plot].item()
    # Plotting the predictions
    plt.subplot(how_many_plots // 2, 2, plot + 1)
    plt.plot(val_results['targets'][run][batch,:,0], val_results['targets'][run][batch,:,1], label='Real')
    plt.plot(val_results['predictions'][run][batch,:,0], val_results['predictions'][run][batch,:,1], label='Predicted (Reservoir)')
    plt.plot(val_results_benchmark['predictions'][run][batch,:,0], val_results_benchmark['predictions'][run][batch,:,1], label='Predicted (Benchmark)')
    plt.xlabel('Time step')
    plt.legend()
    plt.grid()

plt.tight_layout()
plt.savefig('D:/File_vari/Scuola/Universita/Bicocca/Magistrale/AI4ST/23-24/II_semester/AIModels/3_Body_Problem/RestrictedThreeBodyProblem/Media/3BP_prediction.png')
plt.close()

