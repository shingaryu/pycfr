# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 08:44:49 2020

@author: Koki
"""

import matplotlib.pyplot as plt
import numpy as np

def plot_multiple_y(x, x_label, y_list, y_legends, y_label, title):
  for (y, legend) in zip(y_list, y_legends):            
      plt.plot(x, y, label=legend)  

  plt.xlabel(x_label)
  plt.ylabel(y_label)
  plt.title(title)
  plt.legend()
  plt.show()

def matplotlib_example():
    x = np.linspace(0, 2, 100)
    x = [ x for x in range(20)]
    
    plt.plot(x, x, label='linear')  # Plot some data on the (implicit) axes.
    #plt.plot(x, x**2, label='quadratic')  # etc.
    plt.plot(x, [_x**2 for _x in x], label='quadratic')  # etc.
    #plt.plot(x, x**3, label='cubic')
    plt.plot(x, [_x**3 for _x in x], label='cubic')
    plt.xlabel('x label')
    plt.ylabel('y label')
    plt.title("Simple Plot")
    plt.legend()
    
if __name__ == "__main__":   
  x = [ x for x in range(20)]
  num_y = 4
  x_label = 'x label'
  y_list = [ [val**(i) for val in x] for i in range(num_y) ]
  y_legends = [ 'x^{0}'.format(i) for i in range(num_y) ]
  y_label = 'y label'
  plot_multiple_y(x, x_label, y_list, y_legends, y_label, 'sample plot')