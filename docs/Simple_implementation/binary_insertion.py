from base import SortingAlgorithm
from typing import List, Dict, Tuple
import bisect

class BinaryInsertionSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Binary Insertion Sort")
        
    def sort(self , arr :List[int])-> Tuple[List[int] , int , int]:
        comparisons = 0
        swaps = 0
        n = len(arr)
        
        for i in range (1 , n):
            key =  arr[i]
            left = 0
            right = i    
            while(left < right):
                mid = (left + right)//2
                comparisons += 1
                if arr[mid] > key:
                    right = mid
                else:
                    left = mid + 1
                    
            for j in range(i , left , -1):
                arr[j] = arr[j-1]
                swaps += 1
                
            arr[left] = key
                 
        return arr, comparisons , swaps
    
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {
            "best": "O(n log n)",
            "average": "O(n^2)",
            "worst": "O(n^2)"
        }

    def get_space_complexity(self) -> str:
        return "O(1)"