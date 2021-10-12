import typer
import torch
from typing import List
import time
import os
from enum import Enum
from pathlib import Path
import math
from tqdm import tqdm
import torch.fx as fx


# TODO: Make commands return a nn.Module instead of None so operations can be composed

app = typer.Typer()

class Precision(Enum):
    int8 = "int8"
    float16 = "float16"

class Device(str, Enum):
    cpu = "cpu"
    gpu = "gpu"

class Architecture(str, Enum):
    ipex = "ipex"
    tensorrt = "tensorrt"
    fastertransformer = "fastertransformer"


@app.command()
def hello() -> None:
    typer.echo(f"Hello torchprep")

@app.command()
def distill(model_path : Path, device : Device, parameter_scaling : int, layer_scaling : int = None, profile : List[int] = None) -> torch.nn.Module:
    """
    Create a smaller student model by setting a distillation ratio and teach it how to behave exactly like your existing model
    """
    typer.echo(f"Coming soon")
    typer.echo("See this notebook for more information https://colab.research.google.com/drive/1RzQtprrHx8PokLQsFiQPAKzfn_DiTpDN?usp=sharing")

@app.command()
def fuse(model_path : Path, device : Device = Device.cpu) -> torch.nn.Module:
    """
    Supports optimizations including conv/bn fusion, dropout removal and mkl layout optimizations
    https://github.com/pytorch/pytorch/blob/master/torch/fx/experimental/optimization.py#L234
    """
    # model = load_model(model_path, device)
    # optimized_model = fx.experimental.optimization.optimize_for_inference(model)
    # # TODO: Add profiling

    # torch.save(optimized_model, 'optimized_model.pt') 
    # return optimized_model
    typer.echo("coming soon")

@app.command()
def env_variables(model_path : Path, architecture : Architecture) -> None:
    """
    Set environment variables for optimized inference. Run this command on the machine where inference will happen!
    """
    if architecture == Architecture.ipex:
        os.environ["OMP_NUM_THREADS"] = 1
        os.environ["KMP_BLOCKTIME"] = 1
    else:
        typer.echo(f"support for architecture {architecture} coming soon")


@app.command()
def quantize(model_path : Path, precision : Precision ,
 device : Device = Device.cpu, profile : str = typer.Option(default=None, help="Comma seperated input tensor shape")) -> torch.nn.Module:
    # TODO: define model output path
    """
    Quantize a saved torch model to a lower precision float format to reduce its size and latency
    """
    model = load_model(model_path, device)

    if device == Device.cpu:
        if precision == "int8":
            dtype = torch.qint8
        else:
            dtype = torch.float16
    quantized_model = torch.quantization.quantize_dynamic(
    model, {torch.nn.LSTM, torch.nn.Linear, torch.nn.Conv2d}, dtype=dtype
)
    # TODO: Add AMP
    if device == Device.gpu:
        if precision == Precision.int8:
            print("int8 precision is not supported for GPUs, defaulting to float16")
        quantized_model = model.half()
    
    print("Model successfully quantized")

    print_size_of_model(model, label = "base model")
    print_size_of_model(quantized_model, label = "quantized_model")
    
    if profile:
        profile = map(int,profile.split(','))
        input_tensor = torch.randn(*profile)
        profile_model(model, input_tensor, label = "base model")
        profile_model(quantized_model, input_tensor, label = "quantized_model")
    
    torch.save(quantized_model, 'quantized_model.pt')
    print(f"model quantized_model.pt was saved")
    return quantized_model


def profile_model(model :torch.nn.Module, input_tensor, label : str = "model", iterations : int = 100) -> List[float]:
    print("Starting profile")

    warmup_iterations = iterations // 10
    for step in range(warmup_iterations):
        model(input_tensor)

    durations = []
    for step in tqdm(range(iterations)):
        tic = time.time()
        model(input_tensor)
        toc = time.time()
        duration = toc - tic
        duration = math.trunc(duration * 1000)
        durations.append(duration)
    avg = sum(durations) / len(durations)
    min_latency = min(durations)
    max_latency = max(durations)
    print(f"Average latency for {label} is: {avg} ms")
    print(f"Min latency for {label} is: {min_latency} ms")
    print(f"Max p99 latency for {label} is: {max_latency} ms")
    return [avg, min_latency, max_latency]

def load_model(model_path: str, device="cpu") -> torch.nn.Module:
    map_location = torch.device(device)
    model = torch.load(model_path, map_location=map_location)
    return model

def print_size_of_model(model : torch.nn.Module, label : str = ""):
    torch.save(model.state_dict(), "temp.p")
    size=os.path.getsize("temp.p")
    print("model: ",label,':','Size (MB):', size/1e6)
    os.remove('temp.p')
    return size