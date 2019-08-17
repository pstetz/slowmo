import tensorflow as tf

class Model:
    def __init__(self):
        # Add ops to save and restore all the variables.
        self.saver = tf.train.Saver()

    
    def run(self):
        pass
    
    def load_model(self, model_path):
        """
        More information on loading models can be found here:
        https://www.tensorflow.org/guide/saved_model
        """
        with tf.Session() as sess:
            # Restore variables from disk.
            self.saver.restore(sess, model_path)
            print("Model restored.")
            # Check the values of the variables
            print("v1 : %s" % v1.eval())
            print("v2 : %s" % v2.eval())
    
    def save_model(self, save_path):
        """
        More information on saving models can be found here:
        https://www.tensorflow.org/guide/saved_model
        """
        with tf.Session() as sess:
            sess.run(init_op)
            # Do some work with the model.
            inc_v1.op.run()
            dec_v2.op.run()
            
            # Save the variables to disk.
            self.saver.save(sess, save_path)
            print("Model saved to path: %s" % save_path)
