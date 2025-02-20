# Copyright 2021 Sony Semiconductor Israel, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
from enum import Enum
from typing import Callable, Any, Dict
from model_compression_toolkit.core.common.defaultdict import DefaultDict
from model_compression_toolkit.core import common
from model_compression_toolkit.gptq.common.gptq_constants import N_BATCHES_STR, QUANT_PARAM_LEARNING_STR, N_EPOCHS_STR, \
    MAX_LSB_STR
from model_compression_toolkit.gptq.common.gptq_quantizer_config import GPTQQuantizerConfig, SoftQuantizerConfig


class RoundingType(Enum):
    """
    An enum for choosing the GPTQ rounding methods
    0. STRAIGHT-THROUGH ESTIMATOR
    1. SoftQuantizer
    """
    STE = 0
    SoftQuantizer = 1


class GradientPTQConfig:
    """
    Configuration to use for quantization with GradientPTQ (experimental).
    """

    def __init__(self,
                 n_iter: int,
                 optimizer: Any,
                 optimizer_rest: Any = None,
                 loss: Callable = None,
                 log_function: Callable = None,
                 train_bias: bool = True,
                 quantization_parameters_learning: bool = False,
                 rounding_type: RoundingType = RoundingType.SoftQuantizer,
                 lsb_change_per_bit_width: dict = DefaultDict({}, lambda: 1),
                 eps: float = 1e-6,
                 use_jac_based_weights: bool = True,
                 num_samples_for_loss: int = 16,
                 norm_weights: bool = False,
                 optimizer_quantization_parameter: Any = None,
                 optimizer_bias: Any = None,
                 log_norm: bool = True,
                 weights_n_iter: int = 50,
                 quantizer_config: GPTQQuantizerConfig = SoftQuantizerConfig()):
        """
        Initialize a GradientPTQConfig.

        Args:
            n_iter (int): Number of iterations to train.
            optimizer (Any): Optimizer to use.
            optimizer_rest (Any): Optimizer to use for bias and quantizer parameters.
            loss (Callable): The loss to use. should accept 6 lists of tensors. 1st list of quantized tensors, the 2nd list is the float tensors,
             the 3rd is a list of quantized weights, the 4th is a list of float weights, the 5th and 6th lists are the mean and std of the tensors
             accordingly. see example in multiple_tensors_mse_loss
            log_function (Callable): Function to log information about the GPTQ process.
            train_bias (bool): Whether to update the bias during the training or not.
            quantization_parameters_learning (bool): Whether to update the quantization param during the training or not.
            rounding_type (RoundingType): An enum that defines the rounding type.
            lsb_change_per_bit_width (dict): Whether to update the bias during the training or not.
            eps (float): A floating point value for numeric stability.
            use_jac_based_weights (bool): Whether to use jacobian-based weights for weighted average loss.
            num_samples_for_loss (int): Number of samples to use for computing the jacobian-based weights.
            norm_weights (bool): Whether to normalize the returned weights (to get values between 0 and 1).
            optimizer_quantization_parameter (Any): Optimizer to override the rest optimizer  for quantizer parameters.
            optimizer_bias (Any): Optimizer to override the rest optimizer for bias.
            log_norm (bool): Whether to use log normalization to the GPTQ Jacobian-based weights.
            weights_n_iter (int): Number of random iterations to run Jacobian approximation for GPTQ weights.
            quantizer_config (GPTQQuantizerConfig): A class that contains the quantizer specific config.

        """
        self.n_iter = n_iter
        self.optimizer = optimizer
        self.optimizer_rest = optimizer_rest
        self.loss = loss
        self.log_function = log_function
        self.train_bias = train_bias

        if quantization_parameters_learning and rounding_type == RoundingType.STE:
            common.Logger.error("Quantization parameters learning is not supported with STE rounding.")

        self.quantization_parameters_learning = quantization_parameters_learning
        self.rounding_type = rounding_type
        self.lsb_change_per_bit_width = lsb_change_per_bit_width
        self.eps = eps
        self.use_jac_based_weights = use_jac_based_weights
        self.num_samples_for_loss = num_samples_for_loss
        self.norm_weights = norm_weights
        self.optimizer_quantization_parameter = optimizer_quantization_parameter
        self.optimizer_bias = optimizer_bias
        self.log_norm = log_norm
        self.weights_n_iter = weights_n_iter

        if self._verify_quantizer_config(quantizer_config, rounding_type):
            self.quantizer_config = quantizer_config
        else:
            common.Logger.error(f"Quantizer config of type {type(quantizer_config)} "
                                f"is not suitable for rounding type {rounding_type}")

    def _verify_quantizer_config(self, quantizer_config, rounding_type) -> bool:
        """
        Verifies that the given quantizer config matches the given rounding type.

        Args:
            quantizer_config: A quantizer config.
            rounding_type: A RoundingType.

        Returns: True if the quantizer config matches the rounding type, False otherwise.

        """
        if rounding_type == RoundingType.SoftQuantizer:
            return type(quantizer_config) == SoftQuantizerConfig

        # Here, we compare type() and not isinstance to exclude instance equality because of inheritance
        return type(quantizer_config) == GPTQQuantizerConfig


