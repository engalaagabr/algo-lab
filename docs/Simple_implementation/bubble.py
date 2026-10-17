from base import SortingAlgorithm
from typing import List , Tuple , Dict

class BubbleSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Bubble sort")
        
    def sort(self , arr:List[int])-> Tuple[List[int] ,int , int ]:
           comparisons = 0
           swaps = 0
           n = len(arr)
           for i in range (n):
               swapped = False
               for j in range (0 , n-i-1):
                   comparisons += 1
                   if arr[j] > arr[j+1]:
                       arr[j], arr[j + 1] = arr[j + 1], arr[j]
                        
                       swaps += 1
                       swapped = True                      
               if not swapped:
                    break
           return arr , comparisons , swaps    
        
        
    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n)",
            "average": "O(n^2)",
            "worst": "O(n^2)"
        }

    def get_space_complexity(self) -> str:
        return "O(1)"
                       
        