# Copyright 2023 Sony Semiconductor Israel, Inc. All rights reserved.
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

from model_compression_toolkit import qunatizers_infrastructure as qi
from model_compression_toolkit.core.common import BaseNode
from model_compression_toolkit.core.keras.default_framework_info import DEFAULT_KERAS_INFO
from model_compression_toolkit.exporter.model_wrapper.keras.builder.node_to_quantizer import \
    get_weights_quantizer_for_node, get_activations_quantizer_for_node


def get_quantization_dispatcher(node: BaseNode) -> qi.KerasNodeQuantizationDispatcher:
    """
    Create a KerasNodeQuantizationDispatcher to wrap a layer for its corresponding node.

    Args:
        node: Node to create a KerasNodeQuantizationDispatcher for.

    Returns:
        KerasNodeQuantizationDispatcher to use for wrapping the layer from the passed node.
    """
    weight_quantizers = {}
    activation_quantizers = []

    if node.is_weights_quantization_enabled():
        weight_attrs = DEFAULT_KERAS_INFO.get_kernel_op_attributes(node.type)
        weight_quantizer = get_weights_quantizer_for_node(node)
        for attr in weight_attrs:
            weight_quantizers[attr] = weight_quantizer

    if node.is_activation_quantization_enabled():
        num_of_outputs = len(node.output_shape) if isinstance(node.output_shape, list) else 1
        activation_quantizers = [get_activations_quantizer_for_node(node)] * num_of_outputs

    dispatcher = qi.KerasNodeQuantizationDispatcher(weight_quantizers,
                                                    activation_quantizers)

    return dispatcher
