from base import SortingAlgorithm
from typing import List , Tuple , Dict

class SelectionSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Selection sort")
    
    def sort(self , arr:List[int])-> Tuple[List[int] ,int , int ]:
        comparisons = 0
        swaps = 0
        n = len(arr)
        
        for i in range(n):
            min_idx = i
            for j in range(i+1 , n):
                comparisons += 1
                if arr[j] < arr[min_idx]:
                    min_idx = j
            if min_idx!= i:
                arr[i], arr[min_idx] = arr[min_idx], arr[i]
                
                swaps += 1
                
        return arr , comparisons , swaps
    
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n^2)",
            "average": "O(n^2)",
            "worst": "O(n^2)"
        }
        
    def get_space_complexity(self) -> str:
        return "O(1)"
          
                    
                    