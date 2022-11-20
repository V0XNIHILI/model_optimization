# Copyright 2022 Sony Semiconductor Israel, Inc. All rights reserved.
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
import copy
from abc import ABC
from typing import Callable, List, Tuple

import numpy as np
import tensorflow as tf

import model_compression_toolkit as mct
from model_compression_toolkit import CoreConfig, QuantizationConfig, DEFAULTCONFIG, FrameworkInfo, DebugConfig
from model_compression_toolkit import get_target_platform_capabilities
from model_compression_toolkit.core.common import Graph
from model_compression_toolkit.core.common.constants import TENSORFLOW
from model_compression_toolkit.core.common.network_editors import EditRule
from model_compression_toolkit.core.common.statistics_correction.apply_second_moment_correction_to_graph import \
    quantized_model_builder_for_second_moment_correction
from model_compression_toolkit.core.common.target_platform import QuantizationMethod, TargetPlatformCapabilities
from model_compression_toolkit.core.keras.constants import DEFAULT_TP_MODEL
from model_compression_toolkit.core.keras.constants import EPSILON_VAL, GAMMA, BETA, MOVING_MEAN, MOVING_VARIANCE
from model_compression_toolkit.core.keras.default_framework_info import DEFAULT_KERAS_INFO
from model_compression_toolkit.core.keras.keras_implementation import KerasImplementation
from model_compression_toolkit.core.keras.keras_model_validation import KerasModelValidation
from model_compression_toolkit.core.keras.statistics_correction.apply_second_moment_correction import \
    keras_apply_second_moment_correction
from model_compression_toolkit.core.runner import _init_tensorboard_writer, core_runner
from model_compression_toolkit.core.tpc_models.default_tpc.latest import generate_keras_tpc
from tests.common_tests.helpers.generate_test_tp_model import generate_test_tp_model
from tests.keras_tests.feature_networks_tests.base_keras_feature_test import BaseKerasFeatureNetworkTest

DEFAULT_KERAS_TPC = get_target_platform_capabilities(TENSORFLOW, DEFAULT_TP_MODEL)
from tensorflow.keras.models import Model

keras = tf.keras
layers = keras.layers
tp = mct.target_platform


class BaseSecondMomentTest(BaseKerasFeatureNetworkTest, ABC):
    """
    This is the base test for the Second Moment Correction feature.
    """

    def __init__(self, unit_test):
        super(BaseSecondMomentTest, self).__init__(unit_test=unit_test, val_batch_size=128, input_shape=(32, 32, 1))

    def get_tpc(self):
        tp = generate_test_tp_model({'weights_n_bits': 16,
                                     'activation_n_bits': 16,
                                     'weights_quantization_method': QuantizationMethod.SYMMETRIC})
        return generate_keras_tpc(name="second_moment_correction_test", tp_model=tp)

    def get_quantization_config(self):
        return mct.QuantizationConfig(weights_second_moment_correction=True, weights_second_moment_iters=200)

    def compare(self, quantized_model, float_model, input_x=None, quantization_info=None):
        quantized_model_kernel = quantized_model.layers[2].weights[0]
        quantized_model_bias = quantized_model.layers[2].weights[1]
        float_model_gamma = float_model.layers[2].weights[0]
        float_model_beta = float_model.layers[2].weights[1]
        float_model_kernel = float_model.layers[1].weights[0]
        float_model_bias = float_model.layers[1].weights[1]
        input_var = np.var(self.inp)
        input_mean = np.mean(self.inp)
        eps = EPSILON_VAL
        weight_scale = np.sqrt(float_model_gamma + eps) / np.sqrt(input_var + eps)

        # new_kernel = kernel * gamma/sqrt(moving_var+eps)
        # new_bias = beta + (bias - moving_mean) * *gamma/sqrt(moving_var+eps)
        calculated_kernel = float_model_kernel * weight_scale
        calculated_bias = float_model_beta + (float_model_bias - input_mean) * weight_scale

        self.unit_test.assertTrue(np.isclose(quantized_model_kernel, calculated_kernel, atol=1e-1))
        self.unit_test.assertTrue(np.isclose(quantized_model_bias, calculated_bias, atol=1e-1))

    def generate_inputs(self):
        # We want to keep the same input in order to stabilize the input's statistics
        if self.i == 0:
            self.inp = [np.random.normal(scale=0.5, loc=8.0, size=in_shape) for in_shape in self.get_input_shapes()]
            self.i += 1
        return self.inp


class DepthwiseConv2DSecondMomentTest(BaseSecondMomentTest):
    """
    This is the test for the Second Moment Correction feature with DepthwiseConv2D.
    """

    def __init__(self, unit_test):
        self.i = 0
        super().__init__(unit_test)

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.DepthwiseConv2D((1, 1), padding='same',
                                   depthwise_initializer='ones',
                                   kernel_initializer="ones",
                                   bias_initializer="zeros")(inputs)
        x = layers.BatchNormalization(
            beta_initializer="zeros",
            gamma_initializer="ones",
            moving_mean_initializer="zeros",
            moving_variance_initializer="ones")(x)
        x = layers.Activation('relu')(x)
        return tf.keras.models.Model(inputs=inputs, outputs=x)


class DepthwiseConv2DWithMultiplierSecondMomentTest(BaseSecondMomentTest):
    """
    This is the test for the Second Moment Correction feature with DepthwiseConv2D with multiplier.
    """

    def __init__(self, unit_test):
        self.i = 0
        super().__init__(unit_test)

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.DepthwiseConv2D((1, 1), padding='same',
                                   depthwise_initializer='ones',
                                   kernel_initializer="ones",
                                   bias_initializer="zeros", depth_multiplier=3)(inputs)
        x = layers.BatchNormalization(
            beta_initializer="zeros",
            gamma_initializer="ones",
            moving_mean_initializer="zeros",
            moving_variance_initializer="ones")(x)
        x = layers.Activation('relu')(x)
        return tf.keras.models.Model(inputs=inputs, outputs=x)