class GradientPTQConfigV2(GradientPTQConfig):
    """
    Configuration to use for quantization with GradientPTQV2 (experimental).
    """
    def __init__(self,
                 n_epochs: int,
                 optimizer: Any,
                 optimizer_rest: Any = None,
                 loss: Callable = None,
                 log_function: Callable = None,
                 train_bias: bool = True,
                 quantization_parameters_learning: bool = False,
                 rounding_type: RoundingType = RoundingType.SoftQuantizer,
                 lsb_change_per_bit_width: dict = DefaultDict({}, lambda: 1),
                 eps: float = 1e-6,
                 use_jac_based_weights: bool = True,
                 num_samples_for_loss: int = 16,
                 norm_weights: bool = False,
                 optimizer_quantization_parameter: Any = None,
                 optimizer_bias: Any = None,
                 log_norm: bool = True,
                 weights_n_iter: int = 50,
                 quantizer_config: GPTQQuantizerConfig = SoftQuantizerConfig()):
        """
        Initialize a GradientPTQConfigV2.

        Args:
            n_epochs (int): Number of representative dataset epochs to train.
            optimizer (Any): Optimizer to use.
            optimizer_rest (Any): Optimizer to use for bias and quantizer parameters.
            loss (Callable): The loss to use. should accept 6 lists of tensors. 1st list of quantized tensors, the 2nd list is the float tensors,
             the 3rd is a list of quantized weights, the 4th is a list of float weights, the 5th and 6th lists are the mean and std of the tensors
             accordingly. see example in multiple_tensors_mse_loss
            log_function (Callable): Function to log information about the GPTQ process.
            train_bias (bool): Whether to update the bias during the training or not.
            quantization_parameters_learning (bool): Whether to update the quantization param during the training or not.
            rounding_type (RoundingType): An enum that defines the rounding type.
            lsb_change_per_bit_width (dict): Whether to update the bias during the training or not.
            eps (float): A floating point value for numeric stability.
            use_jac_based_weights (bool): Whether to use jacobian-based weights for weighted average loss.
            num_samples_for_loss (int): Number of samples to use for computing the jacobian-based weights.
            norm_weights (bool): Whether to normalize the returned weights (to get values between 0 and 1).
            optimizer_quantization_parameter (Any): Optimizer to override the rest optimizer  for quantizer parameters.
            optimizer_bias (Any): Optimizer to override the rest optimizerfor bias.
            log_norm (bool): Whether to use log normalization to the GPTQ Jacobian-based weights.
            weights_n_iter (int): Number of random iterations to run Jacobian approximation for GPTQ weights.
            quantizer_config (Any): A class that contains the quantizer specific config.

        """

        super().__init__(n_iter=None,
                         optimizer=optimizer,
                         optimizer_rest=optimizer_rest,
                         loss=loss,
                         log_function=log_function,
                         train_bias=train_bias,
                         quantization_parameters_learning=quantization_parameters_learning,
                         rounding_type=rounding_type,
                         lsb_change_per_bit_width=lsb_change_per_bit_width,
                         eps=eps,
                         use_jac_based_weights=use_jac_based_weights,
                         num_samples_for_loss=num_samples_for_loss,
                         norm_weights=norm_weights,
                         optimizer_quantization_parameter=optimizer_quantization_parameter,
                         optimizer_bias=optimizer_bias,
                         log_norm=log_norm,
                         weights_n_iter=weights_n_iter,
                         quantizer_config=quantizer_config)
        self.n_epochs = n_epochs

    @classmethod
    def from_v1(cls, n_ptq_iter: int, config_v1: GradientPTQConfig):
        """
        Initialize a GradientPTQConfigV2 from GradientPTQConfig instance.

        Args:
            n_ptq_iter (int): Number of PTQ calibration iters (length of representative dataset).
            config_v1 (GradientPTQConfig): A GPTQ config to convert to V2.

        """
        n_epochs = int(round(config_v1.n_iter) / n_ptq_iter)
        v1_params = config_v1.__dict__
        v1_params = {k: v for k, v in v1_params.items() if k != 'n_iter'}
        return cls(n_epochs, **v1_params)

    def get_extended_quantizer_parametes(self) -> Dict[str, Any]:
        """
        Return a dictionary with a mapping to necessary additional parameters for initializing the GPTQ quantizer.

        Returns: A dictionary with parameters for initializing a quantizer.

        """

        if self.rounding_type == RoundingType.SoftQuantizer:
            return {N_BATCHES_STR: self.quantizer_config.n_batches,
                    QUANT_PARAM_LEARNING_STR: self.quantization_parameters_learning,
                    N_EPOCHS_STR: self.n_epochs}
        elif self.rounding_type == RoundingType.STE:
            return {MAX_LSB_STR: self.lsb_change_per_bit_width}

        return {}


