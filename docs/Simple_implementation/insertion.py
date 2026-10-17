from base import SortingAlgorithm
from typing import List , Tuple , Dict

class InsertionSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Insertion sort")
    
    def sort(self , arr:List[int])-> Tuple[List[int] ,int , int ]:
        comparisons = 0
        swaps = 0
        n = len(arr)
        for i in range (1 , n):
            key = arr[i]
            j = i - 1
            while j >= 0:
                comparisons+=1
                if arr[j] > key:
                    arr[j+1] = arr[j]
                    swaps += 1
                    j-=1
                else:
                    break
            arr[j+1] = key
                               
        return arr , comparisons , swaps
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {"best": "O(n)", "average": "O(n^2)", "worst": "O(n^2)"}

    def get_space_complexity(self) -> str:
        return "O(1)"
