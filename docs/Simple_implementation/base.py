import time
from abc import ABC , abstractmethod
from typing import List , Dict , Tuple , Any


class SortingAlgorithm(ABC):
    
    def __init__(self , name:str):
        self.name = name
        
    @abstractmethod
    def sort(self , arr:List[int])->Tuple[List[int] , int , int]:
        pass
    
    
    @abstractmethod
    def get_time_complexity(self)->Dict[str , str]:
        pass
    
    
    @abstractmethod
    def get_space_complexity(self)-> str:
        pass
    
    def benchmark(self , arr:List[int])-> Dict[str , Any]:
        data = arr.copy()
        start_time = time.perf_counter()
        sorted_arr , comparisons , swaps = self.sort(data)
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time)*1000
        
        return{
           "algorithm" : self.name,
           "sorted_data" : sorted_arr,
           "comparisons" : comparisons,
           "swaps": swaps ,
           "execution_time_ms" : round(execution_time_ms,3),
           "time_complexity" : self.get_time_complexity(),
           "space_complexity" : self.get_space_complexity()
        }
        
    
    