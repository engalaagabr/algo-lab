from base import SortingAlgorithm
from typing import List , Tuple , Dict

class CocktailSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Cocktail sort")
        
    def sort(self , arr:List[int])-> Tuple[List[int] ,int , int ]:
           comparisons = 0
           swaps = 0
           n = len(arr)
           start = 0
           end = n - 1
           swapped = True
           
           while swapped:
               swapped = False
               for i in range (start , end):
                   comparisons += 1
                   
                   if arr[i] > arr[i+1]:
                       arr[i] = arr[i+1]
                       arr[i+1] = arr[i]
                       swaps += 1
                       swapped = True
                       
               if not swapped:
                   break
               
               swapped = False
               end -= 1
               
               
               for i in range (start-1 , end-1 , -1):
                   comparisons += 1
                   if arr[i] > arr[i+1]:
                       arr[i] = arr[i+1]
                       arr[i+1] = arr[i]
                       swaps += 1
                       swapped = True
                       
               start += 1
               
           return arr , comparisons , swaps
       
    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n)",
            "average": "O(n^2)",
            "worst": "O(n^2)"
        }

    def get_space_complexity(self) -> str:
        return "O(1)"
                       