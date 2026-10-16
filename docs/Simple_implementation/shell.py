from base import SortingAlgorithm
from typing import List , Tuple , Dict

class ShellSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Shell sort")
        
    def sort(self , arr:List[int])-> Tuple[List[int] ,int , int ]:
        comparisons = 0
        swaps = 0
        n = len(arr)
        
        gap = n // 2
        while gap >0:
            for i in range (gap , n):
               temp = arr[i]
               j = i
               
               while j >= gap:
                    comparisons += 1
                    if arr[j - gap] > temp:
                        arr[j] = arr[j - gap]
                        swaps += 1
                        j -= gap
                    else:
                        break
                    
               if j >= gap:
                    comparisons += 1
                    
               arr[j] = temp
            gap //=2
            
        return arr, comparisons, swaps
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n log n)",
            "average": "O(n^2)",  
            "worst": "O(n^2)"
        }

    def get_space_complexity(self) -> str:
        return "O(1)"  
                
                