class Conv2DSecondMomentTest(BaseSecondMomentTest):
    """
    This is the test for the Second Moment Correction feature with Conv2d.
    """

    def __init__(self, unit_test):
        self.i = 0
        super().__init__(unit_test)

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.Conv2D(1, 1, padding='same',
                          kernel_initializer="ones",
                          bias_initializer="zeros")(inputs)
        x = layers.BatchNormalization(
            beta_initializer="zeros",
            gamma_initializer="ones",
            moving_mean_initializer="zeros",
            moving_variance_initializer="ones")(x)
        x = layers.Activation('relu')(x)
        return tf.keras.models.Model(inputs=inputs, outputs=x)


class Conv2DTSecondMomentTest(BaseSecondMomentTest):
    """
    This is the test for the Second Moment Correction feature with Conv2DTranspose.
    """

    def __init__(self, unit_test):
        self.i = 0
        super().__init__(unit_test)

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.Conv2DTranspose(1, 1, padding='same',
                                   kernel_initializer="ones",
                                   bias_initializer="zeros")(inputs)
        x = layers.BatchNormalization(
            beta_initializer="zeros",
            gamma_initializer="ones",
            moving_mean_initializer="zeros",
            moving_variance_initializer="ones")(x)
        x = layers.Activation('relu')(x)
        return tf.keras.models.Model(inputs=inputs, outputs=x)


class ValueSecondMomentTest(BaseSecondMomentTest):
    """
    This is the test for the Second Moment Correction feature.
    This test check that the gamma&beta values of the reconstructed BN didn't change during second moment application.
    """

    def __init__(self, unit_test):
        self.i = 0
        super().__init__(unit_test)

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.Conv2D(1, 1, padding='same',
                          kernel_initializer="ones",
                          bias_initializer="zeros")(inputs)
        x = layers.BatchNormalization(
            beta_initializer="zeros",
            gamma_initializer="ones",
            moving_mean_initializer="zeros",
            moving_variance_initializer="ones")(x)
        x = layers.Activation('relu')(x)
        return tf.keras.models.Model(inputs=inputs, outputs=x)

    def run_test(self, experimental_facade=False, experimental_exporter=False):
        feature_networks = self.create_networks()
        feature_networks = feature_networks if isinstance(feature_networks, list) else [feature_networks]
        for model_float in feature_networks:
            qc = self.get_quantization_config()
            tg, graph_after_second_moment_correction = self.prepare_graph(model_float,
                                                                          self.representative_data_gen,
                                                                          quant_config=qc,
                                                                          fw_info=self.get_fw_info(),
                                                                          network_editor=self.get_network_editor(),
                                                                          target_platform_capabilities=self.get_tpc())
            for node in graph_after_second_moment_correction.nodes:
                if node.layer_class == layers.BatchNormalization:
                    bf_second_moment_node = tg.find_node_by_name(node.name)[0]

                    gamma0 = bf_second_moment_node.get_weights_by_keys(GAMMA)
                    beta0 = bf_second_moment_node.get_weights_by_keys(BETA)
                    moving_mean0 = bf_second_moment_node.get_weights_by_keys(MOVING_MEAN)
                    moving_variance0 = bf_second_moment_node.get_weights_by_keys(MOVING_VARIANCE)

                    gamma1 = node.get_weights_by_keys(GAMMA)
                    beta1 = node.get_weights_by_keys(BETA)
                    moving_mean1 = node.get_weights_by_keys(MOVING_MEAN)
                    moving_variance1 = node.get_weights_by_keys(MOVING_VARIANCE)

                    # check that gamma&beta didn't change
                    self.unit_test.assertTrue(gamma0 == gamma1)
                    self.unit_test.assertTrue(beta0 == beta1)

                    # check that moving_mean&moving_variance did change
                    self.unit_test.assertFalse(moving_mean0 == moving_mean1)
                    self.unit_test.assertFalse(moving_variance0 == moving_variance1)

    def prepare_graph(self,
                      in_model: Model,
                      representative_data_gen: Callable,
                      quant_config: QuantizationConfig = DEFAULTCONFIG,
                      fw_info: FrameworkInfo = DEFAULT_KERAS_INFO,
                      network_editor: List[EditRule] = [],
                      analyze_similarity: bool = False,
                      target_platform_capabilities: TargetPlatformCapabilities = DEFAULT_KERAS_TPC) -> \
            Tuple[Graph, Graph]:

        KerasModelValidation(model=in_model,
                             fw_info=fw_info).validate()

        core_config = CoreConfig(quantization_config=quant_config,
                                 debug_config=DebugConfig(analyze_similarity=analyze_similarity,
                                                          network_editor=network_editor)
                                 )

        tb_w = _init_tensorboard_writer(fw_info)

        fw_impl = KerasImplementation()

        tg, bit_widths_config = core_runner(in_model=in_model,
                                            representative_data_gen=representative_data_gen,
                                            core_config=core_config,
                                            fw_info=fw_info,
                                            fw_impl=fw_impl,
                                            tpc=target_platform_capabilities,
                                            tb_w=tb_w)
        graph_to_apply_second_moment = copy.deepcopy(tg)
        semi_quantized_model = quantized_model_builder_for_second_moment_correction(graph_to_apply_second_moment,
                                                                                    fw_info, fw_impl)
        keras_apply_second_moment_correction(semi_quantized_model, core_config, representative_data_gen,
                                             graph_to_apply_second_moment)

        return tg, graph_to_apply_second_moment
