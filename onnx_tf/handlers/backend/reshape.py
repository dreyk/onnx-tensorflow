import copy

import tensorflow as tf

from onnx_tf.handlers.backend_handler import BackendHandler
from onnx_tf.handlers.handler import onnx_op
from onnx_tf.handlers.handler import tf_func


@onnx_op("Reshape")
@tf_func(tf.reshape)
class Reshape(BackendHandler):

  @classmethod
  def _common(cls, node, **kwargs):
    tensor = kwargs["tensor_dict"][node.inputs[0]]
    if cls.SINCE_VERSION == 1:
      shape = tf.constant(node.attrs["shape"], dtype=tf.int32)
    else:  # since_version >= 5
      shape = tf.cast(kwargs["tensor_dict"][node.inputs[1]], tf.int32)
    input_shape = tf.shape(tensor, out_type=tf.int32)


    copied_shape = shape
    attrs = copy.deepcopy(node.attrs)
    attrs.pop("shape", None)
    return [
      cls.make_tensor_from_onnx_node(
        node, inputs=[tensor, copied_shape], attrs=attrs, **kwargs)
    ]


  def _common1(cls, node, **kwargs):
    tensor = kwargs["tensor_dict"][node.inputs[0]]
    if cls.SINCE_VERSION == 1:
      shape = tf.constant(node.attrs["shape"], dtype=tf.int32)
    else:  # since_version >= 5
      shape = tf.cast(kwargs["tensor_dict"][node.inputs[1]], tf.int32)
    input_shape = tf.shape(tensor, out_type=tf.int32)

    # Extract indicies of the shape paramter where
    # a copy from the original dimension size is needed.
    copy_indices = tf.squeeze(
        tf.where(tf.equal(shape, tf.constant(0, dtype=tf.int32))), -1)
    copy_indices = tf.cast(copy_indices, tf.int32)
    indices_gathered = tf.gather(input_shape, copy_indices)
    indices_gathered = tf.cast(indices_gathered, tf.int32)
    indices_scattered = tf.sparse_to_dense(copy_indices,
                                           tf.cast(tf.shape(shape), tf.int32),
                                           indices_gathered)

    # Perform the copy wherever requested (wherever dim_size == 0)
    copied_shape = shape + indices_scattered
    attrs = copy.deepcopy(node.attrs)
    attrs.pop("shape", None)
    return [
        cls.make_tensor_from_onnx_node(
            node, inputs=[tensor, copied_shape], attrs=attrs, **kwargs)
    ]

  @classmethod
  def version_1(cls, node, **kwargs):
    return cls._common(node, **kwargs)

  @classmethod
  def version_5(cls, node, **kwargs):
    return cls._common(node, **kwargs)
