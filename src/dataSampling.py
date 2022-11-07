import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

class SequenceGenerator(object):
    
    def __init__(self,input_width,label_width,shift,train_df,test_df,label_column=None):
        
        self.train_df = train_df
        self.test_df = test_df

        self.label_column = label_column
        
        if label_column is not None:
            self.label_columns_indices = {name: i for i, name in enumerate(label_column)}
            
        self.column_indices = {name: i for i, name in enumerate(train_df.columns)}

        self.input_width = input_width
        self.label_width = label_width
        self.shift = shift

        self.total_window_size = input_width + shift

        self.input_slice = slice(0, input_width)
        self.input_indices = np.arange(self.total_window_size)[self.input_slice]

        self.label_start = self.total_window_size - self.label_width
        self.labels_slice = slice(self.label_start, None)
        self.label_indices = np.arange(self.total_window_size)[self.labels_slice]
    
    def __repr__(self):
        
        return '\n'.join([
            f'Total window size: {self.total_window_size}',
            f'Input indices: {self.input_indices}',
            f'Label indices: {self.label_indices}',
            f'Label column name(s): {self.label_column}'])
        
    def split_window(self, features):
        
        inputs = features[:, self.input_slice, :]
        labels = features[:, self.labels_slice, :]
        
        if self.label_column is not None:
            labels = tf.stack([labels[:, :, self.column_indices[name]] for name in self.label_column],axis=-1)
            
        inputs.set_shape([None, self.input_width, None])
        labels.set_shape([None, self.label_width, None])

        return inputs, labels
    
    def make_dataset(self, data):
        
        data = np.array(data, dtype=np.float32)
        
        ds = tf.keras.utils.timeseries_dataset_from_array(
            
            data=data,
            targets=None,
            sequence_length=self.total_window_size,
            sequence_stride=1,
            shuffle=True,
            batch_size=32
        )

        ds = ds.map(self.split_window)

        return ds
    
    def plot(self, model=None, plot_col='Mid', max_subplots=3):
        
        inputs, labels = self.example
        
        plt.figure(figsize=(12, 8))
        plot_col_index = self.column_indices[plot_col]
        
        max_n = min(max_subplots, len(inputs))
        
        for n in range(max_n):
            
            plt.subplot(max_n, 1, n+1)
            plt.ylabel(f'{plot_col} [normed]')
            plt.plot(self.input_indices, inputs[n, :, plot_col_index],label='Inputs', marker='.', zorder=-10)
            

            if self.label_column:
                label_col_index = self.label_columns_indices.get(plot_col, None)
            else:
                label_col_index = plot_col_index

            if label_col_index is None:
                continue

            plt.scatter(self.label_indices, labels[n, :, label_col_index],edgecolors='k', label='Labels', c='#2ca02c', s=64)
            
            if model is not None:
                
                predictions = model(inputs)
                
                plt.scatter(
                            
                    self.label_indices, 
                    predictions[n, :, label_col_index],
                    marker='X', 
                    edgecolors='k', 
                    label='Predictions',
                    c='#ff7f0e', 
                    s=64
                )

            if n == 0:
                plt.legend()

        plt.xlabel('Date')
    
    @property
    def train(self):
        return self.make_dataset(self.train_df)
    
    @property
    def example(self):
        
        """Get and cache an example batch of `inputs, labels` for plotting."""
        
        result = getattr(self, '_example', None)
        
        if result is None:

            result = next(iter(self.train))

            self._example = result
            
        return result

    @property
    def test(self):
        return self.make_dataset(self.test_df)
            
        
    