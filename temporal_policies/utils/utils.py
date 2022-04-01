from typing import Tuple, Union

import gym  # type: ignore
import numpy as np  # type: ignore
import torch  # type: ignore


def to_device(batch, device):
    if isinstance(batch, dict):
        batch = {k: to_device(v, device) for k, v in batch.items()}
    elif isinstance(batch, list) or isinstance(batch, tuple):
        batch = [to_device(v, device) for v in batch]
    elif isinstance(batch, torch.Tensor):
        batch = batch.to(device)
    return batch

def to_tensor(batch):
    if isinstance(batch, dict):
        batch = {k: to_tensor(v) for k, v in batch.items()}
    elif isinstance(batch, list) or isinstance(batch, tuple):
        batch = [to_tensor(v) for v in batch]
    elif isinstance(batch, np.ndarray):
        batch = torch.from_numpy(batch)
    return batch

def to_np(batch):
    if isinstance(batch, dict):
        batch = {k: to_np(v) for k, v in batch.items()}
    elif isinstance(batch, list) or isinstance(batch, tuple):
        batch = [to_np(v) for v in batch]
    elif isinstance(batch, torch.Tensor):
        batch = batch.detach().cpu().numpy()
    return batch

def unsqueeze(batch, dim):
    if isinstance(batch, dict):
        batch = {k: unsqueeze(v, dim) for k, v in batch.items()}
    elif isinstance(batch, list) or isinstance(batch, tuple):
        batch = [unsqueeze(v, dim) for v in batch]
    elif isinstance(batch, np.ndarray):
        batch = np.expand_dims(batch, dim)
    elif isinstance(batch, torch.Tensor):
        batch = batch.unsqueeze(dim)
    return batch

def squeeze(batch, dim):
    if isinstance(batch, dict):
        batch = {k: squeeze(v, dim) for k, v in batch.items()}
    elif isinstance(batch, list) or isinstance(batch, tuple):
        batch = [squeeze(v, dim) for v in batch]
    elif isinstance(batch, np.ndarray):
        batch = np.squeeze(batch, dim)
    elif isinstance(batch, torch.Tensor):
        batch = batch.squeeze(dim)
    return batch

def get_from_batch(batch, start, end=None):
    if isinstance(batch, dict):
        batch = {k: get_from_batch(v, start, end=end) for k, v in batch.items()}
    elif isinstance(batch, list) or isinstance(batch, tuple):
        batch = [get_from_batch(v, start, end=end) for v in batch]
    elif isinstance(batch, np.ndarray) or isinstance(batch, torch.Tensor):
        if end is None:
            batch = batch[start]
        else:
            batch = batch[start:end]
    return batch

def contains_tensors(batch):
    if isinstance(batch, dict):
        return any([contains_tensors(v) for v in batch.values()])
    if isinstance(batch, list):
        return any([contains_tensors(v) for v in batch])
    elif isinstance(batch, torch.Tensor):
        return True
    else:
        return False

class PrintNode(torch.nn.Module):

    def __init__(self, name=""):
        super().__init__()
        self.name = name

    def forward(self, x):
        print(self.name, x.shape)
        return x

def fetch_from_dict(data_dict, keys):
    '''
    inputs:
        data_dict: a nested dictionary datastrucutre
        keys: a list of string keys, with '.' separating nested items.
    '''
    outputs = []
    if not isinstance(keys, list) and not isinstance(keys, tuple):
        keys = [keys]
    for key in keys:
        key_parts = key.split('.')
        current_dict = data_dict
        while len(key_parts) > 1:
            current_dict = current_dict[key_parts[0]]
            key_parts.pop(0)
        outputs.append(current_dict[key_parts[0]])  
    if len(outputs) == 1:
        outputs = outputs[0]
    return outputs
