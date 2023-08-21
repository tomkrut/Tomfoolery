#! /usr/bin/env python
from PyQt6.QtCore import QRunnable, QObject, pyqtSlot, pyqtSignal
from .scrape_common import console_output
import textwrap


def emit_signal(kwargs, signal, args=[]):
  
    if sig:=kwargs.get(signal):
        sig.emit(*args)  
    else:
        raise ValueError(f'Missing signal in the kwargs: {signal}.')

class WorkerSlots:

    def __init__(self, **kwargs): 

        super().__init__(**kwargs)       

        self.progressbars = None
        self.tableWidget = None
        self.checkboxes = None
        self.messageboxes = None        

    def progressBarSet(self, idx, value):

        pbar = self.progressbars[idx]   
        pbar.setValue(value)

    def progressBarInit(self, idx, max):
      
        pbar = self.progressbars[idx]                         
        pbar.reset()       
        pbar.setMaximum(max)     

    def checkBoxSet(self, idx, state):

        self.checkboxes[idx].setChecked(state)
   
    def messageBoxSet(self, idx, txt):

        wrapped_txt = ('\n').join(textwrap.wrap(txt, 40))
        self.messageboxes[idx].setText(wrapped_txt)
        console_output(txt)


class initWorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    '''
    unavailable_for_scraping = pyqtSignal(int)
    worker_finished = pyqtSignal() 
    worker_error = pyqtSignal(object)

class execWorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    '''
    resize_window = pyqtSignal() 
    checkbox_set = pyqtSignal(int, bool)
    messagebox_set = pyqtSignal(int, str) 
    progress_init = pyqtSignal(int, int)    
    progress_set = pyqtSignal(int, int)
    worker_finished = pyqtSignal() # currently unused
    worker_error = pyqtSignal(object)  


class execWorker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''
    def __init__(self, fn, *args, **kwargs):
        super(execWorker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = execWorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_init'] = self.signals.progress_init
        self.kwargs['progress_set'] = self.signals.progress_set        
        self.kwargs['resize_window'] = self.signals.resize_window
        self.kwargs['checkbox_set'] = self.signals.checkbox_set
        self.kwargs['messagebox_set'] = self.signals.messagebox_set   
        
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''        
        try:
            ret = self.fn(*self.args, **self.kwargs) 
        except Exception as e:
            try: 
                emit_signal(self.kwargs, 'messagebox_set', [e.idx, str(e)]) 
                emit_signal(self.kwargs, 'progress_init', [e.idx, 100])    
                emit_signal(self.kwargs, 'resize_window')
            except AttributeError:
                pass
            self.signals.worker_error.emit(e)
            return
        self.signals.worker_finished.emit()

class initWorker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''
    def __init__(self, fn, *args, **kwargs):
        super(initWorker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = initWorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['unavailable_for_scraping'] = self.signals.unavailable_for_scraping      
        
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''           
        try:
            self.fn(*self.args, **self.kwargs) 
        except Exception as e:
            try: 
                emit_signal(self.kwargs, 'messagebox_set', [e.idx, str(e)]) 
                emit_signal(self.kwargs, 'progress_init', [e.idx, 100])    
                emit_signal(self.kwargs, 'resize_window')
            except AttributeError:
                pass
            self.signals.worker_error.emit(e)            
            return
        self.signals.worker_finished.emit()       
        