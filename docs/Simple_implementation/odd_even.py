from base import SortingAlgorithm
from typing import List , Tuple , Dict

class OddEvenSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Odd even sort")
    
    def sort(self , arr:List[int])-> Tuple[List[int] ,int , int ]:
        comparisons = 0
        swaps = 0
        is_sorted = True
        n = len(arr)
        
        while not is_sorted:
            for i in range (0, n-1, 2):
                comparisons += 1
                if arr[i] > arr[i+1]:
                    arr[i] = arr[i+1]
                    arr[i+1] = arr[i]
                    swaps += 1
                    is_sorted = False
                    
            for i in range (1 , n-1 ,2):
                comparisons += 1
                if arr[i] > arr[i+1]:
                    arr[i] = arr[i+1]
                    arr[i+1] = arr[i]
                    swaps += 1
                    is_sorted = False
        
                
        return arr , comparisons , swaps
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n)",
            "average": "O(n^2)",
            "worst": "O(n^2)"
        }

    def get_space_complexity(self) -> str:
        return "O(1)"
    
 