## Introduction

PyTorch inferable quantizers are used for inference only. The inferable quantizer should contain all quantization
information needed for quantizing a PyTorch tensor. The quantization of the tensor can be done by calling the quantizer
while passing the unquantized tensor.

## Implemented PyTorch Inferable Quantizers

Several PyTorch inferable quantizers were implemented for activation quantization:

[ActivationPOTInferableQuantizer](activation_inferable_quantizers/activation_pot_inferable_quantizer.py)

[ActivationSymmetricInferableQuantizer](activation_inferable_quantizers/activation_symmetric_inferable_quantizer.py)

[ActivationUniformInferableQuantizer](activation_inferable_quantizers/activation_uniform_inferable_quantizer.py)

Each of them should be used according to the quantization method of the quantizer (power-of-two, symmetric and uniform
quantization respectively).

Similarly, several PyTorch inferable quantizers were implemented for weights quantization:

[WeightsPOTInferableQuantizer](weights_inferable_quantizers/weights_pot_inferable_quantizer.py)

[WeightsSymmetricInferableQuantizer](weights_inferable_quantizers/weights_symmetric_inferable_quantizer.py)

[WeightsUniformInferableQuantizer](weights_inferable_quantizers/weights_uniform_inferable_quantizer.py)

Each of them should be used according to the quantization method of the quantizer (power-of-two, symmetric and uniform
quantization respectively).

## Usage Example

The following example demonstrates how to use a weights inferable quantizer:

```python
# Import PyTorch, Numpy and quantizers_infrastructure
import numpy as np
import torch

from model_compression_toolkit import quantizers_infrastructure as qi

# Create a WeightsSymmetricInferableQuantizer quantizer for quantizing a kernel.
# The quantizer uses 8 bits for quantization and quantizes the tensor per channel.
# The quantizer uses three thresholds (1.5, 3, and 4.7) for quantizing each of the three output channels.
# The quantization axis is 3 (the last dimension).
# Notice that for weights we use signed quantization.
quantizer = qi.pytorch_inferable_quantizers.WeightsSymmetricInferableQuantizer(num_bits=8,
                                                                               per_channel=True,
                                                                               threshold=np.asarray([1.5, 3, 4.7]),
                                                                               channel_axis=3)

# Get working device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize a random input to quantize between -50 to 50. Move the tensor to the working device
input_tensor = torch.rand(1, 3, 3, 3).to(device) * 100 - 50

# Quantize tensor
quantized_tensor = quantizer(input_tensor)
print(quantized_tensor)

# The maximal threshold is 4.7 using a signed quantization, so we expect all values to be in this range
assert torch.max(quantized_tensor) < 4.7, f'Quantized values should not contain values greater than maximal threshold'
assert torch.min(quantized_tensor) >= -4.7, f'Quantized values should not contain values lower than minimal threshold'

```

The following example demonstrates how to use an activation inferable quantizer:

```python
# Import PyTorch, Numpy and quantizers_infrastructure
import numpy as np
import torch

from model_compression_toolkit import quantizers_infrastructure as qi

# Create an ActivationSymmetricInferableQuantizer quantizer.
# The quantizer uses 8 bits for quantization and quantizes the tensor per-tensor
# (per-channel quantization is not supported in activation quantizers).
# The quantization is unsigned, meaning the range of values is between 0 and the
# threshold, which is 3.5.
quantizer = qi.pytorch_inferable_quantizers.ActivationSymmetricInferableQuantizer(num_bits=8,
                                                                                  threshold=np.asarray([3.5]),
                                                                                  signed=False)

# Get working device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize a random input to quantize between -50 to 50. Move the tensor to the working device
input_tensor = torch.rand(1, 3, 3, 3).to(device) * 100 - 50

# Quantize tensor
quantized_tensor = quantizer(input_tensor)
print(quantized_tensor)

# The quantization is unsigned with threshold of 3.5 - so quantized tensor values should be between 0 to 3.5
assert torch.max(quantized_tensor) < 3.5, f'Quantized values should not contain values greater than threshold'
assert torch.min(quantized_tensor) >= 0, f'Quantized values should not contain negative values for unsigned quantization'

```

If you have any questions or issues using the Keras inferable quantizers, please [open an issue](https://github.com/sony/model_optimization/issues/new/choose) in this GitHub repository.